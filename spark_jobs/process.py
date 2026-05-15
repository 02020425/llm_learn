"""
Spark 数据清洗 + 分析
服务器上运行: spark-submit spark_jobs/process.py
输入: data/raw/  输出: data/processed/
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, round as sround

spark = SparkSession.builder \
    .appName("StockAnalysis") \
    .getOrCreate()

INPUT = "data/raw"
OUTPUT = "data/processed"

# ========== 1. 读取 ==========
print("=== 读取数据 ===")

spot = spark.read.option("header", True).option("inferSchema", True) \
    .csv(f"{INPUT}/a_spot/*.csv")
spot.printSchema()
print(f"A股行情: {spot.count()} 条")

hist = spark.read.option("header", True).option("inferSchema", True) \
    .csv(f"{INPUT}/a_hist/*.csv")

pe = spark.read.option("header", True).option("inferSchema", True) \
    .csv(f"{INPUT}/market_pe/*.csv")

# ========== 2. 清洗 ==========
print("\n=== 清洗 ===")

# A股行情: 涨跌幅 top10
spot_clean = spot.dropna(subset=["code", "trade"]) \
    .withColumn("price", col("trade").cast("double")) \
    .withColumn("change_pct", col("changepercent").cast("double"))
spot_clean.printSchema()
print(f"清洗后: {spot_clean.count()} 条")

# 历史日线: 计算涨跌幅
hist = hist.withColumn("change_pct",
    sround((col("close") - col("open")) / col("open") * 100, 2))

# 市场PE: 按年份统计
pe = pe.withColumn("year", col("日期").substr(1, 4).cast("int"))

# ========== 3. 分析 ==========
print("\n=== 分析结果 ===")

# 3.1 涨幅前10
print("\n--- 今日涨幅 TOP10 ---")
spot_clean.select("code", "name", "change_pct") \
    .orderBy(col("change_pct").desc()) \
    .limit(10).show(truncate=False)

# 3.2 跌幅前10
print("\n--- 今日跌幅 TOP10 ---")
spot_clean.select("code", "name", "change_pct") \
    .orderBy(col("change_pct").asc()) \
    .limit(10).show(truncate=False)

# 3.3 成交额前10
print("\n--- 成交额 TOP10 ---")
spot_clean.select("code", "name", col("amount").cast("double").alias("amount")) \
    .orderBy(col("amount").desc()) \
    .limit(10).show(truncate=False)

# 3.4 历史 PE 统计: 各年份均值
print("\n--- 市场 PE 各年份均值 ---")
pe.groupBy("year").avg("平均市盈率") \
    .orderBy("year") \
    .limit(30).show(truncate=False)

# 3.5 沪深300区间统计
print("\n--- 沪深300 区间统计 ---")
hist.agg(
    {"open": "min", "close": "max", "volume": "sum"}
).show()

# ========== 4. 写出结果 ==========
print("\n=== 写出结果 ===")

# 涨幅榜
spot_clean.select("code", "name", "change_pct") \
    .orderBy(col("change_pct").desc()) \
    .limit(50).coalesce(1) \
    .write.mode("overwrite").option("header", True).csv(f"{OUTPUT}/top_gainers")

# PE年份统计
pe.groupBy("year").avg("平均市盈率") \
    .orderBy("year").coalesce(1) \
    .write.mode("overwrite").option("header", True).csv(f"{OUTPUT}/pe_by_year")

# 清洗后的行情全量
spot_clean.coalesce(1) \
    .write.mode("overwrite").option("header", True).csv(f"{OUTPUT}/spot_clean")

print("\n完成!")
spark.stop()
