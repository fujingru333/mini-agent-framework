"""Agent 核心：编排 LLM 与工具的循环。"""

from .llm import LLM
from .tool import Tool


class Agent:
    """最简 Agent：持有 LLM 与工具列表，提供 run 入口。

    后续步骤将在此加入工具调用循环、记忆、上下文管理等能力。
    """

    def __init__(self, llm: LLM, tools: list[Tool] | None = None):
        self.llm = llm
        self.tools = tools or []

    def run(self, user_input: str) -> str:
        """接收用户输入，返回 Agent 的回复。"""
        # TODO: 后续步骤实现完整的思考-调用工具-回答循环
        return self.llm.chat([{"role": "user", "content": user_input}])
