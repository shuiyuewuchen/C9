#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pulse MVP v0.1 — Week 1 产出
============================
最小可行产品：读取一个单周 AAR 的 JSON 文件，提取"动力分数"并输出一份
结构化文本报告。目的只有一个——证明"把 AAR 变成可测量数据"这件事
在技术上可行，并且我已经从想法进入了行动。

运行：
    python 赵心皓_C9_mvp.py sample_week.json

设计取舍（Week 1 有意为之的极简）：
 - 只读单周，不读多周（多周趋势留到 V1）
 - 只输出终端文本，不做可视化（可视化留到 V2）
 - 只依赖 Python 标准库
"""
import json
import sys
from pathlib import Path


def bar(score, width=20):
    """把 1-10 的动力分数画成文本条。"""
    filled = max(0, min(width, round(score / 10 * width)))
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def render(week):
    required = ["week", "date", "did", "motivation"]
    for key in required:
        if key not in week:
            raise ValueError("缺少必要字段: " + key)
    score = week["motivation"]
    if not isinstance(score, (int, float)) or not (1 <= score <= 10):
        raise ValueError("motivation 必须是 1-10 的数字")

    lines = []
    lines.append("=" * 46)
    lines.append("  PULSE 单周脉搏报告 v0.1 (MVP)")
    lines.append("=" * 46)
    lines.append("第 {} 周  |  {}".format(week["week"], week["date"]))
    lines.append("")
    lines.append("本周产出：")
    lines.append("  " + str(week.get("did", "（未填写）")))
    lines.append("")
    lines.append("动力指数： {}/10  {}".format(score, bar(score)))
    if score >= 7:
        lines.append("  -> 状态良好，保持节奏")
    elif score >= 5:
        lines.append("  -> 状态一般，留意下滑")
    else:
        lines.append("  -> 警告：动力偏低，需要干预")
    lines.append("=" * 46)
    return "\n".join(lines)


def main():
    if len(sys.argv) != 2:
        print("用法: python 赵心皓_C9_mvp.py <单周AAR.json>")
        sys.exit(1)
    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    # 兼容两种输入：① 直接的周对象（含 motivation）② {"week": {...}} 包装
    # 修复记录：初版误用 data.get("week", data)，当 "week" 是周次数字(1)时
    # 会把 int 当成 dict 传入 render()，触发 TypeError。Week 1 实测发现并修复。
    if isinstance(data, dict) and "motivation" in data:
        week = data
    elif isinstance(data, dict) and isinstance(data.get("week"), dict):
        week = data["week"]
    else:
        week = data
    print(render(week))


if __name__ == "__main__":
    main()
