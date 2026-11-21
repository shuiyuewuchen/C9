# Pulse（脉搏）—— 个人成长脉搏监测系统

> 把每周 AAR 变成可测量的"生命体征"，用数据发现"缓慢死亡"信号并提前预警。

Pulse 是一个自驱项目（C9）中诞生、并反过来管理这个项目本身的开源命令行工具。
它源于一个真实痛点：**自驱项目最大的敌人不是失败，而是"缓慢死亡"**——你不会某天
突然放弃，而是越来越忙、越来越拖、直到忘了。Pulse 把这条洞察变成了一套可计算的
预警系统。

- 纯 Python 3 标准库实现，**零第三方依赖**，克隆即可运行。
- 单文件 HTML 仪表盘，内嵌 SVG，**无需服务器或联网**即可打开。
- 8 周真实使用数据内置，可一键复现完整进化过程。

---

## 一、安装

```bash
# 1. 确认 Python 版本（需 3.8+）
python3 --version

# 2. 获取项目（本地目录即可，无需 pip install）
cd 03_项目主体_Pulse

# 3. 无需安装依赖
# 本项目仅使用 json / csv / argparse / datetime / pathlib / html 标准库
```

## 二、快速开始（3 条命令看懂全流程）

```bash
python3 pulse.py demo        # ① 写入内置 8 周示例数据
python3 pulse.py analyze     # ② 查看动力曲线 + 缓亡预警
python3 pulse.py dashboard   # ③ 生成 output/dashboard.html，用浏览器打开
```

## 三、命令详解

| 命令 | 作用 | 示例 |
|------|------|------|
| `demo` | 写入内置 8 周真实数据 | `python3 pulse.py demo` |
| `list` | 列出所有周记录 | `python3 pulse.py list` |
| `analyze` | 动力趋势分析 + 缓亡预警（文本） | `python3 pulse.py analyze` |
| `dashboard` | 生成自包含 HTML 仪表盘 | `python3 pulse.py dashboard --out report.html` |
| `export` | 导出 CSV / JSON | `python3 pulse.py export --format csv > weeks.csv` |
| `add` | 追加或更新某一周 | `python3 pulse.py add --file week5.json` |

全局选项 `--data` 可指定数据文件，**放在子命令前后均可**：

```bash
python3 pulse.py --data data/weeks.json analyze
python3 pulse.py analyze --data ../07_验收/W5时刻数据快照.json
```

## 四、数据格式

`data/weeks.json` 中每周是一条记录：

```json
{
  "week": 1,
  "date": "2026-10-01",
  "did": "本周可展示的产出（必填）",
  "worked": "哪些方法有效",
  "failed": "哪些方法失败、为什么",
  "motivation": 7,
  "motivation_note": "动力变化原因",
  "next_plan": "下周计划",
  "output_type": "代码 / 文档 / 报告 / 无",
  "public_link": "公开发布渠道"
}
```

`motivation`（1–10）与 `did` 为核心字段。`output_type` 填"无"会被判定为**无可见产出**，
计入缓亡风险。

## 五、缓亡预警算法（Slow Death Detector）

风险分 0–100，由四类信号加权得出：

| 信号 | 判定 | 最高加分 |
|------|------|----------|
| 动力绝对值过低 | ≤5 分 +25，≤3 分 +40 | +40 |
| 动力趋势下滑 | 最近 4 周回归斜率 < −0.3 | +30 |
| 连续无可见产出 | 连续 ≥2 周无产出 | +30 |
| 连续下降周数 | 连续 ≥3 周下降 | +15 |

分级：`≥60 危险` / `≥40 警告` / `≥20 关注` / `其余 健康`。

**实证**：用本项目的 W1–W5 数据运行 `analyze`，工具输出 `85/100 [critical]`，
准确在我动力最低、连续无产出的那一周发出预警——这是"自举"最有说服力的证据。

## 六、项目结构

```
03_项目主体_Pulse/
├── pulse.py              # 主程序（全部逻辑，单文件）
├── README.md             # 本说明
├── requirements.txt      # 依赖声明（无第三方依赖）
├── data/weeks.json       # 8 周真实数据
├── tests/test_pulse.py   # 13 项单元测试
└── output/dashboard.html # 生成的仪表盘（可直接打开）
```

## 七、验证

```bash
python3 -m unittest discover -s tests -v   # 13 tests, OK
```

## 八、8 周进化路径

| 阶段 | 周次 | 关键产出 |
|------|------|----------|
| MVP | W1 | 单周 JSON → 文本动力报告（修复解析 bug） |
| V1 | W2 | 多周数据层 + 文本动力曲线 |
| V2 | W3–W4 | SVG 折线图 + HTML 仪表盘 + 预警算法设计 |
| 低谷与干预 | W5–W6 | 触发失败信号 → 降范围 → 预警算法落地 |
| V3 | W7–W8 | 自举自用 + 导出 + 测试 + 复盘报告 |

## 九、已知局限与后续

- 数据需手工录入，尚未接入自动抓取（AAR 文件 / Git 提交 / 日历）。
- 单用户本地工具，无 Web 服务、无协同。
- 预警基于规则阈值，非预测模型；样本量小时斜率可能不稳定。

后续计划：接入 AAR Markdown 自动解析、加入 7 日移动平均与趋势预测、提供轻量 Web UI。

## 十、公开与许可

公开渠道：GitHub（代码）+ Elite20 群（进度）。MIT License，可自由使用与改进。
