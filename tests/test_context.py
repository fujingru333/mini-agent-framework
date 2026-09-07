"""测试上下文管理的两个策略：SlidingWindowStrategy 与 SummaryManager。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mini_agent.context import SlidingWindowStrategy, SummaryManager

# 模拟LLM输出
class FakeLLM:
    def chat(self, messages, **kwargs):
        return "【摘要】用户连续询问了多个问题，全部已回答。"


def make_messages(n: int) -> list[dict]:
    """构造 n 条非 system 消息（首条是 system，后面是 user/assistant 交替）。"""
    msgs = [{"role": "system", "content": "你是一个助手。"}]
    for i in range(n):
        msgs.append({"role": "user" if i % 2 == 0 else "assistant",
                     "content": f"消息{i}"})
    return msgs

def test_sliding_window():
    print("1.滑动截断")

    s = SlidingWindowStrategy(max_messages=3)

    # 未超限
    msgs = make_messages(3)
    out = s.manage(msgs)
    assert out == msgs, "未超限时应原样返回"
    print(f"未超限(3条): 原样返回, 共{len(out)}条 ")

    # 超限：只留system和最近max_messages条
    msgs = make_messages(6)
    out = s.manage(msgs)
    assert len(out) == 4, f"应剩 system+3条=4条, 实际{len(out)}"
    assert out[0]["role"] == "system"
    # 剩下的必须是最后3条（内容为 消息3/4/5）
    assert [m["content"] for m in out[1:]] == ["消息3", "消息4", "消息5"]
    print(f"超限(6条): 保留 system+最后3条 = {[m['content'] for m in out]} ")

    # 极端：max_messages=0 时只剩 system
    s0 = SlidingWindowStrategy(max_messages=0)
    out0 = s0.manage(make_messages(4))
    assert len(out0) == 1 and out0[0]["role"] == "system"
    print("max_messages=0: 只剩 system ")
    print("滑动截断全部通过 \n")


def test_summary():
    print("1.摘要压缩")

    m = SummaryManager(model=FakeLLM(), threshold=5, keep_recent=2)

    # 未超阈值：不压缩
    msgs = make_messages(5)
    out = m.manage(msgs)
    assert out == msgs, "未超阈值时应原样返回"
    print(f"未超阈值(5条): 原样返回, 共{len(out)}条, 未触发摘要 ")

    # ② 超阈值：system 并入摘要 + 保留最近 keep_recent 条原文
    msgs = make_messages(8)  # system + 8 条
    out = m.manage(msgs)
    # 结果应为: 1条(带摘要的system) + keep_recent=2 条原文 = 3条
    assert len(out) == 3, f"应为 1+2=3 条, 实际{len(out)}"
    # 首条 system 里应包含摘要
    assert "[历史对话摘要]" in out[0]["content"]
    assert "【摘要】" in out[0]["content"]
    # 保留的原文是最后2条：消息6/7
    assert [x["content"] for x in out[1:]] == ["消息6", "消息7"]
    print("超阈值(8条): 首条带摘要, 保留最后2条原文:")
    print("   system 内容:", out[0]["content"].replace("\n", " | "))
    print("   原文保留:", [x["content"] for x in out[1:]])
    print("摘要压缩全部通过 \n")


def test_compose():
    print("3. 组合(Compose)")

    # 用两个现有策略串联
    s = SlidingWindowStrategy(max_messages=3)
    m = SummaryManager(model=FakeLLM(), threshold=4, keep_recent=3)

    msgs = make_messages(10)
    # 先摘要：10条 -> system(带摘要) + 最后3条 = 4条
    after_summary = m.manage(msgs)
    # 再截断：4条没超过 max_messages=3 的限制吗? 超过 -> 截成 system+2
    final = s.manage(after_summary)
    print(f"摘要后: {len(after_summary)}条 -> 截断后: {len(final)}条")
    assert len(final) <= 4, "组合后不应超过单策略上限"
    assert "[历史对话摘要]" in final[0]["content"]
    print("组合链路: 摘要 -> 截断 正常 \n")


if __name__ == "__main__":
    test_sliding_window()
    test_summary()
    test_compose()
    print("全部测试通过 ")