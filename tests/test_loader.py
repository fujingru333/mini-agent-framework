"""测试迭代四：FileSkillLoader 把 SKILL.md 解析成 Skill，下游零改动。"""

import sys
import tempfile
from pathlib import Path
from mini_agent.skill import FileSkillLoader, SkillLibrary
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mini_agent import Agent,agent
from mini_agent.skill import FileSkillLoader, Skill, SkillLibrary
from mini_agent import DeepSeekLLM


def make_skill_dir() -> Path:
    base = Path(tempfile.mkdtemp())
    (base / "research").mkdir()
    (base / "research" / "SKILL.md").write_text("""---
name: research
description: 进行资料调研和多来源交叉验证
---

当用户要求进行资料调研时：
1. 明确研究问题
2. 搜索相关资料
3. 交叉验证
4. 总结
""", encoding="utf-8")
    (base / "coding").mkdir()
    (base / "coding" / "SKILL.md").write_text("""---
name: coding
description: 编写和调试代码
---

当用户要求写代码时：
1. 分析需求
2. 编写代码
3. 运行测试
""", encoding="utf-8")
    return base


def test_loader():
    print("1. load 单个 SKILL.md -> Skill 对象")
    loader = FileSkillLoader()
    s = loader.load(Path(make_skill_dir()) / "research" / "SKILL.md")
    assert isinstance(s, Skill)
    assert s.name == "research"
    assert "交叉验证" in s.instructions
    assert "当用户要求" in s.instructions
    print(f"name={s.name}, description={s.description}")
    print("instructions(节选):", s.instructions[:30], "...\n")

    print("2. discover 扫描目录 -> Skill 列表")
    skills = loader.discover(make_skill_dir())
    assert {s.name for s in skills} == {"research", "coding"}
    print("发现:", [s.name for s in skills], "\n")

    print("3. 下游零改动：SkillLibrary + Agent 直接吃文件来的 Skill")
    agent = Agent(None, skills=SkillLibrary(skills), prompt="你是助手")
    rt = agent.create_runtime()
    assert "research" in rt.prompt and "coding" in rt.prompt
    assert "明确研究问题" not in rt.prompt, "索引模式：正文不该进 prompt"
    print("索引:\n", rt.prompt, sep="", end="\n\n")

    print("4. 类化 Skill 仍然兼容（老写法不破坏）")
    from mini_agent.skill.base import Skill as _S

    class OldStyleSkill(_S):
        name = "old"
        instructions = "老写法"
    old = OldStyleSkill()
    assert old.name == "old" and old.instructions == "老写法"
    print("类化写法: OK")

    print("\n迭代四全部通过")


if __name__ == "__main__":
    # test_loader()
    loader = FileSkillLoader()
    skills = loader.discover("skills/")
    agent = Agent(model=DeepSeekLLM(), skills=SkillLibrary(skills))
    rt = agent.create_runtime()
    print(rt.prompt)
    out = rt.run("请帮我格式化这段 JSON：{'name':'张三','age':28}")
    print("result",out)