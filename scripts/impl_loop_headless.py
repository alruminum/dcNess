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
import json
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
                     issue_nums: dict = None,
                     retry_attempt: int = 0,
                     prev_error: str = None) -> tuple:
    """슬래시 직호출 invocation 조립 (#425 follow-up + #431 강화).

    반환: (extra_cli_args, user_prompt)
    - user_prompt = `/dcness:impl <task-path>` — CC 가 슬래시 파싱 후
      commands/impl.md 스킬 본문을 system-reminder 로 자식 세션에 자동 inject
    - extra_cli_args = `--append-system-prompt <mandate + (retry context)>` —
      자식이 system prompt 로 받는 1st-class 의무. commands/impl.md 본문보다
      *우선* (#431 자식이 본문만으론 conveyor + inner 4-step 자율 미호출 사단)

    의무 4 카테고리:
    - 진입 즉시 begin-run 호출 (없으면 `.steps.jsonl` 미작성 → dcness-review --latest
      자식 run 못 찾고 메인 history 무관 run 반환, #431 결함 1+2)
    - inner 4-step 모두 호출 — test-engineer → engineer → code-validator → pr-reviewer.
      test-engineer + engineer 만 호출하고 PASS 박는 false-clean 차단 (#431 결함 3)
    - PR merge 직후 end-run 호출 — Stop hook 안전망 위 1차 명시
    - 종료 prose enum (PASS/FAIL/ESCALATE) 박음 — false-clean fallback 차단
    """
    issue_nums = issue_nums or {}
    task_num = issue_nums.get("task")
    issue_arg = f" --issue-num {task_num}" if task_num else ""

    helper_resolve = (
        'HELPER="$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} '
        '2>/dev/null | sort -V | tail -1)/scripts/dcness-helper"'
    )

    mandate_parts = [
        "## 헤드리스 자식 세션 의무 (MUST — system prompt 1st-class, #431)",
        "",
        "본 세션은 `scripts/impl_loop_headless.py` 가 spawn 한 headless 자식. "
        "commands/impl.md 본문보다 *우선* 적용되는 의무 4 항목:",
        "",
        "### 1. 진입 즉시 conveyor begin-run (필수)",
        "",
        "task 진행 *전* 다음 Bash 명령 1회 실행:",
        "",
        "```bash",
        helper_resolve,
        f'RUN_ID=$("$HELPER" begin-run impl{issue_arg})',
        "```",
        "",
        "누락 시 자식 sid 의 `runs/<rid>/.steps.jsonl` 미작성 → `dcness-review --latest` "
        "가 자식 run 못 찾고 메인 history 의 무관 run 반환 (#431 결함 1+2).",
        "",
        "### 2. inner 4-step 모두 호출 (필수)",
        "",
        "`commands/impl.md` default 시퀀스 = test-engineer → engineer → "
        "**code-validator → pr-reviewer**. 각 sub-agent 호출 전후 `begin-step` / "
        "`end-step` 명시 (loop-procedure.md §3.1).",
        "",
        "test-engineer + engineer 만 호출하고 commit/push/PR 안 만들고 PASS 박는 "
        "false-clean 안티패턴 = 본 자식 spawn 의 핵심 보장 (1 자식 = 1 PR + 1 이슈 close) "
        "을 깨뜨림. headless parent 가 stdout text fragility 검사로 차단 (#431 결함 3).",
        "",
        "### 3. PR merge 직후 conveyor end-run (필수)",
        "",
        "```bash",
        '"$HELPER" end-run',
        "```",
        "",
        "Stop hook 안전망 (`hooks/stop-end-run.sh`) 이 누락 보완하지만 *명시 호출* 우선.",
        "",
        "### 4. 종료 prose enum 박음 (필수)",
        "",
        "- 코드 + 테스트 + commit + push + PR 머지 + `Closes #<task-num>` → "
        "stdout 마지막 줄: `PASS: <한 줄 요약>`",
        "- 빌드/테스트 실패 → `FAIL: <원인>`",
        "- 사용자 협업 필요 / 측정 환경 부재 / blocked → `ESCALATE: <위임 내용>`",
        "",
        "enum 누락 + exit 0 = headless parent 가 false-clean fallback 판정 → "
        "다음 task silent 진행 (#422 NS2 사단).",
    ]
    mandate = "\n".join(mandate_parts)

    if retry_attempt > 0 and prev_error:
        mandate = (
            f"이전 시도 실패 (attempt {retry_attempt}):\n\n{prev_error}\n\n"
            "위 에러 참고하여 수정 후 진행.\n\n---\n\n"
        ) + mandate

    extra_args = ["--append-system-prompt", mandate]
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


