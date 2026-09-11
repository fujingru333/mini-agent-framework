"""测试迭代三：load_skill 渐进披露（只披露指令，不再注册工具）。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mini_agent import Agent
from mini_agent.skill import Skill


class ResearchSkill(Skill):
    name = "research"
    description = "帮助用户进行资料搜索、分析和总结"
    instructions = """当用户要求进行资料调研时：
1. 明确研究问题
2. 搜索相关资料
3. 交叉验证
4. 总结"""


class CallingModel:
    """第一轮调用 load_skill；看到工具结果后就正常回答。"""
    def __init__(self):
        self.calls = 0

    def chat(self, messages, **kwargs):
        self.calls += 1
        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        if tool_msgs:
            return {"role": "assistant", "content": f"已完成，共{self.calls}轮"}
        return {
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "id": "call_1",
                "type": "function",
                "function": {"name": "load_skill", "arguments": '{"name": "research"}'},
            }],
        }


def test_progressive():
    print("1. create_runtime 注册 load_skill 工具（全局工具之一）")
    agent = Agent(CallingModel(), skills=[ResearchSkill()], prompt="你是助手")
    rt = agent.create_runtime()
    assert any(s["function"]["name"] == "load_skill" for s in rt.tool_schemas)
    print("load_skill 已注册: OK\n")

    print("2. 模型调用 load_skill：全文进上下文，工具列表不变")
    out = rt.run("帮我调研一下 Qwen3")
    assert out == "已完成，共2轮"
    assert len(rt.tools) == 1, "加载 skill 不该改变工具列表"
    full = next(m["content"] for m in rt.state.messages
                if m.get("role") == "tool")
    assert "交叉验证" in full
    print("run 返回:", out)
    print("工具列表(应只有 load_skill):", [t.name for t in rt.tools])
    print("工具结果(节选):", full[:50], "...\n")

    print("\n迭代三（解耦版）全部通过")


if __name__ == "__main__":
    test_progressive()