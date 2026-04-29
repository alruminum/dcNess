"""impl_driver.py — sequence 순회 + orchestration_agent 동적 갱신 driver (옵션 c).

발상 (orchestration.md §9 옵션 c):
    driver 자체는 분기 룰 hardcode 0. sequence 순회 + agent 호출 + prose 해석 + 카운터.
    각 step 후 orchestration_agent.decide_next_sequence() 가 *남은 시퀀스* 갱신.
    catastrophic backbone (orchestration.md §2.3) 와 retry 한도 (§5) 만 코드 hook 으로 강제.

핵심 API:
    StepResult         — 단일 step 실행 결과 (step / prose / prose_path / parsed_enum)
    DriverContext      — run 상태 (run_id / history / attempts / paths)
    CatastrophicViolation — §2.3 백본 위반 시 raise
    OrchestrationEscalate — §6 escalate enum 또는 retry 한도 도달 시 raise
    run_impl_loop(...) — 메인 진입점

설계 정합:
    - signal_io.write_prose / read_prose / interpret_signal 단일 호출
    - interpret_strategy.interpret_with_fallback heuristic-first
    - orchestration_agent.decide_next_sequence post-LLM
    - proposal §2.5 원칙 1 (룰 순감소) — 분기 룰 0, catastrophic backbone 만 hard-code
    - proposal §2.5 원칙 4 ("흐름 강제는 catastrophic 시퀀스만") — 본 driver 가 강제하는 흐름은 §2.3 4 항목만
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence

from harness.interpret_strategy import interpret_with_fallback
from harness.orchestration_agent import (
    ESCALATE_ENUMS,
    Step,
    decide_next_sequence,
)
from harness.signal_io import MissingSignal, write_prose

__all__ = [
    "Step",
    "StepResult",
    "DriverContext",
    "CatastrophicViolation",
    "OrchestrationEscalate",
    "DriverHaltError",
    "RETRY_LIMITS",
    "default_impl_sequence",
    "check_catastrophic",
    "check_retry_limit",
    "run_impl_loop",
]

# orchestration.md §5 retry 한도 표.
# key = (agent, mode) — None mode = mode 무관.
# value = (limit, escalate_enum)
# limit = 완료된 history 횟수 도달 시 다음 schedule 거부.
RETRY_LIMITS: dict[tuple[str, Optional[str]], tuple[int, str]] = {
    ("engineer", "IMPL"): (3, "IMPLEMENTATION_ESCALATE"),
    ("architect", "SPEC_GAP"): (2, "IMPLEMENTATION_ESCALATE"),
    ("engineer", "POLISH"): (2, "IMPLEMENTATION_ESCALATE"),
}


@dataclass
class StepResult:
    """단일 step 실행 결과."""

    step: Step
    prose: str
    prose_path: Path
    parsed_enum: str


@dataclass
class DriverContext:
    """run 전체에 걸친 상태."""

    run_id: str
    impl_path: Optional[str]
    issue_num: Optional[int]
    history: List[StepResult] = field(default_factory=list)
    attempts: dict[str, int] = field(default_factory=dict)
    base_dir: Optional[Path] = None
    state_dir: Optional[Path] = None


class CatastrophicViolation(RuntimeError):
    """orchestration.md §2.3 백본 위반."""

    def __init__(self, rule: str, detail: str) -> None:
        self.rule = rule
        self.detail = detail
        super().__init__(f"[{rule}] {detail}")


class OrchestrationEscalate(RuntimeError):
    """§6 escalate enum 수신 또는 §5 retry 한도 도달."""

    def __init__(
        self,
        enum: str,
        prose_path: Optional[Path] = None,
        reason: str = "agent_emit",
    ) -> None:
        self.enum = enum
        self.prose_path = prose_path
        self.reason = reason  # "agent_emit" | "retry_limit"
        super().__init__(f"escalate({reason}): {enum} (prose={prose_path})")


class DriverHaltError(RuntimeError):
    """driver 안전장치 (max_steps 등) 도달."""


# ---------------------------------------------------------------------------
# 기본 시퀀스 (orchestration.md §2.1 minimal pass)
# ---------------------------------------------------------------------------


def default_impl_sequence() -> List[Step]:
    return [
        Step("architect", "MODULE_PLAN", ("READY_FOR_IMPL",)),
        Step(
            "validator",
            "PLAN_VALIDATION",
            ("PASS", "FAIL", "SPEC_MISSING"),
        ),
        Step("test-engineer", None, ("TESTS_WRITTEN", "SPEC_GAP_FOUND")),
        Step(
            "engineer",
            "IMPL",
            (
                "IMPL_DONE",
                "SPEC_GAP_FOUND",
                "TESTS_FAIL",
                "IMPLEMENTATION_ESCALATE",
            ),
        ),
        Step(
            "validator",
            "CODE_VALIDATION",
            ("PASS", "FAIL", "SPEC_MISSING"),
        ),
        Step("pr-reviewer", None, ("LGTM", "CHANGES_REQUESTED")),
    ]


# ---------------------------------------------------------------------------
# Catastrophic backbone (orchestration.md §2.3)
# ---------------------------------------------------------------------------


def _last_index(items: Sequence[Any], pred: Callable[[Any], bool]) -> Optional[int]:
    for i in range(len(items) - 1, -1, -1):
        if pred(items[i]):
            return i
    return None


def check_catastrophic(
    history: Sequence[StepResult],
    next_step: Step,
) -> Optional[str]:
    """orchestration.md §2.3 4 항목 검증. 위반 시 reason 문자열 반환.

    1. pr-reviewer 직전 — 가장 최근 engineer (IMPL_DONE/POLISH_DONE) 후
       validator (CODE/BUGFIX_VALIDATION) PASS 가 history 에 있어야 함.
    2. (driver 가 squash merge 안 함 — Rule 2 외부 game)
    3. engineer 직전 (mode != POLISH) — validator PLAN_VALIDATION PASS 또는
       architect LIGHT_PLAN LIGHT_PLAN_READY 가 history 에 있어야 함.
    4. architect SYSTEM_DESIGN / TASK_DECOMPOSE 직전 —
       가장 최근 product-planner PRODUCT_PLAN_READY/UPDATED 후
       plan-reviewer PLAN_REVIEW_PASS 와 ux-architect UX_FLOW_READY/PATCHED 가 history 에 있어야 함.
    """
    # Rule 1: pr-reviewer
    if next_step.agent == "pr-reviewer":
        last_eng_idx = _last_index(
            history,
            lambda r: r.step.agent == "engineer"
            and r.parsed_enum in ("IMPL_DONE", "POLISH_DONE"),
        )
        if last_eng_idx is not None:
            tail = history[last_eng_idx + 1:]
            ok = any(
                r.step.agent == "validator"
                and r.step.mode in ("CODE_VALIDATION", "BUGFIX_VALIDATION")
                and r.parsed_enum == "PASS"
                for r in tail
            )
            if not ok:
                return (
                    "§2.3.1: pr-reviewer scheduled before validator "
                    "CODE_VALIDATION/BUGFIX_VALIDATION PASS (after most recent engineer write)"
                )

    # Rule 3: engineer non-POLISH
    if next_step.agent == "engineer" and next_step.mode != "POLISH":
        light_path_ok = any(
            r.step.agent == "architect"
            and r.step.mode == "LIGHT_PLAN"
            and r.parsed_enum == "LIGHT_PLAN_READY"
            for r in history
        )
        plan_validated = any(
            r.step.agent == "validator"
            and r.step.mode == "PLAN_VALIDATION"
            and r.parsed_enum == "PASS"
            for r in history
        )
        if not (light_path_ok or plan_validated):
            return (
                "§2.3.3: engineer scheduled before validator PLAN_VALIDATION PASS "
                "(or architect LIGHT_PLAN_READY for light path)"
            )

    # Rule 4: architect SYSTEM_DESIGN / TASK_DECOMPOSE after PRD change
    if next_step.agent == "architect" and next_step.mode in (
        "SYSTEM_DESIGN",
        "TASK_DECOMPOSE",
    ):
        last_pp_idx = _last_index(
            history,
            lambda r: r.step.agent == "product-planner"
            and r.parsed_enum in ("PRODUCT_PLAN_READY", "PRODUCT_PLAN_UPDATED"),
        )
        if last_pp_idx is not None:
            tail = history[last_pp_idx + 1:]
            has_plan_review = any(
                r.step.agent == "plan-reviewer"
                and r.parsed_enum == "PLAN_REVIEW_PASS"
                for r in tail
            )
            has_ux = any(
                r.step.agent == "ux-architect"
                and r.parsed_enum in ("UX_FLOW_READY", "UX_FLOW_PATCHED")
                for r in tail
            )
            if not (has_plan_review and has_ux):
                return (
                    "§2.3.4: architect SYSTEM_DESIGN/TASK_DECOMPOSE scheduled after PRD change "
                    "without plan-reviewer + ux-architect review"
                )

    return None


# ---------------------------------------------------------------------------
# Retry limits (orchestration.md §5)
# ---------------------------------------------------------------------------


def check_retry_limit(
    history: Sequence[StepResult],
    next_step: Step,
) -> Optional[str]:
    """history 에서 (agent, mode) 횟수 == limit 도달 시 escalate enum 반환.

    completed history 만 카운트. 다음 schedule 이 limit 째 +1 이면 거부.
    """
    key: tuple[str, Optional[str]] = (next_step.agent, next_step.mode)
    if key not in RETRY_LIMITS:
        return None
    limit, escalate_enum = RETRY_LIMITS[key]
    count = sum(
        1
        for r in history
        if r.step.agent == next_step.agent and r.step.mode == next_step.mode
    )
    if count >= limit:
        return escalate_enum
    return None


# ---------------------------------------------------------------------------
# Attempts state persistence
# ---------------------------------------------------------------------------


def _persist_attempts(state_dir: Path, attempts: dict[str, int]) -> Path:
    """`.attempts.json` atomic 저장."""
    state_dir.mkdir(parents=True, exist_ok=True)
    target = state_dir / ".attempts.json"
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(attempts, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, target)
    return target


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

AgentInvoker = Callable[[Step, "DriverContext"], str]
SequenceDecider = Callable[..., List[Step]]


def run_impl_loop(
    impl_path: Optional[str],
    issue_num: Optional[int] = None,
    initial_sequence: Optional[List[Step]] = None,
    *,
    agent_invoker: AgentInvoker,
    run_id: Optional[str] = None,
    sequence_decider: SequenceDecider = decide_next_sequence,
    decision_table_path: Optional[Path] = None,
    interpreter: Optional[Callable[[str, list[str]], str]] = None,
    base_dir: Optional[Path] = None,
    state_dir: Optional[Path] = None,
    max_steps: int = 50,
    orchestrator_kwargs: Optional[dict] = None,
) -> DriverContext:
    """impl loop 실행.

    Args:
        impl_path: 구현 계획 파일 경로 (`docs/impl/NN-*.md`). agent_invoker 가 사용.
        issue_num: GitHub issue 번호 (선택).
        initial_sequence: 시작 sequence. None = `default_impl_sequence()`.
        agent_invoker: (step, ctx) -> prose. 메인 Claude / subprocess / mock.
        run_id: run 식별자. None = `impl_<unix_ts>`.
        sequence_decider: 시퀀스 갱신 함수. None default = orchestration_agent.decide_next_sequence.
        decision_table_path: orchestration.md 경로. None = `<cwd>/docs/orchestration.md`.
        interpreter: interpret_with_fallback 의 LLM fallback. None = heuristic only.
        base_dir: signal_io prose 루트. None = `<cwd>/.claude/harness-state`.
        state_dir: `.attempts.json` 저장 디렉토리. None = `<base_dir>/<run_id>`.
        max_steps: 무한루프 안전장치. 초과 시 DriverHaltError.
        orchestrator_kwargs: sequence_decider 호출 시 추가로 전달할 kwargs (예: client=).

    Returns:
        DriverContext — 완료된 history / attempts.

    Raises:
        CatastrophicViolation: §2.3 백본 위반.
        OrchestrationEscalate: §6 escalate enum 수신 또는 §5 retry 한도 도달.
        DriverHaltError: max_steps 초과.
        MissingSignal: prose 결론 해석 실패 (catastrophic 으로 wrap 됨).
    """
    if run_id is None:
        run_id = f"impl_{int(time.time())}"
    if initial_sequence is None:
        initial_sequence = default_impl_sequence()
    if decision_table_path is None:
        decision_table_path = Path.cwd() / "docs" / "orchestration.md"
    if base_dir is None:
        base_dir = Path.cwd() / ".claude" / "harness-state"
    if state_dir is None:
        state_dir = base_dir / run_id
    state_dir.mkdir(parents=True, exist_ok=True)

    ctx = DriverContext(
        run_id=run_id,
        impl_path=impl_path,
        issue_num=issue_num,
        history=[],
        attempts={},
        base_dir=base_dir,
        state_dir=state_dir,
    )

    sequence: List[Step] = list(initial_sequence)
    decider_kwargs = dict(orchestrator_kwargs or {})

    for _ in range(max_steps):
        if not sequence:
            return ctx  # 정상 종료 — sequence 소진

        next_step = sequence[0]

        # 1. catastrophic backbone (§2.3)
        violation = check_catastrophic(ctx.history, next_step)
        if violation:
            raise CatastrophicViolation("orchestration.md §2.3", violation)

        # 2. retry 한도 (§5)
        retry_escalate = check_retry_limit(ctx.history, next_step)
        if retry_escalate:
            last_path = (
                ctx.history[-1].prose_path if ctx.history else state_dir
            )
            raise OrchestrationEscalate(
                retry_escalate,
                prose_path=last_path,
                reason="retry_limit",
            )

        # 3. agent 호출 → prose
        prose = agent_invoker(next_step, ctx)
        if not isinstance(prose, str):
            raise TypeError(
                f"agent_invoker must return str, got {type(prose).__name__}"
            )
        prose_path = write_prose(
            next_step.agent,
            run_id,
            prose,
            mode=next_step.mode,
            base_dir=base_dir,
        )

        # 4. enum 해석 (heuristic-first + LLM fallback)
        try:
            parsed = interpret_with_fallback(
                prose,
                list(next_step.allowed_enums),
                llm_interpreter=interpreter,
            )
        except MissingSignal as e:
            raise CatastrophicViolation(
                "interpret_failed",
                f"{next_step.agent}-{next_step.mode}: {e.detail}",
            ) from e

        result = StepResult(
            step=next_step,
            prose=prose,
            prose_path=prose_path,
            parsed_enum=parsed,
        )
        ctx.history.append(result)

        # 5. attempts 카운터 + 영속화
        attempts_key = (
            f"{next_step.agent}:{next_step.mode}"
            if next_step.mode
            else next_step.agent
        )
        ctx.attempts[attempts_key] = ctx.attempts.get(attempts_key, 0) + 1
        _persist_attempts(state_dir, ctx.attempts)

        # 6. escalate enum 수신
        if parsed in ESCALATE_ENUMS:
            raise OrchestrationEscalate(
                parsed,
                prose_path=prose_path,
                reason="agent_emit",
            )

        # 7. orchestration agent 가 새 sequence 결정
        remaining = sequence[1:]
        new_sequence = sequence_decider(
            last_step=next_step,
            last_parsed_enum=parsed,
            last_prose=prose,
            remaining_sequence=remaining,
            decision_table_path=decision_table_path,
            history_summary=[
                {
                    "agent": r.step.agent,
                    "mode": r.step.mode,
                    "enum": r.parsed_enum,
                }
                for r in ctx.history
            ],
            **decider_kwargs,
        )
        if not isinstance(new_sequence, list):
            raise TypeError(
                f"sequence_decider must return list[Step], "
                f"got {type(new_sequence).__name__}"
            )
        sequence = new_sequence

    raise DriverHaltError(
        f"impl_driver exceeded max_steps ({max_steps}) — possible infinite loop. "
        f"history_len={len(ctx.history)}, run_id={run_id}"
    )
