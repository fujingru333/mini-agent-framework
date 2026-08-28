"""工具（Tool）抽象：Agent 可调用的外部能力。"""
import inspect

class Tool:
    """工具基类：包装一个普通函数，让模型可以调用它。

    - name: 模型点名用的工具名（在工具列表里必须唯一）
    - description: 告诉模型"什么时候该用这个工具"
    - func: 真正干活的函数，模型填好参数后由框架执行
    """
    def __init__(self, name, description, func):
        self.name = name
        self.description = description
        self.func = func


    def execute(self, **kwargs):
        """执行工具逻辑，返回结果。"""
        return self.func(**kwargs)
    def to_schema(self) -> dict:
        """把工具转为openai兼容的function schema，随请求发给模型"""
        sig = inspect.signature(self.func)
        properties = {}
        required = []
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            dict: "object",
            list: "array",
        }
        for p_name,p in sig.parameters.items():
            properties[p_name] = {"type": type_map.get(p.annotation,"string")}
            if p.default is inspect.Parameter.empty:
                required.append(p_name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

