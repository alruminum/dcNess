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
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

__all__ = [
    "SESSION_ID_RE",
    "DEFAULT_RUN_TTL_SEC",
    "DEFAULT_PID_TTL_SEC",
    "LIVE_JSON_VERSION",
    "STDIN_TIMEOUT_SEC",
    "valid_cc_pid",
    "pid_session_path",
    "pid_run_path",
    "write_pid_session",
    "read_pid_session",
    "write_pid_current_run",
    "read_pid_current_run",
    "clear_pid_current_run",
    "cleanup_stale_pid_files",
    "get_cc_pid_via_ppid_chain",
    "auto_detect_session_id",
    "auto_detect_run_id",
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
DEFAULT_PID_TTL_SEC = 24 * 60 * 60        # 24h — by-pid 파일 stale 기준 (PID 재사용 보호)
LIVE_JSON_VERSION = 1                      # 스키마 진화 추적
STDIN_TIMEOUT_SEC = 2.0                    # 훅 stdin 읽기 hang 방지
_ATOMIC_FILE_MODE = 0o600
_PPID_LOOKUP_TIMEOUT_SEC = 2.0


# ── 경로 유틸 ───────────────────────────────────────────────────────


_DEFAULT_BASE_CACHE: Dict[str, Path] = {}


def _resolve_state_root_for_cwd(cwd_str: str) -> Path:
    """git rev-parse --git-common-dir 으로 main repo 의 state root 해석.

    worktree 진입 (cwd = `.claude/worktrees/{name}/`) 후에도 `git rev-parse
    --git-common-dir` 은 main repo `.git` 를 가리킨다 (git 표준). 그래서 main repo
    의 `.claude/harness-state/` 가 단일 source 가 됨 → SessionStart 훅이 main
    repo 에서 박은 by-pid / live.json 을 worktree 안 helper 도 그대로 본다.

    git 미설치 / git 리포 아님 / subprocess 실패 → cwd 폴백 (legacy 동작).
    cwd 별 캐시 (subprocess 반복 호출 회피).
    """
    if cwd_str in _DEFAULT_BASE_CACHE:
        return _DEFAULT_BASE_CACHE[cwd_str]
    cwd = Path(cwd_str)
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd_str,
            timeout=_PPID_LOOKUP_TIMEOUT_SEC,
        )
        common_str = result.stdout.strip()
        if common_str:
            common_path = Path(common_str)
            if not common_path.is_absolute():
                common_path = cwd / common_path
            main_root = common_path.parent.resolve()
            base = main_root / ".claude" / "harness-state"
            _DEFAULT_BASE_CACHE[cwd_str] = base
            return base
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
        OSError,
    ):
        pass
    base = cwd / ".claude" / "harness-state"
    _DEFAULT_BASE_CACHE[cwd_str] = base
    return base


def _clear_default_base_cache() -> None:
    """테스트 보조 — _DEFAULT_BASE_CACHE 무력화."""
    _DEFAULT_BASE_CACHE.clear()


def _default_base() -> Path:
    return _resolve_state_root_for_cwd(str(Path.cwd().resolve()))


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


# ── by-pid 레지스트리 (멀티세션 정합 핵심) ─────────────────────────


def valid_cc_pid(cc_pid: Any) -> bool:
    """양수 정수만 유효."""
    return isinstance(cc_pid, int) and cc_pid > 0


def pid_session_path(cc_pid: int, *, base_dir: Optional[Path] = None) -> Path:
    """`.by-pid/{cc_pid}` 절대 경로."""
    if not valid_cc_pid(cc_pid):
        raise ValueError(f"invalid cc_pid: {cc_pid!r}")
    return _resolve_base(base_dir) / ".by-pid" / str(cc_pid)


def pid_run_path(cc_pid: int, *, base_dir: Optional[Path] = None) -> Path:
    """`.by-pid-current-run/{cc_pid}` 절대 경로."""
    if not valid_cc_pid(cc_pid):
        raise ValueError(f"invalid cc_pid: {cc_pid!r}")
    return _resolve_base(base_dir) / ".by-pid-current-run" / str(cc_pid)


def write_pid_session(
    cc_pid: int, session_id: str, *, base_dir: Optional[Path] = None
) -> Path:
    """`.by-pid/{cc_pid}` ← session_id atomic 작성."""
    if not valid_session_id(session_id):
        raise ValueError(f"invalid session_id: {session_id!r}")
    target = pid_session_path(cc_pid, base_dir=base_dir)
    atomic_write(target, session_id.encode("utf-8"))
    return target


