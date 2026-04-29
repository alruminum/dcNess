"""orchestration_agent.py — sequence 동적 갱신 결정 메타 LLM (옵션 c).

발상 (orchestration.md §9 옵션 c):
    driver 는 sequence list 만 받아 순회. 각 step 후 본 모듈의
    decide_next_sequence() 가 직전 prose + 결정표 (orchestration.md §4) 보고
    *남은 sequence* 동적 갱신 (재정렬 / 추가 / 제거).

    catastrophic backbone (orchestration.md §2.3 + §7 권한 매트릭스) 은
    driver (impl_driver.py) 가 *post-LLM* 검증. 본 모듈은 LLM raw 결정만 반환.

핵심 API:
    Step                     — frozen dataclass: agent / mode / allowed_enums
    parse_sequence_json(raw) — LLM raw text → list[Step]
    decide_next_sequence(...) — Anthropic LLM 호출 + 결과 파싱

설계 정합:
    - llm_interpreter.py 패턴 정합 (model=haiku, telemetry JSONL, DI client=)
    - signal_io.MissingSignal('ambiguous') 단일 예외 normalize
    - proposal §2.5 원칙 1 (룰 순감소) — 분기 룰 코드 hardcode 0, 결정표 LLM 위임
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

from harness.signal_io import MissingSignal

__all__ = [
    "Step",
    "DEFAULT_MODEL",
    "ALLOWED_AGENTS",
    "ESCALATE_ENUMS",
    "decide_next_sequence",
    "parse_sequence_json",
]

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
MAX_PROSE_TAIL_CHARS = 4000

# orchestration.md §4 — 13 agent (validator/architect mode 펼치기 전 단일 이름)
ALLOWED_AGENTS = (
    "product-planner",
    "plan-reviewer",
    "ux-architect",
    "architect",
    "validator",
    "test-engineer",
    "engineer",
    "designer",
    "design-critic",
    "pr-reviewer",
    "qa",
    "security-reviewer",
)

# orchestration.md §6 — 자동 복구 금지, 수신 시 즉시 사용자 보고
ESCALATE_ENUMS = (
    "IMPLEMENTATION_ESCALATE",
    "UX_FLOW_ESCALATE",
    "DESIGN_LOOP_ESCALATE",
    "SCOPE_ESCALATE",
    "PRODUCT_PLANNER_ESCALATION_NEEDED",
    "TECH_CONSTRAINT_CONFLICT",
    "UX_REDESIGN_SHORTLIST",
    "CLARITY_INSUFFICIENT",
)

_AGENT_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_MODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_ENUM_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")


@dataclass(frozen=True)
class Step:
    """단일 게이트 step. (agent, mode, allowed_enums) 3-tuple.

    allowed_enums 는 interpret_with_fallback 의 allowed 인자로 그대로 전달.
    orchestration.md §4 결정표의 각 행 = 한 Step.
    """

    agent: str
    mode: Optional[str] = None
    allowed_enums: tuple = ()

    def __post_init__(self) -> None:
        if not isinstance(self.agent, str) or not _AGENT_RE.match(self.agent):
            raise ValueError(f"invalid agent: {self.agent!r}")
        if self.agent not in ALLOWED_AGENTS:
            raise ValueError(
                f"unknown agent (not in orchestration.md §4 ALLOWED_AGENTS): "
                f"{self.agent!r}"
            )
        if self.mode is not None and (
            not isinstance(self.mode, str) or not _MODE_RE.match(self.mode)
        ):
            raise ValueError(f"invalid mode: {self.mode!r}")
        if not isinstance(self.allowed_enums, tuple):
            object.__setattr__(self, "allowed_enums", tuple(self.allowed_enums))
        if not self.allowed_enums:
            raise ValueError(f"allowed_enums must be non-empty for {self.agent}")
        for e in self.allowed_enums:
            if not isinstance(e, str) or not _ENUM_RE.match(e):
                raise ValueError(f"invalid enum {e!r} for {self.agent}")

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "mode": self.mode,
            "allowed_enums": list(self.allowed_enums),
        }


def parse_sequence_json(raw: str) -> list[Step]:
    """LLM raw 응답을 list[Step] 으로 파싱.

    JSON fence (```json ... ```) / 선후행 공백 허용. schema 위반 시 ambiguous.

    Raises:
        MissingSignal('ambiguous'): JSON parse 실패, schema 위반, agent 미허용.
    """
    text = (raw or "").strip()
    # ```json fence 처리
    if text.startswith("```"):
        lines = [
            line for line in text.split("\n")
            if not line.strip().startswith("```")
        ]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise MissingSignal(
            "ambiguous", f"orchestration agent returned invalid JSON: {e}"
        ) from e

    if not isinstance(data, list):
        raise MissingSignal(
            "ambiguous",
            f"expected JSON array, got {type(data).__name__}",
        )

    out: list[Step] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise MissingSignal(
                "ambiguous", f"sequence[{i}]: expected object, got {type(item).__name__}"
            )
        try:
            step = Step(
                agent=item.get("agent", ""),
                mode=item.get("mode"),
                allowed_enums=tuple(item.get("allowed_enums", []) or []),
            )
        except (ValueError, TypeError) as e:
            raise MissingSignal(
                "ambiguous", f"sequence[{i}]: {e}"
            ) from e
        out.append(step)
    return out


def _build_system_prompt(decision_table_text: str) -> str:
    enums = " / ".join(ESCALATE_ENUMS)
    agents = ", ".join(ALLOWED_AGENTS)
    return (
        "You are the orchestration agent for the dcNess harness. "
        "Given the most-recently-completed agent step + its prose result + the "
        "currently-planned remaining sequence, decide the NEW remaining sequence.\n\n"
        "## Decision table (orchestration.md §4)\n"
        "---\n"
        f"{decision_table_text}\n"
        "---\n\n"
        "## Output rules (STRICT)\n"
        "- Output ONLY a JSON array. No prose. No fence. No explanation.\n"
        "- Each element: {\"agent\": str, \"mode\": null|str, \"allowed_enums\": [str,...]}.\n"
        f"- agent ∈ {{{agents}}}.\n"
        "- mode: UPPERCASE_SNAKE_CASE or null.\n"
        "- allowed_enums: non-empty list of UPPERCASE_SNAKE_CASE strings.\n"
        "- Output the FULL new remaining sequence (not a delta).\n"
        f"- If the previous parsed enum is one of [{enums}], output an empty array []\n"
        "  (escalate stops the loop — driver reports to user).\n"
        "- Catastrophic backbone (orchestration.md §2.3) — DO honor:\n"
        "  1. After engineer src/ write, schedule validator CODE_VALIDATION (or BUGFIX_VALIDATION) before pr-reviewer.\n"
        "  2. Before engineer non-POLISH, ensure plan_validation passed.\n"
        "  3. After PRD change, schedule plan-reviewer + ux-architect before architect SYSTEM_DESIGN.\n"
        "- If unsure, keep the currently-planned remaining sequence as-is."
    )


def _build_user_prompt(
    last_step: Step,
    last_parsed_enum: str,
    last_prose: str,
    remaining_sequence: Sequence[Step],
    history_summary: Optional[list[dict]],
) -> str:
    tail = (last_prose or "")[-MAX_PROSE_TAIL_CHARS:]
    remaining_json = json.dumps(
        [s.to_dict() for s in remaining_sequence],
        ensure_ascii=False,
    )
    history_json = json.dumps(history_summary or [], ensure_ascii=False)
    return (
        "## Last completed step\n"
        f"agent={last_step.agent}, mode={last_step.mode}, "
        f"parsed_enum={last_parsed_enum}\n\n"
        "## Last prose (tail, possibly truncated)\n"
        "```\n"
        f"{tail}\n"
        "```\n\n"
        "## Currently planned remaining sequence (JSON)\n"
        f"{remaining_json}\n\n"
        "## History summary (JSON)\n"
        f"{history_json}\n\n"
        "Output the new full remaining sequence as a JSON array now."
    )


def _telemetry_path(base_dir: Optional[Path]) -> Path:
    base = base_dir or (Path.cwd() / ".metrics")
    return base / "orchestration-calls.jsonl"


def _record_telemetry(event: dict, *, base_dir: Optional[Path] = None) -> None:
    if os.environ.get("DCNESS_LLM_TELEMETRY", "1") == "0":
        return
    path = _telemetry_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def decide_next_sequence(
    last_step: Step,
    last_parsed_enum: str,
    last_prose: str,
    remaining_sequence: Sequence[Step],
    *,
    decision_table_path: Path,
    history_summary: Optional[list[dict]] = None,
    client: Any = None,
    model: str = DEFAULT_MODEL,
    telemetry_dir: Optional[Path] = None,
) -> list[Step]:
    """Anthropic LLM 호출로 새 remaining sequence 결정.

    Args:
        last_step: 직전 실행된 Step.
        last_parsed_enum: interpret_with_fallback 가 추출한 결론 enum.
        last_prose: 직전 agent 가 emit 한 prose 본문.
        remaining_sequence: 현재 driver 가 갖고 있는 남은 시퀀스.
        decision_table_path: orchestration.md (§4 결정표 포함) 경로.
        history_summary: 이전 step 들의 요약 (compact dict 리스트). 없으면 빈 리스트.
        client: Anthropic SDK client. None 이면 anthropic.Anthropic() 자동 생성.
        model: 모델 ID. 기본 = haiku-4-5.
        telemetry_dir: 텔레메트리 디렉토리. None = `.metrics/`.

    Returns:
        새 list[Step]. 빈 리스트 = "더 이상 진행할 step 없음" (escalate 또는 완료).

    Raises:
        FileNotFoundError: decision_table_path 없음.
        ImportError: client=None + anthropic 미설치.
        RuntimeError: API 호출 실패.
        MissingSignal('ambiguous'): JSON 파싱 실패.
    """
    if not isinstance(decision_table_path, Path):
        decision_table_path = Path(decision_table_path)
    if not decision_table_path.exists():
        raise FileNotFoundError(
            f"decision table not found: {decision_table_path}"
        )
    decision_text = decision_table_path.read_text(encoding="utf-8")

    if client is None:
        try:
            import anthropic  # noqa: WPS433
        except ImportError as e:
            raise ImportError(
                "anthropic 패키지 미설치 — pip install anthropic 또는 client= 주입."
            ) from e
        client = anthropic.Anthropic()

    system = _build_system_prompt(decision_text)
    user = _build_user_prompt(
        last_step,
        last_parsed_enum,
        last_prose,
        remaining_sequence,
        history_summary,
    )

    started = time.time()
    try:
        response = client.messages.create(
            model=model,
            max_tokens=2000,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
    except Exception as e:
        raise RuntimeError(f"orchestration agent API call failed: {e}") from e
    elapsed_ms = int((time.time() - started) * 1000)

    raw_text = ""
    for block in getattr(response, "content", []):
        if getattr(block, "type", None) == "text":
            raw_text = getattr(block, "text", "")
            break

    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
    output_tokens = getattr(usage, "output_tokens", 0) if usage else 0

    base_event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "last_agent": last_step.agent,
        "last_mode": last_step.mode,
        "last_enum": last_parsed_enum,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "elapsed_ms": elapsed_ms,
        "raw_response": raw_text[:500],
    }

    if not raw_text:
        _record_telemetry(
            {**base_event, "outcome": "empty_response"},
            base_dir=telemetry_dir,
        )
        raise MissingSignal(
            "ambiguous", f"empty orchestration response (model={model})"
        )

    try:
        new_sequence = parse_sequence_json(raw_text)
    except MissingSignal as e:
        _record_telemetry(
            {**base_event, "outcome": "parse_failed", "detail": e.detail[:300]},
            base_dir=telemetry_dir,
        )
        raise

    _record_telemetry(
        {
            **base_event,
            "outcome": "ok",
            "new_sequence_len": len(new_sequence),
            "new_sequence": [s.to_dict() for s in new_sequence],
        },
        base_dir=telemetry_dir,
    )
    return new_sequence
