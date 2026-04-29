"""test_impl_driver — sequence 순회 + orchestrator 동적 갱신 driver 검증.

Coverage:
    Happy path:
        - default 6-step impl 시퀀스 완주 (architect MODULE_PLAN → ... → pr-reviewer LGTM)
        - history 6 entries, attempts.json 영속화
        - agent_invoker / sequence_decider 호출 횟수

    Escalate:
        - agent emit IMPLEMENTATION_ESCALATE → OrchestrationEscalate(reason=agent_emit)
        - retry 한도: engineer IMPL × 3 도달 후 4번째 schedule → reason=retry_limit
        - architect SPEC_GAP × 2 도달

    Catastrophic backbone (orchestration.md §2.3):
        - Rule 1: pr-reviewer 직전 CODE_VALIDATION PASS 부재 → 거부
        - Rule 3: engineer (non-POLISH) 직전 PLAN_VALIDATION PASS 부재 → 거부
        - Rule 4: architect SYSTEM_DESIGN 후 PRD 변경 + plan-reviewer 부재 → 거부
        - Rule 1 light path (BUGFIX_VALIDATION) 허용

    SPEC_GAP detour:
        - engineer SPEC_GAP_FOUND → orchestrator inserts architect SPEC_GAP → engineer 재진입 성공

    Edge cases:
        - 빈 initial sequence → 즉시 ctx 반환 (history 0)
        - agent_invoker 가 str 외 반환 → TypeError
        - prose 안 enum 매칭 0 → CatastrophicViolation('interpret_failed')
        - max_steps 초과 → DriverHaltError
"""
from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

from harness.impl_driver import (
    CatastrophicViolation,
    DriverContext,
    DriverHaltError,
    OrchestrationEscalate,
    Step,
    StepResult,
    check_catastrophic,
    check_retry_limit,
    default_impl_sequence,
    run_impl_loop,
)


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def make_drain_decider() -> Callable:
    """remaining_sequence 를 그대로 반환 (detour 없음)."""

    def decider(*, remaining_sequence, **kwargs):
        return list(remaining_sequence)

    return decider


def make_static_decider(returns: list[list[Step]]) -> Callable:
    """호출 순서대로 미리 정해진 sequence 를 반환."""
    it = iter(returns)

    def decider(**kwargs):
        return next(it)

    return decider


def prose_with_enum(enum: str, body: str = "") -> str:
    return f"## 결과\n\n{body}\n\n## 결론\n\n{enum}\n"


def make_invoker_by_agent(mapping: dict) -> Callable:
    """(agent, mode) 또는 agent → prose 매핑."""

    def invoker(step: Step, ctx: DriverContext) -> str:
        key = (step.agent, step.mode)
        if key in mapping:
            return mapping[key]
        if step.agent in mapping:
            return mapping[step.agent]
        raise KeyError(f"no mapping for {key}")

    return invoker


def make_invoker_seq(proses: list[str]) -> Callable:
    it = iter(proses)

    def invoker(step: Step, ctx: DriverContext) -> str:
        return next(it)

    return invoker


# ---------------------------------------------------------------------------
# Static helpers — check_catastrophic / check_retry_limit 단위 검증
# ---------------------------------------------------------------------------


def _make_result(agent: str, mode, enum: str) -> StepResult:
    return StepResult(
        step=Step(agent, mode, (enum, "DUMMY_OTHER")),
        prose=prose_with_enum(enum),
        prose_path=Path("/tmp/dummy.md"),
        parsed_enum=enum,
    )


