"""interpret_strategy.py — heuristic-only enum 추출 + telemetry.

발상 (DCN-CHG-20260430-04 정착):
    `signal_io.interpret_signal` 의 휴리스틱만 사용.
    `interpret_with_fallback` = 호환성 wrapper (heuristic 호출 + telemetry 기록).
    LLM fallback 폐기 — 휴리스틱 ambiguous 시 그대로 raise → 메인 Claude 가 cascade
    (재호출 / 사용자 위임) 결정.

LLM fallback 폐기 이유 (DCN-CHG-20260430-04):
    - dcness 의 도그푸딩 호환 (API 키 의존 회피).
    - 메타 LLM 호출 = 비용 + latency + 또 다른 사다리 진입 (LLM 결과 검증).
    - 메인 Claude 가 자체 LLM 이라 별도 LLM judge 불필요.
    - 트렌드상 [2026 structured output] 으로 가는 길에 [2025 meta LLM] 단계 skip.

Outcome 분류 (telemetry):
    - heuristic_hit       : 휴리스틱 단어경계 단일 매칭 → 즉시 결론
    - heuristic_ambiguous : 휴리스틱 ambiguous → MissingSignal propagate (메인이 cascade)
    - heuristic_not_found : 마커 자체 부재
    - heuristic_empty     : prose 자체 비어있음

대 원칙 정합 (proposal §2.5):
    원칙 1 (룰 순감소): LLM fallback 코드 / 의존성 (anthropic SDK) 제거.
    원칙 3 (prose-only): agent 자유 emit, 휴리스틱 단어경계로 결론 추출.
    원칙 5 (30일 측정): telemetry JSONL 누적 → 휴리스틱 hit/ambiguous 비율 분석.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

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
    telemetry_dir: Optional[Path] = None,
) -> str:
    """휴리스틱 enum 추출 + telemetry. ambiguous 시 그대로 propagate.

    Args:
        prose: agent 의 자유 emit.
        allowed: 허용 enum 리스트.
        telemetry_dir: 로그 디렉토리. None = `.metrics/`.

    Returns:
        allowed 안의 단일 enum.

    Raises:
        MissingSignal: 휴리스틱이 단일 enum 못 뽑음 (ambiguous / not_found / empty).
                       메인 Claude 가 cascade (재호출 / 사용자 위임) 결정.
        ValueError: allowed 비어 있음.

    Note:
        함수명에 `_with_fallback` 잔존 — 호환성 (외부 호출자 변경 비용 ↓).
        실제론 LLM fallback 폐기 (DCN-CHG-20260430-04). 휴리스틱-only.
    """
    allowed_list = [str(a) for a in allowed]
    if not allowed_list:
        raise ValueError("allowed must be non-empty")

    base_event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "allowed": allowed_list,
        "prose_len": len(prose),
    }

    try:
        result = interpret_signal(prose, allowed_list)  # interpreter=None → 휴리스틱
        _record(
            {**base_event, "outcome": "heuristic_hit", "parsed": result},
            base_dir=telemetry_dir,
        )
        return result
    except MissingSignal as exc:
        _record(
            {
                **base_event,
                "outcome": f"heuristic_{exc.reason}",
                "detail": exc.detail[:200],
            },
            base_dir=telemetry_dir,
        )
        raise
