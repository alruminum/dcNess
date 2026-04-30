"""tests/test_run_review.py — DCN-CHG-20260430-19 run_review 단위 테스트."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from harness.run_review import (  # noqa: E402
    StepRecord, build_report, detect_goods, detect_wastes,
    parse_steps, render_report, list_runs, find_run_dir,
    _normalize_agent_type, assign_invocations_to_steps,
    EXPECTED_AGENT_BUDGETS,
)


def _make_run_dir(tmp: Path, sid: str, rid: str, step_records: list[dict],
                    prose_files: dict[str, str] | None = None) -> Path:
    run_dir = tmp / ".claude" / "harness-state" / ".sessions" / sid / "runs" / rid
    run_dir.mkdir(parents=True, exist_ok=True)
    jsonl = run_dir / ".steps.jsonl"
    with open(jsonl, "w", encoding="utf-8") as f:
        for r in step_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    for filename, content in (prose_files or {}).items():
        (run_dir / filename).write_text(content, encoding="utf-8")
    return run_dir


class ParseStepsTests(unittest.TestCase):
    def test_parses_steps_jsonl(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            rd = _make_run_dir(tmp, "sid1", "rid1", [
                {"ts": "2026-04-30T10:00:00", "agent": "architect", "mode": "MODULE_PLAN",
                 "enum": "READY_FOR_IMPL", "must_fix": False,
                 "prose_excerpt": "## 결론\nMODULE_PLAN 완성\nREADY_FOR_IMPL"},
                {"ts": "2026-04-30T10:05:00", "agent": "engineer", "mode": "IMPL",
                 "enum": "IMPL_DONE", "must_fix": False,
                 "prose_excerpt": "구현 완료\n## 결론\nIMPL_DONE"},
            ])
            steps = parse_steps(rd)
            self.assertEqual(len(steps), 2)
            self.assertEqual(steps[0].agent, "architect")
            self.assertEqual(steps[0].mode, "MODULE_PLAN")
            self.assertEqual(steps[0].enum, "READY_FOR_IMPL")
            self.assertEqual(steps[0].elapsed_s, 300)
            self.assertEqual(steps[1].agent, "engineer")

    def test_returns_empty_when_no_jsonl(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            rd = tmp / "empty"
            rd.mkdir()
            self.assertEqual(parse_steps(rd), [])

    def test_loads_full_prose(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            rd = _make_run_dir(tmp, "sid1", "rid1", [
                {"ts": "2026-04-30T10:00:00", "agent": "architect", "mode": "SYSTEM_DESIGN",
                 "enum": "SYSTEM_DESIGN_READY", "must_fix": False, "prose_excerpt": "x"},
            ], prose_files={"architect-SYSTEM_DESIGN.md": "## Domain Model\nEntity X\n"})
            steps = parse_steps(rd)
            self.assertIn("Domain Model", steps[0].prose_full)


class WasteDetectionTests(unittest.TestCase):
    def test_retry_same_fail(self):
        steps = [
            StepRecord(idx=0, ts="t1", agent="engineer", mode="IMPL",
                       enum="TESTS_FAIL", must_fix=False, prose_excerpt="a\nb\nc\nd\ne"),
            StepRecord(idx=1, ts="t2", agent="engineer", mode="IMPL",
                       enum="TESTS_FAIL", must_fix=False, prose_excerpt="a\nb\nc\nd\ne"),
        ]
        wastes = detect_wastes(steps)
        kinds = {w.pattern for w in wastes}
        self.assertIn("RETRY_SAME_FAIL", kinds)

    def test_echo_violation(self):
        steps = [
            StepRecord(idx=0, ts="t", agent="architect", mode="MODULE_PLAN",
                       enum="READY_FOR_IMPL", must_fix=False, prose_excerpt="too short"),
        ]
        wastes = detect_wastes(steps)
        self.assertTrue(any(w.pattern == "ECHO_VIOLATION" for w in wastes))

    def test_placeholder_leak(self):
        steps = [
            StepRecord(idx=0, ts="t", agent="architect", mode="SYSTEM_DESIGN",
                       enum="SYSTEM_DESIGN_READY", must_fix=False,
                       prose_excerpt="a\nb\nc\nd\ne",
                       prose_full="## Voice Cloning\n외부 의존: [미기록] — M0 이후 결정"),
        ]
        wastes = detect_wastes(steps)
        leak = [w for w in wastes if w.pattern == "PLACEHOLDER_LEAK"]
        self.assertEqual(len(leak), 1)
        self.assertEqual(leak[0].severity, "HIGH")

    def test_must_fix_ghost(self):
        steps = [
            StepRecord(idx=0, ts="t1", agent="validator", mode="CODE_VALIDATION",
                       enum="FAIL", must_fix=True, prose_excerpt="a\nb\nc\nd\ne"),
            StepRecord(idx=1, ts="t2", agent="engineer", mode="IMPL",
                       enum="IMPL_DONE", must_fix=False, prose_excerpt="a\nb\nc\nd\ne"),
        ]
        wastes = detect_wastes(steps)
        self.assertTrue(any(w.pattern == "MUST_FIX_GHOST" for w in wastes))

    def test_spec_gap_loop(self):
        steps = [
            StepRecord(idx=i, ts=f"t{i}", agent="architect", mode="SPEC_GAP",
                       enum="SPEC_GAP_RESOLVED", must_fix=False, prose_excerpt="a\nb\nc\nd\ne")
            for i in range(3)
        ]
        wastes = detect_wastes(steps)
        self.assertTrue(any(w.pattern == "SPEC_GAP_LOOP" for w in wastes))

    def test_external_verified_missing(self):
        steps = [
            StepRecord(idx=0, ts="t", agent="plan-reviewer", mode=None,
                       enum="PLAN_REVIEW_PASS", must_fix=False,
                       prose_excerpt="a\nb\nc\nd\ne",
                       prose_full="## 8 차원 판정\n모두 PASS"),
        ]
        wastes = detect_wastes(steps)
        self.assertTrue(any(w.pattern == "EXTERNAL_VERIFIED_MISSING" for w in wastes))


class GoodDetectionTests(unittest.TestCase):
    def test_enum_clean(self):
        steps = [
            StepRecord(idx=0, ts="t", agent="architect", mode="MODULE_PLAN",
                       enum="READY_FOR_IMPL", must_fix=False, prose_excerpt="a\nb\nc\nd\ne"),
        ]
        goods = detect_goods(steps)
        self.assertTrue(any(g.pattern == "ENUM_CLEAN" for g in goods))

    def test_prose_echo_ok(self):
        steps = [
            StepRecord(idx=0, ts="t", agent="engineer", mode="IMPL",
                       enum="IMPL_DONE", must_fix=False,
                       prose_excerpt="line1\nline2\nline3\nline4\nline5\nline6"),
        ]
        goods = detect_goods(steps)
        self.assertTrue(any(g.pattern == "PROSE_ECHO_OK" for g in goods))

    def test_ddd_phase_a(self):
        steps = [
            StepRecord(idx=0, ts="t", agent="architect", mode="SYSTEM_DESIGN",
                       enum="SYSTEM_DESIGN_READY", must_fix=False,
                       prose_excerpt="a\nb\nc\nd\ne",
                       prose_full="## Domain Model\nEntity / VO / Aggregate ..."),
        ]
        goods = detect_goods(steps)
        self.assertTrue(any(g.pattern == "DDD_PHASE_A" for g in goods))

    def test_dependency_causal(self):
        steps = [
            StepRecord(idx=0, ts="t", agent="architect", mode="SYSTEM_DESIGN",
                       enum="SYSTEM_DESIGN_READY", must_fix=False,
                       prose_excerpt="a\nb\nc\nd\ne",
                       prose_full="A → B (B 의 결과를 입력으로 사용 — 비즈니스 흐름상 필수)"),
        ]
        goods = detect_goods(steps)
        self.assertTrue(any(g.pattern == "DEPENDENCY_CAUSAL" for g in goods))


class ReportRenderTests(unittest.TestCase):
    def test_render_smoke(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            rd = _make_run_dir(tmp, "sid1", "rid1", [
                {"ts": "2026-04-30T10:00:00", "agent": "architect", "mode": "MODULE_PLAN",
                 "enum": "READY_FOR_IMPL", "must_fix": False,
                 "prose_excerpt": "line1\nline2\nline3\nline4\nline5\nline6"},
                {"ts": "2026-04-30T10:05:00", "agent": "engineer", "mode": "IMPL",
                 "enum": "IMPL_DONE", "must_fix": False,
                 "prose_excerpt": "line1\nline2\nline3\nline4\nline5\nline6"},
            ])
            report = build_report(rd, repo_path=tmp)
            text = render_report(report)
            self.assertIn("# Run Review", text)
            self.assertIn("## 호출 흐름", text)
            self.assertIn("## 단계별 상세", text)
            self.assertIn("MODULE_PLAN", text)
            self.assertIn("IMPL_DONE", text)


class RunListTests(unittest.TestCase):
    def test_list_and_find(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            sessions_root = tmp / ".claude" / "harness-state" / ".sessions"
            _make_run_dir(tmp, "sid1", "rid_a", [
                {"ts": "2026-04-30T10:00:00", "agent": "architect", "mode": None,
                 "enum": "READY_FOR_IMPL", "must_fix": False, "prose_excerpt": "x"}])
            _make_run_dir(tmp, "sid1", "rid_b", [
                {"ts": "2026-04-30T11:00:00", "agent": "engineer", "mode": "IMPL",
                 "enum": "IMPL_DONE", "must_fix": False, "prose_excerpt": "x"}])
            runs = list_runs(sessions_root)
            self.assertEqual(len(runs), 2)
            self.assertEqual(find_run_dir(sessions_root, "rid_a", False).name, "rid_a")
            self.assertEqual(find_run_dir(sessions_root, None, True).name, runs[0].name)


class NormalizeAgentTypeTests(unittest.TestCase):
    def test_dcness_namespaced_strips_prefix(self):
        self.assertEqual(_normalize_agent_type("dcness:architect"), "architect")
        self.assertEqual(_normalize_agent_type("dcness:architect:system-design"), "architect")
        self.assertEqual(_normalize_agent_type("dcness:engineer"), "engineer")

    def test_non_namespaced_returns_as_is(self):
        self.assertEqual(_normalize_agent_type("architect"), "architect")
        self.assertEqual(_normalize_agent_type("Explore"), "Explore")

    def test_none_or_empty(self):
        self.assertIsNone(_normalize_agent_type(None))
        self.assertIsNone(_normalize_agent_type(""))


class AssignInvocationsTests(unittest.TestCase):
    def test_assigns_by_timestamp_proximity(self):
        # DCN-30-21: timestamp-proximity matching.
        from datetime import datetime as dt
        steps = [
            StepRecord(idx=0, ts="2026-04-30T10:05:00+00:00", agent="architect", mode="MODULE_PLAN",
                       enum="READY_FOR_IMPL", must_fix=False, prose_excerpt="x"),
            StepRecord(idx=1, ts="2026-04-30T10:15:00+00:00", agent="engineer", mode="IMPL",
                       enum="IMPL_DONE", must_fix=False, prose_excerpt="x"),
        ]
        invocations = [
            {"ts": dt(2026, 4, 30, 10, 4, 30), "agent": "architect", "duration_ms": 60000,
             "total_tokens": 5000, "output_tokens": 1500, "cost_usd": 0.05},
            {"ts": dt(2026, 4, 30, 10, 14, 30), "agent": "engineer", "duration_ms": 120000,
             "total_tokens": 8000, "output_tokens": 2500, "cost_usd": 0.10},
        ]
        assign_invocations_to_steps(steps, invocations)
        self.assertTrue(steps[0].matched_invocation)
        self.assertEqual(steps[0].duration_ms, 60000)
        self.assertEqual(steps[0].output_tokens, 1500)
        self.assertTrue(steps[1].matched_invocation)
        self.assertEqual(steps[1].cost_usd, 0.10)

    def test_skips_unmatched_agents(self):
        from datetime import datetime as dt
        steps = [
            StepRecord(idx=0, ts="2026-04-30T10:05:00+00:00", agent="architect", mode=None,
                       enum="READY_FOR_IMPL", must_fix=False, prose_excerpt="x"),
        ]
        invocations = [
            {"ts": dt(2026, 4, 30, 10, 4, 30), "agent": "engineer", "duration_ms": 60000,
             "total_tokens": 5000, "output_tokens": 1500, "cost_usd": 0.05},
        ]
        assign_invocations_to_steps(steps, invocations)
        self.assertFalse(steps[0].matched_invocation)

    def test_handles_missing_first_invocation(self):
        # DCN-30-21 regression — jajang 사례. step 0 invocation 부재 시 후속 step
        # 매칭 cascade 어긋남 X.
        from datetime import datetime as dt
        steps = [
            StepRecord(idx=0, ts="2026-04-30T10:00:00+00:00", agent="product-planner", mode=None,
                       enum="PRODUCT_PLAN_UPDATED", must_fix=False, prose_excerpt="x"),
            StepRecord(idx=1, ts="2026-04-30T10:10:00+00:00", agent="plan-reviewer", mode=None,
                       enum="PLAN_REVIEW_PASS", must_fix=False, prose_excerpt="x"),
            StepRecord(idx=2, ts="2026-04-30T10:20:00+00:00", agent="product-planner", mode=None,
                       enum="PRODUCT_PLAN_UPDATED", must_fix=False, prose_excerpt="x"),
        ]
        invocations = [
            {"ts": dt(2026, 4, 30, 10, 9, 30), "agent": "plan-reviewer", "duration_ms": 60000,
             "total_tokens": 5000, "output_tokens": 1500, "cost_usd": 0.05},
            {"ts": dt(2026, 4, 30, 10, 19, 30), "agent": "product-planner", "duration_ms": 120000,
             "total_tokens": 8000, "output_tokens": 2500, "cost_usd": 0.10},
        ]
        assign_invocations_to_steps(steps, invocations)
        self.assertFalse(steps[0].matched_invocation, "step 0 invocation 없으니 미매칭")
        self.assertTrue(steps[1].matched_invocation, "step 1 plan-reviewer 정확 매칭")
        self.assertEqual(steps[1].output_tokens, 1500)
        self.assertTrue(steps[2].matched_invocation, "step 2 product-planner 정확 매칭")
        self.assertEqual(steps[2].output_tokens, 2500)

    def test_excludes_invocation_after_step_ts(self):
        # invocation ts > step ts → 매칭 X (sub-agent 는 end-step 전에 끝남).
        from datetime import datetime as dt
        steps = [
            StepRecord(idx=0, ts="2026-04-30T10:00:00+00:00", agent="architect", mode=None,
                       enum="READY_FOR_IMPL", must_fix=False, prose_excerpt="x"),
        ]
        invocations = [
            {"ts": dt(2026, 4, 30, 10, 5, 0), "agent": "architect", "duration_ms": 60000,
             "total_tokens": 5000, "output_tokens": 1500, "cost_usd": 0.05},
        ]
        assign_invocations_to_steps(steps, invocations)
        self.assertFalse(steps[0].matched_invocation)


class ThinkingLoopDetectionTests(unittest.TestCase):
    def test_thinking_loop_high_duration_low_output(self):
        # 사용자 jajang 사례 시뮬레이션 — product-planner 6분 + 624 tokens
        budget = EXPECTED_AGENT_BUDGETS["product-planner"]
        s = StepRecord(idx=0, ts="t", agent="product-planner", mode=None,
                        enum="PRODUCT_PLAN_CHANGE_DIFF", must_fix=False,
                        prose_excerpt="line1\nline2\nline3\nline4\nline5\nline6")
        s.matched_invocation = True
        s.duration_ms = 360000  # 6분
        s.output_tokens = 624
        s.total_tokens = 1000
        wastes = detect_wastes([s])
        kinds = {w.pattern for w in wastes}
        self.assertIn("THINKING_LOOP", kinds)

    def test_no_thinking_loop_when_healthy(self):
        # 정상 — 60s + 5000 tokens
        s = StepRecord(idx=0, ts="t", agent="architect", mode="MODULE_PLAN",
                        enum="READY_FOR_IMPL", must_fix=False,
                        prose_excerpt="line1\nline2\nline3\nline4\nline5\nline6")
        s.matched_invocation = True
        s.duration_ms = 60000
        s.output_tokens = 5000
        s.total_tokens = 30000
        wastes = detect_wastes([s])
        self.assertFalse(any(w.pattern == "THINKING_LOOP" for w in wastes))

    def test_no_thinking_loop_when_unmatched(self):
        # matched_invocation=False 면 detection skip
        s = StepRecord(idx=0, ts="t", agent="product-planner", mode=None,
                        enum="PRODUCT_PLAN_READY", must_fix=False,
                        prose_excerpt="line1\nline2\nline3\nline4\nline5\nline6")
        s.matched_invocation = False
        s.duration_ms = 0
        s.output_tokens = 0
        wastes = detect_wastes([s])
        self.assertFalse(any(w.pattern == "THINKING_LOOP" for w in wastes))


if __name__ == "__main__":
    unittest.main()
