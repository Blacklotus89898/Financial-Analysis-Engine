import argparse
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql import functions as F

def create_spark(app_name="SilverProcessing"):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark

def process_silver(spark, mode="batch"):
    # Schema
    schema = "ticker STRING, price DOUBLE, timestamp LONG, source STRING"

    # 1️⃣ Read Bronze Data
    if mode == "stream":
        df = spark.readStream.schema(schema).parquet("datalake/bronze")
    else:
        df = spark.read.schema(schema).parquet("datalake/bronze")

    # 2️⃣ Deduplicate
    df_clean = df.dropDuplicates(["ticker", "timestamp"])

    if mode == "batch":
        # Batch mode: row-based rolling window (SMA_5, volatility)
        window_spec = Window.partitionBy("ticker").orderBy("timestamp")
        df_features = df_clean.withColumn(
            "SMA", F.avg("price").over(window_spec.rowsBetween(-4, 0))
        ).withColumn(
            "volatility", F.stddev("price").over(window_spec.rowsBetween(-4, 0))
        ).withColumn(
            "window_start", F.from_unixtime("timestamp")
        ).withColumn(
            "window_end", F.from_unixtime("timestamp")
        )

        # Write batch output
        df_features.select("ticker", "SMA", "volatility", "window_start", "window_end") \
            .write.mode("overwrite").parquet("datalake/silver")

        print("✅ Batch Silver Layer Processing Complete.")
        df_features.show(5)

    else:
        # Streaming mode: time-based window aggregation
        df_stream = df_clean.withColumn("ts", F.from_unixtime("timestamp").cast("timestamp"))

        # Add watermark: lets Spark handle late data up to 2 minutes
        df_stream = df_stream.withWatermark("ts", "2 minutes")

        df_features = df_stream.groupBy(
            "ticker",
            F.window("ts", "1 minute", "30 seconds")
        ).agg(
            F.avg("price").alias("SMA"),
            F.stddev("price").alias("volatility")
        ).select(
            "ticker",
            "SMA",
            "volatility",
            F.col("window.start").alias("window_start"),
            F.col("window.end").alias("window_end")
        )

        # Write streaming output
        query = df_features.writeStream \
            .format("parquet") \
            .option("path", "datalake/silver") \
            .option("checkpointLocation", "datalake/checkpoints/silver") \
            .outputMode("append") \
            .start()

        print("🔥 Streaming Silver Layer started...")
        query.awaitTermination()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Silver Layer Processing")
    parser.add_argument(
        "--mode", type=str, default="batch",
        choices=["batch", "stream"],
        help="Mode to run the pipeline: batch or stream"
    )
    args = parser.parse_args()

    spark = create_spark()
    process_silver(spark, mode=args.mode)