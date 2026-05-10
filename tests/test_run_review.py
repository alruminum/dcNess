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
    RunReport, StepRecord, build_report, detect_goods, detect_wastes,
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
            prose_path = tmp / "architect-SYSTEM_DESIGN.md"
            prose_path.write_text("## Domain Model\nEntity X\n")
            rd = _make_run_dir(tmp, "sid1", "rid1", [
                {"ts": "2026-04-30T10:00:00", "agent": "architect", "mode": "SYSTEM_DESIGN",
                 "enum": "SYSTEM_DESIGN_READY", "must_fix": False, "prose_excerpt": "x",
                 "prose_file": str(prose_path)},
            ])
            steps = parse_steps(rd)
            self.assertIn("Domain Model", steps[0].prose_full)


class ProseFileTests(unittest.TestCase):
    """prose_file 필드 기반 prose 로딩 테스트."""

    def test_parse_steps_recomputes_must_fix_from_prose(self):
        """prose_file 있을 때 must_fix 재계산 (negation-aware retro accuracy)."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            prose_path = tmp / "pr-reviewer.md"
            prose_path.write_text("MUST FIX 0, NICE TO HAVE 6 (let tree: any / dead code).\nLGTM\n")
            rd = _make_run_dir(tmp, "sid1", "rid1", [
                {"ts": "2026-04-30T10:00:00", "agent": "pr-reviewer", "mode": None,
                 "enum": "LGTM", "must_fix": True,
                 "prose_excerpt": "MUST FIX 0, NICE TO HAVE 6\nLGTM",
                 "prose_file": str(prose_path)},
            ])
            steps = parse_steps(rd)
            self.assertEqual(len(steps), 1)
            self.assertFalse(steps[0].must_fix, "negation 부정문 → False 재계산")

    def test_parse_steps_must_fix_falls_back_to_jsonl(self):
        """prose_file 없을 때 jsonl must_fix fallback."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            rd = _make_run_dir(tmp, "sid1", "rid1", [
                {"ts": "2026-04-30T10:00:00", "agent": "validator", "mode": "CODE_VALIDATION",
                 "enum": "FAIL", "must_fix": True, "prose_excerpt": "x"},
            ])
            steps = parse_steps(rd)
            self.assertEqual(len(steps), 1)
            self.assertTrue(steps[0].must_fix, "prose 부재 → jsonl fallback")

    def test_parse_steps_resolves_per_occurrence_via_prose_file(self):
        """같은 (agent, mode) 반복 시 prose_file 로 각 step 독립 파일 읽기."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            p1 = tmp / "engineer-IMPL.md"
            p2 = tmp / "engineer-IMPL-1.md"
            p1.write_text("first batch\n## 자가 검증\n- jest PASS")
            p2.write_text("second batch\nno anchor")
            rd = _make_run_dir(tmp, "sid1", "rid1", [
                {"ts": "2026-04-30T10:00:00", "agent": "engineer", "mode": "IMPL",
                 "enum": "IMPL_DONE", "must_fix": False, "prose_excerpt": "x",
                 "prose_file": str(p1)},
                {"ts": "2026-04-30T10:05:00", "agent": "engineer", "mode": "IMPL",
                 "enum": "IMPL_DONE", "must_fix": False, "prose_excerpt": "x",
                 "prose_file": str(p2)},
            ])
            steps = parse_steps(rd)
            self.assertEqual(len(steps), 2)
            self.assertIn("first batch", steps[0].prose_full)
            self.assertIn("second batch", steps[1].prose_full)
            self.assertNotEqual(steps[0].prose_full, steps[1].prose_full)

    def test_parse_steps_legacy_fallback_outer_file(self):
        """prose_file 없는 레거시 record → outer <agent>[-mode].md fallback."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            rd = _make_run_dir(tmp, "sid1", "rid1", [
                {"ts": "2026-04-30T10:00:00", "agent": "architect", "mode": "SYSTEM_DESIGN",
                 "enum": "SYSTEM_DESIGN_READY", "must_fix": False, "prose_excerpt": "x"},
            ], prose_files={"architect-SYSTEM_DESIGN.md": "## Domain Model\nlegacy\n"})
            steps = parse_steps(rd)
            self.assertIn("legacy", steps[0].prose_full)


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

    def test_retry_same_fail_prose_logged_skip(self):
        """이슈 #302 #1 — PROSE_LOGGED 는 prose-only mode 정상 sentinel.
        연속 발생해도 RETRY_SAME_FAIL false positive 안 됨."""
        steps = [
            StepRecord(idx=0, ts="t1", agent="architect", mode="MODULE_PLAN",
                       enum="PROSE_LOGGED", must_fix=False, prose_excerpt="task 01"),
            StepRecord(idx=1, ts="t2", agent="architect", mode="MODULE_PLAN",
                       enum="PROSE_LOGGED", must_fix=False, prose_excerpt="task 02"),
            StepRecord(idx=2, ts="t3", agent="architect", mode="MODULE_PLAN",
                       enum="PROSE_LOGGED", must_fix=False, prose_excerpt="task 03"),
        ]
        wastes = detect_wastes(steps)
        kinds = {w.pattern for w in wastes}
        self.assertNotIn("RETRY_SAME_FAIL", kinds,
                         "PROSE_LOGGED 는 advance sentinel — 연속 발생해도 retry 아님")

    def test_retry_same_fail_different_prose_skip(self):
        """이슈 #302 #1 — 같은 enum 이라도 prose 내용이 다르면 다른 invocation (N task 순회 등).
        retry 아님."""
        steps = [
            StepRecord(idx=0, ts="t1", agent="engineer", mode="IMPL",
                       enum="TESTS_FAIL", must_fix=False,
                       prose_excerpt="task 01 첫 시도",
                       prose_full="task 01 첫 시도\n실패 원인 A"),
            StepRecord(idx=1, ts="t2", agent="engineer", mode="IMPL",
                       enum="TESTS_FAIL", must_fix=False,
                       prose_excerpt="task 02 첫 시도",
                       prose_full="task 02 첫 시도\n실패 원인 B"),
        ]
        wastes = detect_wastes(steps)
        kinds = {w.pattern for w in wastes}
        self.assertNotIn("RETRY_SAME_FAIL", kinds,
                         "다른 task / 다른 prose = 다른 invocation, retry 아님")

    def test_echo_violation(self):
        # prose_full 이 짧을 때만 ECHO_VIOLATION (prose_excerpt 기준 X)
        steps = [
            StepRecord(idx=0, ts="t", agent="architect", mode="MODULE_PLAN",
                       enum="READY_FOR_IMPL", must_fix=False,
                       prose_excerpt="too short",
                       prose_full="too short\n"),
        ]
        wastes = detect_wastes(steps)
        self.assertTrue(any(w.pattern == "ECHO_VIOLATION" for w in wastes))

    def test_echo_violation_no_prose_full_skipped(self):
        # prose_full 없으면 오탐 방지 — skip
        steps = [
            StepRecord(idx=0, ts="t", agent="architect", mode="MODULE_PLAN",
                       enum="READY_FOR_IMPL", must_fix=False, prose_excerpt="too short"),
        ]
        wastes = detect_wastes(steps)
        self.assertFalse(any(w.pattern == "ECHO_VIOLATION" for w in wastes))

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


