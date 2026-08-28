"""DeepSeek 模型接入：OpenAI 兼容协议的 HTTP 客户端实现。"""

import os

import requests

from .llm import LLM

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"


class DeepSeekLLM(LLM):
    """通过 DeepSeek 官方 API 调用模型。

    设计要点：
    - DeepSeek 暴露的是 OpenAI 兼容的 /chat/completions 端点，
      所以这个类本质上是一个"OpenAI 兼容客户端"——以后想接其他
      兼容服务（OpenAI、智谱、本地 vLLM 等），只需换 base_url 和 model。
    - api_key 从环境变量 DEEPSEEK_API_KEY 读取，不写死在代码里，
      也不进 git（见项目根目录 .env.example）。
    """

    def __init__(
            self,
            api_key: str | None = None,
            model: str = DEFAULT_MODEL,
            base_url: str = DEEPSEEK_BASE_URL,
            timeout: float = 60.0,
    ):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "缺少 API Key：请设置环境变量 DEEPSEEK_API_KEY，"
                "或在构造时传入 api_key 参数。"
            )
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def chat(self, messages: list[dict], **kwargs) -> dict:
        """发送一轮对话，返回模型回复的完整消息 dict。

        content 是文本回复；如果请求带了 tools 参数，
        返回里可能还有 tool_calls（模型想调用的工具列表）。
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.model, "messages": messages}
        payload.update(kwargs)

        try:
            resp = requests.post(
                url, headers=headers, json=payload, timeout=self.timeout
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(f"请求 DeepSeek API 超时（{self.timeout}s）") from None
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"无法连接 DeepSeek API：{e}") from None

        if resp.status_code != 200:
            # 把常见错误翻译成人话，方便排查
            hint = {
                400: "请求参数错误（通常是模型名不对）",
                401: "API Key 无效",
                402: "账户余额不足",
                429: "请求过于频繁（限流）",
            }.get(resp.status_code, "未知错误")
            raise RuntimeError(
                f"DeepSeek API 返回 {resp.status_code}：{hint}\n{resp.text[:500]}"
            )

        data = resp.json()

        return data["choices"][0]["message"]
