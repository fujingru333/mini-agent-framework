"""Runtime：一次会话的执行实例。

与 Agent 的分工：
- Agent   = 配置（我要做什么、有什么能力），可被多个 Runtime 共享
- Runtime = 一次会话的执行现场（这次任务怎么跑），持有本会话的状态
"""

import json
import uuid
from typing import Any

from .context import ContextManager
from .memory import Storage
from .state import AgentState


class AgentRuntime:
    """一次会话的执行实例：持有本次会话的messages，负责完整执行循环。

    同一个Agent可以创建多个Runtime（多个用户/多个会话），
    各自的messages互不干扰
    """

    def __init__(
            self,
            model,
            tools,
            tool_schemas,
            prompt,
            max_iterations,
            context_manage: ContextManager | None,
            storage: Storage | None = None,
            session_id: str | None = None,
    ):
        self.model = model
        self.tools = tools
        self.tool_schemas = tool_schemas
        self.prompt = prompt
        self.max_iterations = max_iterations
        self.context_manager = context_manage
        self.storage = storage
        #全部可变数据收进State：session_id实现计算方便恢复历史
        sid = session_id or f"session-{uuid.uuid4().hex[:8]}"
        self.state = AgentState(
            session_id=sid,
            messages=self._restore_history(sid),
        )

    def add_tool(self, tool) -> None:
        """动态注册一个工具：load_skill加载一个skill时，把该skill声明的工具逐个注册"""
        if any(t.name == tool.name for t in self.tools):
            raise ValueError(f"工具重名：'{tool.name}'")
        self.tools.append(tool)
        self.tool_schemas.append(tool.to_schema())

    def _restore_history(self,session_id: str) -> list[dict[str, Any]]:
        """从存储恢复会话历史，没有历史就从system消息开始"""
        if self.storage is None:
            return [{"role": "system", "content": self.prompt}]
        history = self.storage.load_messages(session_id)
        if history:
            return history
        system_msg = {"role": "system", "content": self.prompt}
        self.storage.save_message(session_id, system_msg)
        return [system_msg]

    def _remember(self, message: dict[str, Any]) -> None:
        """追加一条消息：写入内存，有存储则同时落库"""
        self.state.messages.append(message)
        if self.storage is not None:
            self.storage.save_message(self.state.session_id, message)

    def run(self, user_input: str) -> str:
        """接收用户输入，调用模型并返回 Agent 的回复。"""
        self._remember({"role": "user", "content": user_input})

        while self.state.iteration < self.max_iterations:
            self.state.iteration += 1
            # 发给模型的：完整历史经过上下文管理器处理后的版本
            send_messages = (
                self.context_manager.manage(self.state.messages)
                if self.context_manager else self.state.messages
            )# 由于context_manager默认为None，不引入就不对message进行任何操作
            response = self.model.chat(
                send_messages, tools=self.tool_schemas
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

    def _execute_tool(self, call: dict) -> str:
        """执行单个工具调用；失败也返回错误文本，交给大模型处理纠错"""
        name = call["function"]["name"]
        try:
            arguments = json.loads(call["function"]["arguments"])
        except json.JSONDecodeError:
            return f"错误：工具参数不是合法 JSON：{call['function']['arguments']}"

        tool = next((t for t in self.tools if t.name == name), None)
        if tool is None:
            return f"错误：找不到名为 {name} 的工具"
        try:
            return str(tool.execute(**arguments))
        except Exception as e:
            return f"错误：工具 {name} 执行失败：{e}"