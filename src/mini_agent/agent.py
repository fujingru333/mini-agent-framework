"""Agent 核心：编排 LLM 与工具的循环。"""

import json
import uuid
from typing import Any

from .context import ContextManager
from .memory import Storage
from .runtime import AgentRuntime
from .skill import Skill, SkillLibrary
from .tool import Tool


def _as_library(skills) -> SkillLibrary:
    """把 list[Skill] 或 SkillLibrary 统一成 SkillLibrary。"""
    if isinstance(skills, SkillLibrary):
        return skills
    return SkillLibrary(skills or [])


# def _merge_tools(base_tools, skill_tools):
#     """合并工具列表：按name去重，重名直接报错"""
#     merged = {}
#     for t in [*base_tools, *skill_tools]:
#         if t.name in merged:
#             raise ValueError(
#                  f"工具重名：'{t.name}' 同时出现在多个来源，请改名或去掉一个"
#             )
#         merged[t.name] = t
#     return list(merged.values())


def _compose_prompt(base: str, library: SkillLibrary) -> str:
    """基础 prompt + Skill 索引，拼成最终 system prompt。

    索引只列"有哪些 Skill、各是什么"（元数据常驻），不展开 instructions
    全文——全文由迭代三的 load_skill 按需读取（渐进披露）。
    """
    blocks = [base, library.render_index()]
    return "\n\n".join(b for b in blocks if b)


class Agent:
    """持有 LLM 与工具、Skill 库，可创建会话执行实例。

    Agent 是"配置"：model / tools / library / prompt 都是跨会话共享的。
    真正跑循环的是 create_runtime() 返回的 AgentRuntime。
    Skill 在这里以 SkillLibrary 形式登记；create_runtime() 把"可用 Skill
    索引"注入 system prompt，让 Agent 知道有哪些能力、各是什么。
    """

    def __init__(
            self,
            model,
            tools=None,
            skills=None,
            prompt="",
            max_iterations=10,
            storage: Storage | None = None,
            context_manager: ContextManager | None = None,
    ):
        self.model = model
        self.tools = tools or []
        self.library = _as_library(skills)
        # 工具 schema 只生成一次，循环里复用（模型签名不会变）
        # self.tool_schemas = [t.to_schema() for t in self.tools]
        self.prompt = prompt
        self.max_iterations = max_iterations
        self.storage = storage
        self.context_manager = context_manager

    def create_runtime(
            self,
            storage: Storage | None = None,
            session_id: str | None = None,
            skills=None,
    ) -> AgentRuntime:
        """创建一个新的会话执行实例:可用skills指定本次会话激活的skill"""

        system_prompt = _compose_prompt(self.prompt, self.library)
        runtime = AgentRuntime(
            model=self.model,
            tools=list(self.tools),
            tool_schemas=[t.to_schema() for t in self.tools],
            prompt=system_prompt,
            max_iterations=self.max_iterations,
            context_manage=self.context_manager,
            storage=storage if storage is not None else self.storage,
            session_id=session_id,
        )

        # 渐进披露：注册load_skill工具
        # 模型看到索引后，调用它按需加载某个Skill的完整做法
        def load_skill(name: str) -> str:
            skill = self.library.get(name)
            for t in skill.tools:
                runtime.add_tool(t)
            return skill.render()

        runtime.add_tool(Tool(
            name="load_skill",
            description=(
                "加载一个 Skill 的完整做法。可用 Skill 见 system prompt 的"
                " [可用 Skills] 清单，参数 name 传 Skill 名。"
            ),
            func=load_skill,
        ))
        return runtime