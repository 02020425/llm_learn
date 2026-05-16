# A 股全自动日报系统

基于 PySpark + Qwen LLM 的全自动 A 股市场日报生成系统，数据爬取、清洗分析到 AI 报告输出一站式完成。

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
| AI 模型 | Qwen (DashScope) | 中文金融文本生成表现优秀 |
| 调度 | cron | 系统级零依赖，交易日下午自动触发 |
| 部署 | Docker | 一键启动，环境无关 |

## 快速开始（Docker）

```bash
# 1. 设置 API Key
echo "DASHSCOPE_API_KEY=你的Key" > .env

# 2. 构建 & 启动
docker compose up -d

# 3. 手动触发一次
docker compose exec mypj bash run.sh
```

定时调度已内置——容器启动后，每个交易日下午 3:30 自动运行。

## 快速开始（WSL）

```bash
bash setup_wsl.sh
echo 'export DASHSCOPE_API_KEY="你的Key"' >> ~/.bashrc
source ~/.bashrc
bash daily_job.sh
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
├── run.sh                   # Docker 单次执行脚本
├── daily_job.sh             # WSL 单次执行脚本
├── Dockerfile               # 容器镜像定义
├── docker-compose.yml       # 容器编排
├── setup_wsl.sh             # WSL 环境一键安装
├── data/                    # 数据目录（挂载到宿主机）
└── pyproject.toml           # Python 依赖声明
```

## License

MIT
