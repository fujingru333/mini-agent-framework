# """Skill打包。
#
# Skill 不直接参与工具调用,通过指令块进入 system prompt 让模型知道
# 怎么做；它声明的 tools 在 create_runtime() 时被合并进工具列表。
# """
"""Skill打包。
Skill 不携带工具：工具全局常驻，instructions 里按名引用要用的工具即可。
"""

class Skill:

    name: str = ""
    description: str = ""
    instructions: str = ""
    tools: list = []

    def __init__(self, name=None, description=None, instructions=None, tools=None):
        self.name = name if name is not None else getattr(self, "name", "")
        self.description = (
            description if description is not None else getattr(self, "description", "")
        )
        self.instructions = (
            instructions if instructions is not None else getattr(self, "instructions", "")
        )
        self.tools = list(tools) if tools is not None else list(getattr(self, "tools", []))

    def render(self) -> str:
        """把skill渲染成system prompt里的一个指令"""
        return (
            f"<skill name=\"{self.name}\">\n"
            f"{self.description.strip()}\n"
            f"{self.instructions.strip()}\n"
            f"</skill>"
        )