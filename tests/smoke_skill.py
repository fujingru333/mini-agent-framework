"""真模型冒烟：文件 skill + 渐进披露 + 全局工具 + SQLite 记忆 全栈验收。

覆盖点：
- 用例1：JSON 任务 → 模型看到索引 → load_skill("json-formatter")
         → 指令进上下文 → 产出可解析且数据保留的格式化 JSON
         同时验证解耦：加载 skill 不改变工具列表
- 用例2：纯计算 → 调 calculator，且不该再次 load_skill（反向用例）
- 用例3：坏 JSON → 按 skill 指令报出精确错误
- 用例4：同 session_id 重启 → 历史从 SQLite 恢复

不是 pytest（需要真实 API Key），手动运行：
    PYTHONPATH=src .venv/Scripts/python.exe tests/smoke_skill.py
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 读取项目根目录的 .env，把 API Key 注入环境变量（不硬编码进代码）
env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

sys.path.insert(0, str(ROOT))

from mini_agent import Agent, DeepSeekLLM            # noqa: E402
from mini_agent.memory import SQLiteStorage          # noqa: E402
from mini_agent.skill.loader import FileSkillLoader  # noqa: E402
from tools.calculator import calculator              # noqa: E402

SESSION = "skill-smoke-1"
fails = 0


def check(name: str, cond: bool) -> bool:
    global fails
    print(("  ✅" if cond else "  ❌"), name)
    if not cond:
        fails += 1
    return cond


def tool_calls_used(rt) -> list[str]:
    """按顺序返回会话历史上模型调用过的所有工具名。"""
    names = []
    for m in rt.state.messages:
        if m.get("role") == "assistant" and m.get("tool_calls"):
            names += [tc["function"]["name"] for tc in m["tool_calls"]]
    return names


def parse_json_reply(reply: str):
    """从模型回复里抠出 JSON（容忍 ```json 围栏）；解析失败返回 None。"""
    text = reply.strip()
    if text.startswith("```"):
        parts = text.split("```", 2)
        if len(parts) >= 2:
            text = parts[1].lstrip()
            if text.startswith("json"):
                text = text[4:]
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def main():
    print("== 冒烟：文件 skill + 渐进披露 + 全局工具 + SQLite 记忆 ==\n")

    # 0. 发现文件 skill 并组装 Agent（全新数据库，避免上次残留干扰）
    skills = FileSkillLoader().discover(ROOT / "skills")
    print("发现的 skill:")
    for s in skills:
        print(f"  - {s.name}: {s.description[:40]}...")
    check("发现 json-formatter", any(s.name == "json-formatter" for s in skills))

    db_path = ROOT / "smoke_skill.db"
    if db_path.exists():
        db_path.unlink()
    agent = Agent(
        DeepSeekLLM(),
        tools=[calculator],          # 全局工具：calculator + 框架自动拼的 load_skill
        skills=skills,
        prompt="回答尽量简洁。",
        storage=SQLiteStorage(str(db_path)),
    )
    rt = agent.create_runtime(session_id=SESSION)
    check("load_skill 在模型工具表里（识别入口）",
          any(s["function"]["name"] == "load_skill" for s in rt.tool_schemas))

    # 用例1：JSON 格式化
    print("\n-- 用例1: JSON 格式化 --")
    res1 = rt.run('请把这段 JSON 格式化：{"a":1,"b":[1,2,3],"c":{"d":4}}')
    print("  回复:", res1[:300])
    calls1 = tool_calls_used(rt)
    check("调用了 load_skill", "load_skill" in calls1)
    check("工具列表没变（calculator+load_skill，无动态注册）",
          sorted(t.name for t in rt.tools) == ["calculator", "load_skill"])
    parsed = parse_json_reply(res1)
    check("输出可被 json.loads 解析", parsed is not None)
    check("数据完整保留（a==1 且 b==[1,2,3]）",
          parsed is not None and parsed.get("a") == 1 and parsed.get("b") == [1, 2, 3])

    # 用例2：计算（不该加载 skill 的反向用例）
    print("\n-- 用例2: 计算 234*567 --")
    before = len(calls1)
    res2 = rt.run("234*567 等于多少？")
    print("  回复:", res2[:300])
    calls2 = tool_calls_used(rt)[before:]
    check("调用了 calculator", "calculator" in calls2)
    check("没有再次 load_skill", "load_skill" not in calls2)
    check("答案包含正确结果",
          any(k in res2 for k in ("132678", "132,678", "132 678")))

    # 用例3：坏 JSON
    print("\n-- 用例3: 坏 JSON（尾随逗号）--")
    res3 = rt.run('这段 JSON 哪里错了：{"a":1,}')
    print("  回复:", res3[:300])
    check("指出了错误（错/逗号/尾随/不合法 等）",
          any(k in res3 for k in ("错", "逗号", "尾随", "不合法", "invalid", "trailing")))

    # 用例4：跨会话恢复
    print("\n-- 用例4: 重启后从 SQLite 恢复历史 --")
    rt_b = agent.create_runtime(session_id=SESSION)
    n = len(rt_b.state.messages)
    check(f"恢复 {n} 条消息（应 >= 3）", n >= 3)
    check("system 消息在", any(m.get("role") == "system" for m in rt_b.state.messages))
    check("用户历史消息在（含第一条 JSON 任务）", any(
        m.get("role") == "user" and "JSON" in m.get("content", "")
        for m in rt_b.state.messages))

    print()
    if fails:
        print(f"冒烟结束：{fails} 项失败")
        sys.exit(1)
    print("冒烟结束：全部通过 ✅")


if __name__ == "__main__":
    main()
