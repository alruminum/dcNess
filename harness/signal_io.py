"""signal_io.py — agent prose 저장 + 결론 해석 단일 책임 모듈.

발상 (status-json-mutate-pattern.md §2):
    "agent 는 prose 자유롭게 emit. harness 는 prose 의 *의미* 를
     메타 LLM 으로 해석. 형식 강제 0, flag 0, schema 0."

본 모듈은 RWHarness 의 `parse_marker` (regex + alias 사다리) + dcNess 의
이전 `state_io.py` (status JSON schema 강제) 를 모두 대체한다.

핵심 API:
    signal_path(agent, run_id, mode=None, base_dir=None) -> Path
    write_prose(agent, run_id, prose, mode=None, base_dir=None) -> Path
    read_prose(agent, run_id, mode=None, base_dir=None) -> str
    interpret_signal(prose, allowed, *, interpreter=None) -> str
    clear_run_state(run_id, base_dir=None) -> int

§4.2 폐기 항목 정합:
    - status JSON schema 강제 → prose .md 파일 + LLM 해석
    - allowed_status set 강제 → interpret_signal 의 allowed enum 인자
    - MissingStatus 5 reasons → MissingSignal 3 reasons (not_found/empty/ambiguous)

interpret_signal 의 swap point:
    기본 휴리스틱은 prose 의 마지막 500 토큰 영역에서 allowed enum 을
    case-insensitive 하게 scan. exact 1개 hit = 결론. 0개/2개+ = ambiguous.
    프로덕션 환경에선 `interpreter=` 인자로 Anthropic SDK haiku 호출 주입.
    proposal §3 비용: cycle 당 +$0.001 미만.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable, Iterable, Optional

__all__ = [
    "MissingSignal",
    "signal_path",
    "write_prose",
    "read_prose",
    "interpret_signal",
    "clear_run_state",
    "DEFAULT_BASE",
]

_AGENT_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_MODE_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

_TAIL_SCAN_CHARS = 2000


def _default_base() -> Path:
    return Path.cwd() / ".claude" / "harness-state"


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


class MissingSignal(Exception):
    """prose 또는 결론 해석 실패의 단일 normalize 예외.

    Attributes:
        reason: REASONS 중 하나.
        detail: 디버깅용 상세 메시지.
    """

    REASONS = (
        "not_found",
        "empty",
        "ambiguous",
    )

    def __init__(self, reason: str, detail: str = "") -> None:
        if reason not in self.REASONS:
            raise ValueError(
                f"unknown MissingSignal reason: {reason!r} "
                f"(allowed: {self.REASONS})"
            )
        self.reason = reason
        self.detail = detail
        super().__init__(f"[{reason}] {detail}")


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


def signal_path(
    agent: str,
    run_id: str,
    mode: Optional[str] = None,
    base_dir: Optional[Path] = None,
) -> Path:
    """prose 파일의 절대 경로 반환.

    경로 규칙: <base_dir>/<run_id>/<agent>[-<mode>].md

    예) base/run_001/validator-CODE_VALIDATION.md
        base/run_001/architect.md   (mode None)

    화이트리스트 + path traversal 자기검증.
    """
    _validate_agent(agent)
    _validate_mode(mode)
    _validate_run_id(run_id)

    base = _resolve_base(base_dir)
    name = f"{agent}-{mode}.md" if mode else f"{agent}.md"
    target = (base / run_id / name).resolve()

    try:
        target.relative_to(base)
    except ValueError as e:
        raise ValueError(
            f"path escape detected: {target} not under {base}"
        ) from e
    return target


def write_prose(
    agent: str,
    run_id: str,
    prose: str,
    *,
    mode: Optional[str] = None,
    base_dir: Optional[Path] = None,
) -> Path:
    """prose 작성. 형식 강제 없음. atomic rename 으로 race 회피.

    Returns: 작성된 파일의 절대 경로.

    Raises:
        TypeError: prose 가 str 아님.
        ValueError: 화이트리스트 위반.
        OSError: 디스크 I/O 실패.
    """
    if not isinstance(prose, str):
        raise TypeError(f"prose must be str, got {type(prose).__name__}")

    target = signal_path(agent, run_id, mode, base_dir)
    target.parent.mkdir(parents=True, exist_ok=True)

    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(prose, encoding="utf-8")
    os.replace(tmp, target)  # POSIX atomic rename
    return target


def read_prose(
    agent: str,
    run_id: str,
    *,
    mode: Optional[str] = None,
    base_dir: Optional[Path] = None,
) -> str:
    """prose 읽기. 미존재/빈 파일은 MissingSignal.

    Raises:
        MissingSignal(not_found): 파일 없음
        MissingSignal(empty): 빈 파일
    """
    target = signal_path(agent, run_id, mode, base_dir)

    if not target.exists():
        raise MissingSignal("not_found", str(target))

    try:
        raw = target.read_text(encoding="utf-8")
    except OSError as e:
        raise MissingSignal("not_found", f"{target}: {e}") from e

    if not raw.strip():
        raise MissingSignal("empty", str(target))

    return raw


def _heuristic_interpret(prose: str, allowed: list[str]) -> str:
    """Default interpreter — prose 마지막 영역에서 allowed enum 1개 매칭.

    프로덕션은 `interpret_signal(..., interpreter=anthropic_haiku_call)` 로 swap.
    """
    tail = prose[-_TAIL_SCAN_CHARS:]
    hits: list[tuple[int, str]] = []
    for value in allowed:
        # 단어 경계 매칭 (case-insensitive). enum 은 보통 ALL_CAPS 또는 단어.
        pattern = re.compile(rf"\b{re.escape(value)}\b", re.IGNORECASE)
        last = None
        for m in pattern.finditer(tail):
            last = m
        if last is not None:
            hits.append((last.start(), value))

    if not hits:
        raise MissingSignal(
            "ambiguous",
            f"no allowed enum found in tail (allowed={allowed})",
        )

    # 가장 마지막 등장한 enum 채택. tie 시 ambiguous.
    hits.sort(key=lambda x: x[0])
    last_pos, last_value = hits[-1]
    same_pos = [v for pos, v in hits if pos == last_pos]
    if len(same_pos) > 1:
        raise MissingSignal(
            "ambiguous",
            f"multiple enums at same position: {same_pos}",
        )
    return last_value


def interpret_signal(
    prose: str,
    allowed: Iterable[str],
    *,
    interpreter: Optional[Callable[[str, list[str]], str]] = None,
) -> str:
    """prose 의 결론을 allowed enum 1개로 해석.

    Args:
        prose: agent 가 emit 한 자유 텍스트.
        allowed: 허용 enum 리스트 (예: ["PASS", "FAIL", "SPEC_MISSING"]).
        interpreter: (prose, allowed_list) -> str. None 이면 휴리스틱.
                     프로덕션은 Anthropic haiku 호출 함수 주입.

    Returns:
        allowed 안의 단일 enum.

    Raises:
        MissingSignal(ambiguous): 결론 모호 (0개/복수 매칭).
        ValueError: allowed 비어있음 / interpreter 가 allowed 외 값 반환.
    """
    if not isinstance(prose, str):
        raise TypeError(f"prose must be str, got {type(prose).__name__}")
    allowed_list = [str(a) for a in allowed]
    if not allowed_list:
        raise ValueError("allowed must be non-empty")

    fn = interpreter or _heuristic_interpret
    result = fn(prose, allowed_list)
    if result not in allowed_list:
        raise ValueError(
            f"interpreter returned {result!r} not in allowed {allowed_list}"
        )
    return result


def clear_run_state(
    run_id: str,
    *,
    base_dir: Optional[Path] = None,
) -> int:
    """run 디렉토리 안의 *.md prose 파일 삭제.

    catastrophic 회피: base_dir/run_id 안만. 그 외 path 거부.

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
    for f in run_dir.glob("*.md"):
        try:
            f.unlink()
            count += 1
        except OSError:
            pass
    return count