class CatastrophicCheckTests(unittest.TestCase):
    def test_no_history_no_violation(self) -> None:
        # validator PLAN_VALIDATION 시작은 항상 OK
        self.assertIsNone(
            check_catastrophic(
                [],
                Step("validator", "PLAN_VALIDATION", ("PASS", "FAIL")),
            )
        )

    def test_pr_reviewer_without_code_validation_blocked(self) -> None:
        history = [
            _make_result("validator", "PLAN_VALIDATION", "PASS"),
            _make_result("engineer", "IMPL", "IMPL_DONE"),
        ]
        violation = check_catastrophic(
            history,
            Step("pr-reviewer", None, ("LGTM", "CHANGES_REQUESTED")),
        )
        self.assertIsNotNone(violation)
        self.assertIn("§2.3.1", violation)

    def test_pr_reviewer_after_code_validation_pass_ok(self) -> None:
        history = [
            _make_result("validator", "PLAN_VALIDATION", "PASS"),
            _make_result("engineer", "IMPL", "IMPL_DONE"),
            _make_result("validator", "CODE_VALIDATION", "PASS"),
        ]
        self.assertIsNone(
            check_catastrophic(
                history,
                Step("pr-reviewer", None, ("LGTM", "CHANGES_REQUESTED")),
            )
        )

    def test_pr_reviewer_light_path_with_bugfix_validation_ok(self) -> None:
        history = [
            _make_result("architect", "LIGHT_PLAN", "LIGHT_PLAN_READY"),
            _make_result("engineer", "IMPL", "IMPL_DONE"),
            _make_result("validator", "BUGFIX_VALIDATION", "PASS"),
        ]
        self.assertIsNone(
            check_catastrophic(
                history,
                Step("pr-reviewer", None, ("LGTM", "CHANGES_REQUESTED")),
            )
        )

    def test_engineer_without_plan_validation_blocked(self) -> None:
        violation = check_catastrophic(
            [],
            Step("engineer", "IMPL", ("IMPL_DONE", "TESTS_FAIL")),
        )
        self.assertIsNotNone(violation)
        self.assertIn("§2.3.3", violation)

    def test_engineer_polish_skips_plan_check(self) -> None:
        # POLISH 는 plan_validation 요구 안 됨
        self.assertIsNone(
            check_catastrophic(
                [],
                Step("engineer", "POLISH", ("POLISH_DONE",)),
            )
        )

    def test_engineer_light_path_ok_without_plan_validation(self) -> None:
        history = [_make_result("architect", "LIGHT_PLAN", "LIGHT_PLAN_READY")]
        self.assertIsNone(
            check_catastrophic(
                history,
                Step("engineer", "IMPL", ("IMPL_DONE", "TESTS_FAIL")),
            )
        )

    def test_architect_system_design_after_prd_change_blocked(self) -> None:
        history = [_make_result("product-planner", None, "PRODUCT_PLAN_READY")]
        violation = check_catastrophic(
            history,
            Step("architect", "SYSTEM_DESIGN", ("SYSTEM_DESIGN_READY",)),
        )
        self.assertIsNotNone(violation)
        self.assertIn("§2.3.4", violation)

    def test_architect_system_design_after_full_review_ok(self) -> None:
        history = [
            _make_result("product-planner", None, "PRODUCT_PLAN_READY"),
            _make_result("plan-reviewer", None, "PLAN_REVIEW_PASS"),
            _make_result("ux-architect", None, "UX_FLOW_READY"),
        ]
        self.assertIsNone(
            check_catastrophic(
                history,
                Step("architect", "SYSTEM_DESIGN", ("SYSTEM_DESIGN_READY",)),
            )
        )


class RetryLimitTests(unittest.TestCase):
    def test_engineer_impl_under_limit(self) -> None:
        history = [_make_result("engineer", "IMPL", "TESTS_FAIL") for _ in range(2)]
        self.assertIsNone(
            check_retry_limit(
                history,
                Step("engineer", "IMPL", ("IMPL_DONE", "TESTS_FAIL")),
            )
        )

    def test_engineer_impl_at_limit_returns_escalate(self) -> None:
        history = [_make_result("engineer", "IMPL", "TESTS_FAIL") for _ in range(3)]
        self.assertEqual(
            check_retry_limit(
                history,
                Step("engineer", "IMPL", ("IMPL_DONE", "TESTS_FAIL")),
            ),
            "IMPLEMENTATION_ESCALATE",
        )

    def test_architect_spec_gap_at_limit(self) -> None:
        history = [
            _make_result("architect", "SPEC_GAP", "SPEC_GAP_RESOLVED")
            for _ in range(2)
        ]
        self.assertEqual(
            check_retry_limit(
                history,
                Step("architect", "SPEC_GAP", ("SPEC_GAP_RESOLVED",)),
            ),
            "IMPLEMENTATION_ESCALATE",
        )

    def test_no_limit_for_unmapped_step(self) -> None:
        # validator PLAN_VALIDATION 은 limit 표 미등록
        self.assertIsNone(
            check_retry_limit(
                [_make_result("validator", "PLAN_VALIDATION", "FAIL")] * 10,
                Step("validator", "PLAN_VALIDATION", ("PASS", "FAIL")),
            )
        )


