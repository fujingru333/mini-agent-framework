"""Agent 核心：编排 LLM 与工具的循环。"""

import json
import uuid
from typing import Any

from .memory import Storage


class Agent:
    """持有 LLM 与工具列表，运行"思考-调用工具-回答"循环。

    记忆：默认纯内存；传入 storage（+ session_id）后自动持久化，
    同一个 session_id 可以跨进程恢复对话。
    """

    def __init__(
            self,
            model,
            tools = None,
            prompt = "",
            max_iterations=10,
            storage: Storage | None = None,
            session_id: str | None = None,
    ):
        self.model = model
        self.tools = tools or []
        # 工具 schema 只生成一次，循环里复用（模型签名不会变）
        self.tool_schemas = [t.to_schema() for t in self.tools]
        self.prompt = prompt
        self.max_iterations = max_iterations
        self.storage = storage
        self.session_id = session_id or f"session-{uuid.uuid4().hex[:8]}"
        self.messages: list[dict[str, Any]] = self._restore_history()

    def _restore_history(self) -> list[dict[str,Any]]:
        """从存储恢复会话历史，没有历史就从system消息开始"""
        if self.storage is None:
            return [{"role":"system","content":self.prompt}]
        history = self.storage.load_messages(self.session_id)
        if history:
            return history
        system_msg = {"role":"system","content":self.prompt}
        self.storage.save_message(self.session_id,system_msg)
        return [system_msg]

    def _remember(self,message: dict[str,Any]) -> None:
        """追加一条消息：写入内存，有存储则同时落库"""
        self.messages.append(message)
        if self.storage is not None:
            self.storage.save_message(self.session_id,message)
    def run(self, user_input: str) -> str:
        """接收用户输入，调用模型并返回 Agent 的回复。"""
        self._remember({"role": "user", "content": user_input})

        for _ in range(self.max_iterations):
            response = self.model.chat(
                self.messages, tools=self.tool_schemas
            )
            self._remember(response)

            tool_calls = response.get("tool_calls")
            if not tool_calls:
                return response["content"]

            for call in tool_calls:
                self._remember({
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": self._execute_tool(call),
                })
        raise RuntimeError(
            f"超过最大迭代次数（{self.max_iterations}），未能得到最终回答"
        )
    def _execute_tool(self,call: dict)->str:
        """执行单个工具调用；失败也返回错误文本，交给大模型处理纠错"""
        name = call["function"]["name"]
        try:
            arguments = json.loads(call["function"]["arguments"])
        except json.JSONDecodeError:
            return f"错误：工具参数不是合法 JSON：{call['function']['arguments']}"

        tool = next((t for t in self.tools if t.name == name),None)
        if tool is None:
            return f"错误：找不到名为 {name} 的工具"
        try:
            return str(tool.execute(**arguments))
        except Exception as e:
            return f"错误：工具 {name} 执行失败：{e}"