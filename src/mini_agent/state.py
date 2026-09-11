"""AgentState：一次执行过程中的全部可变数据。

与 Runtime 的分工：
- Runtime = 控制流程（下一步做什么、调模型还是调工具、是否结束）
- State   = 记录数据（当前会话是谁、消息有哪些）

注意：迭代次数属于"单次 run"，不放在 State 里——否则多次 run()
会累计计数，导致第二次 run() 直接撞上 max_iterations（见 runtime.run）。
"""

from dataclasses import dataclass,field
from typing import Any


@dataclass
class AgentState:
    session_id: str
    messages: list[dict[str, Any]] = field(default_factory=list)


