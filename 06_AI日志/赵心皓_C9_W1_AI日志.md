# 赵心皓_C9_W1_AI日志.md

## Week 1 AI 使用记录（2026-10-01）

**本周任务**：用 AI 生成 MVP 脚本初稿，并用真实数据验证、修复。

**迭代 1** — 初稿生成
- Prompt："用 Python 标准库写脚本，读取含 week/date/did/motivation 的 JSON，输出带 20 格文本条的动力报告，命令行可跑。"
- AI 输出：结构正确的 60 行脚本。
- 我的判断：框架采纳，但 `week = data.get("week", data)` 一行有隐藏假设，我保留待验证。

**迭代 2** — 带错误反馈的定向修复
- 运行真实 `sample_week.json` 报 `TypeError: argument of type 'int' is not iterable`。
- Prompt："代码在这份数据上报错了：[traceback + 数据]。week 是周次数字不是对象，请兼容两种输入格式并加注释。"
- AI 输出：三分支类型判断修复版。
- 采纳：✅ 全部采纳，我补上"Week 1 实测发现并修复"的注释。

**心得**：AI 生成的代码"看起来对"和"真的能跑"是两件事。真实数据是照妖镜。—— 这条后来成了整个项目的核心方法论。
