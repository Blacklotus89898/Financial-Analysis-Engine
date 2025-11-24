from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, DoubleType, LongType

import pyspark
print("PySpark version:", pyspark.__version__)

# Schema matches the Producer JSON
schema = StructType() \
    .add("ticker", StringType()) \
    .add("price", DoubleType()) \
    .add("timestamp", LongType()) \
    .add("source", StringType())

# 1️⃣ Spark session with Kafka package
spark = SparkSession.builder \
    .appName("StockStreamIngest") \
    .config("spark.sql.streaming.checkpointLocation", "datalake/checkpoints/bronze") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# 2️⃣ Read from Kafka
df_kafka = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "stock-ticks") \
    .option("startingOffsets", "earliest") \
    .load()

# Kafka value is binary by default, cast to string
df_values = df_kafka.selectExpr("CAST(value AS STRING) as json_str")

# 3️⃣ Parse JSON
df_parsed = df_values.select(from_json(col("json_str"), schema).alias("data")) \
    .select("data.*")

# 4️⃣ Write to Parquet with checkpointing
query = df_parsed.writeStream \
    .format("parquet") \
    .outputMode("append") \
    .option("path", "datalake/bronze") \
    .start()

print("🔥 Streaming to Data Lake started...")
query.awaitTermination()
