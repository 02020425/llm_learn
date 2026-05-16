# A 股全自动日报系统

基于 PySpark + Qwen LLM 的全自动 A 股市场日报生成系统，从数据爬取、清洗分析到 AI 报告输出一站式完成。

## 架构

```
akshare (爬取) ──→ PySpark (清洗/分析) ──→ Qwen LLM (报告生成)
     │                    │                      │
     ▼                    ▼                      ▼
  data/raw/          data/processed/         data/report_*.md
```

## 技术栈

| 层 | 技术 | 选型理由 |
|---|------|---------|
| 数据源 | akshare | 国内 A 股数据最全的 Python 接口库 |
| 计算引擎 | PySpark 3.5 | 可横向扩展至 TB 级历史行情分析 |
| AI 模型 | Qwen (DashScope) | 中文金融文本生成优于 GPT 系列 |
| 调度 | cron | 系统级零依赖，交易日下午自动触发 |
| 环境 | Docker + WSL | 开发环境一键复现 |

## 快速开始

```bash
# 1. 环境配置
bash setup_wsl.sh

# 2. 设置 API Key
echo 'export DASHSCOPE_API_KEY="你的Key"' >> ~/.bashrc
source ~/.bashrc

# 3. 手动运行一次完整流程
bash daily_job.sh
```

## 定时调度

cron 已配置为交易日下午 3:30 自动运行。如需修改：

```bash
crontab -e
# 格式: 分 时 日 月 周 命令
# 当前: 30 15 * * 1-5 /mnt/e/MYPJ/daily_job.sh
```

## 报告示例

日报包含：
- 整体市况（涨跌比、市场情绪）
- PE 估值分析（当前估值在历史中的位置）
- 热点方向（资金流向归纳）
- 风险提示

## 项目结构

```
.
├── crawler/crawler.py       # akshare 爬取 A 股行情/PE/历史数据
├── spark_jobs/process.py    # PySpark 数据清洗与统计分析
├── llm/report.py            # Qwen LLM 生成日报
├── daily_job.sh             # 一日调度脚本
├── setup_wsl.sh             # WSL 环境一键安装
├── data/raw/                # 爬取原始数据
├── data/processed/          # Spark 处理结果
└── pyproject.toml           # Python 依赖声明
```

## License

MIT
