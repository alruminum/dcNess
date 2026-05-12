#!/usr/bin/env python3
"""
/impl-loop 헤드리스 spawn — 각 impl task 마다 새 claude -p 자식 세션 발사.

Usage:
    python3 scripts/impl_loop_headless.py <impl-glob> [--retry-limit N] [--escalate-on <signals>] [--timeout S]

예시:
    python3 scripts/impl_loop_headless.py 'docs/milestones/v1/epics/epic-01-*/impl/*.md'

동작:
- glob 매치 파일 정렬 (prefix NN- 기준)
- 각 파일마다 claude -p cold start spawn (cwd = 현 outer worktree)
- 명령문 [A]~[E] 조립 + 자식 세션이 dcness skill 자동 등록 (plug-in SessionStart hook)
- 종료 후 결과 회수 3 layer:
  - 1차 stdout 마지막 prose enum (PASS / FAIL / ESCALATE)
  - 2차 자식 종료 코드 (0 = clean / !=0 = error)
  - 3차 GitHub 이슈 close 확인 (gh issue view <num>)
- error → 자동 retry (한도)
- blocked → 즉시 정지 (사용자 개입 필수)

설계: docs/plugin/orchestration.md §4.9 (chain 정책) + #375 그릴 D 가지 종합.

본 스크립트는 외부 dcness 활성 프로젝트의 outer worktree cwd 에서 호출. dcness self §0.2
적용 외 — 자기 자신 미적용.
"""

import argparse
import glob
import os
import re
import subprocess
import sys
from pathlib import Path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="impl-loop headless spawn")
    parser.add_argument("impl_glob", help="impl task glob (예: 'docs/.../impl/*.md')")
    parser.add_argument("--retry-limit", type=int, default=3,
                        help="task 당 자동 재시도 한도 (default 3, 0 = 즉시 정지)")
    parser.add_argument("--escalate-on", default="blocked",
                        help="즉시 정지 신호 (comma-separated, default 'blocked')")
    parser.add_argument("--timeout", type=int, default=1800,
                        help="자식 세션 timeout 초 (default 1800 = 30분)")
    parser.add_argument("--cwd", default=None,
                        help="자식 세션 cwd (default = 현재 cwd)")
    return parser.parse_args(argv)


def read_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def extract_issue_nums(task_path: str) -> dict:
    """task 파일 본문 + 부모 stories.md 에서 epic/story/task 이슈 번호 추출.

    반환: {"epic": int|None, "story": int|None, "task": int|None}
    매치 못 하면 None 으로 채움 (skip 사유).
    """
    nums = {"epic": None, "story": None, "task": None}

    task_body = read_file(task_path)
    # task 본문 안 `**GitHub Issue:** [#N]` 또는 `closes #N` 패턴
    m = re.search(r"\*\*GitHub Issue:\*\*\s*\[?#(\d+)\]?", task_body)
    if m:
        nums["task"] = int(m.group(1))
    else:
        m = re.search(r"(?:closes?|fixes?)\s*#(\d+)", task_body, re.IGNORECASE)
        if m:
            nums["task"] = int(m.group(1))

    # 부모 stories.md = task 파일의 grandparent (impl/<task>.md → epic-NN-*/stories.md)
    stories_path = Path(task_path).parent.parent / "stories.md"
    if stories_path.exists():
        stories_body = stories_path.read_text(encoding="utf-8")
        m = re.search(r"\*\*GitHub Epic Issue:\*\*\s*\[?#(\d+)\]?", stories_body)
        if m:
            nums["epic"] = int(m.group(1))
        # story 매치는 task slug 기반 (v1 = skip)

    return nums