class LocalTimeRenderTests(unittest.TestCase):
    def test_step_table_shows_local_time(self):
        # DCN-30-24: UTC ts → system local time (e.g. KST = UTC+9)
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            rd = _make_run_dir(tmp, "sid1", "rid1", [
                {"ts": "2026-04-30T02:46:47+00:00", "agent": "architect", "mode": "MODULE_PLAN",
                 "enum": "READY_FOR_IMPL", "must_fix": False,
                 "prose_excerpt": "a\nb\nc\nd\ne\nf"},
            ])
            report = build_report(rd, repo_path=tmp)
            text = render_report(report)
            self.assertIn("시작(local)", text)
            # `:46:47` 부분만 확인 — 시스템 timezone 무관 (분/초는 동일)
            self.assertIn(":46:47", text)


class ToolUsesColumnTests(unittest.TestCase):
    """DCN-CHG-20260430-39: render_report tool_uses 컬럼 + ≥ 100 강조."""

    def _make_report(self, steps: list[StepRecord]) -> RunReport:
        with tempfile.TemporaryDirectory() as td:
            return RunReport(run_id="rid", session_id="sid", run_dir=Path(td), steps=steps)

    def test_header_has_tool_uses_column(self):
        step = StepRecord(idx=0, ts="t", agent="engineer", mode="IMPL",
                          enum="IMPL_DONE", must_fix=False,
                          prose_excerpt="a\nb\nc\nd\ne",
                          matched_invocation=True, tool_use_count=42)
        text = render_report(self._make_report([step]))
        self.assertIn("tool_uses", text)
        self.assertIn("| 42 |", text)

    def test_overflow_threshold_bolded(self):
        step = StepRecord(idx=0, ts="t", agent="engineer", mode="IMPL",
                          enum="IMPL_DONE", must_fix=False,
                          prose_excerpt="a\nb\nc\nd\ne",
                          matched_invocation=True, tool_use_count=153)
        text = render_report(self._make_report([step]))
        self.assertIn("**153**", text)

    def test_unmatched_invocation_dash(self):
        step = StepRecord(idx=0, ts="t", agent="engineer", mode="IMPL",
                          enum="IMPL_DONE", must_fix=False,
                          prose_excerpt="a\nb\nc\nd\ne",
                          matched_invocation=False, tool_use_count=0)
        text = render_report(self._make_report([step]))
        # 단계별 표 row 안 tool_uses 자리 = "-" (cost 와 동일 형식)
        # 검사: "| - | - |" 같은 dash 시퀀스 존재 (out_tok / total_tok / tool_uses / cost 모두 dash)
        self.assertRegex(text, r"\|\s*-\s*\|\s*-\s*\|\s*-\s*\|\s*-\s*\|")


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


