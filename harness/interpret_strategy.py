"""interpret_strategy.py — DEPRECATED (issue #284 폐기 진행).

이슈 #280 epic — prose-only routing 전환:
    - 메인 Claude 가 prose 직접 분류해 routing → 휴리스틱 enum 추출 무용지물.
    - 본 모듈은 *legacy 호환* 을 위해 시그니처만 유지. 신규 호출 추가 X.

이슈 #284 정착 후 동작:
    - `interpret_with_fallback` 는 휴리스틱 추출 자체는 *legacy 호환* 으로 보존
      (기존 외부 skill 이 `--allowed-enums` 박은 채 호출해도 crash 회피).
    - 단 telemetry 신규 기록은 **중단** — `.metrics/heuristic-calls.jsonl` 에
      더 이상 append 안 함. 누적된 baseline 데이터는 보존 (회고 자료, 이슈 #277).
    - 정형 routing telemetry 는 `harness/routing_telemetry.py` 가 대체 (#281).

폐기 배경 (이슈 #277 ROI baseline + #280 epic 결정):
    - 99.2% hit rate 는 enum 가치가 아니라 prompt 강제력. 자유 prose 도 동등 routing
      정확도 가능.
    - matrix ↔ 코드 drift 9 종 누적. enum 변경 시 다중 SSOT 동기 의무 = 실 비용.
    - orchestration.md §0 (LLM 자율 + 최소 가이드레일) 와 충돌.

Outcome 분류 (legacy):
    - heuristic_hit       : 휴리스틱 단어경계 단일 매칭 → 즉시 결론
    - heuristic_ambiguous : 휴리스틱 ambiguous → MissingSignal propagate
    - heuristic_not_found : 마커 자체 부재
    - heuristic_empty     : prose 자체 비어있음
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from harness.signal_io import MissingSignal, interpret_signal

__all__ = [
    "interpret_with_fallback",
    "HEURISTIC_TELEMETRY_FILE",
]

# 폐기됨 — 더 이상 신규 기록 안 함. 외부 분석 스크립트 호환을 위해 상수만 보존.
HEURISTIC_TELEMETRY_FILE = "heuristic-calls.jsonl"


def interpret_with_fallback(
    prose: str,
    allowed: Iterable[str],
    *,
    telemetry_dir: Optional[Path] = None,  # 무시 (deprecated)
) -> str:
    """[DEPRECATED — 이슈 #284] 휴리스틱 enum 추출. ambiguous 시 propagate.

    Args:
        prose: agent 의 자유 emit.
        allowed: 허용 enum 리스트.
        telemetry_dir: 무시됨 (이슈 #284 telemetry 중단).

    Returns:
        allowed 안의 단일 enum.

    Raises:
        MissingSignal: 휴리스틱이 단일 enum 못 뽑음 (ambiguous / not_found / empty).
        ValueError: allowed 비어 있음.

    Note:
        - 본 함수 호출은 legacy compat 영역만. 신규 routing 결정은 메인 Claude 가
          prose 직접 읽고 판단.
        - 이슈 #284 정착 후 telemetry 신규 기록 0 — `.metrics/heuristic-calls.jsonl`
          에 더 이상 append 안 함.
    """
    allowed_list = [str(a) for a in allowed]
    if not allowed_list:
        raise ValueError("allowed must be non-empty")

    # 휴리스틱 자체는 legacy 호환 (기존 외부 skill `--allowed-enums` 호출 cover).
    # telemetry 신규 기록 X — 이슈 #284 acceptance.
    return interpret_signal(prose, allowed_list)  # interpreter=None → 휴리스틱
