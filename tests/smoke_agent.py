"""冒烟脚本：用真实 DeepSeek 模型跑通 Agent 的单轮对话。

这不是 pytest 测试（需要真实 API Key），手动运行：

    python tests/smoke_agent.py
"""

import os
import sys
from pathlib import Path

# 读取项目根目录的 .env，把 API Key 注入环境变量（避免硬编码进代码）
env_file = Path(__file__).resolve().parents[1] / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from mini_agent import Agent, DeepSeekLLM
from tools.calculator import calculator
from mini_agent.memory import SQLiteStorage,PostgreSQLStorage

# storage = SQLiteStorage("agent_memory.db")
storage = PostgreSQLStorage()
agent = Agent(DeepSeekLLM(), tools=[calculator],prompt="回答尽量简洁。", storage = storage)
runtime = agent.create_runtime(session_id="demo-1")

print("第一轮", runtime.run("我叫AI"))
print("第二轮", runtime.run("我不叫AI了我叫agent"))

agent2 = Agent(DeepSeekLLM(), tools=[calculator],prompt="回答尽量简洁。",storage = storage)
runtime_b = agent2.create_runtime(session_id="demo-1")
# result = agent.run("帮我算一下(1+2)*4等于多少？")
print("重启后：", runtime_b.run("我到底叫什么？"))
