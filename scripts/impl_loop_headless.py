#!/usr/bin/env python3
"""
/impl-loop 헤드리스 spawn — 각 impl task 마다 새 claude -p 자식 세션 발사.

Usage:
    python3 scripts/impl_loop_headless.py <impl-glob> [--retry-limit N] [--escalate-on <signals>] [--timeout S]

예시:
    python3 scripts/impl_loop_headless.py 'docs/milestones/v1/epics/epic-01-*/impl/*.md'
    python3 scripts/impl_loop_headless.py 'docs/.../impl/01-foo.md'  # 단발 task 동일 처리

동작:
- glob 매치 파일 정렬 (prefix NN- 기준)
- 각 파일마다 claude -p cold start spawn (cwd = 현 outer worktree)
- 자식 prompt = `/dcness:impl <task-path>` 슬래시 직호출 (chain 깊이 0)
  → 자식 CC 가 슬래시 파싱 후 commands/impl.md 본문을 system-reminder 로 자동 inject
  → 사전 read 의무 / conveyor cycle / enum 룰 등 정식 instruction 으로 자식에 도달
- retry 시 `--append-system-prompt` 로 이전 에러 컨텍스트 inject
- 종료 후 결과 회수 3 layer:
  - 1차 stdout 마지막 enum (PASS / FAIL / ESCALATE)
  - 2차 자식 종료 코드 (0 = clean / !=0 = error)
  - 3차 GitHub 이슈 close 확인 (gh issue view <num>) — false-clean 안전망
- error → 자동 retry (한도)
- blocked → 즉시 정지 (사용자 개입 필수)

설계: #422 = 자식 conveyor cycle 누락 + false-clean → 안전망 추가 + 슬래시 직호출
리팩토링으로 chain 깊이 0 단축. #375 그릴 D 가지 종합 후속.

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


def build_invocation(task_path: str,
                     retry_attempt: int = 0,
                     prev_error: str = None) -> tuple:
    """슬래시 직호출 invocation 조립 (#425 follow-up — chain 깊이 0).

    반환: (extra_cli_args, user_prompt)
    - user_prompt = `/dcness:impl <task-path>` — CC 가 슬래시 파싱 후
      commands/impl.md 스킬 본문을 system-reminder 로 자식 세션에 자동 inject
    - extra_cli_args = retry 시 `--append-system-prompt <prev_error>` 추가

    이전 `[A]~[E]` 5 묶음 자연어 본문 폐기. 사유 = chain 깊이 3 → 0 단축:
    - 옛: 자식이 본문 [E] → /impl 스킬 결정 → loop-procedure.md 결정 → 명령 호출
    - 신: 자식이 슬래시 = 스킬 본문 직접 instruction → 명령 호출 (1 단계)

    부수 정보 ([A] task 본문 inline / [B] 부모 이슈 read / [C] ADR 사전 read /
    [D] enum 규칙) 은 commands/impl.md 본문이 이미 강제. 중복 제거.
    """
    extra_args = []
    if retry_attempt > 0 and prev_error:
        retry_context = (
            f"이전 시도 실패 (attempt {retry_attempt}):\n\n"
            f"{prev_error}\n\n"
            "위 에러 참고하여 수정 후 진행. /dcness:impl 본문 룰 따름."
        )
        extra_args = ["--append-system-prompt", retry_context]

    user_prompt = f"/dcness:impl {task_path}"
    return extra_args, user_prompt


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


def spawn_child(prompt: str, cwd: str, timeout: int,
                extra_args: list = None,
                stream_to: "io.TextIOBase | None" = None) -> tuple:
    """claude -p 자식 세션 spawn — 슬래시 직호출 + 실시간 stdout stream.

    extra_args = `--append-system-prompt <retry_context>` 등 추가 CLI 인자.
    stream_to = 자식 stdout line 실시간 echo 대상 (default sys.stderr).
                None 박으면 echo skip (capture only).
    반환: (exit_code, stdout, stderr)

    옛 `subprocess.run(capture_output=True)` (전체 buffer) → `Popen + line stream`
    으로 교체 (#429 follow-up — 사용자 메인 세션에서 자식 진행 실시간 가시화).
    헤드리스 parent 가 `run_in_background=true` 로 호출되면 Monitor tool 이
    stdout line stream 을 메인 Claude 로 notification 으로 전달.
    """
    cmd = [
        "claude", "-p",
        "--dangerously-skip-permissions",
        "--output-format", "text",
    ]
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(prompt)

    if stream_to is None:
        stream_to = sys.stderr

    captured_stdout = []
    captured_stderr = []

    try:
        proc = subprocess.Popen(
            cmd, cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True, bufsize=1,  # line-buffered
        )
    except FileNotFoundError as e:
        return 127, "", f"claude CLI not found: {e}"

    import threading

    def _drain(pipe, sink, prefix):
        try:
            for line in iter(pipe.readline, ""):
                sink.append(line)
                if stream_to is not None:
                    stream_to.write(f"{prefix}{line}")
                    stream_to.flush()
        finally:
            pipe.close()

    t_out = threading.Thread(
        target=_drain, args=(proc.stdout, captured_stdout, "  [child] "),
        daemon=True,
    )
    t_err = threading.Thread(
        target=_drain, args=(proc.stderr, captured_stderr, "  [child:err] "),
        daemon=True,
    )
    t_out.start()
    t_err.start()

    try:
        exit_code = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        t_out.join(timeout=2)
        t_err.join(timeout=2)
        return 124, "".join(captured_stdout), "".join(captured_stderr)

    t_out.join(timeout=5)
    t_err.join(timeout=5)
    return exit_code, "".join(captured_stdout), "".join(captured_stderr)


def process_task(task_path: str, cwd: str, retry_limit: int,
                 escalate_signals: set, timeout: int) -> dict:
    """단일 task 처리 (retry 포함). 반환 = {enum, message, stdout}."""
    issue_nums = extract_issue_nums(task_path)
    prev_error = None

    for attempt in range(retry_limit + 1):
        print(f"\n[task] {task_path} (attempt {attempt + 1}/{retry_limit + 1})",
              file=sys.stderr)

        extra_args, prompt = build_invocation(
            task_path,
            retry_attempt=attempt,
            prev_error=prev_error,
        )
        exit_code, stdout, stderr = spawn_child(prompt, cwd, timeout, extra_args=extra_args)
        enum, message = parse_result(stdout, exit_code)
        print(f"[task] result: {enum} — {message}", file=sys.stderr)

        # blocked / escalate 신호 즉시 정지
        if enum in escalate_signals:
            return {"enum": "blocked", "message": message, "stdout": stdout}

        # clean — 이슈 close 2차 confirm (#422 강화: WARN → blocked 강등)
        if enum == "clean":
            task_issue = issue_nums.get("task")
            if task_issue is not None:
                closed = confirm_issue_closed(task_issue)
                if closed is False:
                    # PASS prose / exit 0 fallback 인데 이슈 미 close = false-clean.
                    # 사용자 위임 prose + enum 누락 + 미머지 (#422 NS2 케이스) 잡힘.
                    return {
                        "enum": "blocked",
                        "message": (
                            f"prose PASS / exit 0 인데 이슈 #{task_issue} 미 close — "
                            f"false-clean 의심 (자식이 enum 누락 + PR 미머지 상태로 종료 가능성)"
                        ),
                        "stdout": stdout,
                    }
            else:
                # 이슈 번호 부재 → cwd uncommitted files 로 fallback 검사.
                # cwd 자체에 잔존하는 케이스만 잡힘 (worktree 안 잔존은 미검출 — 한계).
                try:
                    res = subprocess.run(
                        ["git", "status", "--porcelain"],
                        cwd=cwd, capture_output=True, text=True, timeout=10,
                    )
                    if res.stdout.strip():
                        return {
                            "enum": "blocked",
                            "message": (
                                "prose PASS / exit 0 인데 cwd uncommitted files 잔존 — "
                                "false-clean 의심"
                            ),
                            "stdout": stdout,
                        }
                except Exception:
                    pass
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
