"""interpret_strategy.py — heuristic-first + LLM-fallback 합성 전략 + telemetry.

발상:
    `signal_io.interpret_signal` 는 휴리스틱 OR custom interpreter 둘 중 하나만.
    실 운영에선 *둘 다* 합성 필요:
      1. 휴리스틱 시도 → 단일 enum 매칭이면 LLM 호출 0 (비용 0).
      2. 휴리스틱 ambiguous → LLM fallback (비용 ~$0.0001).

    본 모듈은 두 단계를 합성하고, 매 호출의 outcome 을 telemetry 에 기록한다.
    분석 스크립트(`scripts/analyze_metrics.mjs`) 가 비율을 집계.

Outcome 분류:
    - heuristic_hit       : 휴리스틱이 단어경계 단일 매칭 → 즉시 결론
    - llm_fallback_hit    : 휴리스틱 ambiguous → LLM 호출 → 결론
    - llm_fallback_unknown: 휴리스틱 ambiguous → LLM 호출 → 모호 (UNKNOWN/allowed 외)
    - heuristic_ambiguous : 휴리스틱 ambiguous + LLM 미주입 → MissingSignal propagate

proposal R1 / R8 정합:
    R1: ambiguous 카탈로그 → `.metrics/heuristic-calls.jsonl` + `meta-llm-calls.jsonl`
        분석으로 발생 패턴 파악 → agent writing guide 정정 사이클.
    R8: 비용 측정 — heuristic_hit 비율 ↑ = LLM 호출 ↓ = 비용 ↓.

대 원칙 정합 (proposal §2.5):
    원칙 1: 신규 strategy 모듈 ~80 LOC. signal_io 자체 변경 0 (interface 보존).
    원칙 3: agent prose 자유 emit 그대로. interpreter 가 결론 추출.
    원칙 5: 30일 측정 = telemetry JSONL 누적 → 분석 후 정책 결정.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Optional

from harness.signal_io import MissingSignal, interpret_signal

__all__ = [
    "interpret_with_fallback",
    "HEURISTIC_TELEMETRY_FILE",
]

HEURISTIC_TELEMETRY_FILE = "heuristic-calls.jsonl"


def _telemetry_path(base_dir: Optional[Path]) -> Path:
    base = base_dir or (Path.cwd() / ".metrics")
    return base / HEURISTIC_TELEMETRY_FILE


def _record(
    event: dict,
    *,
    base_dir: Optional[Path] = None,
) -> None:
    if os.environ.get("DCNESS_LLM_TELEMETRY", "1") == "0":
        return
    path = _telemetry_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def interpret_with_fallback(
    prose: str,
    allowed: Iterable[str],
    *,
    llm_interpreter: Optional[Callable[[str, list[str]], str]] = None,
    telemetry_dir: Optional[Path] = None,
) -> str:
    """휴리스틱 우선, LLM fallback. 매 호출 outcome 기록.

    Args:
        prose: agent 의 자유 emit.
        allowed: 허용 enum 리스트.
        llm_interpreter: heuristic ambiguous 시 호출. None 이면 ambiguous propagate.
        telemetry_dir: 로그 디렉토리. None = `.metrics/`.

    Returns:
        allowed 안의 단일 enum.

    Raises:
        MissingSignal: 휴리스틱 + LLM 모두 ambiguous, 또는 LLM 미주입 + 휴리스틱 ambiguous.
        ValueError: allowed 비어 있음.
    """
    allowed_list = [str(a) for a in allowed]
    if not allowed_list:
        raise ValueError("allowed must be non-empty")

    base_event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "allowed": allowed_list,
        "prose_len": len(prose),
    }

    # 1단계: 휴리스틱
    heuristic_detail = ""
    try:
        result = interpret_signal(prose, allowed_list)  # interpreter=None → 휴리스틱
        _record(
            {**base_event, "outcome": "heuristic_hit", "parsed": result},
            base_dir=telemetry_dir,
        )
        return result
    except MissingSignal as heuristic_exc:
        # Python 3 에선 except as 변수가 블록 종료 시 unbind 됨 → 외부 변수에 보존
        heuristic_detail = heuristic_exc.detail
        heuristic_reason = heuristic_exc.reason
        if heuristic_reason != "ambiguous":
            # not_found / empty 는 fallback 무의미 (prose 자체 부재)
            _record(
                {
                    **base_event,
                    "outcome": f"heuristic_{heuristic_reason}",
                    "detail": heuristic_detail[:200],
                },
                base_dir=telemetry_dir,
            )
            raise
        saved_exc = heuristic_exc

    # 2단계: LLM fallback (heuristic ambiguous 만)
    if llm_interpreter is None:
        _record(
            {
                **base_event,
                "outcome": "heuristic_ambiguous_no_fallback",
                "detail": heuristic_detail[:200],
            },
            base_dir=telemetry_dir,
        )
        raise saved_exc

    try:
        llm_result = llm_interpreter(prose, allowed_list)
    except MissingSignal as llm_exc:
        _record(
            {
                **base_event,
                "outcome": "llm_fallback_unknown",
                "heuristic_detail": heuristic_detail[:200],
                "llm_detail": llm_exc.detail[:200],
            },
            base_dir=telemetry_dir,
        )
        raise

    if llm_result not in allowed_list:
        # llm_interpreter contract 위반 — defensive
        raise ValueError(
            f"llm_interpreter returned {llm_result!r} not in allowed {allowed_list}"
        )

    _record(
        {**base_event, "outcome": "llm_fallback_hit", "parsed": llm_result},
        base_dir=telemetry_dir,
    )
    return llm_result
