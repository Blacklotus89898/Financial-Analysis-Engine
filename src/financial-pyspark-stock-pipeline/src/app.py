import time
import streamlit as st
import matplotlib.pyplot as plt
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Create Spark session
def create_spark(app_name="GoldProcessing"):
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark

def load_gold_data(spark):
    # Read Silver parquet files
    df = spark.read.parquet("datalake/silver/*.parquet")
    df = df.na.drop(subset=["SMA","volatility"])

    # Aggregate Gold features
    df_gold = df.groupBy("ticker").agg(
        F.avg("SMA").alias("avg_SMA"),
        F.avg("volatility").alias("avg_volatility")
    )
    return df, df_gold

# Streamlit UI
st.title("Gold Layer Dashboard")
refresh_rate = st.sidebar.slider("Refresh interval (seconds)", 5, 60, 10)

spark = create_spark()

# Auto-refresh loop
placeholder = st.empty()
while True:
    with placeholder.container():
        df, df_gold = load_gold_data(spark)

        st.subheader("Aggregated Gold Features")
        st.dataframe(df_gold.toPandas())

        st.subheader("Visualizations")
        pdf = df.select("ticker","window_start","SMA","volatility").limit(1000).toPandas()

        for ticker in pdf["ticker"].unique():
            subset = pdf[pdf["ticker"] == ticker]

            fig, ax = plt.subplots(figsize=(10,5))
            ax.plot(subset["window_start"], subset["SMA"], label="SMA", linewidth=2)
            ax.fill_between(
                subset["window_start"],
                subset["SMA"] - subset["volatility"],
                subset["SMA"] + subset["volatility"],
                color="gray", alpha=0.2, label="Volatility Band"
            )
            ax.set_title(f"{ticker} SMA with Volatility Band")
            ax.set_xlabel("Time Window Start")
            ax.set_ylabel("Price")
            ax.legend()
            st.pyplot(fig)

    time.sleep(refresh_rate)