def format_progress_event(ev: dict) -> "str | None":
    """stream-json event → 간결한 사람 친화 progress line.

    None 반환 = 해당 event skip (raw line stream noise 회피).
    """
    t = ev.get("type")

    # assistant tool_use → 도구 호출 시작
    if t == "assistant":
        msg = ev.get("message", {}) or {}
        for c in msg.get("content", []) or []:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "tool_use":
                name = c.get("name", "")
                inp = c.get("input", {}) or {}
                if name == "Task":
                    sub = inp.get("subagent_type", "?")
                    desc = (inp.get("description", "") or "")[:50]
                    return f"  ㄴ {sub} — {desc}"
                if name == "Bash":
                    cmd = (inp.get("command", "") or "").splitlines()[0][:80]
                    # conveyor lifecycle 명령만 echo (begin-run / begin-step / end-step / end-run)
                    if any(kw in cmd for kw in (
                        "begin-run", "begin-step", "end-step", "end-run",
                    )):
                        return f"  ㄴ {cmd}"
                    # 그 외 일반 Bash 는 skip (verbose noise)
                    return None
                # 그 외 도구 (Edit/Read/Glob/Grep 등) 는 skip
                return None

    # result → 최종 메시지
    if t == "result":
        res = (ev.get("result", "") or "").strip()
        if res:
            short = res.splitlines()[0][:120]
            return f"  [result] {short}"

    return None


def extract_event_text(ev: dict) -> "str | None":
    """parse_result / 4-step 검사가 사용할 text 추출.

    assistant text + tool_use 의 subagent_type / Bash command 도 함께 누적
    (4-step keyword 매칭 + parse_result enum 매칭 양쪽 대응).
    """
    t = ev.get("type")
    if t == "assistant":
        msg = ev.get("message", {}) or {}
        parts = []
        for c in msg.get("content", []) or []:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "text":
                parts.append(c.get("text", "") or "")
            elif c.get("type") == "tool_use":
                inp = c.get("input", {}) or {}
                if c.get("name") == "Task":
                    sub = inp.get("subagent_type", "")
                    if sub:
                        parts.append(f"[tool_use:Task subagent_type={sub}]")
                elif c.get("name") == "Bash":
                    cmd = (inp.get("command", "") or "").splitlines()[0][:200]
                    parts.append(f"[tool_use:Bash {cmd}]")
        return "\n".join(parts) if parts else None
    if t == "result":
        return ev.get("result", "") or None
    return None


