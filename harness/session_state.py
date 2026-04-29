"""session_state.py — 세션/run 격리 상태 API (멀티세션 기본 가정).

발상 (`docs/conveyor-design.md` §4 / §6 / §9):
    Claude Code 가 세션 단위 동작 → 한 사용자가 동시 다중 세션 띄울 수 있음.
    각 세션 안에서 컨베이어가 다중 run 가능 (예: 백그라운드 ralph + foreground quick).
    sid × run_id 별 격리된 디렉토리 구조 + `_meta` envelope 으로 leftover 방어.

본 모듈은 다음을 단일 책임으로 묶는다:
    1. session_id 검증 + resolution (3-tier: env → project pointer; 글로벌 폴백 제외)
    2. session pointer 파일 (`.session-id`) 읽기/쓰기
    3. run_id 생성 (`run-{token_hex(4)}`)
    4. atomic write (O_EXCL+fsync+rename+dir fsync, 0o600 — RWH 패턴)
    5. live.json 스키마 + active_runs map 조작 (OMC `SkillActiveStateV2` 차용)

OMC + RWH 차용 매핑:
    - regex `^[a-zA-Z0-9][a-zA-Z0-9_-]{0,255}$`           ← OMC SESSION_ID_ALLOWLIST
    - stdin 3 변형 fallback (sessionId/session_id/sessionid) ← OMC
    - 3-tier resolution (env > pointer)                    ← RWH (글로벌 폴백 제외)
    - `_meta` envelope + 자기참조 sessionId 검증            ← RWH
    - atomic write O_EXCL+fsync+rename+dir fsync           ← RWH
    - active_runs map + soft tombstone                     ← OMC SkillActiveStateV2

핵심 상수:
    SESSION_ID_RE       : path traversal 방어
    DEFAULT_RUN_TTL_SEC : run 슬롯 stale 기준 (24h)
    LIVE_JSON_VERSION   : 스키마 진화 추적
"""
from __future__ import annotations

import json
import os
import re
import secrets
import select
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

__all__ = [
    "SESSION_ID_RE",
    "DEFAULT_RUN_TTL_SEC",
    "LIVE_JSON_VERSION",
    "STDIN_TIMEOUT_SEC",
    "valid_session_id",
    "session_id_from_stdin",
    "current_session_id",
    "read_session_pointer",
    "write_session_pointer",
    "generate_run_id",
    "atomic_write",
    "session_dir",
    "run_dir",
    "live_path",
    "read_live",
    "update_live",
    "start_run",
    "update_current_step",
    "complete_run",
    "cleanup_stale_runs",
]

# ── 상수 ─────────────────────────────────────────────────────────────
SESSION_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,255}$")
RUN_ID_RE = re.compile(r"^run-[a-z0-9]{8}$")

DEFAULT_RUN_TTL_SEC = 24 * 60 * 60        # 24h — completed slot 보관 후 cleanup
LIVE_JSON_VERSION = 1                      # 스키마 진화 추적
STDIN_TIMEOUT_SEC = 2.0                    # 훅 stdin 읽기 hang 방지
_ATOMIC_FILE_MODE = 0o600


# ── 경로 유틸 ───────────────────────────────────────────────────────


def _default_base() -> Path:
    return Path.cwd() / ".claude" / "harness-state"


def _resolve_base(base_dir: Optional[Path]) -> Path:
    if base_dir is None:
        return _default_base().resolve()
    if not isinstance(base_dir, (str, Path)):
        raise TypeError(f"base_dir must be Path or str, got {type(base_dir).__name__}")
    return Path(base_dir).resolve()


def session_dir(
    session_id: str, *, base_dir: Optional[Path] = None, create: bool = False
) -> Path:
    """`.sessions/{sid}/` 절대 경로."""
    if not valid_session_id(session_id):
        raise ValueError(f"invalid session_id: {session_id!r}")
    base = _resolve_base(base_dir)
    target = (base / ".sessions" / session_id).resolve()
    # path traversal 방어
    try:
        target.relative_to(base)
    except ValueError as e:
        raise ValueError(f"path escape: {target} not under {base}") from e
    if create:
        target.mkdir(parents=True, exist_ok=True)
    return target


