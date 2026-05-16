"""
Spark 数据清洗 + 分析
本地运行: spark-submit spark_jobs/process.py
输入: data/raw/  输出: data/processed/
"""
import os
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("StockAnalysis") \
    .master("local[*]") \
    .getOrCreate()

INPUT = "data/raw"
OUTPUT = "data/processed"

# ========== 1. 读取 & 统一英文列名 ==========
print("=== 读取数据 ===")

# a_spot (Sina): 剥离BOM, 中文->英文
spot = spark.read.option("header", "true").option("inferSchema", "true") \
    .csv(f"{INPUT}/a_spot/*.csv") \
    .toDF("code", "name", "price", "change_amt", "change_pct", "bid", "ask",
          "prev_close", "open", "high", "low", "volume", "amount", "ts")
spot.createOrReplaceTempView("spot")
print(f"a_spot: {spot.count()} 条, 列: {','.join(spot.columns)}")

# a_hist (EastMoney): 剥离BOM
hist_files = os.listdir(f"{INPUT}/a_hist")
if not hist_files:
    print("a_hist: 无数据, 创建空表")
    hist = spark.createDataFrame([], "date string, open double, close double, high double, low double, volume double, amount double")
else:
    hist = spark.read.option("header", "true").option("inferSchema", "true") \
        .csv(f"{INPUT}/a_hist/*.csv") \
        .toDF("date", "open", "close", "high", "low", "volume", "amount")
hist.createOrReplaceTempView("hist")
print(f"a_hist: {hist.count()} 条, 列: {','.join(hist.columns)}")

# market_pe: 剥离BOM, 中文->英文
pe = spark.read.option("header", "true").option("inferSchema", "true") \
    .csv(f"{INPUT}/market_pe/*.csv") \
    .toDF("date", "index_val", "avg_pe")
pe.createOrReplaceTempView("pe")
print(f"market_pe: {pe.count()} 条, 列: {','.join(pe.columns)}")

# ========== 2. 清洗 ==========
print("\n=== 清洗 ===")

spot_clean = spark.sql("""SELECT code, name,
    CAST(price AS double) AS price,
    CAST(change_pct AS double) AS change_pct,
    CAST(volume AS double) AS volume_num,
    CAST(amount AS double) AS amount_num
    FROM spot
    WHERE code IS NOT NULL AND price IS NOT NULL""")
spot_clean.createOrReplaceTempView("spot_clean")
print(f"spot_clean: {spot_clean.count()} 条")

hist_clean = spark.sql("""SELECT *,
    ROUND((close - open) / open * 100, 2) AS change_pct
    FROM hist""")
hist_clean.createOrReplaceTempView("hist_clean")

pe_clean = spark.sql("""SELECT *,
    CAST(SUBSTR(date, 1, 4) AS int) AS year
    FROM pe""")
pe_clean.createOrReplaceTempView("pe_clean")

# ========== 3. 分析 ==========
print("\n=== 分析结果 ===")

print("\n--- 今日涨幅 TOP10 ---")
spark.sql("""SELECT code, name, change_pct
    FROM spot_clean ORDER BY change_pct DESC LIMIT 10""") \
    .show(truncate=False)

print("\n--- 今日跌幅 TOP10 ---")
spark.sql("""SELECT code, name, change_pct
    FROM spot_clean ORDER BY change_pct ASC LIMIT 10""") \
    .show(truncate=False)

print("\n--- 成交额 TOP10 ---")
spark.sql("""SELECT code, name, amount_num AS amount
    FROM spot_clean ORDER BY amount_num DESC LIMIT 10""") \
    .show(truncate=False)

print("\n--- 市场 PE 各年份均值 ---")
spark.sql("""SELECT year, AVG(avg_pe) AS avg_pe_val
    FROM pe_clean GROUP BY year ORDER BY year LIMIT 30""") \
    .show(truncate=False)

print("\n--- 沪深300 区间统计 ---")
spark.sql("""SELECT
    MIN(close) AS close_min,
    MAX(close) AS close_max,
    ROUND(AVG(change_pct), 2) AS avg_change_pct
    FROM hist_clean""") \
    .show(truncate=False)

# ========== 4. 写出结果 ==========
print("\n=== 写出结果 ===")

spark.sql("""SELECT code, name, change_pct
    FROM spot_clean ORDER BY change_pct DESC LIMIT 50""") \
    .coalesce(1).write.mode("overwrite").option("header", "true") \
    .csv(f"{OUTPUT}/top_gainers")

spark.sql("""SELECT year, AVG(avg_pe) AS avg_pe_val
    FROM pe_clean GROUP BY year ORDER BY year""") \
    .coalesce(1).write.mode("overwrite").option("header", "true") \
    .csv(f"{OUTPUT}/pe_by_year")

spark.sql("SELECT * FROM spot_clean") \
    .coalesce(1).write.mode("overwrite").option("header", "true") \
    .csv(f"{OUTPUT}/spot_clean")

print("\n完成!")
spark.stop()
