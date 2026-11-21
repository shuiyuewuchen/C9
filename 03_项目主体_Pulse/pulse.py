#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pulse（脉搏）—— 个人成长脉搏监测系统
========================================
把每周 AAR 变成可测量的"生命体征"，用数据发现"缓慢死亡"信号并提前预警。

设计哲学
--------
自驱项目最大的敌人不是失败，而是"缓慢死亡"：你不会某天突然放弃，
而是越来越忙、越来越拖、直到忘了。Pulse 把 CHALLENGE 里那条重要洞察
（"提前定义什么情况说明我已经放弃了"）变成了一套可计算的预警系统。

特性
----
  list      列出所有周记录
  analyze   动力趋势分析 + 缓亡预警（文本报告）
  dashboard 生成自包含 HTML 仪表盘（内嵌 SVG，无外部依赖）
  export    导出 CSV / JSON
  add       追加/更新一周记录
  demo      用内置示例数据初始化

依赖：仅 Python 3 标准库（json / csv / argparse / datetime / pathlib / html）
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DATA = Path(__file__).parent / "data" / "weeks.json"
DEFAULT_OUT = Path(__file__).parent / "output" / "dashboard.html"

# "没有产出"的判定值（大小写/空白不敏感）
NO_OUTPUT_MARKERS = {"", "无", "none", "n/a", "没有", "停滞"}


# ---------------------------------------------------------------------------
# 数据层
# ---------------------------------------------------------------------------
def load_data(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "weeks" not in data or not isinstance(data["weeks"], list):
        raise ValueError("数据文件缺少 weeks 数组")
    data["weeks"].sort(key=lambda w: w.get("week", 0))
    return data


def save_data(data: dict, path: Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def has_output(week: dict) -> bool:
    value = str(week.get("output_type", week.get("did", ""))).strip().lower()
    return value not in NO_OUTPUT_MARKERS


# ---------------------------------------------------------------------------
# 分析层
# ---------------------------------------------------------------------------
def slope(values: list[float]) -> float:
    """最小二乘线性回归斜率（每周期望变化量），不依赖第三方库。"""
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    mx, my = sum(xs) / n, sum(values) / n
    denom = sum((x - mx) ** 2 for x in xs)
    if denom == 0:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, values)) / denom


def consecutive_declines(values: list[int]) -> int:
    """末尾连续下降的周数。"""
    count = 0
    for i in range(len(values) - 1, 0, -1):
        if values[i] < values[i - 1]:
            count += 1
        else:
            break
    return count


def risk_assessment(data: dict) -> dict:
    """
    缓亡预警（Slow Death Detector）
    ------------------------------
    综合 4 类信号算出 0-100 的风险分：
      1) 动力绝对值过低        最高 +40
      2) 动力趋势持续下滑      最高 +30
      3) 连续无可见产出        最高 +30
      4) 连续下降周数          最高 +15
    分级：>=60 critical / >=40 warning / >=20 watch / 其余 healthy。
    """
    weeks = data["weeks"]
    if not weeks:
        return {"score": 0, "level": "healthy", "reasons": ["暂无数据"]}

    scores = [int(w.get("motivation", 0)) for w in weeks]
    recent = scores[-4:]
    latest = recent[-1]
    recent_slope = slope(recent)
    declines = consecutive_declines(scores)
    no_out_streak = 0
    for w in reversed(weeks):
        if not has_output(w):
            no_out_streak += 1
        else:
            break

    score = 0
    reasons = []
    if latest <= 3:
        score += 40
        reasons.append("动力绝对值极低（%d/10），接近放弃边缘" % latest)
    elif latest <= 5:
        score += 25
        reasons.append("动力偏低（%d/10），需要主动干预" % latest)
    elif latest <= 6:
        score += 10
        reasons.append("动力中等（%d/10），留意下滑趋势" % latest)

    if recent_slope < -0.8:
        score += 30
        reasons.append("最近4周动力快速下滑（斜率 %.2f/周）" % recent_slope)
    elif recent_slope < -0.3:
        score += 18
        reasons.append("最近4周动力持续下滑（斜率 %.2f/周）" % recent_slope)
    elif recent_slope < 0:
        score += 8
        reasons.append("最近4周动力轻微下滑（斜率 %.2f/周）" % recent_slope)

    if no_out_streak >= 2:
        score += 30
        reasons.append("连续 %d 周无可见产出，命中" % no_out_streak + "失败信号")
    elif no_out_streak == 1:
        score += 15
        reasons.append("本周无可见产出，需尽快补上")

    if declines >= 3:
        score += 15
        reasons.append("连续 %d 周动力下降" % declines)
    elif declines == 2:
        score += 8
        reasons.append("连续 2 周动力下降")

    score = min(100, score)
    if score >= 60:
        level = "critical"
    elif score >= 40:
        level = "warning"
    elif score >= 20:
        level = "watch"
    else:
        level = "healthy"
    if not reasons:
        reasons.append("各项指标正常，保持当前节奏")
    return {
        "score": score,
        "level": level,
        "slope": round(recent_slope, 2),
        "declines": declines,
        "no_output_streak": no_out_streak,
        "reasons": reasons,
    }


