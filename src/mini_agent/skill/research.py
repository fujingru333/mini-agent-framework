"""一个真实的 Skill 示例：资料调研。"""

from .base import Skill


class ResearchSkill(Skill):
    name = "research"
    description = "帮助用户进行资料搜索、分析和总结"
    instructions = """当用户要求进行资料调研时：
1. 明确研究问题
2. 搜索相关资料
3. 判断资料可信度
4. 对多个来源交叉验证
5. 给出结构化结论"""
    # 有真实的 search / read_file 工具时填进来，例如：
    # tools = [search_tool, read_file_tool]
    tools = []