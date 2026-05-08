"""routing_telemetry.py — prose-only routing 회귀 검증용 raw 측정 데이터.

이슈 #281 (epic #280): enum 시스템 폐기 *전후* routing 정확도 비교 baseline.

기록 대상 (raw 데이터만 — 정형 검증 X, dcness-rules.md §1 원칙 2 정합):

    1. agent_call    PostToolUse Agent 발화 시 1줄 — 어떤 sub 가 어떤 prose 결론
                     으로 종료했는지. 이후 메인이 prose 보고 다음 routing 결정.
                     prose_tail 만 보존 (마지막 1200 자).
    2. cascade       메인이 결정 못 해 사용자에게 위임한 명시적 marker. CLI/helper
                     로 메인이 직접 1줄 박는다. enum 시스템의 ambiguous 비율과 동등.

저장 위치:
    `.metrics/routing-decisions.jsonl`  — 프로젝트 전역 누적 (enum heuristic-calls.jsonl
    와 동일 패턴). 외부 활성화 프로젝트도 자동 동일 형식.

전제:
    - 형식 검증 / schema 강제 X. raw append-only.
    - 회고 분석은 사후 (`scripts/research/*.mjs` 패턴).
    - DCNESS_LLM_TELEMETRY=0 → 비활성 (테스트·dryrun 회피).

Schema (강제 X — 권장 필드):
    ts          ISO8601 UTC, 자동
    event       "agent_call" | "cascade"
    sub         subagent_type (agent_call 일 때)
    mode        sub mode (선택)
    tool_use_id PreToolUse↔PostToolUse 매칭 키 (선택)
    prose_tail  결론 prose 마지막 1200 자 (agent_call 일 때)
    reason      cascade 사유 자유 텍스트 (cascade 일 때)
    run_id      현재 run_id (선택)
    session_id  현재 session_id (선택)
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

__all__ = [
    "ROUTING_TELEMETRY_FILE",
    "record_agent_call",
    "record_cascade",
]


ROUTING_TELEMETRY_FILE = "routing-decisions.jsonl"

_PROSE_TAIL_LIMIT = 1200


def _telemetry_path(base_dir: Optional[Path]) -> Path:
    base = base_dir or (Path.cwd() / ".metrics")
    return base / ROUTING_TELEMETRY_FILE


def _ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _append(event: dict, *, base_dir: Optional[Path] = None) -> None:
    if os.environ.get("DCNESS_LLM_TELEMETRY", "1") == "0":
        return
    path = _telemetry_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)


def record_agent_call(
    sub: str,
    prose: str,
    *,
    mode: Optional[str] = None,
    tool_use_id: str = "",
    run_id: str = "",
    session_id: str = "",
    base_dir: Optional[Path] = None,
) -> None:
    """sub agent 종료 시 1줄 append. prose 결론 부분만 보존 (tail-cap)."""
    if not isinstance(sub, str) or not sub.strip():
        return  # 잘못된 sub_type 은 silent skip — 훅 본 흐름 보호
    if not isinstance(prose, str):
        prose = ""
    tail = prose[-_PROSE_TAIL_LIMIT:] if prose else ""
    event = {
        "ts": _ts(),
        "event": "agent_call",
        "sub": sub,
        "mode": mode or "",
        "tool_use_id": tool_use_id or "",
        "run_id": run_id or "",
        "session_id": session_id or "",
        "prose_len": len(prose),
        "prose_tail": tail,
    }
    _append(event, base_dir=base_dir)


def record_cascade(
    reason: str,
    *,
    sub: str = "",
    mode: Optional[str] = None,
    run_id: str = "",
    session_id: str = "",
    base_dir: Optional[Path] = None,
) -> None:
    """메인이 routing 결정 못 해 사용자에게 위임 시 1줄 append.

    enum 시스템의 ambiguous 비율과 동등. 메인이 명시적으로 박아야 의미.
    """
    event = {
        "ts": _ts(),
        "event": "cascade",
        "sub": sub or "",
        "mode": mode or "",
        "run_id": run_id or "",
        "session_id": session_id or "",
        "reason": (reason or "")[:500],
    }
    _append(event, base_dir=base_dir)


def _cli(argv: Optional[list] = None) -> int:
    """CLI: routing_telemetry record-cascade --reason "..." [--sub ... --mode ...]."""
    import argparse

    p = argparse.ArgumentParser(prog="routing_telemetry")
    sub_p = p.add_subparsers(dest="cmd", required=True)

    cas = sub_p.add_parser("record-cascade", help="cascade marker 1줄 append")
    cas.add_argument("--reason", required=True, help="cascade 사유")
    cas.add_argument("--sub", default="", help="직전 sub_type (선택)")
    cas.add_argument("--mode", default="", help="직전 mode (선택)")
    cas.add_argument("--run-id", default="", help="현재 run_id (선택)")
    cas.add_argument("--session-id", default="", help="현재 session_id (선택)")
    cas.add_argument(
        "--base-dir", default="",
        help=".metrics 부모 디렉토리. 미지정 시 cwd/.metrics",
    )

    args = p.parse_args(argv)
    if args.cmd == "record-cascade":
        base = Path(args.base_dir) if args.base_dir else None
        record_cascade(
            args.reason,
            sub=args.sub or "",
            mode=args.mode or None,
            run_id=args.run_id or "",
            session_id=args.session_id or "",
            base_dir=base,
        )
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(_cli())
