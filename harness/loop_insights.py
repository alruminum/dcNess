"""loop_insights — 루프별 agent 학습 누적 (DCN-CHG-20260502-02).

각 루프 종료 시 redo-log + WASTE/GOOD findings → agent별 파일에 누적.
begin-step 에서 읽어 메인 Claude 에게 주입.

저장 위치: <main_repo_root>/.claude/loop-insights/<agent>[-<mode>].md

worktree 진입 후에도 main repo root 기준으로 저장 — ExitWorktree(remove)
시 누적분 손실 회피 (#306 개선점 5). main repo root 해석은
`_resolve_project_root` (`session_state.py`) 의 git common-dir γ-resolution
재사용. git 미설치 / 리포 아님 시 cwd 폴백.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from harness import redo_log
from harness import run_review as rv
from harness.session_state import run_dir as get_run_dir
from harness.session_state import _resolve_project_root


__all__ = ["insights_path", "read", "append_findings", "append_from_run"]

_INSIGHTS_DIR = Path(".claude") / "loop-insights"


def _normalize_cwd(cwd: Path) -> Path:
    """cwd 를 main repo root 로 정규화 (#306 개선점 5).

    worktree 안 cwd 면 main repo root 반환. git 미사용 환경 폴백 시 cwd 자체.
    """
    try:
        return _resolve_project_root(Path(cwd).resolve()).resolve()
    except OSError:
        return Path(cwd).resolve()


def insights_path(
    agent: str, mode: Optional[str] = None, cwd: Path = Path(".")
) -> Path:
    name = agent if not mode else f"{agent}-{mode}"
    return _normalize_cwd(cwd) / _INSIGHTS_DIR / f"{name}.md"


def read(
    agent: str, mode: Optional[str] = None, cwd: Path = Path(".")
) -> str:
    p = insights_path(agent, mode, cwd)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8").strip()


def append_findings(
    agent: str,
    mode: Optional[str],
    bads: list[str],
    goods: list[str],
    cwd: Path = Path("."),
    date_str: Optional[str] = None,
) -> None:
    """bads/goods 항목을 agent 파일에 append. 이미 존재하는 항목은 스킵."""
    if not bads and not goods:
        return

    p = insights_path(agent, mode, cwd)
    p.parent.mkdir(parents=True, exist_ok=True)

    existing = p.read_text(encoding="utf-8") if p.exists() else ""

    header = f"# Loop Insights: {agent}" + (f" / {mode}" if mode else "") + "\n"
    if not existing:
        existing = header + "\n## 하지 말 것\n\n## 잘 됐던 것\n"

    lines_to_add: list[tuple[str, str]] = []  # (section, item)
    for item in bads:
        if item not in existing:
            lines_to_add.append(("하지 말 것", item))
    for item in goods:
        if item not in existing:
            lines_to_add.append(("잘 됐던 것", item))

    if not lines_to_add:
        return

    result = existing
    for section, item in lines_to_add:
        marker = f"## {section}"
        if marker in result:
            idx = result.index(marker) + len(marker)
            # 다음 ## 또는 끝 전에 삽입
            next_h = result.find("\n## ", idx)
            insert_at = next_h if next_h != -1 else len(result)
            result = result[:insert_at].rstrip() + f"\n- {item}\n" + result[insert_at:]
        else:
            result = result.rstrip() + f"\n\n## {section}\n- {item}\n"

    p.write_text(result, encoding="utf-8")


def append_from_run(
    sid: str, rid: str, cwd: Path = Path(".")
) -> list[str]:
    """finalize-run --accumulate 진입점. 수정된 파일 경로 목록 반환."""
    rd = get_run_dir(sid, rid)
    today = time.strftime("%Y-%m-%d", time.gmtime())

    # 1. redo-log → REDO_* 항목에서 (agent, mode, reason) 추출
    redo_entries = redo_log.read_all(sid, rid)
    redo_bads: dict[tuple[str, Optional[str]], list[str]] = {}
    for e in redo_entries:
        decision = e.get("decision", "")
        if not str(decision).startswith("REDO"):
            continue
        sub = e.get("sub") or "unknown"
        mode: Optional[str] = e.get("mode") or None
        reason = str(e.get("reason", "")).strip()
        if not reason:
            continue
        key = (sub, mode)
        redo_bads.setdefault(key, []).append(f"{reason} ({decision}, {today})")

    # 2. steps → WASTE/GOOD findings (mode는 step에서 조회)
    steps = rv.parse_steps(rd)
    wastes = rv.detect_wastes(steps)
    goods = rv.detect_goods(steps)

    waste_bads: dict[tuple[str, Optional[str]], list[str]] = {}
    for w in wastes:
        m = steps[w.step_idx].mode if w.step_idx < len(steps) else None
        key = (w.agent, m)
        waste_bads.setdefault(key, []).append(
            f"{w.detail} [{w.pattern}] ({today})"
        )

    good_items: dict[tuple[str, Optional[str]], list[str]] = {}
    for g in goods:
        m = steps[g.step_idx].mode if g.step_idx < len(steps) else None
        key = (g.agent, m)
        good_items.setdefault(key, []).append(
            f"{g.detail} [{g.pattern}] ({today})"
        )

    # 3. 전체 key 수집 → append
    all_keys: set[tuple[str, Optional[str]]] = (
        set(redo_bads) | set(waste_bads) | set(good_items)
    )
    modified: list[str] = []
    for key in all_keys:
        agent, mode = key
        bads = redo_bads.get(key, []) + waste_bads.get(key, [])
        gs = good_items.get(key, [])
        if bads or gs:
            append_findings(agent, mode, bads, gs, cwd=cwd)
            modified.append(str(insights_path(agent, mode, cwd)))

    return modified
