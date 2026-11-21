# 赵心皓_C9_W7_AI日志.md

## Week 7 AI 使用记录（2026-11-12）

**本周任务**：单元测试生成、导出功能、修复两个接口 bug。

**迭代 1** — 测试生成
- Prompt："为 pulse.py 写 unittest，覆盖：slope 正/负/零/单点、consecutive_declines、risk 分级（健康/危险/空数据）、HTML 含关键区块、demo 数据完整性。放在 tests/test_pulse.py，能 `python -m unittest discover -s tests` 直接跑。"
- AI 输出：13 项测试。
- 我的验证：`Ran 13 tests ... OK`。采纳 ✅。

**迭代 2** — CSV 中文乱码
- Prompt："export csv 在 Excel 打开中文乱码，请修复。"
- AI 输出：在 stdout 写入前加 `\ufeff` BOM。
- 采纳：✅ 实测修复。

**迭代 3** — 参数位置 bug
- Prompt："用户写 `pulse.py analyze --data x` 报 unrecognized arguments，因为 --data 是全局参数。请让它同时支持全局和子命令两种位置。"
- AI 输出：双 dest 方案——全局用 `global_data`、子命令用 `data`，`main` 里 `args.data or args.global_data or DEFAULT_DATA`。
- 采纳：✅ 两种写法实测都通过。

**迭代 4** — README 生成与裁剪
- Prompt："按可独立使用的标准写 README：安装、快速开始、命令表、数据格式、算法说明、验证、已知局限。"
- AI 输出：完整但偏长，我删掉了营销性描述，补上真实的 W5 预警实证。

**心得**：测试 + 边界条件（参数顺序、编码）是 AI 最容易漏的部分，必须主动点名。本周我第一次感受到"有测试罩着"的安全感，改代码不再心惊胆战。
