"""SkillLibrary：框架内的 Skill 集合，负责"发现"与"索引"。

与单个 Skill 的分工：
- Skill        = 一类任务的"做法"（指令 + 工具声明）
- SkillLibrary = 一堆 Skill 的目录：知道有哪些、各是什么，但不展开全文

"""


class SkillLibrary:
    def __init__(self, skills):
        self._skills = {s.name: s for s in skills}

    def discover(self) -> list[dict]:
        """返回所有skill的元数据（名字+一句话描述），不包含全文"""
        return [
            {"name": s.name, "description": s.description}
            for s in self._skills.values()
        ]

    def get(self, name: str):
        """按名字取完整Skill：不存在时给出清晰报错"""
        if name not in self._skills:
            raise KeyError(
                f"Skill不存在： '{name}',可用: {sorted(self._skills)}"
            )
        return self._skills[name]

    def render_index(self) -> str:
        """把可用 Skill 的索引渲染成可注入 system prompt 的文本块。

       只列名字和描述（元数据常驻），不含 instructions 全文——
       全文由 load_skill 按需读取。
       """
        if not self._skills:
            return ""
        lines = [
            f"- {name}: {s.description}"
            for name, s in self._skills.items()
        ]
        return ("[可用 Skills]\n" + "\n".join(lines) +
                "\n\n需要某类任务时，调用 load_skill 加载对应 Skill 的完整做法。")