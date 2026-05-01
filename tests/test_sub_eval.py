"""test_sub_eval — DCN-CHG-20260501-13.

Coverage matrix:
    evaluate_sub:
        - 정상 PASS — 적당한 호출 수 + 다양한 tool
        - REDO_SUSPECT: tool_uses 0 (아예 안 함)
        - REDO_SUSPECT: tool_uses 1 (< MIN_TOOL_USES)
        - REDO_SUSPECT: 같은 tool 5회 (반복)
        - REDO_SUSPECT: prompt 에 Write 약속 + Write+Edit 0건 (prose-only)
        - prompt hint 없으면 prose-only 검사 skip
        - 다중 anomaly 한 번에 검출

    format_histogram:
        - 빈 dict → "(none)"
        - 정렬된 짧은 문자열
"""
from __future__ import annotations

import unittest

from harness.sub_eval import (
    MIN_TOOL_USES,
    REPEAT_TOOL_THRESHOLD,
    evaluate_sub,
    format_histogram,
)


class EvaluateSubTests(unittest.TestCase):
    def test_pass_normal(self):
        result = evaluate_sub({"Read": 4, "Bash": 2, "Write": 1})
        self.assertEqual(result["decision"], "PASS")
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["tool_uses"], 7)

    def test_redo_zero_calls(self):
        result = evaluate_sub({})
        self.assertEqual(result["decision"], "REDO_SUSPECT")
        self.assertTrue(any("tool_uses=0" in a for a in result["anomalies"]))

    def test_redo_below_min(self):
        result = evaluate_sub({"Read": 1})
        self.assertEqual(result["decision"], "REDO_SUSPECT")
        self.assertTrue(any(f"< {MIN_TOOL_USES}" in a for a in result["anomalies"]))

    def test_redo_repeat_tool(self):
        result = evaluate_sub({"Bash": REPEAT_TOOL_THRESHOLD})
        self.assertEqual(result["decision"], "REDO_SUSPECT")
        self.assertTrue(any("Bash" in a and "반복" in a for a in result["anomalies"]))

    def test_redo_prose_only(self):
        # Write 약속 prompt + Write+Edit 0건
        result = evaluate_sub(
            {"Read": 4, "Bash": 1},
            sub_prompt_hint="Write the implementation plan to docs/foo.md",
        )
        self.assertEqual(result["decision"], "REDO_SUSPECT")
        self.assertTrue(any("prose-only" in a for a in result["anomalies"]))

    def test_no_hint_no_prose_check(self):
        # 같은 histogram 이지만 hint 없으면 PASS
        result = evaluate_sub({"Read": 4, "Bash": 1}, sub_prompt_hint="")
        self.assertEqual(result["decision"], "PASS")

    def test_korean_hint_detected(self):
        result = evaluate_sub(
            {"Read": 3},
            sub_prompt_hint="impl 파일 작성해줘",
        )
        self.assertEqual(result["decision"], "REDO_SUSPECT")

    def test_multiple_anomalies(self):
        result = evaluate_sub({"Bash": 6})
        self.assertEqual(result["decision"], "REDO_SUSPECT")
        # 6 개라 MIN_TOOL_USES 통과, REPEAT_TOOL_THRESHOLD 위반 1개
        self.assertEqual(len(result["anomalies"]), 1)


class FormatHistogramTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(format_histogram({}), "(none)")

    def test_normal(self):
        s = format_histogram({"Read": 4, "Bash": 2, "Write": 0})
        # sorted alphabetical
        self.assertEqual(s, "Bash:2 Read:4 Write:0")


if __name__ == "__main__":
    unittest.main()
