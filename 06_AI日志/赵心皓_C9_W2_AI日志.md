# 赵心皓_C9_W2_AI日志.md

## Week 2 AI 使用记录（2026-10-08）

**本周任务**：扩展多周数据层与文本动力曲线，解决斜率算法兼容性。

**迭代 1** — 让 AI 加多周分析
- Prompt："在 MVP 基础上加多周支持：data/weeks.json 存数组，analyze 命令输出 ASCII 折线图和最近几周的趋势斜率。只许用标准库。"
- AI 输出：给出 `statistics.linear_regression` 方案。
- 我的验证：本地 Python 3.9 运行报 `AttributeError`——该 API 是 3.10+ 才有的。

**迭代 2** — 定向替换
- Prompt："statistics.linear_regression 在 Python 3.9 不可用。请手写最小二乘斜率函数 slope(values)，无依赖，并给出 5 组测试数据（递增/递减/平坦/单点/两点）。"
- AI 输出：6 行实现 + 测试建议。
- 采纳：✅ 采纳实现，测试建议并入 W7 的单元测试。

**迭代 3** — 提示词优化
- 我发现只要在 prompt 里加一句"只许用 Python 3.8+ 标准库，不要引入 3.10 新 API"，AI 就不会再犯同类错误。这条约束被我写进了后续所有代码 prompt 的模板。

**心得**："拿来"一个库 API 前要先确认版本边界。AI 对版本兼容性并不总能主动规避，约束要由人给出。