class RegressionPatternsTests(unittest.TestCase):
    """DCN-CHG-20260430-37 — 4 신규 회귀 패턴."""

    def test_tool_use_overflow_emits_finding(self):
        # 자장 실측 임계 ≥ 100. 102/119/153/170/223 모두 PARTIAL 회귀.
        s = StepRecord(idx=0, ts="t", agent="engineer", mode="IMPL",
                        enum="IMPL_DONE", must_fix=False,
                        prose_excerpt="line1\nline2\nline3\nline4\nline5")
        s.matched_invocation = True
        s.tool_use_count = 119
        wastes = detect_wastes([s])
        kinds = {w.pattern for w in wastes}
        self.assertIn("TOOL_USE_OVERFLOW", kinds)

    def test_tool_use_overflow_below_threshold(self):
        # ≤ 99 = silent. 정상 invocation 36~64 영역.
        s = StepRecord(idx=0, ts="t", agent="engineer", mode="IMPL",
                        enum="IMPL_DONE", must_fix=False,
                        prose_excerpt="line1\nline2\nline3\nline4\nline5")
        s.matched_invocation = True
        s.tool_use_count = 64
        wastes = detect_wastes([s])
        self.assertFalse(any(w.pattern == "TOOL_USE_OVERFLOW" for w in wastes))

    def test_tool_use_overflow_unmatched_invocation_skipped(self):
        # matched_invocation=False → tool_use_count 신뢰 X → skip
        s = StepRecord(idx=0, ts="t", agent="engineer", mode="IMPL",
                        enum="IMPL_DONE", must_fix=False,
                        prose_excerpt="line1\nline2\nline3\nline4\nline5")
        s.matched_invocation = False
        s.tool_use_count = 200
        wastes = detect_wastes([s])
        self.assertFalse(any(w.pattern == "TOOL_USE_OVERFLOW" for w in wastes))

    def test_partial_loop_three_or_more(self):
        # IMPL_PARTIAL ≥ 3 회 → PARTIAL_LOOP 검출
        steps = [
            StepRecord(idx=i, ts=f"t{i}", agent="engineer", mode="IMPL",
                        enum="IMPL_PARTIAL", must_fix=False,
                        prose_excerpt="line1\nline2\nline3\nline4\nline5")
            for i in range(3)
        ]
        wastes = detect_wastes(steps)
        kinds = {w.pattern for w in wastes}
        self.assertIn("PARTIAL_LOOP", kinds)

    def test_partial_loop_two_silent(self):
        # 2회는 정상 (cycle 한도 ≤ 3 권고 안)
        steps = [
            StepRecord(idx=i, ts=f"t{i}", agent="engineer", mode="IMPL",
                        enum="IMPL_PARTIAL", must_fix=False,
                        prose_excerpt="line1\nline2\nline3\nline4\nline5")
            for i in range(2)
        ]
        wastes = detect_wastes(steps)
        self.assertFalse(any(w.pattern == "PARTIAL_LOOP" for w in wastes))

    def test_end_step_skip_when_invocations_exceed_steps(self):
        # invocations 3 vs steps 1 (engineer) — 2 누락 의심
        from datetime import datetime
        steps = [
            StepRecord(idx=0, ts="2026-04-30T10:00:00", agent="engineer", mode="IMPL",
                        enum="IMPL_DONE", must_fix=False,
                        prose_excerpt="line1\nline2\nline3\nline4\nline5"),
        ]
        invocations = [
            {"agent": "engineer", "ts": datetime(2026, 4, 30, 10, 0, 0),
             "duration_ms": 1000, "output_tokens": 100, "total_tokens": 100,
             "input_tokens": 100, "cache_read": 0, "cost_usd": 0.0,
             "tool_use_count": 50, "agent_type_raw": "dcness:engineer"},
            {"agent": "engineer", "ts": datetime(2026, 4, 30, 10, 5, 0),
             "duration_ms": 1000, "output_tokens": 100, "total_tokens": 100,
             "input_tokens": 100, "cache_read": 0, "cost_usd": 0.0,
             "tool_use_count": 60, "agent_type_raw": "dcness:engineer"},
            {"agent": "engineer", "ts": datetime(2026, 4, 30, 10, 10, 0),
             "duration_ms": 1000, "output_tokens": 100, "total_tokens": 100,
             "input_tokens": 100, "cache_read": 0, "cost_usd": 0.0,
             "tool_use_count": 40, "agent_type_raw": "dcness:engineer"},
        ]
        wastes = detect_wastes(steps, invocations=invocations)
        kinds = {w.pattern for w in wastes}
        self.assertIn("END_STEP_SKIP", kinds)

    def test_end_step_skip_silent_within_margin(self):
        # invocations 2 vs steps 1 = diff 1, margin 1 안 → silent
        from datetime import datetime
        steps = [
            StepRecord(idx=0, ts="2026-04-30T10:00:00", agent="engineer", mode="IMPL",
                        enum="IMPL_DONE", must_fix=False,
                        prose_excerpt="line1\nline2\nline3\nline4\nline5"),
        ]
        invocations = [
            {"agent": "engineer", "ts": datetime(2026, 4, 30, 10, 0, 0),
             "duration_ms": 0, "output_tokens": 0, "total_tokens": 0,
             "input_tokens": 0, "cache_read": 0, "cost_usd": 0.0,
             "tool_use_count": 0, "agent_type_raw": "dcness:engineer"},
            {"agent": "engineer", "ts": datetime(2026, 4, 30, 10, 5, 0),
             "duration_ms": 0, "output_tokens": 0, "total_tokens": 0,
             "input_tokens": 0, "cache_read": 0, "cost_usd": 0.0,
             "tool_use_count": 0, "agent_type_raw": "dcness:engineer"},
        ]
        wastes = detect_wastes(steps, invocations=invocations)
        self.assertFalse(any(w.pattern == "END_STEP_SKIP" for w in wastes))

    def test_main_sed_misdiagnosis_detects_self_correction(self):
        # CC JSONL 안 메인 self-correction 패턴 — 실제 fixture 박음
        from datetime import datetime
        from harness.run_review import encode_repo_path_dcness
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            os.chdir(tmp)
            try:
                # CC JSONL fake — 메인 정정 발화
                encoded = encode_repo_path_dcness(str(tmp))
                proj = Path.home() / ".claude" / "projects" / encoded
                proj.mkdir(parents=True, exist_ok=True)
                jsonl = proj / "fake-sid.jsonl"
                jsonl.write_text(json.dumps({
                    "type": "assistant",
                    "timestamp": "2026-04-30T10:05:00.000Z",
                    "message": {"content": [
                        {"type": "text", "text": "**중요 정정** — sed 변경사항 0 (실제 0개)."}
                    ]},
                }, ensure_ascii=False) + "\n", encoding="utf-8")
                try:
                    steps = [
                        StepRecord(idx=0, ts="2026-04-30T10:00:00", agent="engineer", mode="IMPL",
                                    enum="IMPL_DONE", must_fix=False,
                                    prose_excerpt="line1\nline2\nline3\nline4\nline5"),
                    ]
                    window = (datetime(2026, 4, 30, 10, 0, 0), datetime(2026, 4, 30, 10, 30, 0))
                    wastes = detect_wastes(steps, repo_path=tmp, window=window)
                    kinds = {w.pattern for w in wastes}
                    self.assertIn("MAIN_SED_MISDIAGNOSIS", kinds)
                finally:
                    jsonl.unlink(missing_ok=True)
            finally:
                os.chdir(REPO_ROOT)


