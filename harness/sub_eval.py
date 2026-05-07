"""sub_eval — sub completion 자동 평가 (DCN-CHG-20260501-13).

PostToolUse Agent hook 가 sub 종료 시 trace 집계 → tool histogram + anomaly 검출
→ additionalContext inject + redo_log 자동 append.

jajang 메인 자기 진단 반영 (DCN-CHG-20260501-13 plan):
    - 룰 추가 < surface 개선 (능동 retrieval → push)
    - 매번 reminder = theater. anomaly 시에만 발화
    - redo_log 권고 → 인프라 자동화

Anomaly 룰 (보수적):
    - tool_uses < 2 — sub 가 거의 일 안 함
    - 도구별 차등 임계 초과 반복 — 뻘짓 의심 (실측 baseline 반영, #272/#273)
    - prompt 에 Write/Edit 약속했는데 Write+Edit 0건 — prose-only
      단 prose-only agent (qa/validator/pr-reviewer 등) 는 promised_write 검사 자체
      미적용 (false positive 다발 — #272 W1).

자동 결정:
    - PASS — anomaly 없음
    - REDO_SUSPECT — anomaly 1+ 검출. 메인이 봐서 재정의 가능.
"""
from __future__ import annotations

from typing import Any, Dict, List


__all__ = [
    "evaluate_sub",
    "format_histogram",
    "REPEAT_TOOL_THRESHOLD",
    "REPEAT_TOOL_THRESHOLDS",
    "PROSE_ONLY_AGENTS",
]


# 도구별 차등 임계 (#272/#273 실측 — 정상 architect Read×8 / engineer Edit×6~10
# / pr-reviewer Read×5 / test-engineer Read×5 모두 false positive 였다).
# 의미: "같은 도구 N+ 반복" 신호는 *자연스러운 다중 파일 read* 가 아니라
# *동일 파일 동일 작업 무의미 반복* 을 잡는 것. 자연 baseline 반영해 상향.
REPEAT_TOOL_THRESHOLDS: Dict[str, int] = {
    "Read": 15,    # 다중 파일 탐색 / 인접 컨텍스트 자연
    "Edit": 12,    # 단일 파일 multi-section + 다중 파일
    "Bash": 10,    # 다중 검증 명령 자연 (test + grep + build)
    "Write": 8,
    "Glob": 10,
    "Grep": 10,
}
REPEAT_TOOL_THRESHOLD_DEFAULT = 12

# 호환용 export — 외부 import 안전. 도구 미지정 시 default 와 동일.
REPEAT_TOOL_THRESHOLD = REPEAT_TOOL_THRESHOLD_DEFAULT
MIN_TOOL_USES = 2

# prose-only agent — handoff-matrix.md §4.1 ALLOW_MATRIX 상 src 쓰기 권한 X.
# Write/Edit 0건이 *정상*. promised_write false positive 차단 (#272 W1).
PROSE_ONLY_AGENTS = frozenset({
    "qa",
    "validator",
    "pr-reviewer",
    "design-critic",
    "security-reviewer",
    "plan-reviewer",
})


def evaluate_sub(
    histogram: Dict[str, int],
    *,
    sub_prompt_hint: str = "",
    sub_type: str = "",
) -> Dict[str, Any]:
    """histogram + 옵션 prompt hint + sub_type 기반 자동 평가.

    Args:
        histogram: agent_trace.histogram 결과 — {"Read": 4, "Bash": 2, ...}
        sub_prompt_hint: sub 호출 prompt 의 일부 (Write/Edit 약속 검출용). 미사용 가능.
        sub_type: subagent_type. PROSE_ONLY_AGENTS 검사용. 미지정 시 폴백 검사.

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

    # 룰 2 — 도구별 차등 임계 초과 반복
    for tool, count in histogram.items():
        threshold = REPEAT_TOOL_THRESHOLDS.get(tool, REPEAT_TOOL_THRESHOLD_DEFAULT)
        if count >= threshold:
            anomalies.append(f"{tool}×{count} (≥ {threshold} 반복)")

    # 룰 3 — prompt 에 Write/Edit 약속 vs 실제 0건 (prose-only agent 제외)
    sub_short = (sub_type or "").split(":", 1)[0].lower()
    # plugin-namespaced (e.g. "dcness:qa") 와 short ("qa") 양쪽 호환
    if ":" in (sub_type or ""):
        sub_short = sub_type.split(":")[-1].lower()
    is_prose_only = sub_short in PROSE_ONLY_AGENTS
    if not is_prose_only:
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
