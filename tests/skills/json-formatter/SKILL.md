---
name: json-formatter
description: 当用户需要格式化、校验或压缩 JSON，或从 JSON 中提取特定字段时使用。接收一段文本，输出格式化后的 JSON 或精确的错误信息。
---

# JSON 格式化 / 校验

## 职责

把用户提供的文本当作 JSON 处理：解析成功后输出格式化结果；解析失败则给出精确错误及修复建议。

## 处理步骤

1. **接收输入**
   获取用户提供的 JSON 文本；若未提供，提示用户输入。

2. **解析**
   使用 Python 标准库 `json` 模块解析（`json.loads`）。

3. **按需处理**
   - 格式化：`json.dumps(data, indent=2, ensure_ascii=False)`
   - 压缩：`json.dumps(data, separators=(",", ":"), ensure_ascii=False)`
   - 字段提取：解析后按路径逐层取值（如 `data["items"][0]["name"]`）

4. **输出**
   - 成功：用 ```json 代码块展示格式化结果
   - 失败：给出错误类型、行号/列号、出错上下文，并给出修复建议（补全引号、移除多余逗号等）

## 注意事项

- JSON 的 key 必须用双引号包裹，单引号或裸 key 都不合法
- 尾随逗号（trailing comma）不合法
- 使用 `ensure_ascii=False` 以正确显示中文
- 结果超过约 500 行时截断展示，并提示用户
