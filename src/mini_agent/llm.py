"""LLM 客户端抽象：统一不同模型提供方的调用接口。"""


class LLM:
    """所有 LLM 客户端的基类。

    子类实现 `chat` 即可接入具体的模型（OpenAI / DeepSeek / 本地模型等）。
    """

    def chat(self, messages: list[dict], **kwargs) -> str:
        """发送一轮对话消息，返回模型回复文本。"""
        raise NotImplementedError
