# mini-agent-framework

一个自创的轻量级 mini agent 框架。

## 项目结构

```
mini-agent-framework/
│
├── README.md
├── pyproject.toml
│
├── src/
│   └── mini_agent/
│       ├── __init__.py
│       ├── agent.py      # Agent 核心：编排 LLM 与工具
│       ├── llm.py        # LLM 客户端抽象
│       ├── deepseek.py   # DeepSeek 模型接入（OpenAI 兼容）
│       ├── tool.py       # 工具（Tool）抽象
│       └── prompt.py     # 提示词构建
│
└── tests/
    └── smoke_agent.py    # 冒烟脚本：真实调用 DeepSeek 跑通 Agent
```

## 快速开始

```bash
# 创建虚拟环境并安装（开发模式）
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e .

# 配置 API Key：复制 .env.example 为 .env 并填入 Key
copy .env.example .env

# 用真实模型跑一次冒烟对话
python tests/smoke_agent.py
```