def build_command(task_path: str, issue_nums: dict,
                  retry_attempt: int = 0, prev_error: str = None) -> str:
    """명령문 첫머리 [A]~[E] 5 묶음 조립.

    Skip: CLAUDE.md (cwd auto-load) + dcness 운영 룰 (plug-in SessionStart hook).
    Inline: 본 함수 출력.
    """
    task_body = read_file(task_path)
    parts = []

    # retry 시 prev_error 머리말
    if retry_attempt > 0 and prev_error:
        parts.append(
            f"## ⚠ 이전 시도 실패 (attempt {retry_attempt})\n\n"
            f"```\n{prev_error}\n```\n\n"
            f"위 에러 참고하여 수정 후 진행.\n\n---\n"
        )

    # [A] impl 본문
    parts.append(f"## [A] 이번 task impl 본문\n\n`{task_path}`:\n\n{task_body}\n")

    # [B] 부모 이슈 + read 명령
    if any(v is not None for v in issue_nums.values()):
        issue_lines = []
        for kind, num in issue_nums.items():
            if num is not None:
                issue_lines.append(
                    f"- {kind}: #{num} — `gh issue view {num} | head -80` 로 본문 read 의무"
                )
        parts.append(
            "## [B] 부모 이슈\n\n" + "\n".join(issue_lines) +
            "\n\n구현 진입 *전* 위 이슈 본문 read 필수. "
            "이슈에 수용 기준 / 추가 컨텍스트 / 결정 사항이 박혀있을 수 있음.\n"
        )
    else:
        parts.append(
            "## [B] 부모 이슈\n\n매칭된 이슈 번호 없음 — task 파일 본문의 수용 기준 직접 따름.\n"
        )

    # [C] ADR / architecture
    parts.append(
        "## [C] 사전 read 의무\n\n"
        "구현 *전*:\n"
        "- `docs/architecture.md` 다시 read — 모듈 흐름 / 인터페이스 / 의존성 확인\n"
        "- `docs/adr.md` 다시 read — 관련 결정 사항 확인 (의도 모르고 덮어쓰는 회귀 회피)\n"
    )

    # [D] 종료 신호 규칙
    parts.append(
        "## [D] 종료 신호 규칙 (필수)\n\n"
        "본 task 완료/정지 시 stdout 마지막 줄에 정확히 다음 enum 중 하나 박음:\n\n"
        "- **clean** → 코드 + 테스트 + commit + push + PR 생성 + 머지 + `Closes #<task-num>` trailer 로 이슈 자동 close. "
        "마지막 줄: `PASS: <한 줄 요약>`\n"
        "- **error** → 빌드/테스트 실패. 자동 재시도됨. 마지막 줄: `FAIL: <이유>`\n"
        "- **blocked** → 사용자 개입 필수 (API 키 / 인증 / 정책 결정 / Spike 의심 / 미정 의존). "
        "마지막 줄: `ESCALATE: <이유>`\n"
    )

    # [E] 본 task 명령
    parts.append(
        "## [E] 작업 시작\n\n"
        "위 [A]~[D] 룰 따라 본 task 구현 시작. "
        "dcness skill `/impl` 본문 의무 (sub-agent 호출 시퀀스 / 워크트리 / Pre-flight gate / "
        "impl 파일 사전 read) 도 함께 따름. 현행 dcness 룰은 cwd CLAUDE.md + plug-in "
        "SessionStart hook 자동 inject 된 system-reminder 참조.\n"
    )

    return "\n".join(parts)


def parse_result(stdout: str, exit_code: int) -> tuple:
    """결과 회수 1차 — stdout 마지막 prose enum 매치.

    반환: (enum, message) — enum ∈ {clean, error, blocked}
    """
    # 마지막 20 줄에서 매치 우선
    last_lines = stdout.strip().split("\n")[-20:]
    last_text = "\n".join(last_lines)

    # ESCALATE 우선 (blocked 신호 — 다른 enum 보다 우선)
    m = re.search(r"ESCALATE:\s*(.+?)(?:\n|$)", last_text)
    if m:
        return "blocked", m.group(1).strip()

    # FAIL
    m = re.search(r"FAIL:\s*(.+?)(?:\n|$)", last_text)
    if m:
        return "error", m.group(1).strip()

    # PASS
    m = re.search(r"PASS:\s*(.+?)(?:\n|$)", last_text)
    if m:
        return "clean", m.group(1).strip()

    # enum 미박힘 → exit code fallback
    if exit_code == 0:
        return "clean", "(prose enum 미박힘 — exit 0 으로 clean 판정)"
    return "error", f"(prose enum 미박힘 — exit {exit_code})"


