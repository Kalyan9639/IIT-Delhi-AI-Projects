import dlt
from pyspark.sql.functions import col, sum, avg, regexp_replace, to_date, date_format

# --- 1. BRONZE LAYER ---
@dlt.table(name="marketing_bronze")
def marketing_bronze():
    return spark.read.format("csv") \
        .option("header", "true") \
        .option("inferSchema", "true") \
        .load("/Volumes/dai/default/medallion/marketing_campaign_dataset.csv")

# --- 2. SILVER LAYER (Cleaning & Feature Preparation) ---
@dlt.table(name="marketing_silver")
def marketing_silver():
    return dlt.read("marketing_bronze") \
        .withColumn("Acquisition_Cost", regexp_replace(col("Acquisition_Cost"), "[$,]", "").cast("float")) \
        .withColumn("Date", to_date(col("Date"), "yyyy-MM-dd")) \
        .withColumn("Month", date_format(col("Date"), "yyyy-MM")) \
        .withColumn("Total_Conversions", (col("Conversion_Rate") * col("Clicks"))) \
        .withColumn("Revenue", (col("ROI") * col("Acquisition_Cost")) + col("Acquisition_Cost")) \
        .withColumn("Net_Profit", (col("ROI") * col("Acquisition_Cost")))

# --- 3. GOLD LAYER (Analytics Ready) ---
@dlt.table(name="marketing_gold")
def gold_marketing():
    return dlt.read("marketing_silver") \
        .groupBy("Month", "Channel_Used", "Campaign_Type", "Customer_Segment") \
        .agg(
            sum("Acquisition_Cost").alias("Total_Spend"),
            sum("Total_Conversions").alias("Total_Conversions"),
            sum("Revenue").alias("Total_Revenue"),
            sum("Net_Profit").alias("Total_Net_Profit"),
            avg("ROI").alias("Avg_ROI"),
            # Calculate efficiency metrics on the aggregated data
            (sum("Revenue") / sum("Acquisition_Cost")).alias("ROAS"),
            (sum("Acquisition_Cost") / sum("Total_Conversions")).alias("CAC")
        ) \
        .fillna(0, subset=["ROAS", "CAC"]) # Clean up division by zero errors
