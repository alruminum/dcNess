#!/usr/bin/env python3
"""
Auto Loop — 야간 자판기 (Issue #299).

dcness 활성 프로젝트의 impl task 디렉토리를 받아 매 task 마다 새 `claude -p`
프로세스 (cold start) 로 발사한다. 매 호출이 새 프로세스 = 자동 컨텍스트 클리어.
dcness SessionStart hook 이 매 호출 자동 발화 → CLAUDE.md / docs / SSOT inject.

자판기의 책임은 *발사 + escalate 감지 + retry 카운팅* 만.
모든 작업 판단 (PR 생성 / agent 호출 순서 / 워크트리 / 트레일러 분기 등) 은
임시 메인 (claude -p 안의 클로드) 자율. dcness §1 자율성 원칙 정합.

Usage:
    python3 auto_loop.py <impl_dir> [--max-budget-usd 0.5] [--retry 3]

예시:
    python3 auto_loop.py docs/milestones/v1/epics/epic-X/impl
"""

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

KST = timezone(timedelta(hours=9))

# escalate 결론 enum — handoff-matrix.md §6 카탈로그 정합.
# 발견 시 자판기 즉시 종료 (사용자 위임).
ESCALATE_ENUMS = {
    "IMPLEMENTATION_ESCALATE",
    "SPEC_GAP_FOUND",
    "DESIGN_REVIEW_ESCALATE",
    "UX_REVIEW_ESCALATE",
    "VARIANTS_ALL_REJECTED",
    "ESCALATE",
}

# 정상 완료 enum — 다음 task 진행.
ADVANCE_ENUMS = {
    "IMPL_DONE",
    "IMPL_PARTIAL",
    "LIGHT_PLAN_READY",
    "VALIDATED",
    "LGTM",
    "DOCS_SYNC_READY",
    "PRODUCT_PLAN_READY",
    "TASK_DONE",
}


def stamp() -> str:
    return datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S%z")


def log(msg: str):
    print(f"[auto-loop {stamp()}] {msg}", file=sys.stderr, flush=True)


def discover_tasks(impl_dir: Path) -> list[Path]:
    """impl/*.md 정렬 (파일명 prefix `NN-` 기준)."""
    if not impl_dir.is_dir():
        log(f"ERROR: {impl_dir} not a directory")
        sys.exit(1)
    tasks = sorted(impl_dir.glob("*.md"))
    if not tasks:
        log(f"ERROR: {impl_dir} 에 *.md 없음")
        sys.exit(1)
    return tasks


def extract_enum(prose: str) -> Optional[str]:
    """prose 마지막 1500자 안에서 결론 enum 추출.

    dcness §1 — prose 마지막 영역에서 enum heuristic. handoff-matrix 카탈로그
    + 정상 advance enum 둘 다 매칭. 가장 마지막에 등장하는 enum 우선.
    """
    if not prose:
        return None
    tail = prose[-1500:]
    candidates = ESCALATE_ENUMS | ADVANCE_ENUMS
    found = []
    for token in re.finditer(r"\b([A-Z][A-Z_]{4,})\b", tail):
        word = token.group(1)
        if word in candidates:
            found.append((token.start(), word))
    if not found:
        return None
    found.sort(key=lambda x: x[0])
    return found[-1][1]


def extract_prose(claude_json: dict) -> str:
    """claude -p --output-format json 응답에서 prose 추출.

    응답 구조는 claude 버전에 따라 다를 수 있음. fail-soft 로 여러 키 시도.
    """
    for key in ("result", "text", "content", "output"):
        v = claude_json.get(key)
        if isinstance(v, str) and v.strip():
            return v
        if isinstance(v, list):
            joined = "\n".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in v
            )
            if joined.strip():
                return joined
    return json.dumps(claude_json, ensure_ascii=False)


def build_prompt(task_file: Path, prev_prose_path: Optional[Path]) -> str:
    """claude -p 에 발사할 prompt 생성.

    - 작업 본문 (impl/NN-foo.md 통째)
    - (retry 시) 직전 시도 prose 파일 path inject — 임시 메인 자율 read
    - dcness §1 정합: 형식 강제 X. 임시 메인이 자율 판단.
    """
    body = task_file.read_text(encoding="utf-8")
    sections = []

    if prev_prose_path and prev_prose_path.exists():
        sections.append(
            f"## ⚠ 이전 시도 실패\n\n"
            f"직전 시도의 prose 결과: `{prev_prose_path}`\n"
            f"필요시 read 후 직전 실패 분석. 같은 실수 회피."
        )

    sections.append(
        f"## 작업\n\n"
        f"파일: `{task_file}`\n\n"
        f"본 작업을 dcness 룰 따라 진행. 워크트리 / 에이전트 호출 순서 / "
        f"PR 생성 / 트레일러 분기 모두 임시 자율 판단 (dcness §1).\n\n"
        f"끝나면 prose 마지막 단락에 결론 enum 명시 (예: IMPL_DONE / "
        f"IMPLEMENTATION_ESCALATE / SPEC_GAP_FOUND 등 — handoff-matrix.md §6).\n\n"
        f"---\n\n{body}"
    )

    return "\n\n---\n\n".join(sections)


