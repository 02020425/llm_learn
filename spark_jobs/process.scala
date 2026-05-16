/**

 * Spark 数据清洗 + 分析
 * 运行: spark-shell -i spark_jobs/process.scala
 */
import org.apache.spark.sql.DataFrame

val INPUT = "data/raw"
val OUTPUT = "data/processed"

// ========== 1. 读取 & 统一英文列名 ==========
println("=== 读取数据 ===")

// a_spot (Sina): 剥离BOM, 中文->英文
val spot = spark.read.option("header", "true").option("inferSchema", "true")
  .csv(s"$INPUT/a_spot/*.csv")
  .toDF("code","name","price","change_amt","change_pct","bid","ask",
        "prev_close","open","high","low","volume","amount","ts")
spot.createOrReplaceTempView("spot")
println(s"a_spot: ${spot.count()} 条, 列: ${spot.columns.mkString(",")}")

// a_hist (EastMoney): 剥离BOM
val hist = spark.read.option("header", "true").option("inferSchema", "true")
  .csv(s"$INPUT/a_hist/*.csv")
  .toDF("date","open","close","high","low","volume","amount")
hist.createOrReplaceTempView("hist")
println(s"a_hist: ${hist.count()} 条, 列: ${hist.columns.mkString(",")}")

// market_pe: 剥离BOM, 中文->英文
val pe = spark.read.option("header", "true").option("inferSchema", "true")
  .csv(s"$INPUT/market_pe/*.csv")
  .toDF("date","index_val","avg_pe")
pe.createOrReplaceTempView("pe")
println(s"market_pe: ${pe.count()} 条, 列: ${pe.columns.mkString(",")}")

// ========== 2. 清洗 ==========
println("\n=== 清洗 ===")

val spotClean = spark.sql(
  """SELECT code, name,
     |  CAST(price AS double) AS price,
     |  CAST(change_pct AS double) AS change_pct,
     |  CAST(volume AS double) AS volume_num,
     |  CAST(amount AS double) AS amount_num
     |FROM spot
     |WHERE code IS NOT NULL AND price IS NOT NULL""")
spotClean.createOrReplaceTempView("spot_clean")
println(s"spot_clean: ${spotClean.count()} 条")

val histClean = spark.sql(
  """SELECT *,
     |  ROUND((close - open) / open * 100, 2) AS change_pct
     |FROM hist""")
histClean.createOrReplaceTempView("hist_clean")

val peClean = spark.sql(
  """SELECT *,
     |  CAST(SUBSTR(date, 1, 4) AS int) AS year
     |FROM pe""")
peClean.createOrReplaceTempView("pe_clean")

// ========== 3. 分析 ==========
println("\n=== 分析结果 ===")

println("\n--- 今日涨幅 TOP10 ---")
spark.sql(
  """SELECT code, name, change_pct
     |FROM spot_clean ORDER BY change_pct DESC LIMIT 10""")
  .show(false)

println("\n--- 今日跌幅 TOP10 ---")
spark.sql(
  """SELECT code, name, change_pct
     |FROM spot_clean ORDER BY change_pct ASC LIMIT 10""")
  .show(false)

println("\n--- 成交额 TOP10 ---")
spark.sql(
  """SELECT code, name, amount_num AS amount
     |FROM spot_clean ORDER BY amount_num DESC LIMIT 10""")
  .show(false)

println("\n--- 市场 PE 各年份均值 ---")
spark.sql(
  """SELECT year, AVG(avg_pe) AS avg_pe_val
     |FROM pe_clean GROUP BY year ORDER BY year LIMIT 30""")
  .show(false)

println("\n--- 沪深300 区间统计 ---")
spark.sql(
  """SELECT
     |  MIN(close) AS close_min,
     |  MAX(close) AS close_max,
     |  ROUND(AVG(change_pct), 2) AS avg_change_pct
     |FROM hist_clean""")
  .show(false)

// ========== 4. 写出 ==========
println("\n=== 写出结果 ===")

spark.sql(
  """SELECT code, name, change_pct
     |FROM spot_clean ORDER BY change_pct DESC LIMIT 50""")
  .coalesce(1).write.mode("overwrite").option("header", "true")
  .csv(s"$OUTPUT/top_gainers")

spark.sql(
  """SELECT year, AVG(avg_pe) AS avg_pe_val
     |FROM pe_clean GROUP BY year ORDER BY year""")
  .coalesce(1).write.mode("overwrite").option("header", "true")
  .csv(s"$OUTPUT/pe_by_year")

spark.sql("SELECT * FROM spot_clean")
  .coalesce(1).write.mode("overwrite").option("header", "true")
  .csv(s"$OUTPUT/spot_clean")

println("\n完成!")
System.exit(0)