def confirm_issue_closed(task_issue_num) -> bool:
    """결과 회수 3차 — gh issue view 로 task 이슈 close 확인."""
    if task_issue_num is None:
        return None  # 이슈 번호 모르면 skip
    try:
        result = subprocess.run(
            ["gh", "issue", "view", str(task_issue_num), "--json", "state", "-q", ".state"],
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip() == "CLOSED"
    except Exception:
        return None


def spawn_child(prompt: str, cwd: str, timeout: int) -> tuple:
    """claude -p 자식 세션 spawn.

    반환: (exit_code, stdout, stderr)
    """
    cmd = [
        "claude", "-p",
        "--dangerously-skip-permissions",
        "--output-format", "text",
        prompt,
    ]
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as e:
        return 124, e.stdout or "", e.stderr or ""


def process_task(task_path: str, cwd: str, retry_limit: int,
                 escalate_signals: set, timeout: int) -> dict:
    """단일 task 처리 (retry 포함). 반환 = {enum, message, stdout}."""
    issue_nums = extract_issue_nums(task_path)
    prev_error = None

    for attempt in range(retry_limit + 1):
        print(f"\n[task] {task_path} (attempt {attempt + 1}/{retry_limit + 1})",
              file=sys.stderr)

        prompt = build_command(
            task_path, issue_nums,
            retry_attempt=attempt,
            prev_error=prev_error,
        )
        exit_code, stdout, stderr = spawn_child(prompt, cwd, timeout)
        enum, message = parse_result(stdout, exit_code)
        print(f"[task] result: {enum} — {message}", file=sys.stderr)

        # blocked / escalate 신호 즉시 정지
        if enum in escalate_signals:
            return {"enum": "blocked", "message": message, "stdout": stdout}

        # clean — 이슈 close 2차 confirm
        if enum == "clean":
            closed = confirm_issue_closed(issue_nums["task"])
            if closed is False:
                print(
                    f"[task] WARN: prose PASS 인데 이슈 #{issue_nums['task']} 미 close",
                    file=sys.stderr,
                )
            return {"enum": "clean", "message": message, "stdout": stdout}

        # error — retry
        prev_error = (
            f"exit {exit_code}\nenum {enum}\n{message}\n\n"
            f"stderr (tail):\n{(stderr or '')[-500:]}"
        )
        if attempt < retry_limit:
            print(f"[task] retry {attempt + 1}/{retry_limit}", file=sys.stderr)
            continue

    return {
        "enum": "error",
        "message": f"retry 한도 ({retry_limit}) 초과 — {prev_error or 'unknown'}",
        "stdout": "",
    }


def print_summary(results: list) -> None:
    print("\n=== 처리 요약 ===", file=sys.stderr)
    for r in results:
        print(f"  [{r['enum']}] {r['task']} — {r['message']}", file=sys.stderr)


def main(argv=None) -> int:
    args = parse_args(argv)

    impl_files = sorted(glob.glob(args.impl_glob))
    if not impl_files:
        print(
            f"[impl-loop-headless] ERROR: no files matched: {args.impl_glob}",
            file=sys.stderr,
        )
        return 1

    cwd = args.cwd or os.getcwd()
    escalate_signals = {s.strip() for s in args.escalate_on.split(",") if s.strip()}

    print(
        f"[impl-loop-headless] cwd={cwd}, tasks={len(impl_files)}, "
        f"retry-limit={args.retry_limit}, escalate-on={escalate_signals}",
        file=sys.stderr,
    )

    results = []
    for task_path in impl_files:
        r = process_task(
            task_path, cwd,
            retry_limit=args.retry_limit,
            escalate_signals=escalate_signals,
            timeout=args.timeout,
        )
        r["task"] = task_path
        results.append(r)

        if r["enum"] == "blocked":
            print(
                f"\n[impl-loop-headless] STOP: {task_path} blocked — {r['message']}",
                file=sys.stderr,
            )
            print_summary(results)
            return 2

        if r["enum"] == "error":
            print(
                f"\n[impl-loop-headless] STOP: {task_path} error (retry 초과) — {r['message']}",
                file=sys.stderr,
            )
            print_summary(results)
            return 1

    print(
        f"\n[impl-loop-headless] ALL CLEAN ({len(results)}/{len(impl_files)})",
        file=sys.stderr,
    )
    print_summary(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