# ---------------------------------------------------------------------------
# run_impl_loop — 통합 시나리오
# ---------------------------------------------------------------------------


class RunImplLoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = TemporaryDirectory()
        self.tmp = Path(self._td.name)
        self.base_dir = self.tmp / "harness-state"
        # decision_table_path 는 mock decider 가 안 읽으므로 파일만 있으면 됨
        self.dt_path = self.tmp / "orchestration.md"
        self.dt_path.write_text("# placeholder\n")
        os.environ["DCNESS_LLM_TELEMETRY"] = "0"

    def tearDown(self) -> None:
        self._td.cleanup()
        os.environ.pop("DCNESS_LLM_TELEMETRY", None)

    def _kwargs(self, **extra):
        defaults = dict(
            decision_table_path=self.dt_path,
            base_dir=self.base_dir,
            run_id="test_run_001",
        )
        defaults.update(extra)
        return defaults

    # ----- happy path -----

    def test_default_sequence_happy_path(self) -> None:
        invoker = make_invoker_by_agent({
            ("architect", "MODULE_PLAN"): prose_with_enum("READY_FOR_IMPL"),
            ("validator", "PLAN_VALIDATION"): prose_with_enum("PASS"),
            ("test-engineer", None): prose_with_enum("TESTS_WRITTEN"),
            ("engineer", "IMPL"): prose_with_enum("IMPL_DONE"),
            ("validator", "CODE_VALIDATION"): prose_with_enum("PASS"),
            ("pr-reviewer", None): prose_with_enum("LGTM"),
        })
        ctx = run_impl_loop(
            impl_path="docs/impl/00-test.md",
            agent_invoker=invoker,
            sequence_decider=make_drain_decider(),
            **self._kwargs(),
        )
        self.assertEqual(len(ctx.history), 6)
        self.assertEqual(ctx.history[-1].parsed_enum, "LGTM")
        self.assertEqual(
            [r.step.agent for r in ctx.history],
            [
                "architect",
                "validator",
                "test-engineer",
                "engineer",
                "validator",
                "pr-reviewer",
            ],
        )

        # attempts.json 영속화
        attempts_path = self.base_dir / "test_run_001" / ".attempts.json"
        self.assertTrue(attempts_path.exists())
        attempts = json.loads(attempts_path.read_text())
        self.assertEqual(attempts["engineer:IMPL"], 1)
        self.assertEqual(attempts["pr-reviewer"], 1)

    def test_empty_initial_sequence_returns_immediately(self) -> None:
        invoker = make_invoker_seq([])
        ctx = run_impl_loop(
            impl_path=None,
            initial_sequence=[],
            agent_invoker=invoker,
            sequence_decider=make_drain_decider(),
            **self._kwargs(),
        )
        self.assertEqual(len(ctx.history), 0)

    # ----- escalate -----

    def test_agent_emit_escalate_propagates(self) -> None:
        invoker = make_invoker_by_agent({
            ("validator", "PLAN_VALIDATION"): prose_with_enum("PASS"),
            ("engineer", "IMPL"): prose_with_enum("IMPLEMENTATION_ESCALATE"),
        })
        sequence = [
            Step("validator", "PLAN_VALIDATION", ("PASS", "FAIL")),
            Step(
                "engineer",
                "IMPL",
                ("IMPL_DONE", "TESTS_FAIL", "IMPLEMENTATION_ESCALATE"),
            ),
        ]
        with self.assertRaises(OrchestrationEscalate) as cm:
            run_impl_loop(
                impl_path=None,
                initial_sequence=sequence,
                agent_invoker=invoker,
                sequence_decider=make_drain_decider(),
                **self._kwargs(),
            )
        self.assertEqual(cm.exception.enum, "IMPLEMENTATION_ESCALATE")
        self.assertEqual(cm.exception.reason, "agent_emit")
        self.assertIsNotNone(cm.exception.prose_path)

    def test_engineer_retry_limit_triggers_escalate(self) -> None:
        # PLAN_VALIDATION PASS + engineer IMPL × 4 (4번째에서 limit 초과)
        sequence = [
            Step("validator", "PLAN_VALIDATION", ("PASS", "FAIL")),
        ] + [
            Step("engineer", "IMPL", ("IMPL_DONE", "TESTS_FAIL"))
            for _ in range(4)
        ]
        proses = [
            prose_with_enum("PASS"),
            prose_with_enum("TESTS_FAIL"),
            prose_with_enum("TESTS_FAIL"),
            prose_with_enum("TESTS_FAIL"),
            # 4번째 engineer schedule 은 retry check 에서 막힘 (invoker 미호출)
        ]
        with self.assertRaises(OrchestrationEscalate) as cm:
            run_impl_loop(
                impl_path=None,
                initial_sequence=sequence,
                agent_invoker=make_invoker_seq(proses),
                sequence_decider=make_drain_decider(),
                **self._kwargs(),
            )
        self.assertEqual(cm.exception.enum, "IMPLEMENTATION_ESCALATE")
        self.assertEqual(cm.exception.reason, "retry_limit")

    # ----- catastrophic backbone -----

    def test_catastrophic_pr_reviewer_without_code_validation(self) -> None:
        # plan PASS → engineer IMPL_DONE → orchestrator skips CODE_VALIDATION → pr-reviewer
        invoker = make_invoker_by_agent({
            ("validator", "PLAN_VALIDATION"): prose_with_enum("PASS"),
            ("engineer", "IMPL"): prose_with_enum("IMPL_DONE"),
        })
        decider = make_static_decider([
            # after PLAN_VALIDATION
            [Step("engineer", "IMPL", ("IMPL_DONE", "TESTS_FAIL"))],
            # after engineer IMPL_DONE — orchestrator 가 pr-reviewer 바로 호출 (위반)
            [Step("pr-reviewer", None, ("LGTM", "CHANGES_REQUESTED"))],
        ])
        with self.assertRaises(CatastrophicViolation) as cm:
            run_impl_loop(
                impl_path=None,
                initial_sequence=[
                    Step("validator", "PLAN_VALIDATION", ("PASS", "FAIL")),
                ],
                agent_invoker=invoker,
                sequence_decider=decider,
                **self._kwargs(),
            )
        self.assertIn("§2.3.1", cm.exception.detail)

    def test_catastrophic_engineer_without_plan_validation(self) -> None:
        invoker = make_invoker_seq([prose_with_enum("IMPL_DONE")])
        with self.assertRaises(CatastrophicViolation) as cm:
            run_impl_loop(
                impl_path=None,
                initial_sequence=[
                    Step(
                        "engineer",
                        "IMPL",
                        ("IMPL_DONE", "TESTS_FAIL"),
                    )
                ],
                agent_invoker=invoker,
                sequence_decider=make_drain_decider(),
                **self._kwargs(),
            )
        self.assertIn("§2.3.3", cm.exception.detail)

    # ----- SPEC_GAP detour (orchestrator inserts architect SPEC_GAP) -----

    def test_spec_gap_detour_recovers(self) -> None:
        invoker = make_invoker_seq([
            prose_with_enum("PASS"),  # PLAN_VALIDATION
            prose_with_enum("SPEC_GAP_FOUND"),  # engineer IMPL
            prose_with_enum("SPEC_GAP_RESOLVED"),  # architect SPEC_GAP
            prose_with_enum("IMPL_DONE"),  # engineer IMPL retry
            prose_with_enum("PASS"),  # CODE_VALIDATION
            prose_with_enum("LGTM"),  # pr-reviewer
        ])
        decider = make_static_decider([
            # after PLAN_VALIDATION PASS
            [
                Step(
                    "engineer",
                    "IMPL",
                    ("IMPL_DONE", "SPEC_GAP_FOUND", "TESTS_FAIL"),
                ),
                Step("validator", "CODE_VALIDATION", ("PASS", "FAIL")),
                Step("pr-reviewer", None, ("LGTM", "CHANGES_REQUESTED")),
            ],
            # after engineer SPEC_GAP_FOUND — insert architect SPEC_GAP
            [
                Step("architect", "SPEC_GAP", ("SPEC_GAP_RESOLVED",)),
                Step(
                    "engineer",
                    "IMPL",
                    ("IMPL_DONE", "SPEC_GAP_FOUND", "TESTS_FAIL"),
                ),
                Step("validator", "CODE_VALIDATION", ("PASS", "FAIL")),
                Step("pr-reviewer", None, ("LGTM", "CHANGES_REQUESTED")),
            ],
            # after architect SPEC_GAP_RESOLVED
            [
                Step(
                    "engineer",
                    "IMPL",
                    ("IMPL_DONE", "SPEC_GAP_FOUND", "TESTS_FAIL"),
                ),
                Step("validator", "CODE_VALIDATION", ("PASS", "FAIL")),
                Step("pr-reviewer", None, ("LGTM", "CHANGES_REQUESTED")),
            ],
            # after engineer IMPL_DONE
            [
                Step("validator", "CODE_VALIDATION", ("PASS", "FAIL")),
                Step("pr-reviewer", None, ("LGTM", "CHANGES_REQUESTED")),
            ],
            # after CODE_VALIDATION PASS
            [Step("pr-reviewer", None, ("LGTM", "CHANGES_REQUESTED"))],
            # after pr-reviewer LGTM
            [],
        ])
        ctx = run_impl_loop(
            impl_path=None,
            initial_sequence=[
                Step("validator", "PLAN_VALIDATION", ("PASS", "FAIL")),
            ],
            agent_invoker=invoker,
            sequence_decider=decider,
            **self._kwargs(),
        )
        self.assertEqual(len(ctx.history), 6)
        self.assertEqual(ctx.history[-1].parsed_enum, "LGTM")
        # 카운터: architect SPEC_GAP 1회, engineer IMPL 2회
        self.assertEqual(ctx.attempts["architect:SPEC_GAP"], 1)
        self.assertEqual(ctx.attempts["engineer:IMPL"], 2)

    # ----- edge cases -----

    def test_invoker_returning_non_string_raises(self) -> None:
        def invoker(step, ctx):
            return 42  # not str
        with self.assertRaises(TypeError):
            run_impl_loop(
                impl_path=None,
                initial_sequence=[
                    Step("validator", "PLAN_VALIDATION", ("PASS", "FAIL")),
                ],
                agent_invoker=invoker,
                sequence_decider=make_drain_decider(),
                **self._kwargs(),
            )

    def test_prose_without_enum_raises_catastrophic_interpret_failed(self) -> None:
        invoker = make_invoker_seq(["this prose has no recognizable label"])
        with self.assertRaises(CatastrophicViolation) as cm:
            run_impl_loop(
                impl_path=None,
                initial_sequence=[
                    Step("validator", "PLAN_VALIDATION", ("PASS", "FAIL")),
                ],
                agent_invoker=invoker,
                sequence_decider=make_drain_decider(),
                **self._kwargs(),
            )
        self.assertEqual(cm.exception.rule, "interpret_failed")

    def test_max_steps_overrun_raises_halt(self) -> None:
        # decider 가 같은 sequence 무한 반환
        loop_step = Step("plan-reviewer", None, ("PLAN_REVIEW_PASS",))
        invoker = lambda step, ctx: prose_with_enum("PLAN_REVIEW_PASS")

        def cyclic_decider(**kwargs):
            return [loop_step]

        with self.assertRaises(DriverHaltError):
            run_impl_loop(
                impl_path=None,
                initial_sequence=[loop_step],
                agent_invoker=invoker,
                sequence_decider=cyclic_decider,
                max_steps=5,
                **self._kwargs(),
            )

    def test_default_sequence_helper_returns_six_steps(self) -> None:
        seq = default_impl_sequence()
        self.assertEqual(len(seq), 6)
        self.assertEqual(seq[0].agent, "architect")
        self.assertEqual(seq[-1].agent, "pr-reviewer")


if __name__ == "__main__":
    unittest.main()