LEVEL_CN = {"healthy": "健康", "watch": "关注", "warning": "警告", "critical": "危险"}
LEVEL_COLOR = {"healthy": "#16a34a", "watch": "#2563eb", "warning": "#ea580c", "critical": "#dc2626"}


# ---------------------------------------------------------------------------
# 展示层：文本
# ---------------------------------------------------------------------------
def ascii_chart(scores: list[int], width: int = 40) -> list[str]:
    lines = []
    for tick in (10, 8, 6, 4, 2):
        row = ""
        for s in scores:
            row += "  #  " if s >= tick else "  .  "
        lines.append("%2d |%s" % (tick, row))
    lines.append("   +" + "-" * (len(scores) * 5))
    lines.append("    " + " ".join("W%d" % (i + 1) for i in range(len(scores))))
    return lines


def text_report(data: dict) -> str:
    weeks = data["weeks"]
    scores = [int(w.get("motivation", 0)) for w in weeks]
    risk = risk_assessment(data)
    out = []
    out.append("=" * 58)
    out.append("  PULSE 脉搏分析  |  %s" % data.get("project", "未命名项目"))
    out.append("=" * 58)
    out.append("记录周数：%d    动力序列：%s" % (len(weeks), scores))
    out.append("")
    out.extend(ascii_chart(scores))
    out.append("")
    out.append("最近4周斜率：%.2f / 周    连续下降：%d 周" % (risk["slope"], risk["declines"]))
    out.append("缓亡风险：%d/100  [%s]  %s" % (risk["score"], risk["level"], LEVEL_CN[risk["level"]]))
    out.append("预警依据：")
    for r in risk["reasons"]:
        out.append("  - " + r)
    out.append("=" * 58)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# 展示层：SVG + HTML 仪表盘
# ---------------------------------------------------------------------------
def svg_line_chart(scores: list[int], labels: list[str]) -> str:
    """生成内嵌 SVG 折线图（浅色主题，无外部依赖）。"""
    W, H = 720, 300
    left, right, top, bottom = 52, 24, 28, 52
    pw, ph = W - left - right, H - top - bottom
    n = len(scores)

    def x_at(i):
        return left if n == 1 else left + i * pw / (n - 1)

    def y_at(v):
        return top + ph - (max(1, min(10, v)) - 1) / 9 * ph

    parts = ['<svg viewBox="0 0 %d %d" width="100%%" role="img" aria-label="动力曲线">' % (W, H)]
    # 网格与 y 轴刻度
    for tick in (1, 3, 5, 7, 10):
        y = y_at(tick)
        parts.append(
            '<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#e5e7eb" stroke-width="1"/>'
            % (left, y, W - right, y)
        )
        parts.append(
            '<text x="%d" y="%.1f" font-size="11" fill="#6b7280" text-anchor="end">%d</text>'
            % (left - 8, y + 4, tick)
        )
    # 折线
    pts = " ".join("%.1f,%.1f" % (x_at(i), y_at(s)) for i, s in enumerate(scores))
    parts.append(
        '<polyline points="%s" fill="none" stroke="#2563eb" stroke-width="3" '
        'stroke-linejoin="round" stroke-linecap="round"/>' % pts
    )
    # 面积
    area = "%s %.1f,%.1f %.1f,%.1f" % (pts, x_at(n - 1), y_at(1), x_at(0), y_at(1))
    parts.append('<polygon points="%s" fill="#dbeafe" opacity="0.55"/>' % area)
    # 数据点与标签
    for i, s in enumerate(scores):
        x, y = x_at(i), y_at(s)
        parts.append('<circle cx="%.1f" cy="%.1f" r="5" fill="#2563eb" stroke="#fff" stroke-width="2"/>' % (x, y))
        parts.append(
            '<text x="%.1f" y="%.1f" font-size="12" font-weight="600" fill="#1e3a8a" text-anchor="middle">%d</text>'
            % (x, y - 12, s)
        )
        parts.append(
            '<text x="%.1f" y="%d" font-size="11" fill="#6b7280" text-anchor="middle">%s</text>'
            % (x, H - bottom + 20, html.escape(str(labels[i])))
        )
    parts.append("</svg>")
    return "\n".join(parts)


