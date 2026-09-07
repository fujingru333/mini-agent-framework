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
    messages=[{"role": "system", "content": ""}],
    iteration=9,          # 直接注入"已跑9轮"
)
print(runtime.run("继续"))  # 第10轮正常返回,不报错