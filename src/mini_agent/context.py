"""上下文管理：把各种压缩方法封装成可挑选、可组装的策略。

使用方式：
- 挑选单个：Agent(strategy=SlidingWindowStrategy(max_messages=10))
- 组装：    Agent(strategy=CombinedStrategy(llm, threshold=15, hard_limit=30))
- 扩展：    新写一个类继承 ContextStrategy 实现 apply，就多一个可挑选的零件
"""
import abc

class ContextStrategy(abc.ABC):
    """所有策略的公共接口"""
    @abc.abstractmethod
    def apply(self,messages: list[dict]) -> list[dict]:
        """输入完整消息，返回修建后发给模型的消息"""

# 滑动窗口截断
class SlidingWindowStrategy(ContextStrategy):
    def __init__(self,max_messages: int = 20):
        self.max_messages = max_messages

    def apply(self,messages):
        system_msgs = [m for m in messages if m["role"] == "system"]
        others = [m for m in messages if m["role"] != "system"]
        if len(others) <= self.max_messages:
            return messages
        return system_msgs + others[-self.max_messages:]