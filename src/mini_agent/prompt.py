"""提示词构建：把系统提示、工具描述等组装成发给 LLM 的消息。"""

SYSTEM_PROMPT = "You are a helpful AI agent."


def build_messages(user_input: str, system: str = SYSTEM_PROMPT) -> list[dict]:
    """把用户输入组装成标准消息列表（后续可扩展工具描述等）。"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_input},
    ]
