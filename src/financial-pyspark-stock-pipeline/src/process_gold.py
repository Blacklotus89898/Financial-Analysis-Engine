# process_gold.py
import matplotlib.pyplot as plt
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

def create_spark(app_name="GoldProcessing"):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark

def process_gold(spark):
    df = spark.read.parquet("datalake/silver/*.parquet")
    # df = spark.read.option("ignoreMetadata", "true").parquet("datalake/silver")
    # df = spark.read.parquet("datalake/silver")

    # Drop rows with null SMA/volatility
    df = df.na.drop(subset=["SMA","volatility"])

    # Aggregate Gold features
    df_gold = df.groupBy("ticker").agg(
        F.avg("SMA").alias("avg_SMA"),
        F.avg("volatility").alias("avg_volatility")
    )
    df_gold.write.mode("overwrite").parquet("datalake/gold")
    print("✅ Gold Layer Processing Complete.")
    df_gold.show()

    # Visualization
    pdf = df.select("ticker","window_start","SMA","volatility").toPandas()
    for ticker in pdf["ticker"].unique():
        subset = pdf[pdf["ticker"] == ticker]
        plt.figure(figsize=(12,6))
        plt.plot(subset["window_start"], subset["SMA"], label="SMA", linewidth=2)
        plt.fill_between(
            subset["window_start"],
            subset["SMA"] - subset["volatility"],
            subset["SMA"] + subset["volatility"],
            color="gray", alpha=0.2, label="Volatility Band"
        )
        plt.title(f"{ticker} SMA with Volatility Band")
        plt.xlabel("Time Window Start")
        plt.ylabel("Price")
        plt.legend()
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    spark = create_spark()
    process_gold(spark)