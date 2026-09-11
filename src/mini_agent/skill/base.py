"""Skill打包。
Skill 不携带工具：工具全局常驻，instructions 里按名引用要用的工具即可。
"""

class Skill:

    name: str = ""
    description: str = ""
    instructions: str = ""

    def __init__(self, name=None, description=None, instructions=None):
        self.name = name if name is not None else getattr(self, "name", "")
        self.description = (
            description if description is not None else getattr(self, "description", "")
        )
        self.instructions = (
            instructions if instructions is not None else getattr(self, "instructions", "")
        )

    def render(self) -> str:
        """把skill渲染成system prompt里的一个指令"""
        return (
            f"<skill name=\"{self.name}\">\n"
            f"{self.description.strip()}\n"
            f"{self.instructions.strip()}\n"
            f"</skill>"
        )