"""state_io.py — agent status JSON mutate / read 단일 책임 모듈.

발상 (status-json-mutate-pattern §2):
    "agent 의 자유 텍스트를 신뢰하지 않는다.
     agent 에게 외부 상태 파일 mutate 책임 부여.
     orchestrator 는 그 파일만 read."

본 모듈은 RWHarness 의 `parse_marker` (regex + alias 사다리) 를 대체할
**경로 + I/O 단일 함수** 다. 텍스트 파싱 0, 결정론 100%.

핵심 API:
    state_path(agent, run_id, mode=None, base_dir=None) -> Path
    write_status(agent, run_id, payload, mode=None, base_dir=None) -> Path
    read_status(agent, run_id, mode=None, base_dir=None,
                allowed_status=None) -> dict
    clear_run_state(run_id, base_dir=None) -> int

R8 (status-json-mutate-pattern §8) — 5 failure modes 단일 normalize:
    not_found        : 파일 미존재 (Write 누락)
    empty            : 빈 파일 + mtime 오래된 (Write 직후 sync 실패 후 정착)
    race             : 빈 파일 + mtime 매우 최근 (Write 도중 read)
    malformed_json   : JSONDecodeError (부분 작성)
    schema_violation : root 가 object 아님, 'status' 누락/타입 오류,
                       allowed_status 외 값

caller 측 retry 정책 가이드:
    not_found / malformed_json / schema_violation -> 즉시 fail (재read 무의미)
    empty / race -> 100ms 후 1회 재read 권장

R1 3-layer defense 의 첫 layer:
    write_status 가 path 생성 시 화이트리스트 + path traversal 자기검증
    (agent-boundary.py PreToolUse + PostToolUse 와 합쳐 3-layer)
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Optional, Set

__all__ = [
    "MissingStatus",
    "state_path",
    "write_status",
    "read_status",
    "clear_run_state",
    "DEFAULT_BASE",
]

# ── 화이트리스트 패턴 ──────────────────────────────────────────────────────
# agent: 소문자 + hyphen (validator, pr-reviewer 등)
# mode: 대문자 + 숫자 + underscore (PLAN_VALIDATION, CODE_VALIDATION 등). None 허용.
# run_id: 영숫자 + hyphen + dot + underscore. ".." 별도 차단.
_AGENT_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_MODE_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

# ── 기본 base 디렉토리 ────────────────────────────────────────────────────
# Path.cwd() 호출은 import 시점이 아니라 실제 호출 시점 — DEFAULT_BASE 는 lazy.
def _default_base() -> Path:
    return Path.cwd() / ".claude" / "harness-state"

# 호환성: 외부에서 import 한 module 변수처럼 쓸 수 있게 property-like 노출
class _DefaultBaseProxy:
    def __fspath__(self) -> str:
        return str(_default_base())
    def __str__(self) -> str:
        return str(_default_base())
    def __repr__(self) -> str:
        return f"<DEFAULT_BASE → {_default_base()}>"
    def resolve(self) -> Path:
        return _default_base().resolve()

DEFAULT_BASE = _DefaultBaseProxy()

# 빈 파일이 race condition 인지 empty 인지 가르는 기준 (초)
_RACE_WINDOW_SEC = 0.1


class MissingStatus(Exception):
    """status JSON 의 모든 실패모드를 단일 catch 로 normalize 하는 예외.

    Attributes:
        reason: REASONS 중 하나.
        detail: 디버깅용 상세 메시지 (path + 원인).
    """

    REASONS = (
        "not_found",
        "empty",
        "race",
        "malformed_json",
        "schema_violation",
    )

    def __init__(self, reason: str, detail: str = "") -> None:
        if reason not in self.REASONS:
            raise ValueError(
                f"unknown MissingStatus reason: {reason!r} "
                f"(allowed: {self.REASONS})"
            )
        self.reason = reason
        self.detail = detail
        super().__init__(f"[{reason}] {detail}")


# ── 내부 검증 함수 ─────────────────────────────────────────────────────────

def _validate_agent(agent: str) -> None:
    if not isinstance(agent, str) or not _AGENT_NAME_RE.match(agent):
        raise ValueError(
            f"invalid agent name: {agent!r} "
            f"(must match {_AGENT_NAME_RE.pattern})"
        )


def _validate_mode(mode: Optional[str]) -> None:
    if mode is None:
        return
    if not isinstance(mode, str) or not _MODE_NAME_RE.match(mode):
        raise ValueError(
            f"invalid mode name: {mode!r} "
            f"(must match {_MODE_NAME_RE.pattern} or be None)"
        )


def _validate_run_id(run_id: str) -> None:
    if (
        not isinstance(run_id, str)
        or not _RUN_ID_RE.match(run_id)
        or ".." in run_id
    ):
        raise ValueError(
            f"invalid run_id: {run_id!r} "
            f"(must match {_RUN_ID_RE.pattern} and not contain '..')"
        )


def _resolve_base(base_dir: Optional[Path]) -> Path:
    if base_dir is None:
        return _default_base().resolve()
    if not isinstance(base_dir, (str, Path)):
        raise TypeError(f"base_dir must be Path or str, got {type(base_dir)!r}")
    return Path(base_dir).resolve()


# ── 공개 API ──────────────────────────────────────────────────────────────

def state_path(
    agent: str,
    run_id: str,
    mode: Optional[str] = None,
    base_dir: Optional[Path] = None,
) -> Path:
    """status JSON 의 절대 경로 반환.

    경로 규칙: <base_dir>/<run_id>/<agent>[-<mode>].json

    예) base/run_001/validator-PLAN_VALIDATION.json
        base/run_001/architect.json   (mode None)

    화이트리스트 + path traversal 자기검증 (R1 layer 1).
    """
    _validate_agent(agent)
    _validate_mode(mode)
    _validate_run_id(run_id)

    base = _resolve_base(base_dir)
    name = f"{agent}-{mode}.json" if mode else f"{agent}.json"
    target = (base / run_id / name).resolve()

    # path traversal self-check — 화이트리스트 패턴이 차단하지만
    # symlink 등 경로 의존 공격까지 차단하기 위한 layer.
    try:
        target.relative_to(base)
    except ValueError as e:
        raise ValueError(
            f"path escape detected: {target} not under {base}"
        ) from e
    return target


def write_status(
    agent: str,
    run_id: str,
    payload: dict,
    *,
    mode: Optional[str] = None,
    base_dir: Optional[Path] = None,
) -> Path:
    """status JSON 작성. 'status' 키 필수, 나머지 freeform.

    atomic write: tmp 에 쓰고 rename → 부분 작성 race 회피.

    Returns: 작성된 파일의 절대 경로.

    Raises:
        ValueError: payload 가 dict 아니거나 'status' 키 누락 / 화이트리스트 위반.
        TypeError: payload 가 dict 아님.
        OSError: 디스크 I/O 실패.
    """
    if not isinstance(payload, dict):
        raise TypeError(f"payload must be dict, got {type(payload).__name__}")
    if "status" not in payload:
        raise ValueError("payload must contain 'status' key")
    if not isinstance(payload["status"], str):
        raise ValueError(
            f"payload['status'] must be str, got {type(payload['status']).__name__}"
        )

    target = state_path(agent, run_id, mode, base_dir)
    target.parent.mkdir(parents=True, exist_ok=True)

    # atomic write — 부분 작성 race 회피 (Write 도중 read 시 race / malformed 차단)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False),
        encoding="utf-8",
    )
    os.replace(tmp, target)  # POSIX atomic rename
    return target


def read_status(
    agent: str,
    run_id: str,
    *,
    mode: Optional[str] = None,
    base_dir: Optional[Path] = None,
    allowed_status: Optional[Set[str]] = None,
) -> dict:
    """status JSON 읽기. 모든 실패는 MissingStatus 로 normalize (R8).

    Args:
        agent: 에이전트 이름 (화이트리스트 검증).
        run_id: 실행 식별자.
        mode: 에이전트 모드 (예: 'PLAN_VALIDATION').
        base_dir: 기본 디렉토리 override.
        allowed_status: 지정 시 status 값이 이 집합 안에 있는지 추가 검증.
                        None 이면 status 가 string 인지만 검사.

    Returns:
        status JSON 의 deserialize 결과 (dict).

    Raises:
        MissingStatus: 5 failure modes 중 하나.
        ValueError: 화이트리스트 위반 (path 자체 부정).
    """
    target = state_path(agent, run_id, mode, base_dir)

    if not target.exists():
        raise MissingStatus("not_found", str(target))

    try:
        raw = target.read_text(encoding="utf-8")
    except OSError as e:
        # 파일이 사라진 race 등 — not_found 와 동등 처리
        raise MissingStatus("not_found", f"{target}: {e}") from e

    if not raw.strip():
        # race 휴리스틱: 매우 최근 mtime 이면 race (재read 권장)
        try:
            age = time.time() - target.stat().st_mtime
        except OSError:
            age = float("inf")
        reason = "race" if age < _RACE_WINDOW_SEC else "empty"
        raise MissingStatus(reason, str(target))

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise MissingStatus("malformed_json", f"{target}: {e}") from e

    if not isinstance(data, dict):
        raise MissingStatus(
            "schema_violation",
            f"{target}: root must be object, got {type(data).__name__}",
        )

    if "status" not in data:
        raise MissingStatus(
            "schema_violation",
            f"{target}: missing required key 'status'",
        )

    if not isinstance(data["status"], str):
        raise MissingStatus(
            "schema_violation",
            f"{target}: 'status' must be str, got {type(data['status']).__name__}",
        )

    if allowed_status is not None and data["status"] not in allowed_status:
        raise MissingStatus(
            "schema_violation",
            f"{target}: status={data['status']!r} not in {sorted(allowed_status)}",
        )

    return data


def clear_run_state(
    run_id: str,
    *,
    base_dir: Optional[Path] = None,
) -> int:
    """run 디렉토리 안의 모든 *.json status 파일 삭제.

    catastrophic 회피: base_dir/run_id 안의 파일만. 그 외 path 거부.

    Returns: 삭제된 파일 수.

    Raises:
        ValueError: run_id 화이트리스트 위반 / path traversal.
    """
    _validate_run_id(run_id)

    base = _resolve_base(base_dir)
    run_dir = (base / run_id).resolve()
    try:
        run_dir.relative_to(base)
    except ValueError as e:
        raise ValueError(f"path escape: {run_dir} not under {base}") from e

    if not run_dir.exists():
        return 0

    count = 0
    for f in run_dir.glob("*.json"):
        try:
            f.unlink()
            count += 1
        except OSError:
            # 다른 프로세스가 동시 삭제 — count 는 증가 안 함
            pass
    return count