def read_pid_session(cc_pid: int, *, base_dir: Optional[Path] = None) -> str:
    """`.by-pid/{cc_pid}` 읽기. 미존재 / 잘못된 sid → 빈 문자열."""
    try:
        path = pid_session_path(cc_pid, base_dir=base_dir)
    except ValueError:
        return ""
    try:
        if not path.exists():
            return ""
        sid = path.read_text(encoding="utf-8").strip()
        return sid if valid_session_id(sid) else ""
    except OSError:
        return ""


def write_pid_current_run(
    cc_pid: int, run_id: str, *, base_dir: Optional[Path] = None
) -> Path:
    """`.by-pid-current-run/{cc_pid}` ← run_id atomic 작성."""
    if not RUN_ID_RE.match(run_id):
        raise ValueError(f"invalid run_id: {run_id!r}")
    target = pid_run_path(cc_pid, base_dir=base_dir)
    atomic_write(target, run_id.encode("utf-8"))
    return target


def read_pid_current_run(cc_pid: int, *, base_dir: Optional[Path] = None) -> str:
    """`.by-pid-current-run/{cc_pid}` 읽기. 미존재 → 빈 문자열."""
    try:
        path = pid_run_path(cc_pid, base_dir=base_dir)
    except ValueError:
        return ""
    try:
        if not path.exists():
            return ""
        rid = path.read_text(encoding="utf-8").strip()
        return rid if RUN_ID_RE.match(rid) else ""
    except OSError:
        return ""


def clear_pid_current_run(
    cc_pid: int, *, base_dir: Optional[Path] = None
) -> bool:
    """`.by-pid-current-run/{cc_pid}` 삭제. 성공 여부 반환."""
    try:
        path = pid_run_path(cc_pid, base_dir=base_dir)
    except ValueError:
        return False
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def cleanup_stale_pid_files(
    *,
    ttl_sec: int = DEFAULT_PID_TTL_SEC,
    base_dir: Optional[Path] = None,
) -> int:
    """오래된 by-pid 파일 삭제 (PID 재사용 보호).

    `.by-pid/*` 와 `.by-pid-current-run/*` 의 mtime 기준 ttl_sec 초과 파일 제거.
    Returns: 삭제된 파일 수.
    """
    base = _resolve_base(base_dir)
    now = datetime.now(timezone.utc).timestamp()
    removed = 0
    for sub in (".by-pid", ".by-pid-current-run"):
        d = base / sub
        if not d.exists():
            continue
        for f in d.iterdir():
            try:
                age = now - f.stat().st_mtime
                if age > ttl_sec:
                    f.unlink()
                    removed += 1
            except OSError:
                pass
    return removed


# ── PPID chain — Bash 에서 호출된 helper 의 cc_pid 추출 ───────────


def get_cc_pid_via_ppid_chain() -> Optional[int]:
    """python helper 가 자신의 grandparent (CC main) PID 추출.

    호출 chain: CC main → Bash subprocess → python helper.
    `os.getppid()` = Bash pid. `ps -o ppid= -p <bash_pid>` = CC main pid.

    Returns None if can't determine (e.g. ps 실패, 단독 실행).
    """
    try:
        bash_pid = os.getppid()
        result = subprocess.run(
            ["ps", "-o", "ppid=", "-p", str(bash_pid)],
            capture_output=True,
            text=True,
            check=True,
            timeout=_PPID_LOOKUP_TIMEOUT_SEC,
        )
        cc_pid = int(result.stdout.strip())
        if cc_pid > 0:
            return cc_pid
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
        ValueError,
    ):
        pass
    return None


def auto_detect_session_id(*, base_dir: Optional[Path] = None) -> str:
    """helper 컨텍스트 — by-pid (멀티세션 정합) 우선, env/pointer 폴백."""
    cc_pid = get_cc_pid_via_ppid_chain()
    if cc_pid is not None:
        sid = read_pid_session(cc_pid, base_dir=base_dir)
        if sid:
            return sid
    return current_session_id(base_dir=base_dir)


def auto_detect_run_id(*, base_dir: Optional[Path] = None) -> str:
    """helper 컨텍스트 — by-pid-current-run 에서 rid 추출."""
    cc_pid = get_cc_pid_via_ppid_chain()
    if cc_pid is None:
        return ""
    return read_pid_current_run(cc_pid, base_dir=base_dir)


# ── CLI (python3 -m harness.session_state <subcommand>) ─────────────


def _cli_init_session(args: Any) -> int:
    """SessionStart 훅이 호출. by-pid 작성 + live.json 초기화."""
    if not valid_session_id(args.sid):
        print(f"[session_state] invalid sid: {args.sid!r}", file=sys.stderr)
        return 1
    if not valid_cc_pid(args.cc_pid):
        print(f"[session_state] invalid cc_pid: {args.cc_pid!r}", file=sys.stderr)
        return 1
    write_pid_session(args.cc_pid, args.sid)
    if not read_live(args.sid):
        update_live(args.sid)  # 빈 active_runs 로 초기화
    return 0