def invoke_claude(
    prompt: str,
    cwd: Path,
    max_budget_usd: float,
    output_dir: Path,
    task_name: str,
    attempt: int,
) -> tuple[Optional[str], Optional[Path], int]:
    """claude -p 1회 호출. 반환 = (prose, prose_path, exit_code)."""
    cmd = [
        "claude", "-p",
        "--output-format", "json",
        "--no-session-persistence",
        "--max-budget-usd", str(max_budget_usd),
        "--dangerously-skip-permissions",
        prompt,
    ]
    log(f"  발사: {task_name} (시도 {attempt})")
    t0 = time.monotonic()
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=3600,
        )
    except subprocess.TimeoutExpired:
        log(f"  ⚠ TIMEOUT (3600s) — {task_name} 시도 {attempt}")
        return None, None, -1

    elapsed = int(time.monotonic() - t0)
    log(f"  완료: {task_name} 시도 {attempt} [{elapsed}s, exit {result.returncode}]")

    # raw output 저장 (디버깅용)
    raw_path = output_dir / f"{task_name}-attempt{attempt}.json"
    raw_path.write_text(result.stdout or "", encoding="utf-8")

    # prose 추출
    prose = ""
    try:
        if result.stdout:
            data = json.loads(result.stdout)
            prose = extract_prose(data)
            # budget 초과 / error 감지
            if data.get("is_error") or data.get("subtype", "").startswith("error_"):
                log(f"  ⚠ claude error: {data.get('subtype', 'unknown')}")
                if "max_budget" in str(data.get("subtype", "")):
                    log(f"  ⚠ budget 초과 — 자판기 종료")
                    return prose, raw_path, 2
    except json.JSONDecodeError:
        log(f"  ⚠ JSON 파싱 실패. stdout 일부: {result.stdout[:200] if result.stdout else '(empty)'}")
        prose = result.stdout or ""

    # prose 별도 저장 (다음 시도의 prev_prose_path 후보)
    prose_path = output_dir / f"{task_name}-attempt{attempt}.md"
    prose_path.write_text(prose, encoding="utf-8")

    return prose, prose_path, result.returncode


def run_task(
    task_file: Path,
    cwd: Path,
    max_budget_usd: float,
    max_retry: int,
    output_dir: Path,
) -> tuple[str, Optional[str]]:
    """단일 task 실행 (retry 포함). 반환 = (status, enum)

    status: "completed" | "escalate" | "failed" | "budget_exhausted"
    """
    task_name = task_file.stem
    prev_prose_path = None

    for attempt in range(1, max_retry + 1):
        prompt = build_prompt(task_file, prev_prose_path)
        prose, prose_path, exit_code = invoke_claude(
            prompt, cwd, max_budget_usd, output_dir, task_name, attempt,
        )

        if exit_code == 2:
            return "budget_exhausted", None

        enum = extract_enum(prose) if prose else None
        log(f"  결론 enum: {enum or '(추출 실패)'}")

        if enum in ESCALATE_ENUMS:
            return "escalate", enum

        if enum in ADVANCE_ENUMS:
            return "completed", enum

        # enum 추출 실패 또는 모호 → retry
        if attempt < max_retry:
            log(f"  ↻ retry {attempt}/{max_retry} — enum 불명")
            prev_prose_path = prose_path
        else:
            log(f"  ✗ {max_retry}회 시도 후 실패 — 자판기 종료")
            return "failed", enum

    return "failed", None


def report(results: list[dict], stop_reason: str):
    log("=" * 60)
    log(f"자판기 종료: {stop_reason}")
    log(f"처리: {sum(1 for r in results if r['status'] == 'completed')}/{len(results)}")
    for r in results:
        mark = {
            "completed": "✓",
            "escalate": "⏸",
            "failed": "✗",
            "budget_exhausted": "💰",
        }.get(r["status"], "?")
        log(f"  {mark} {r['task']}: {r['status']} ({r.get('enum') or '-'})")
    log("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="dcness 야간 자판기 (Issue #299)")
    parser.add_argument("impl_dir", help="impl task 디렉토리 (예: docs/milestones/v1/epics/epic-X/impl)")
    parser.add_argument("--max-budget-usd", type=float, default=0.5, help="매 호출 비용 cap (기본 0.5)")
    parser.add_argument("--retry", type=int, default=3, help="실패 시 retry 횟수 (기본 3)")
    parser.add_argument("--cwd", default=".", help="claude -p 실행 cwd (기본 현재 디렉토리)")
    args = parser.parse_args()

    impl_dir = Path(args.impl_dir).resolve()
    cwd = Path(args.cwd).resolve()

    output_dir = impl_dir.parent / ".auto-loop"
    output_dir.mkdir(exist_ok=True)
    log(f"output dir: {output_dir} (디버깅용 prose / json dump)")

    tasks = discover_tasks(impl_dir)
    log(f"task {len(tasks)} 개 발견. cwd={cwd}, budget=${args.max_budget_usd}/call")

    results = []
    stop_reason = "전체 완료"

    for i, task_file in enumerate(tasks, 1):
        log(f"━━━ Task {i}/{len(tasks)}: {task_file.name} ━━━")
        status, enum = run_task(
            task_file, cwd, args.max_budget_usd, args.retry, output_dir,
        )
        results.append({"task": task_file.name, "status": status, "enum": enum})

        if status != "completed":
            stop_reason = f"task {i}/{len(tasks)} 에서 {status} ({enum or '?'})"
            break

    report(results, stop_reason)
    sys.exit(0 if stop_reason == "전체 완료" else 2)


if __name__ == "__main__":
    main()
