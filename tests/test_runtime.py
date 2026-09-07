import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mini_agent import Agent

class FakeModel:
    def chat(self, messages, **kwargs):
        return {"role": "assistant", "content": f"收到{len(messages)}条消息"}

agent = Agent(FakeModel(), prompt="助手")
r1 = agent.create_runtime()
r2 = agent.create_runtime()

print(r1.run("A的第一句"))   # A 的会话
print(r1.run("A的第二句"))   # 消息应该累计到 3 条(system+2)
print(r2.run("B的第一句"))   # B 的会话,只有 2 条(system+1)