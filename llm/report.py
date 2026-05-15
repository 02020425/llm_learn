"""
用 Qwen 生成 A 股日度分析报告。
需要设环境变量 DASHSCOPE_API_KEY=你的key
"""
import os
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from openai import OpenAI

PROCESSED = Path(__file__).parent.parent / "data" / "processed"
REPORT_DIR = Path(__file__).parent.parent / "data"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ---------- 1. 读取 Spark 处理结果，提炼关键指标 ----------

# 行情
spot = pd.read_csv(next((PROCESSED / "spot_clean").glob("part-*.csv")))
spot = spot.dropna(subset=["change_pct"])

up_count = int((spot["change_pct"] > 0).sum())
down_count = int((spot["change_pct"] < 0).sum())
flat_count = int((spot["change_pct"] == 0).sum())
avg_change = round(float(spot["change_pct"].mean()), 2)
top10_up = spot.nlargest(10, "change_pct")[["code", "name", "change_pct"]]
top10_down = spot.nsmallest(10, "change_pct")[["code", "name", "change_pct"]]
top10_amount = spot.nlargest(10, "amount_num")[["code", "name", "amount_num"]]

# PE
pe = pd.read_csv(next((PROCESSED / "pe_by_year").glob("part-*.csv")))
latest_pe = round(float(pe["avg_pe_val"].iloc[-1]), 2)
pe_max = round(float(pe["avg_pe_val"].max()), 2)
pe_min = round(float(pe["avg_pe_val"].min()), 2)
pe_mean = round(float(pe["avg_pe_val"].mean()), 2)

# ---------- 2. 拼 prompt ----------

stats = f"""
今日A股市场概况（{datetime.today().strftime('%Y-%m-%d')}）：
- 上涨: {up_count} 只, 下跌: {down_count} 只, 平盘: {flat_count} 只
- 全市场平均涨跌幅: {avg_change}%
- 当前PE均值: {latest_pe}, 历史最高: {pe_max}, 历史最低: {pe_min}, 历史均值: {pe_mean}

涨幅前10:
{top10_up.to_string(index=False)}

跌幅前10:
{top10_down.to_string(index=False)}

成交额前10:
{top10_amount.to_string(index=False)}
"""

prompt = f"""以下是今日A股市场数据，请用中文写一份简洁的市场日报，包含：
1. 整体市况（涨跌比、平均涨幅、市场情绪判断）
2. PE估值分析（当前估值在历史中处于什么位置）
3. 热点方向（从涨跌幅和成交额数据中归纳资金流向）
4. 风险提示（1-2点）

数据：
{stats}

要求：300-500字，语言简洁，不要数据堆砌，给出你的分析判断。"""

# ---------- 3. 调 Qwen API ----------

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

print("正在调用 Qwen 生成报告...")
resp = client.chat.completions.create(
    model="qwen-plus",
    messages=[
        {"role": "system", "content": "你是一名资深A股市场分析师，擅长从数据中提炼观点。"},
        {"role": "user", "content": prompt},
    ],
    temperature=0.7,
    max_tokens=1024,
)

report = resp.choices[0].message.content

# ---------- 4. 保存 ----------

today = datetime.today().strftime("%Y%m%d")
path = REPORT_DIR / f"report_{today}.md"
path.write_text(f"# A股市场日报 ({datetime.today().strftime('%Y-%m-%d')})\n\n{report}", encoding="utf-8")
print(f"报告已保存: {path}")
print(report)
