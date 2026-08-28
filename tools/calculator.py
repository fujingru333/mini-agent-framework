"""业务工具：安全计算器。"""

import ast
import operator

from mini_agent import Tool

# 白名单：只允许这些运算，其他一律拒绝
_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _calculator(expression: str) -> str:
    """安全地计算数学表达式：只执行白名单内的运算，拒绝任意代码执行。

    eval() 会执行任意 Python 代码，模型输出不可信，必须白名单拦截。
    """
    def _eval(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"不支持的常量：{node.value!r}")
        if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
            return _OPERATORS[type(node.op)](_eval(node.operand))
        raise ValueError(f"不支持的表达式语法：{type(node).__name__}")

    return str(_eval(ast.parse(expression, mode="eval").body))


calculator = Tool(
    name="calculator",
    description="计算简单的数学公式，例如：1+2*3",
    func=_calculator,
)
