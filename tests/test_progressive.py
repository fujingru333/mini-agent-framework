"""测试迭代三：load_skill 渐进披露 + 动态工具注册。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mini_agent import Agent
from mini_agent.skill import Skill
from mini_agent.tool import Tool


def search(query: str) -> str:
    return f"关于「{query}」的搜索结果..."


class ResearchSkill(Skill):
    name = "research"
    description = "帮助用户进行资料搜索、分析和总结"
    instructions = """当用户要求进行资料调研时：
1. 明确研究问题
2. 搜索相关资料
3. 交叉验证
4. 总结"""
    tools = [Tool(name="search", description="搜索资料", func=search)]


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
    print("1. create_runtime 自动注册 load_skill 工具")
    agent = Agent(CallingModel(), skills=[ResearchSkill()], prompt="你是助手")
    rt = agent.create_runtime()
    assert any(s["function"]["name"] == "load_skill" for s in rt.tool_schemas)
    assert not any(t.name == "search" for t in rt.tools), "未加载前不该有 skill 的工具"
    print("load_skill 已注册，search 未注册: OK\n")

    print("2. 模型调用 load_skill：全文进上下文 + 工具动态注册")
    out = rt.run("帮我调研一下 Qwen3")
    assert out == "已完成，共2轮"
    assert any(t.name == "search" for t in rt.tools), "加载后 search 应被注册"
    assert any(s["function"]["name"] == "search" for s in rt.tool_schemas)
    full = next(m["content"] for m in rt.state.messages
                if m.get("role") == "tool")
    assert "交叉验证" in full
    print("run 返回:", out)
    print("动态注册工具:", [t.name for t in rt.tools])
    print("工具结果(节选):", full[:50], "...\n")

    print("3. 工具重名冲突守卫")

    class ConflictSkill(Skill):
        name = "x"
        tools = [Tool(name="load_skill", description="抢名字", func=search)]
    rt2 = agent.create_runtime()
    try:
        for t in ConflictSkill().tools:
            rt2.add_tool(t)
    except ValueError as e:
        print("重名报错:", e)

    print("\n迭代三全部通过")


if __name__ == "__main__":
    test_progressive()