class MissingSelfVerifyTests(unittest.TestCase):
    """DCN-CHG-20260430-38 — engineer self-verify anchor 자율화 + 회귀 검출."""

    def _engineer_step(self, prose_full: str, enum: str = "IMPL_DONE") -> StepRecord:
        s = StepRecord(idx=0, ts="t", agent="engineer", mode="IMPL",
                        enum=enum, must_fix=False,
                        prose_excerpt="line1\nline2\nline3\nline4\nline5")
        s.prose_full = prose_full
        return s

    def test_missing_anchor_emits_finding(self):
        s = self._engineer_step(prose_full="## 결론\nIMPL_DONE\n구현 완료.")
        wastes = detect_wastes([s])
        kinds = {w.pattern for w in wastes}
        self.assertIn("MISSING_SELF_VERIFY", kinds)

    def test_korean_anchor_passes(self):
        s = self._engineer_step(prose_full="## 결론\nIMPL_DONE\n## 자가 검증\ngrep → 0\n")
        wastes = detect_wastes([s])
        self.assertFalse(any(w.pattern == "MISSING_SELF_VERIFY" for w in wastes))

    def test_english_verification_anchor_passes(self):
        s = self._engineer_step(prose_full="## 결론\nIMPL_DONE\n## Verification\nnpm test → PASS\n")
        wastes = detect_wastes([s])
        self.assertFalse(any(w.pattern == "MISSING_SELF_VERIFY" for w in wastes))

    def test_self_verify_anchor_passes(self):
        s = self._engineer_step(prose_full="## 결론\nIMPL_DONE\n### Self-Verify\noutput\n")
        wastes = detect_wastes([s])
        self.assertFalse(any(w.pattern == "MISSING_SELF_VERIFY" for w in wastes))

    def test_short_검증_anchor_passes(self):
        s = self._engineer_step(prose_full="## 결론\nIMPL_DONE\n## 검증\noutput\n")
        wastes = detect_wastes([s])
        self.assertFalse(any(w.pattern == "MISSING_SELF_VERIFY" for w in wastes))

    def test_acceptance_criteria_anchor_passes(self):
        # issue #249 — `## 수용 기준 검증` 같이 heading 에 "검증" 포함된 변형도 통과해야 함.
        s = self._engineer_step(prose_full="## 결론\nIMPL_DONE\n## 수용 기준 검증\n- grep 0줄 ✓\n")
        wastes = detect_wastes([s])
        self.assertFalse(any(w.pattern == "MISSING_SELF_VERIFY" for w in wastes))

    def test_self_verification_anchor_passes(self):
        s = self._engineer_step(prose_full="## 결론\nIMPL_DONE\n## Self Verification\noutput\n")
        wastes = detect_wastes([s])
        self.assertFalse(any(w.pattern == "MISSING_SELF_VERIFY" for w in wastes))

    def test_skipped_when_no_prose_full(self):
        # prose_full 부재 시 skip (parse 실패 case 등)
        s = self._engineer_step(prose_full="")
        wastes = detect_wastes([s])
        self.assertFalse(any(w.pattern == "MISSING_SELF_VERIFY" for w in wastes))

    def test_skipped_for_non_engineer(self):
        s = StepRecord(idx=0, ts="t", agent="architect", mode="MODULE_PLAN",
                        enum="READY_FOR_IMPL", must_fix=False,
                        prose_excerpt="line1\nline2\nline3\nline4\nline5")
        s.prose_full = "## 결론\nREADY"  # no self-verify anchor
        wastes = detect_wastes([s])
        self.assertFalse(any(w.pattern == "MISSING_SELF_VERIFY" for w in wastes))

    def test_skipped_for_non_impl_enum(self):
        # SPEC_GAP_FOUND 같은 escalate enum 은 self-verify 의무 비대상
        s = self._engineer_step(prose_full="## 결론\nSPEC_GAP_FOUND",
                                 enum="SPEC_GAP_FOUND")
        wastes = detect_wastes([s])
        self.assertFalse(any(w.pattern == "MISSING_SELF_VERIFY" for w in wastes))

    def test_skipped_for_polish_done(self):
        # #252 — POLISH 짧은 정리 보고는 본문 자체가 검증. anchor 강제 잉여.
        s = self._engineer_step(
            prose_full="## POLISH — earphone 헬퍼 추출\n중복 제거. 테스트 34 passed.",
            enum="POLISH_DONE",
        )
        s.mode = "POLISH"
        wastes = detect_wastes([s])
        self.assertFalse(any(w.pattern == "MISSING_SELF_VERIFY" for w in wastes))


if __name__ == "__main__":
    unittest.main()
