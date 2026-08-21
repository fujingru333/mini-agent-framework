"""工具（Tool）抽象：Agent 可调用的外部能力。"""


class Tool:
    """工具基类。

    子类需定义 `name` / `description`（供 LLM 理解何时调用），
    并实现 `run` 作为执行入口。
    """

    name: str = ""
    description: str = ""

    def run(self, **kwargs):
        """执行工具逻辑，返回结果。"""
        raise NotImplementedError
