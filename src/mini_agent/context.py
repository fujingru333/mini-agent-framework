"""上下文管理：把各种压缩方法封装成可挑选、可组装的策略。

使用方式：
- 挑选单个：Agent(strategy=SlidingWindowStrategy(max_messages=10))
- 组装：    Agent(strategy=CombinedStrategy(llm, threshold=15, hard_limit=30))
- 扩展：    新写一个类继承 ContextStrategy 实现 manage，就多一个可挑选的零件
"""
import abc


class ContextManager(abc.ABC):
    """所有策略的公共接口"""
    @abc.abstractmethod
    def manage(self,messages: list[dict]) -> list[dict]:
        """输入完整消息，返回修建后发给模型的消息"""


# 滑动窗口截断
class SlidingWindowStrategy(ContextManager):
    def __init__(self,max_messages: int = 20):
        self.max_messages = max_messages

    def manage(self,messages: list[dict]) -> list[dict]:
        systems = [m for m in messages if m["role"] == "system"]
        others = [m for m in messages if m["role"] != "system"]
        if len(others) <= self.max_messages:
            return messages
        # 边界处理：max_messages=0 时 -0 等于 0，切片取不到空列表
        if self.max_messages == 0:
            return systems
        return systems + others[-self.max_messages:]


# 摘要压缩：消息超过阈值，把最早的对话交给模型总结摘要。最近的保留原文
class SummaryManager(ContextManager):
    def __init__(self,model,threshold: int = 30, keep_recent: int = 15):
        self.model = model
        self.threshold = threshold  # 超过触发压缩的条数
        self.keep_recent = keep_recent  # 保留原文的条数

    def manage(self,messages: list[dict]) -> list[dict]:
        systems = [m for m in messages if m["role"] == "system"]
        others = [m for m in messages if m["role"] != "system"]

        if len(others) <= self.threshold:
            return messages

        to_summarize = others[:-self.keep_recent]
        recent = others[-self.keep_recent:]
        summary = self._summarize(to_summarize)

        base = " ".join(m.get("content", "") for m in systems).strip()
        new_system = {
            "role": "system",
            "content": f"{base}\n\n[历史对话摘要]\n{summary}"
        }
        return [new_system] + recent

    def _summarize(self,messages: list[dict]) -> str:
        line = "\n".join(
            f"{m['role']}: {m.get('content', '')}" for m in messages
        )
        prompt = (
            "请把下面的对话压缩成中文要点摘要，保留关键事实、用户偏好和未完成的事项，不要超过200字。\n\n" + line
        )
        return self.model.chat([{"role": "user","content": prompt}])

