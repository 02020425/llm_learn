#!/usr/bin/env bash
set -e
echo "=== WSL 环境一键配置 ==="

# 1. 系统包
echo "[1/4] 安装 Java + Python ..."
sudo apt update
sudo apt install -y openjdk-17-jdk python3.12 python3.12-venv

# 2. 虚拟环境
echo "[2/4] 创建虚拟环境 ..."
PROJ="/mnt/e/MYPJ"
cd "$PROJ"
python3.12 -m venv .venv-wsl
source .venv-wsl/bin/activate

# 3. Python 包
echo "[3/4] 安装 Python 依赖 ..."
pip install --upgrade pip
pip install pyspark>=3.4.0 akshare pandas pyarrow openpyxl openai

# 4. 验证
echo "[4/4] 验证环境 ..."
echo "---"
echo "Java: $(java -version 2>&1 | head -1)"
echo "Python: $(python --version)"
echo "PySpark: $(python -c 'import pyspark; print(pyspark.__version__)')"
echo "---"

echo ""
echo "======================================"
echo "  环境就绪! 激活: source .venv-wsl/bin/activate"
echo "  运行: python spark_jobs/process.py"
echo "======================================"
