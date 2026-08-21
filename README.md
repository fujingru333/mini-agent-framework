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
│       ├── tool.py       # 工具（Tool）抽象
│       └── prompt.py     # 提示词构建
│
└── tests/
    └── test_agent.py
```

## 开发

```bash
# 创建虚拟环境并安装（开发模式）
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e .

# 运行测试
pytest
```
