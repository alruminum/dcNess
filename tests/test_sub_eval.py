"""test_sub_eval — DCN-CHG-20260501-13.

Coverage matrix:
    evaluate_sub:
        - 정상 PASS — 적당한 호출 수 + 다양한 tool
        - REDO_SUSPECT: tool_uses 0 (아예 안 함)
        - REDO_SUSPECT: tool_uses 1 (< MIN_TOOL_USES)
        - REDO_SUSPECT: 도구별 차등 임계 초과 반복 (#272/#273 baseline 반영)
        - REDO_SUSPECT: prompt 에 Write 약속 + Write+Edit 0건 (prose-only)
        - prompt hint 없으면 prose-only 검사 skip
        - prose-only sub_type (qa/validator/pr-reviewer …) 시 promised_write 검사 skip
        - 다중 anomaly 한 번에 검출

    format_histogram:
        - 빈 dict → "(none)"
        - 정렬된 짧은 문자열
"""
from __future__ import annotations

import unittest

from harness.sub_eval import (
    MIN_TOOL_USES,
    PROSE_ONLY_AGENTS,
    REPEAT_TOOL_THRESHOLDS,
    REPEAT_TOOL_THRESHOLD_DEFAULT,
    evaluate_sub,
    format_histogram,
)


class EvaluateSubTests(unittest.TestCase):
    def test_pass_normal(self):
        result = evaluate_sub({"Read": 4, "Bash": 2, "Write": 1})
        self.assertEqual(result["decision"], "PASS")
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["tool_uses"], 7)

    def test_pass_realistic_architect_baseline(self):
        # #273 W1 — architect MODULE_PLAN 정상 패턴 (Read×8 Bash×5 Write×1 Edit×2)
        result = evaluate_sub(
            {"Read": 8, "Bash": 5, "Write": 1, "Edit": 2},
            sub_type="architect",
        )
        self.assertEqual(result["decision"], "PASS", msg=result)

    def test_pass_realistic_engineer_baseline(self):
        # #273 W1 — engineer IMPL 정상 패턴 (Read×6 Edit×6 Bash×2)
        result = evaluate_sub(
            {"Read": 6, "Edit": 6, "Bash": 2},
            sub_type="engineer",
        )
        self.assertEqual(result["decision"], "PASS", msg=result)

    def test_pass_realistic_pr_reviewer_baseline(self):
        # #272 W1 — pr-reviewer prose-only 정상 (Read×5)
        result = evaluate_sub(
            {"Read": 5},
            sub_type="pr-reviewer",
        )
        self.assertEqual(result["decision"], "PASS", msg=result)

    def test_redo_zero_calls(self):
        result = evaluate_sub({})
        self.assertEqual(result["decision"], "REDO_SUSPECT")
        self.assertTrue(any("tool_uses=0" in a for a in result["anomalies"]))

    def test_redo_below_min(self):
        result = evaluate_sub({"Read": 1})
        self.assertEqual(result["decision"], "REDO_SUSPECT")
        self.assertTrue(any(f"< {MIN_TOOL_USES}" in a for a in result["anomalies"]))

    def test_prose_only_sub_skips_min_tool_uses(self):
        # #272 W1 보완 — prose-only sub 는 file-op 0건도 정상.
        for sub in ("pr-reviewer", "qa", "validator"):
            with self.subTest(sub=sub):
                result = evaluate_sub({}, sub_type=sub)
                self.assertEqual(
                    result["decision"], "PASS",
                    msg=f"{sub} → {result} (prose-only file-op 0 도 정상)",
                )

    def test_engineer_below_min_still_fires(self):
        # 일반 sub 는 file-op 1건 미만 시 anomaly 유지
        result = evaluate_sub({"Read": 1}, sub_type="engineer")
        self.assertEqual(result["decision"], "REDO_SUSPECT")

    def test_redo_repeat_read(self):
        # Read 임계 15
        result = evaluate_sub({"Read": REPEAT_TOOL_THRESHOLDS["Read"]})
        self.assertEqual(result["decision"], "REDO_SUSPECT")
        self.assertTrue(any("Read" in a and "반복" in a for a in result["anomalies"]))

    def test_redo_repeat_edit(self):
        # Edit 임계 12
        result = evaluate_sub({"Edit": REPEAT_TOOL_THRESHOLDS["Edit"]})
        self.assertEqual(result["decision"], "REDO_SUSPECT")
        self.assertTrue(any("Edit" in a for a in result["anomalies"]))

    def test_redo_repeat_unknown_tool_uses_default(self):
        # 미정의 도구는 default 임계 적용
        result = evaluate_sub({"Foo": REPEAT_TOOL_THRESHOLD_DEFAULT})
        self.assertEqual(result["decision"], "REDO_SUSPECT")

    def test_under_threshold_read_passes(self):
        # Read 14 < 15 → PASS
        result = evaluate_sub({"Read": REPEAT_TOOL_THRESHOLDS["Read"] - 1})
        self.assertEqual(result["decision"], "PASS", msg=result)

    def test_redo_prose_only_no_sub_type(self):
        # sub_type 미명시 → 폴백으로 promised_write 검사 진행
        result = evaluate_sub(
            {"Read": 4, "Bash": 1},
            sub_prompt_hint="Write the implementation plan to docs/foo.md",
        )
        self.assertEqual(result["decision"], "REDO_SUSPECT")
        self.assertTrue(any("prose-only" in a for a in result["anomalies"]))

    def test_prose_only_agent_skips_promised_write_check(self):
        # #272 W1 — qa 는 prose-only. Write 약속 prompt + Write+Edit 0건이 정상.
        for sub in ("qa", "validator", "pr-reviewer", "design-critic"):
            with self.subTest(sub=sub):
                result = evaluate_sub(
                    {"Read": 4, "Bash": 1},
                    sub_prompt_hint="Write your validation report",
                    sub_type=sub,
                )
                self.assertEqual(result["decision"], "PASS", msg=f"{sub} → {result}")

    def test_prose_only_agent_namespaced(self):
        # plugin-namespaced (e.g. "dcness:qa") 도 prose-only 처리
        result = evaluate_sub(
            {"Read": 4},
            sub_prompt_hint="작성해줘",
            sub_type="dcness:qa",
        )
        self.assertEqual(result["decision"], "PASS", msg=result)

    def test_engineer_promised_write_still_fires(self):
        # engineer 는 prose-only X — Write 약속 후 0건이면 anomaly
        result = evaluate_sub(
            {"Read": 4},
            sub_prompt_hint="구현 코드 작성",
            sub_type="engineer",
        )
        self.assertEqual(result["decision"], "REDO_SUSPECT")

    def test_no_hint_no_prose_check(self):
        # 같은 histogram 이지만 hint 없으면 PASS
        result = evaluate_sub({"Read": 4, "Bash": 1}, sub_prompt_hint="")
        self.assertEqual(result["decision"], "PASS")

    def test_korean_hint_detected(self):
        result = evaluate_sub(
            {"Read": 3},
            sub_prompt_hint="impl 파일 작성해줘",
            sub_type="engineer",
        )
        self.assertEqual(result["decision"], "REDO_SUSPECT")

    def test_prose_only_agents_constant(self):
        # 화이트리스트 회귀 방지 — 핵심 prose-only agent 누락 X
        for sub in ("qa", "validator", "pr-reviewer", "design-critic",
                    "security-reviewer", "plan-reviewer"):
            self.assertIn(sub, PROSE_ONLY_AGENTS)


class FormatHistogramTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(format_histogram({}), "(none)")

    def test_normal(self):
        s = format_histogram({"Read": 4, "Bash": 2, "Write": 0})
        # sorted alphabetical
        self.assertEqual(s, "Bash:2 Read:4 Write:0")


if __name__ == "__main__":
    unittest.main()