def run_dir(
    session_id: str,
    run_id: str,
    *,
    base_dir: Optional[Path] = None,
    create: bool = False,
) -> Path:
    """`.sessions/{sid}/runs/{run_id}/` 절대 경로."""
    if not RUN_ID_RE.match(run_id):
        raise ValueError(
            f"invalid run_id: {run_id!r} (expected format: run-{{8 hex chars}})"
        )
    target = (session_dir(session_id, base_dir=base_dir) / "runs" / run_id).resolve()
    if create:
        target.mkdir(parents=True, exist_ok=True)
    return target


def live_path(session_id: str, *, base_dir: Optional[Path] = None) -> Path:
    """`.sessions/{sid}/live.json` 경로 — 읽기 전용 (디렉토리 미생성)."""
    return session_dir(session_id, base_dir=base_dir) / "live.json"


def _pointer_path(base_dir: Optional[Path] = None) -> Path:
    return _resolve_base(base_dir) / ".session-id"


# ── session_id 검증 ─────────────────────────────────────────────────


def valid_session_id(sid: Any) -> bool:
    """OMC 패턴 — path traversal 방어."""
    if not isinstance(sid, str):
        return False
    return bool(SESSION_ID_RE.match(sid))


def session_id_from_stdin(
    data: Optional[Dict[str, Any]] = None,
    timeout_sec: float = STDIN_TIMEOUT_SEC,
) -> str:
    """훅 stdin 또는 파싱된 dict 에서 session_id 추출.

    OMC 패턴 — 3 변형 fallback (sessionId / session_id / sessionid).
    검증 실패 시 빈 문자열.

    Args:
        data: 이미 파싱된 dict. None 이면 stdin 직접 read.
        timeout_sec: stdin 읽기 타임아웃 (hang 방지).
    """
    d: Optional[Dict[str, Any]] = data
    if d is None:
        try:
            if sys.stdin.isatty():
                return ""
            if timeout_sec > 0:
                ready, _, _ = select.select([sys.stdin], [], [], timeout_sec)
                if not ready:
                    return ""
            raw = sys.stdin.read()
            d = json.loads(raw) if raw.strip() else {}
        except (json.JSONDecodeError, OSError, ValueError):
            return ""
    if not isinstance(d, dict):
        return ""
    sid = d.get("session_id") or d.get("sessionId") or d.get("sessionid") or ""
    return sid if valid_session_id(sid) else ""


def current_session_id(*, base_dir: Optional[Path] = None) -> str:
    """현재 세션 ID resolution — 2-tier (RWH 3-tier 의 글로벌 폴백 제외).

    1. `DCNESS_SESSION_ID` env (subprocess 전파, 가장 권위)
    2. `.claude/harness-state/.session-id` pointer (SessionStart 훅이 작성)

    실패 시 빈 문자열. 호출자가 빈 문자열 처리 책임.
    """
    sid = os.environ.get("DCNESS_SESSION_ID", "")
    if valid_session_id(sid):
        return sid
    return read_session_pointer(base_dir=base_dir)


def read_session_pointer(*, base_dir: Optional[Path] = None) -> str:
    """`.session-id` pointer 파일 읽기. 검증 실패 시 빈 문자열."""
    path = _pointer_path(base_dir)
    try:
        if not path.exists():
            return ""
        sid = path.read_text(encoding="utf-8").strip()
        return sid if valid_session_id(sid) else ""
    except OSError:
        return ""


