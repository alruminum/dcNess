"""sub_eval — sub completion 자동 평가 (DCN-CHG-20260501-13).

PostToolUse Agent hook 가 sub 종료 시 trace 집계 → tool histogram + anomaly 검출
→ additionalContext inject + redo_log 자동 append.

jajang 메인 자기 진단 반영 (DCN-CHG-20260501-13 plan):
    - 룰 추가 < surface 개선 (능동 retrieval → push)
    - 매번 reminder = theater. anomaly 시에만 발화
    - redo_log 권고 → 인프라 자동화

Anomaly 룰 (보수적):
    - tool_uses < 2 — sub 가 거의 일 안 함
    - 같은 tool 5회+ 반복 — 뻘짓 의심
    - prompt 에 Write/Edit 약속했는데 Write+Edit 0건 — prose-only

자동 결정:
    - PASS — anomaly 없음
    - REDO_SUSPECT — anomaly 1+ 검출. 메인이 봐서 재정의 가능.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


__all__ = ["evaluate_sub", "format_histogram", "REPEAT_TOOL_THRESHOLD"]


# 보수적 임계값 (운영 데이터 보고 조정 가능)
REPEAT_TOOL_THRESHOLD = 5
MIN_TOOL_USES = 2


def evaluate_sub(
    histogram: Dict[str, int],
    *,
    sub_prompt_hint: str = "",
) -> Dict[str, Any]:
    """histogram + 옵션 prompt hint 기반 자동 평가.

    Args:
        histogram: agent_trace.histogram 결과 — {"Read": 4, "Bash": 2, ...}
        sub_prompt_hint: sub 호출 prompt 의 일부 (Write/Edit 약속 검출용). 미사용 가능.

    Returns:
        {
            "decision": "PASS" | "REDO_SUSPECT",
            "anomalies": [str, ...],  # 발견된 anomaly 목록
            "tool_uses": int,  # 총 호출 수
        }
    """
    total = sum(histogram.values())
    anomalies: List[str] = []

    # 룰 1 — 너무 적은 호출
    if total < MIN_TOOL_USES:
        anomalies.append(f"tool_uses={total} (< {MIN_TOOL_USES})")

    # 룰 2 — 같은 tool 5회+ 반복
    for tool, count in histogram.items():
        if count >= REPEAT_TOOL_THRESHOLD:
            anomalies.append(f"{tool}×{count} (≥ {REPEAT_TOOL_THRESHOLD} 반복)")

    # 룰 3 — prompt 에 Write/Edit 약속 vs 실제 0건
    write_edit = histogram.get("Write", 0) + histogram.get("Edit", 0)
    hint_lower = (sub_prompt_hint or "").lower()
    promised_write = any(
        kw in hint_lower for kw in ("write", "edit", "create", "작성", "생성")
    )
    if promised_write and write_edit == 0 and total > 0:
        anomalies.append("prompt 에 Write/Edit 약속, 실제 0건 (prose-only 의심)")

    decision = "REDO_SUSPECT" if anomalies else "PASS"
    return {
        "decision": decision,
        "anomalies": anomalies,
        "tool_uses": total,
    }


def format_histogram(histogram: Dict[str, int]) -> str:
    """histogram → result-옆 inject 용 짧은 문자열.

    Returns:
        "Read:4 Bash:2 Write:0" 형식. 빈 dict → "(none)".
    """
    if not histogram:
        return "(none)"
    return " ".join(f"{tool}:{count}" for tool, count in sorted(histogram.items()))
