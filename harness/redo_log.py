"""redo_log — 메인 Claude 의 sub cycle 평가 audit log (DCN-CHG-20260501-11).

매 sub completion notification 평가 후 메인이 1줄 append. 학습 입력.
저장 위치: `.sessions/{sid}/runs/{rid}/redo-log.jsonl`.

Schema (강제 X — 메인 자율, 권장 필드만):
    ts          (auto)  ISO8601 UTC, 미지정 시 자동 추가
    agent_id            sub task id (notification <task-id>)
    sub                 subagent type (engineer / architect / ...)
    mode                sub mode (IMPL / MODULE_PLAN / ...)
    decision            PASS / REDO_SAME / REDO_BACK / REDO_DIFF
    reason              자유 텍스트
    next_action         다음 step 결정
    trace_summary       agent_trace.jsonl 요약 (선택)

규약:
    - jsonl (line-per-entry), 200 bytes 이하 권장
    - POSIX O_APPEND atomic — 동시 write race 안전 (PIPE_BUF=4096 이내)
    - malformed line read 시 skip (silent)
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from harness.session_state import run_dir


__all__ = ["append", "read_all", "tail", "REDO_LOG_NAME"]


REDO_LOG_NAME = "redo-log.jsonl"


def _log_path(
    session_id: str, run_id: str, *, base_dir: Optional[Path] = None
) -> Path:
    return run_dir(session_id, run_id, base_dir=base_dir, create=True) / REDO_LOG_NAME


def append(
    session_id: str,
    run_id: str,
    entry: Dict[str, Any],
    *,
    base_dir: Optional[Path] = None,
) -> None:
    """redo-log.jsonl 에 1줄 append. ts 미지정 시 자동 추가.

    POSIX O_APPEND atomic — 4096 bytes 이내 entry 동시 write 안전.
    """
    if not isinstance(entry, dict):
        raise TypeError(f"entry must be dict, got {type(entry).__name__}")
    if "ts" not in entry:
        entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **entry}
    line = json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n"
    target = _log_path(session_id, run_id, base_dir=base_dir)
    fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)


def read_all(
    session_id: str,
    run_id: str,
    *,
    base_dir: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """모든 entry 반환 (시간 순). 비존재 / 빈 파일 → []."""
    target = _log_path(session_id, run_id, base_dir=base_dir)
    if not target.exists():
        return []
    entries: List[Dict[str, Any]] = []
    with open(target, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def tail(
    session_id: str,
    run_id: str,
    n: int = 10,
    *,
    base_dir: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """마지막 n entry 반환."""
    if n <= 0:
        return []
    return read_all(session_id, run_id, base_dir=base_dir)[-n:]