def write_session_pointer(
    session_id: str, *, base_dir: Optional[Path] = None
) -> Path:
    """`.session-id` pointer atomic 작성."""
    if not valid_session_id(session_id):
        raise ValueError(f"invalid session_id: {session_id!r}")
    target = _pointer_path(base_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(target, session_id.encode("utf-8"))
    return target


# ── run_id 생성 ──────────────────────────────────────────────────────


def generate_run_id() -> str:
    """`run-{token_hex(4)}` — 16M 조합, sid 안 충돌 사실상 0."""
    return f"run-{secrets.token_hex(4)}"


# ── atomic write (O_EXCL+fsync+rename+dir fsync, 0o600) ─────────────


def atomic_write(
    target: Path, content: bytes, *, mode: int = _ATOMIC_FILE_MODE
) -> None:
    """RWH 패턴 — POSIX atomic 보장.

    1. tmp 파일 (O_EXCL — 같은 이름 충돌 시 raise)
    2. write + fsync
    3. close
    4. rename (atomic)
    5. dir fsync (POSIX 강제)

    Args:
        target: 최종 파일 경로.
        content: bytes.
        mode: 0o600 기본 (소유자만).
    """
    if not isinstance(content, (bytes, bytearray)):
        raise TypeError(f"content must be bytes, got {type(content).__name__}")
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)

    # unique tmp 이름 — O_EXCL 충돌 회피 + race-safe
    tmp_name = f"{target.name}.tmp.{os.getpid()}.{uuid.uuid4().hex[:8]}"
    tmp = target.parent / tmp_name

    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        os.write(fd, bytes(content))
        os.fsync(fd)
    finally:
        os.close(fd)

    try:
        os.replace(tmp, target)  # POSIX atomic rename
    except OSError:
        # 정리: tmp 가 남았으면 제거
        try:
            tmp.unlink()
        except OSError:
            pass
        raise

    # dir fsync — 새 entry 가 디스크에 박히도록 (POSIX 권장)
    try:
        dir_fd = os.open(str(target.parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError:
        # 일부 파일시스템 (tmpfs 등) 은 dir fsync 미지원 — 무시
        pass


# ── live.json read / update ──────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _make_meta(session_id: str) -> Dict[str, Any]:
    return {
        "sessionId": session_id,
        "writtenAt": _now_iso(),
        "version": LIVE_JSON_VERSION,
    }


def read_live(
    session_id: str, *, base_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """live.json 읽기 + `_meta.sessionId` 자기참조 검증.

    소유자 불일치 (`_meta.sessionId` ≠ session_id) 면 빈 dict 반환 — leftover 방어.
    파일 미존재 / 파싱 실패 시 빈 dict.
    """
    if not valid_session_id(session_id):
        return {}
    path = live_path(session_id, base_dir=base_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    meta = data.get("_meta", {})
    if not isinstance(meta, dict):
        return {}
    meta_sid = meta.get("sessionId", "")
    if meta_sid and meta_sid != session_id:
        # 다른 세션이 같은 경로에 덮어쓰기 시도 → 거부
        return {}
    return data


def update_live(
    session_id: str,
    *,
    base_dir: Optional[Path] = None,
    **fields: Any,
) -> None:
    """live.json 의 top-level 필드 read-merge-atomic-write.

    `_meta` 와 `session_id` 자기참조는 항상 갱신.
    값이 None 이면 필드 삭제 (단 `active_runs` 같은 dict 는 그대로 유지 — `**fields` 가 None 일 때만 pop).
    """
    if not valid_session_id(session_id):
        raise ValueError(f"invalid session_id: {session_id!r}")

    current = read_live(session_id, base_dir=base_dir) or {}
    # `_meta` 는 항상 새로 작성. 옛 envelope 신뢰 안 함.
    current.pop("_meta", None)

    for k, v in fields.items():
        if v is None:
            current.pop(k, None)
        else:
            current[k] = v

    current["session_id"] = session_id
    current["_meta"] = _make_meta(session_id)
    if "active_runs" not in current:
        current["active_runs"] = {}

    payload = json.dumps(current, ensure_ascii=False, indent=2, sort_keys=True)
    target = live_path(session_id, base_dir=base_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(target, payload.encode("utf-8"))


# ── active_runs map 조작 ────────────────────────────────────────────


def _resolve_run_dir_str(
    session_id: str, run_id: str, base_dir: Optional[Path]
) -> str:
    """run_dir 의 문자열 표현 — base_dir 가 cwd 안이면 상대경로, 아니면 절대."""
    rd = run_dir(session_id, run_id, base_dir=base_dir)
    try:
        return str(rd.relative_to(Path.cwd()))
    except ValueError:
        return str(rd)


def start_run(
    session_id: str,
    run_id: str,
    entry_point: str,
    *,
    base_dir: Optional[Path] = None,
    issue_num: Optional[int] = None,
) -> None:
    """`active_runs[run_id]` 슬롯 추가 + run 디렉토리 생성.

    이미 존재하면 ValueError (중복 run_id 방어).
    """
    if not valid_session_id(session_id):
        raise ValueError(f"invalid session_id: {session_id!r}")
    if not RUN_ID_RE.match(run_id):
        raise ValueError(f"invalid run_id: {run_id!r}")
    if not isinstance(entry_point, str) or not entry_point:
        raise ValueError("entry_point must be non-empty str")

    live = read_live(session_id, base_dir=base_dir) or {}
    active = live.get("active_runs", {})
    if not isinstance(active, dict):
        active = {}
    if run_id in active:
        raise ValueError(f"run_id already active: {run_id}")

    now = _now_iso()
    active[run_id] = {
        "run_id": run_id,
        "entry_point": entry_point,
        "started_at": now,
        "last_confirmed_at": now,
        "completed_at": None,
        "run_dir": _resolve_run_dir_str(session_id, run_id, base_dir),
        "current_step": None,
        "issue_num": issue_num,
    }
    update_live(session_id, base_dir=base_dir, active_runs=active)
    # run 디렉토리 생성
    run_dir(session_id, run_id, base_dir=base_dir, create=True)


def update_current_step(
    session_id: str,
    run_id: str,
    agent: str,
    mode: Optional[str],
    *,
    base_dir: Optional[Path] = None,
) -> None:
    """`active_runs[run_id].current_step` 갱신 + heartbeat (`last_confirmed_at`)."""
    live = read_live(session_id, base_dir=base_dir) or {}
    active = live.get("active_runs", {})
    if not isinstance(active, dict) or run_id not in active:
        raise ValueError(f"run_id not active: {run_id}")
    slot = dict(active[run_id])
    now = _now_iso()
    slot["current_step"] = {
        "agent": agent,
        "mode": mode,
        "started_at": now,
    }
    slot["last_confirmed_at"] = now
    active[run_id] = slot
    update_live(session_id, base_dir=base_dir, active_runs=active)


def complete_run(
    session_id: str,
    run_id: str,
    *,
    base_dir: Optional[Path] = None,
) -> None:
    """`active_runs[run_id].completed_at` 채움 (soft tombstone — 즉시 삭제 X)."""
    live = read_live(session_id, base_dir=base_dir) or {}
    active = live.get("active_runs", {})
    if not isinstance(active, dict) or run_id not in active:
        return  # idempotent — 이미 없으면 noop
    slot = dict(active[run_id])
    now = _now_iso()
    slot["completed_at"] = now
    slot["last_confirmed_at"] = now
    slot["current_step"] = None
    active[run_id] = slot
    update_live(session_id, base_dir=base_dir, active_runs=active)


def cleanup_stale_runs(
    session_id: str,
    *,
    ttl_sec: int = DEFAULT_RUN_TTL_SEC,
    base_dir: Optional[Path] = None,
) -> int:
    """다음 슬롯 삭제:
        1. `completed_at` 채워진 + ttl_sec 초과한 슬롯
        2. `last_confirmed_at` 이 ttl_sec 초과한 슬롯 (heartbeat dead)

    Returns: 삭제된 슬롯 수.
    """
    live = read_live(session_id, base_dir=base_dir) or {}
    active = live.get("active_runs", {})
    if not isinstance(active, dict):
        return 0

    now = datetime.now(timezone.utc)
    removed = 0
    survivors: Dict[str, Any] = {}

    for rid, slot in active.items():
        if not isinstance(slot, dict):
            continue
        completed_at = slot.get("completed_at")
        last_confirmed = slot.get("last_confirmed_at")

        candidate_iso = completed_at or last_confirmed
        if not candidate_iso:
            survivors[rid] = slot
            continue
        try:
            ts = datetime.fromisoformat(str(candidate_iso))
        except ValueError:
            survivors[rid] = slot
            continue
        age_sec = (now - ts).total_seconds()
        if age_sec > ttl_sec:
            removed += 1
        else:
            survivors[rid] = slot

    if removed:
        update_live(session_id, base_dir=base_dir, active_runs=survivors)
    return removed
