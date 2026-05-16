#!/usr/bin/env bash
set -e

# 日志
LOG="/mnt/e/MYPJ/data/daily.log"
exec > >(tee -a "$LOG") 2>&1

echo "=== $(date '+%Y-%m-%d %H:%M:%S') 开始 ==="

cd /mnt/e/MYPJ
source .venv-wsl/bin/activate

echo "[1/3] 爬取数据..."
python crawler/crawler.py

echo "[2/3] Spark 清洗..."
python spark_jobs/process.py

echo "[3/3] 生成报告..."
python llm/report.py

echo "=== $(date '+%Y-%m-%d %H:%M:%S') 完成 ==="
