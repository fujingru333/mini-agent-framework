# mini-agent-framework

一个从零手写的轻量级 Agent 框架。核心思想：**Agent 是配置，Runtime 是会话，能力以可替换的零件（Tool / Skill / Storage / Context）拼装。**

## 核心概念

```text
Agent = 配置（用什么模型、有哪些工具、有哪些 Skill）
  ↓ create_runtime()
AgentRuntime = 一次会话的执行现场（跑 agent 循环，持有会话状态）
  ↓ run("问题")
返回模型回答
```

- **Agent**：跨会话共享的配置对象，持有 model / tools / skills / prompt，通过 `create_runtime()` 创建会话。
- **AgentRuntime**：一次会话的执行实例。同一个 Agent 可创建多个 Runtime（多用户/多会话），消息互不干扰；同一个 Runtime 可多次 `run()`，每次都是一次独立的迭代循环。
- **AgentState**：会话的可变数据（session_id、messages），可注入（如恢复历史后继续对话）。
- **Tool**：包装一个函数，自动用 `inspect.signature()` 生成 OpenAI 兼容的工具 schema。
- **Skill**：一类任务的"做法"（指令文本）。SkillLibrary 只把索引（名字+描述）常驻 system prompt，全文由模型按需调用 `load_skill` 加载（渐进披露）。
- **Storage**：会话消息的持久化口子，可替换后端（SQLite / PostgreSQL），Agent 代码零改动。
- **ContextManager**：上下文压缩策略（滑动窗口 / 摘要），可挑选、可组装。

## 项目结构

```
mini-agent-framework/
│
├── src/mini_agent/
│   ├── agent.py        # Agent 核心：编排模型与工具，持有 Skill 库
│   ├── runtime.py      # AgentRuntime：一次会话的执行现场
│   ├── state.py        # AgentState：会话状态（session_id + messages）
│   ├── llm.py          # LLM 客户端抽象（实现 chat 即可接入新模型）
│   ├── deepseek.py     # DeepSeek 接入（OpenAI 兼容协议）
│   ├── tool.py         # Tool 工具抽象：包装函数 + 自动生成 schema
│   ├── prompt.py       # 提示词构建
│   ├── memory.py       # Storage 抽象 + SQLite / PostgreSQL 实现
│   ├── context.py      # 上下文管理策略（滑动窗口 / 摘要）
│   └── skill/
│       ├── base.py     # Skill 类
│       ├── library.py  # SkillLibrary：发现与索引
│       └── loader.py   # FileSkillLoader：把 SKILL.md 解析成 Skill
│
├── skills/             # 文件化 Skill（目录下放 SKILL.md）
├── tools/              # 业务工具（如安全计算器 calculator）
└── tests/              # 测试与冒烟脚本（冒烟脚本需真实 API Key）
```

## 快速开始

```bash
# 创建虚拟环境并安装（开发模式）
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e .

# 配置 API Key：复制 .env.example 为 .env 并填入 Key
copy .env.example .env

# 用真实模型跑一次单轮对话冒烟
python tests/smoke_agent.py
```

## 示例

```python
from mini_agent import Agent, DeepSeekLLM, Tool

def add(a: int, b: int) -> int:
    return a + b

agent = Agent(
    model=DeepSeekLLM(),
    tools=[Tool(name="add", description="两数相加", func=add)],
    prompt="回答尽量简洁。",
)
runtime = agent.create_runtime(session_id="demo-1")

print(runtime.run("1加2等于多少？"))   # 模型会调用 add 工具再回答
print(runtime.run("那再加3呢？"))      # 同一会话，历史保留
```

## 测试

```bash
pip install -e . pytest
python -m pytest            # 需要先安装 pytest
```

tests/ 里的 `smoke_*.py` 是需真实 API Key 的冒烟脚本，不是 pytest，手动运行：

```bash
python tests/smoke_agent.py      # 单轮对话 + 会话历史恢复
PYTHONPATH=src python tests/smoke_skill.py   # 文件 Skill + 渐进披露 + 记忆全栈
```

## 可选依赖

- **PostgreSQL 存储**：`pip install -e '.[postgres]'`（用到 `PostgreSQLStorage` 时才需要 psycopg2）
