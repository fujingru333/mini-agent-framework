"""验证：计算器安全性 + SQLite/PostgreSQL 存储存取（不调真实模型）。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.calculator import calculator
from mini_agent.memory import SQLiteStorage, PostgreSQLStorage


def test_calculator():
    print("=== 计算器 ===")
    print("正常:", calculator.execute(expression="(1+2)*4"))
    try:
        calculator.execute(expression="__import__('os').system('echo 危险')")
        print("恶意代码: 未拦截!! BUG")
    except Exception as e:
        print(f"恶意代码已拦截: {type(e).__name__}: {e}")
    try:
        calculator.execute(expression="1+2*3")
    except Exception as e:
        print(f"计算出错: {e}")
    else:
        print("1+2*3 =", calculator.execute(expression="1+2*3"))


def test_storage(storage, name):
    print(f"\n=== {name} ===")
    sid = f"verify-{name}"
    storage.clear_session(sid)
    storage.save_message(sid, {"role": "user", "content": "第一轮"})
    storage.save_message(sid, {"role": "assistant", "content": "好的"})
    msgs = storage.load_messages(sid)
    print("写入2条,读出", len(msgs), "条:", [m["content"] for m in msgs])
    assert len(msgs) == 2, "读出的条数不对"
    assert msgs[0]["role"] == "user"
    storage.clear_session(sid)
    assert storage.load_messages(sid) == [], "清空后应无消息"
    print(f"{name}: OK")


if __name__ == "__main__":
    test_calculator()
    test_storage(SQLiteStorage("agent_memory.db"), "SQLiteStorage")
    test_storage(PostgreSQLStorage(), "PostgreSQLStorage")
    print("\n全部单元验证通过 ✅")