def spawn_child(prompt: str, cwd: str, timeout: int,
                extra_args: list = None,
                stream_to: "io.TextIOBase | None" = None) -> tuple:
    """claude -p 자식 세션 spawn — stream-json 파서 + 간결 progress (#431 follow-up).

    extra_args = `--append-system-prompt <retry_context>` 등 추가 CLI 인자.
    stream_to = 사람 친화 progress line 출력 대상 (default sys.stderr).
                None 박으면 echo skip (capture only).
    반환: (exit_code, aggregated_text, stderr)

    옛 `--output-format text` (raw line stream) → `stream-json --verbose` 로 교체.
    parent 가 각 JSON event 파싱 → Task tool 호출 (sub-agent 진입) + conveyor
    lifecycle Bash 명령 + 최종 result 만 사람 친화 1-line 으로 stream_to emit.
    raw event 노이즈 차단 → CC Bash foreground 진행 중 ⎿ 들여쓰기 자연 표시.

    aggregated_text = parse_result + 4-step 검사용 — assistant text + tool_use
    의 subagent_type / Bash command 누적.
    """
    cmd = [
        "claude", "-p",
        "--dangerously-skip-permissions",
        "--output-format", "stream-json",
        "--verbose",  # stream-json 은 verbose 페어링 필수 (CC CLI 강제)
    ]
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(prompt)

    if stream_to is None:
        stream_to = sys.stderr

    captured_text = []
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

    def _drain_stdout():
        try:
            for line in iter(proc.stdout.readline, ""):
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    # 가끔 non-JSON 줄 (CC 디버그 등) → raw echo + skip
                    if stream_to is not None:
                        stream_to.write(f"  [child:raw] {line}\n")
                        stream_to.flush()
                    continue

                # progress line emit
                if stream_to is not None:
                    progress = format_progress_event(ev)
                    if progress:
                        stream_to.write(progress + "\n")
                        stream_to.flush()

                # text aggregation
                text = extract_event_text(ev)
                if text:
                    captured_text.append(text)
        finally:
            proc.stdout.close()

    def _drain_stderr():
        try:
            for line in iter(proc.stderr.readline, ""):
                captured_stderr.append(line)
                if stream_to is not None:
                    stream_to.write(f"  [child:err] {line}")
                    stream_to.flush()
        finally:
            proc.stderr.close()

    t_out = threading.Thread(target=_drain_stdout, daemon=True)
    t_err = threading.Thread(target=_drain_stderr, daemon=True)
    t_out.start()
    t_err.start()

    try:
        exit_code = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        t_out.join(timeout=2)
        t_err.join(timeout=2)
        return 124, "\n".join(captured_text), "".join(captured_stderr)

    t_out.join(timeout=5)
    t_err.join(timeout=5)
    return exit_code, "\n".join(captured_text), "".join(captured_stderr)


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
            issue_nums=issue_nums,
            retry_attempt=attempt,
            prev_error=prev_error,
        )
        exit_code, stdout, stderr = spawn_child(prompt, cwd, timeout, extra_args=extra_args)
        enum, message = parse_result(stdout, exit_code)
        print(f"[task] result: {enum} — {message}", file=sys.stderr)

        # blocked / escalate 신호 즉시 정지
        if enum in escalate_signals:
            return {"enum": "blocked", "message": message, "stdout": stdout}

        # clean — inner 4-step 호출 trace 검사 (#431 결함 3)
        # default 시퀀스 = test-engineer → engineer → code-validator → pr-reviewer.
        # 자식 stdout 에 후반 2 단계 (code-validator / pr-reviewer) 흔적 부재 시 false-clean.
        # echo 룰 (commands/impl.md / loop-procedure.md §3.1) 따라 sub-agent 결과가
        # `[<task>.<agent>] echo` 또는 agent 이름 prose 로 stdout 에 흐름.
        if enum == "clean":
            stdout_lower = stdout.lower()
            has_validator = "code-validator" in stdout_lower
            has_reviewer = "pr-reviewer" in stdout_lower
            if not (has_validator and has_reviewer):
                missing = []
                if not has_validator:
                    missing.append("code-validator")
                if not has_reviewer:
                    missing.append("pr-reviewer")
                return {
                    "enum": "blocked",
                    "message": (
                        f"prose PASS / exit 0 인데 inner 4-step 부분 호출 흔적 "
                        f"(누락: {', '.join(missing)}) — false-clean 의심 (#431 결함 3, "
                        f"자식이 test-engineer + engineer 만 호출하고 commit/push/PR 안 만들고 종료)"
                    ),
                    "stdout": stdout,
                }

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