def _cli_begin_run(args: Any) -> int:
    """sid auto-detect → rid 생성 → start_run + by-pid-current-run."""
    sid = auto_detect_session_id()
    if not sid:
        print("[session_state] sid 미해결 — SessionStart 훅 미실행?", file=sys.stderr)
        return 1
    rid = generate_run_id()
    issue_num = args.issue_num if args.issue_num is not None else None
    start_run(sid, rid, args.entry_point, issue_num=issue_num)
    cc_pid = get_cc_pid_via_ppid_chain()
    if cc_pid is not None:
        write_pid_current_run(cc_pid, rid)
    print(rid)
    return 0


def _cli_end_run(args: Any) -> int:
    """sid+rid auto-detect → complete_run + clear by-pid-current-run."""
    sid = auto_detect_session_id()
    rid = auto_detect_run_id()
    if not sid or not rid:
        print("[session_state] sid/rid 미해결", file=sys.stderr)
        return 1
    complete_run(sid, rid)
    cc_pid = get_cc_pid_via_ppid_chain()
    if cc_pid is not None:
        clear_pid_current_run(cc_pid)
    return 0


def _cli_begin_step(args: Any) -> int:
    """sid+rid auto-detect → update_current_step."""
    sid = auto_detect_session_id()
    rid = auto_detect_run_id()
    if not sid or not rid:
        print("[session_state] sid/rid 미해결", file=sys.stderr)
        return 1
    mode = args.mode if args.mode else None
    update_current_step(sid, rid, args.agent, mode)
    print("ok")
    return 0


def _cli_end_step(args: Any) -> int:
    """sid+rid auto-detect → write_prose + interpret_with_fallback."""
    # 지연 import — interpret_strategy 는 telemetry 등 무거움
    from harness.signal_io import write_prose
    from harness.interpret_strategy import interpret_with_fallback
    from harness.signal_io import MissingSignal

    sid = auto_detect_session_id()
    rid = auto_detect_run_id()
    if not sid or not rid:
        print("[session_state] sid/rid 미해결", file=sys.stderr)
        return 1

    prose = Path(args.prose_file).read_text(encoding="utf-8")
    if not prose.strip():
        print("[session_state] empty prose", file=sys.stderr)
        return 1

    mode = args.mode if args.mode else None
    # prose 저장 — base_dir 은 .sessions/{sid}/runs/ (signal_io 가 그 아래 rid 디렉토리 생성)
    base = session_dir(sid) / "runs"
    write_prose(args.agent, rid, prose, mode=mode, base_dir=base)

    allowed = [s.strip() for s in args.allowed_enums.split(",") if s.strip()]
    if not allowed:
        print("[session_state] empty --allowed-enums", file=sys.stderr)
        return 1

    try:
        enum = interpret_with_fallback(prose, allowed)
    except MissingSignal as e:
        print("AMBIGUOUS", file=sys.stdout)
        print(f"[session_state] interpret 실패: {e.detail[:200]}", file=sys.stderr)
        return 0  # ambiguous 자체는 정상 결과 — 메인이 이 신호 보고 pause 결정

    print(enum)
    return 0


def _build_arg_parser() -> Any:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python3 -m harness.session_state",
        description="dcNess 세션/run 격리 helper CLI",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init-session", help="SessionStart 훅 보조")
    p_init.add_argument("sid")
    p_init.add_argument("cc_pid", type=int)
    p_init.set_defaults(func=_cli_init_session)

    p_br = sub.add_parser("begin-run", help="run_id 발급 + start_run")
    p_br.add_argument("entry_point")
    p_br.add_argument("--issue-num", type=int, default=None)
    p_br.set_defaults(func=_cli_begin_run)

    p_er = sub.add_parser("end-run", help="complete_run + clear by-pid-current-run")
    p_er.set_defaults(func=_cli_end_run)

    p_bs = sub.add_parser("begin-step", help="current_step + heartbeat 갱신")
    p_bs.add_argument("agent")
    p_bs.add_argument("mode", nargs="?", default="")
    p_bs.set_defaults(func=_cli_begin_step)

    p_es = sub.add_parser("end-step", help="prose 저장 + enum 추출 (stdout)")
    p_es.add_argument("agent")
    p_es.add_argument("mode", nargs="?", default="")
    p_es.add_argument("--allowed-enums", required=True, help="comma-separated")
    p_es.add_argument("--prose-file", required=True, help="prose 본문 파일 경로")
    p_es.set_defaults(func=_cli_end_step)

    return parser


def _main(argv: Optional[list] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(_main())
