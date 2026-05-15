"""
A股数据爬取，基于 akshare。
"""
import time
from datetime import datetime, timedelta
from pathlib import Path

import akshare as ak
import pandas as pd

# 数据存到 data/raw 目录
DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def skip_today(name: str) -> bool:
    """今天已经爬过就跳过"""
    today = datetime.today().strftime("%Y%m%d")
    out_dir = DATA_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)
    return (out_dir / f"{today}.csv").exists()


def save_csv(df, name: str):
    """保存数据为 csv 文件"""
    today = datetime.today().strftime("%Y%m%d")
    out_dir = DATA_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{today}.csv"
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"[{name}] 已保存: {path}  ({len(df)} 行)")
    return df


# ======== 工具函数 ========

def retry(func, name: str, max_tries=3):
    """接口挂了自动重试，每次间隔翻倍（2s -> 4s -> 8s）"""
    wait = 2
    for i in range(max_tries):
        try:
            return func()
        except Exception as e:
            if i == max_tries - 1:
                raise e
            print(f"  [{name}] 第{i+1}次失败，{wait}秒后重试... ({e})")
            time.sleep(wait)
            wait *= 2


# ======== 以下为各个数据源 ========

def fetch_a_spot():
    """A股实时行情（Sina 数据源，比东方财富轻量）"""
    if skip_today("a_spot"):
        print("[a_spot] 今日已存在，跳过")
        return
    print("正在获取 A股实时行情（sina源）...")
    df = retry(lambda: ak.stock_zh_a_spot(), "a_spot")
    print(f"  获取到 {len(df)} 只, {len(df.columns)} 列")
    save_csv(df, "a_spot")


def fetch_a_hist(symbol="000300"):
    """历史日线 (默认沪深300)"""
    if skip_today("a_hist"):
        print("[a_hist] 今日已存在，跳过")
        return
    start = (datetime.today() - timedelta(days=365)).strftime("%Y%m%d")
    end = datetime.today().strftime("%Y%m%d")
    print(f"正在获取 {symbol} 历史日线...")
    df = ak.stock_zh_index_daily_em(symbol=f"sh{symbol}", start_date=start, end_date=end)
    print(f"  获取到 {len(df)} 条")
    save_csv(df, "a_hist")


def fetch_market_pe():
    """市场 PE/PB"""
    if skip_today("market_pe"):
        print("[market_pe] 今日已存在，跳过")
        return
    print("正在获取 市场 PE/PB...")
    df = ak.stock_market_pe_lg()
    print(f"  获取到 {len(df)} 条")
    save_csv(df, "market_pe")


# ======== 一键全跑 ========

if __name__ == "__main__":
    print("开始爬取股票数据...\n")

    # 1. 实时行情
    try:
        fetch_a_spot()
    except Exception as e:
        print(f"  实时行情失败: {e}")

    time.sleep(2)

    # 2. 历史日线
    try:
        fetch_a_hist("000300")
    except Exception as e:
        print(f"  历史日线失败: {e}")

    time.sleep(2)

    # 3. 市场PE
    try:
        fetch_market_pe()
    except Exception as e:
        print(f"  市场PE失败: {e}")

    print("\n完成!")
