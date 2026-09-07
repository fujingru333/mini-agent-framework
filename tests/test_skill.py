"""测试迭代二：SkillLibrary 发现、索引注入、get 报错。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mini_agent import Agent
from mini_agent.skill import Skill, SkillLibrary


class FakeModel:
    def chat(self, messages, **kwargs):
        return {"role": "assistant", "content": f"收到{len(messages)}条消息"}


class ResearchSkill(Skill):
    name = "research"
    description = "帮助用户进行资料搜索、分析和总结"
    instructions = "1. 明确研究问题 2. 搜索 3. 交叉验证 4. 总结"
    tools = []


class CodingSkill(Skill):
    name = "coding"
    description = "帮助用户编写和调试代码"
    instructions = "1. 分析需求 2. 写代码 3. 测试"
    tools = []


def test_library():
    print("1. discover 只返回元数据（名字+描述），不含 instructions")
    lib = SkillLibrary([ResearchSkill(), CodingSkill()])
    meta = lib.discover()
    assert {m["name"] for m in meta} == {"research", "coding"}
    assert all("instructions" not in m for m in meta)
    print(meta, "\n")

    print("2. render_index 是目录，不泄漏全文")
    index = lib.render_index()
    assert "research" in index and "coding" in index
    assert "明确研究问题" not in index
    print(index, "\n")

    print("3. create_runtime 把索引注入 system prompt（不注入全文）")
    agent = Agent(FakeModel(), skills=[ResearchSkill(), CodingSkill()], prompt="你是助手")
    rt = agent.create_runtime()
    assert "你是助手" in rt.prompt
    assert "research" in rt.prompt and "coding" in rt.prompt
    assert "明确研究问题" not in rt.prompt, "prompt 里不该有 instructions 全文"
    print("system prompt:\n", rt.prompt, sep="", end="\n\n")

    print("4. 空库时 prompt 只有基础提示")
    rt0 = Agent(FakeModel(), prompt="助手").create_runtime()
    assert rt0.prompt == "助手"
    print("空库: OK\n")

    print("5. get 不存在的 Skill 报错")
    try:
        lib.get("nope")
    except KeyError as e:
        print("报错:", e)

    print("\n迭代二全部通过")


if __name__ == "__main__":
    test_library()