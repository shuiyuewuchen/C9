#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pulse 单元测试 —— 覆盖数据层、预警算法与展示层。运行：python -m unittest discover -s tests -v"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pulse  # noqa: E402


class TestAnalysis(unittest.TestCase):
    def test_slope_increasing(self):
        self.assertGreater(pulse.slope([1, 3, 5, 7, 9]), 0)

    def test_slope_decreasing(self):
        self.assertLess(pulse.slope([9, 7, 5, 3, 1]), 0)

    def test_slope_flat(self):
        self.assertEqual(pulse.slope([5, 5, 5, 5]), 0.0)

    def test_slope_single(self):
        self.assertEqual(pulse.slope([5]), 0.0)

    def test_consecutive_declines(self):
        self.assertEqual(pulse.consecutive_declines([7, 8, 6, 5, 4]), 3)
        self.assertEqual(pulse.consecutive_declines([3, 5, 6, 8]), 0)

    def test_has_output(self):
        self.assertTrue(pulse.has_output({"output_type": "代码"}))
        self.assertFalse(pulse.has_output({"output_type": "无"}))
        self.assertFalse(pulse.has_output({}))


class TestRisk(unittest.TestCase):
    def _data(self, motivations, outputs=None):
        outputs = outputs or ["代码"] * len(motivations)
        return {"project": "t", "weeks": [
            {"week": i + 1, "date": "2026-01-01", "did": "x", "motivation": m, "output_type": o}
            for i, (m, o) in enumerate(zip(motivations, outputs))
        ]}

    def test_healthy(self):
        r = pulse.risk_assessment(self._data([7, 8, 8, 9]))
        self.assertEqual(r["level"], "healthy")

    def test_critical_low_and_no_output(self):
        r = pulse.risk_assessment(self._data([8, 5, 3, 2], ["代码", "文档", "无", "无"]))
        self.assertEqual(r["level"], "critical")
        self.assertGreaterEqual(r["score"], 60)

    def test_warning_decline(self):
        r = pulse.risk_assessment(self._data([9, 7, 6, 4]))
        self.assertIn(r["level"], ("warning", "critical"))

    def test_empty(self):
        r = pulse.risk_assessment({"weeks": []})
        self.assertEqual(r["level"], "healthy")


class TestRendering(unittest.TestCase):
    def test_dashboard_contains_sections(self):
        h = pulse.render_dashboard(pulse.DEMO_DATA)
        self.assertIn("动力曲线", h)
        self.assertIn("缓亡预警", h)
        self.assertIn("<svg", h)
        self.assertIn("周记录明细", h)

    def test_text_report(self):
        t = pulse.text_report(pulse.DEMO_DATA)
        self.assertIn("动力序列", t)
        self.assertIn("缓亡风险", t)

    def test_demo_data_complete(self):
        self.assertEqual(len(pulse.DEMO_DATA["weeks"]), 8)
        for w in pulse.DEMO_DATA["weeks"]:
            self.assertIn("motivation", w)
            self.assertIn("next_plan", w)


if __name__ == "__main__":
    unittest.main()
