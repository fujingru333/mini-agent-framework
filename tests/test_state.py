# 测试2:State 可注入(新能力,改动前做不到)
from mini_agent import Agent
from mini_agent.state import AgentState

class FakeModel:
    def chat(self, messages, **kwargs):
        return {"role": "assistant", "content": f"收到{len(messages)}条消息"}

agent = Agent(FakeModel(), prompt="助手")

runtime = agent.create_runtime()
runtime.state = AgentState(
    session_id="test",
    messages=[
        {"role": "system", "content": ""},
        {"role": "user", "content": "第一轮问题"},
        {"role": "assistant", "content": "第一轮回答"},
    ],
)
print(runtime.run("继续"))  # 从注入的历史继续，应收到 4 条消息