def render_dashboard(data: dict) -> str:
    weeks = data["weeks"]
    scores = [int(w.get("motivation", 0)) for w in weeks]
    labels = ["W%d" % w.get("week", i + 1) for i, w in enumerate(weeks)]
    risk = risk_assessment(data)
    color = LEVEL_COLOR[risk["level"]]
    chart = svg_line_chart(scores, labels)
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")

    rows = []
    for w in weeks:
        did = html.escape(str(w.get("did", "")))
        plan = html.escape(str(w.get("next_plan", "")))
        rows.append(
            "<tr><td><b>W%s</b><br><span class='muted'>%s</span></td>"
            "<td>%s</td><td style='text-align:center'>%d</td>"
            "<td>%s</td><td>%s</td></tr>"
            % (
                html.escape(str(w.get("week", ""))),
                html.escape(str(w.get("date", ""))),
                did,
                int(w.get("motivation", 0)),
                html.escape(str(w.get("output_type", "—"))),
                plan,
            )
        )

    reasons_html = "".join("<li>%s</li>" % html.escape(r) for r in risk["reasons"])

    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pulse · 脉搏仪表盘</title>
<style>
  :root {{ --bg:#f5f7fa; --card:#ffffff; --ink:#1f2937; --muted:#6b7280; --line:#e5e7eb; --accent:#2563eb; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
         font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif; }}
  .wrap {{ max-width:900px; margin:0 auto; padding:32px 20px 56px; }}
  header h1 {{ margin:0 0 4px; font-size:26px; }}
  header p {{ margin:0 0 24px; color:var(--muted); font-size:14px; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:14px;
          padding:20px 22px; margin-bottom:18px; box-shadow:0 1px 3px rgba(16,24,40,.04); }}
  .card h2 {{ margin:0 0 14px; font-size:16px; }}
  .risk {{ display:flex; gap:16px; align-items:center; }}
  .risk .num {{ font-size:40px; font-weight:700; color:{color}; line-height:1; }}
  .risk .tag {{ display:inline-block; padding:3px 10px; border-radius:999px; color:#fff;
               background:{color}; font-size:12px; font-weight:600; }}
  .risk ul {{ margin:0; padding-left:18px; color:var(--muted); font-size:13px; line-height:1.7; }}
  table {{ width:100%%; border-collapse:collapse; font-size:13px; }}
  th,td {{ text-align:left; padding:10px 8px; border-bottom:1px solid var(--line); vertical-align:top; }}
  th {{ color:var(--muted); font-weight:600; }}
  .muted {{ color:var(--muted); font-size:11px; }}
  footer {{ color:var(--muted); font-size:12px; text-align:center; margin-top:28px; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Pulse · 脉搏仪表盘</h1>
    <p>{project} · 生成于 {now}</p>
  </header>

  <section class="card">
    <h2>动力曲线（1–10）</h2>
    {chart}
  </section>

  <section class="card">
    <h2>缓亡预警 · Slow Death Detector</h2>
    <div class="risk">
      <div class="num">{score}</div>
      <div>
        <span class="tag">{level_cn}</span>
        <ul>{reasons}</ul>
      </div>
    </div>
  </section>

  <section class="card">
    <h2>周记录明细</h2>
    <table>
      <thead><tr><th>周次</th><th>本周产出</th><th>动力</th><th>产出类型</th><th>下周计划</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </section>

  <footer>由 Pulse 生成 · 把 AAR 变成可测量的生命体征</footer>
</div>
</body>
</html>
""".format(
        color=color,
        project=html.escape(str(data.get("project", "未命名项目"))),
        now=html.escape(now),
        chart=chart,
        score=risk["score"],
        level_cn=LEVEL_CN[risk["level"]],
        reasons=reasons_html,
        rows="\n".join(rows),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
DEMO_DATA = {
    "project": "Pulse 自驱项目 · 8周实证",
    "owner": "赵心皓",
    "weeks": [
        {"week": 1, "date": "2026-10-01", "did": "完成 MVP v0.1：单周 AAR JSON→文本动力报告，命令行跑通（修复解析 bug）", "worked": "仅标准库、最小依赖快速验证核心假设", "failed": "只支持单周，无趋势；输出不可视化、不便分享", "motivation": 7, "motivation_note": "从想法进入行动，跑通那一刻很有成就感", "next_plan": "V1：支持多周数据，画第一条动力曲线", "output_type": "代码", "public_link": "Elite20 群"},
        {"week": 2, "date": "2026-10-08", "did": "V1：多周数据存储 + 文本动力曲线 analyze 命令", "worked": "JSON 数据层 + 最小二乘斜率，CLI 分命令设计清晰", "failed": "斜率算法一开始用 statistics.linear_regression，Python 3.9 环境不兼容", "motivation": 8, "motivation_note": "看到曲线成形，'数据化反思'的假设被证实", "next_plan": "V2：做 HTML 仪表盘，让成果可展示", "output_type": "代码", "public_link": "Elite20 群"},
        {"week": 3, "date": "2026-10-15", "did": "V2 初版：SVG 动力折线图 + HTML 仪表盘骨架", "worked": "内嵌 SVG 避免外部依赖，单文件可直接打开", "failed": "f-string 与 CSS 大括号冲突，调试花了一小时", "motivation": 6, "motivation_note": "C8 真实项目进入交付高峰，时间被挤压", "next_plan": "加入缓亡预警算法；控制本周范围", "output_type": "代码", "public_link": "Elite20 群"},
        {"week": 4, "date": "2026-10-22", "did": "完成缓亡预警算法设计文档与伪代码（无新增代码产出）", "worked": "把'缓慢死亡'拆成4类可计算信号，逻辑清晰", "failed": "只写了设计没落地代码；连续两周编码停滞", "motivation": 5, "motivation_note": "并行项目疲惫，觉得'写文档'不算真产出，有点心虚", "next_plan": "强制把设计变成代码；降低范围到最小", "output_type": "文档", "public_link": "Elite20 群"},
        {"week": 5, "date": "2026-10-29", "did": "无新产出（本周触发自设失败信号）", "worked": "诚实记录了'本周停滞'，没有粉饰", "failed": "连续两周无代码产出，动力跌到低点；工具本身发出 warning", "motivation": 4, "motivation_note": "最低点。Pulse 自己预警了我——这是最真实的一次'自举'", "next_plan": "执行干预：砍掉非核心功能、公开承诺、把最低标准降到'每周1个commit'", "output_type": "无", "public_link": "Elite20 群"},
        {"week": 6, "date": "2026-11-05", "did": "干预后回升：完成预警算法落地 + 仪表盘风险卡片", "worked": "降范围策略有效；公开承诺带来外部推力", "failed": "预警阈值一开始过于灵敏，误报健康周；回调阈值", "motivation": 6, "motivation_note": "从谷底回来，看到工具真的帮到了自己", "next_plan": "V3：用 Pulse 管理本项目的真实 AAR，形成自举闭环", "output_type": "代码", "public_link": "GitHub + Elite20 群"},
        {"week": 7, "date": "2026-11-12", "did": "V3：内置8周真实数据 demo、export 导出、单元测试与 README", "worked": "自举：本周 AAR 直接由 Pulse 生成并纳入数据", "failed": "导出 CSV 时中文乱码，指定 utf-8-sig 后解决", "motivation": 8, "motivation_note": "工具开始稳定产出价值，正反馈建立", "next_plan": "最终验收：全量测试 + 仪表盘 + 复盘报告", "output_type": "代码", "public_link": "GitHub + Elite20 群"},
        {"week": 8, "date": "2026-11-19", "did": "最终版：全量测试通过、仪表盘生成、8周复盘报告导出", "worked": "一个持续运行、我会继续用下去的系统成型", "failed": "仍有不足：无 Web 服务、无多用户、预警依赖手工录入", "motivation": 9, "motivation_note": "完成不是终点，是'我会继续做'的开始", "next_plan": "Elite20 之后继续：接入自动抓取、加趋势预测", "output_type": "报告", "public_link": "GitHub + Elite20 群"},
    ],
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Pulse 个人成长脉搏监测系统")
    # --data 同时支持全局位置与子命令位置（V2.1 修复：初版只支持全局位置，
    # 用户自然写成 `pulse.py analyze --data x` 会报 unrecognized arguments）
    p.add_argument("--data", dest="global_data", type=Path, default=None, help="数据文件路径")
    sub = p.add_subparsers(dest="cmd")

    def with_data(parser):
        parser.add_argument("--data", dest="data", type=Path, default=None, help="数据文件路径")
        return parser

    with_data(sub.add_parser("list", help="列出所有周记录"))
    with_data(sub.add_parser("analyze", help="动力趋势分析 + 缓亡预警"))
    d = with_data(sub.add_parser("dashboard", help="生成 HTML 仪表盘"))
    d.add_argument("--out", type=Path, default=DEFAULT_OUT, help="输出 HTML 路径")

    e = with_data(sub.add_parser("export", help="导出数据"))
    e.add_argument("--format", choices=["csv", "json"], default="csv")

    a = with_data(sub.add_parser("add", help="追加/更新一周记录"))
    a.add_argument("--file", type=Path, required=True, help="单周 JSON 文件")
    with_data(sub.add_parser("demo", help="写入内置8周示例数据"))
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    cmd = args.cmd
    data_path = getattr(args, "data", None) or args.global_data or DEFAULT_DATA

    if cmd == "demo":
        save_data(DEMO_DATA, data_path)
        print("已写入示例数据：%s（%d 周）" % (data_path, len(DEMO_DATA["weeks"])))
        return 0

    if cmd == "add":
        incoming = json.loads(Path(args.file).read_text(encoding="utf-8"))
        incoming = incoming.get("week", incoming) if isinstance(incoming.get("week"), dict) else incoming
        if "motivation" not in incoming:
            print("错误：记录缺少 motivation 字段", file=sys.stderr)
            return 2
        if data_path.exists():
            data = load_data(data_path)
        else:
            data = {"project": "Pulse 自驱项目", "owner": "赵心皓", "weeks": []}
        data["weeks"] = [w for w in data["weeks"] if w.get("week") != incoming["week"]]
        data["weeks"].append(incoming)
        save_data(data, data_path)
        print("已写入第 %s 周记录" % incoming["week"])
        return 0

    if not data_path.exists():
        print("错误：数据文件不存在，请先运行 'pulse.py demo' 或 --data 指定路径", file=sys.stderr)
        return 2
    data = load_data(data_path)

    if cmd == "list":
        for w in data["weeks"]:
            print("W%-2s %s  动力 %s/10  [%s]  %s"
                  % (w.get("week"), w.get("date"), w.get("motivation"),
                     w.get("output_type", "—"), str(w.get("did", ""))[:38]))
    elif cmd == "analyze":
        print(text_report(data))
    elif cmd == "dashboard":
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(render_dashboard(data), encoding="utf-8")
        print("仪表盘已生成：%s" % args.out)
    elif cmd == "export":
        if args.format == "json":
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            import io
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["week", "date", "did", "motivation", "output_type", "next_plan", "public_link"])
            for w in data["weeks"]:
                writer.writerow([w.get(k, "") for k in
                                 ["week", "date", "did", "motivation", "output_type", "next_plan", "public_link"]])
            sys.stdout.buffer.write(("\ufeff" + buf.getvalue()).encode("utf-8"))
    else:
        build_parser().print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
