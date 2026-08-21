"""Agent 冒烟测试：验证最小骨架可导入、可运行。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mini_agent import Agent
from mini_agent.llm import LLM


class FakeLLM(LLM):
    """测试用假 LLM：直接返回固定文本。"""

    def chat(self, messages: list[dict], **kwargs) -> str:
        return "fake response"


def test_agent_run():
    agent = Agent(llm=FakeLLM())
    assert agent.run("hello") == "fake response"


def test_agent_default_tools():
    agent = Agent(llm=FakeLLM())
    assert agent.tools == []
