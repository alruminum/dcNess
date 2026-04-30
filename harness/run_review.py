"""run_review.py — dcness conveyor run 사후 분석 (RWHarness review skill 의 dcness 변환).

데이터 소스:
  1. `.sessions/{sid}/runs/{rid}/.steps.jsonl` — step 시퀀스 (agent/mode/enum/must_fix/prose_excerpt/ts)
  2. `.sessions/{sid}/runs/{rid}/<agent>[-<MODE>].md` — 각 step 의 전체 prose
  3. CC session JSONL — run timeframe 내 cost/token (run-level coarse)

산출물:
  - markdown 리포트 (요약 / 호출 흐름 / 단계별 표 / 잘한 점 / 잘못한 점 / 수정 제안)

사용:
    python3 -m harness.run_review --run-id RID
    python3 -m harness.run_review --latest
    python3 -m harness.run_review --list

DCN-CHG-20260430-19.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Reuse existing pricing util.
try:
    from harness.efficiency.analyze_sessions import price_for
except Exception:
    def price_for(_model: str) -> dict:  # type: ignore
        return {"in": 15.0, "out": 75.0, "cw5": 18.75, "cw1h": 30.0, "cr": 1.50}

# ── 상수 ───────────────────────────────────────────────────────────────

EXPECTED_FINAL_ENUMS = {
    "architect": {"MODULE_PLAN": "READY_FOR_IMPL", "SYSTEM_DESIGN": "SYSTEM_DESIGN_READY",
                   "TASK_DECOMPOSE": "READY_FOR_IMPL", "LIGHT_PLAN": "LIGHT_PLAN_READY",
                   "SPEC_GAP": "SPEC_GAP_RESOLVED", "DOCS_SYNC": "DOCS_SYNCED"},
    "test-engineer": {None: "TESTS_WRITTEN"},
    "engineer": {"IMPL": "IMPL_DONE", "POLISH": "POLISH_DONE"},
    "validator": {"CODE_VALIDATION": "PASS", "BUGFIX_VALIDATION": "BUGFIX_PASS",
                   "DESIGN_VALIDATION": "DESIGN_REVIEW_PASS",
                   "PLAN_VALIDATION": "PLAN_VALIDATION_PASS",
                   "UX_VALIDATION": "UX_REVIEW_PASS"},
    "pr-reviewer": {None: "LGTM"},
    "security-reviewer": {None: "SECURE"},
    "qa": {None: None},  # qa 다양 (FUNCTIONAL_BUG / CLEANUP / etc.)
    "plan-reviewer": {None: "PLAN_REVIEW_PASS"},
    "product-planner": {"PRODUCT_PLAN": "PRODUCT_PLAN_READY"},
}

PLACEHOLDER_PATTERNS = [
    r"\[미기록\]", r"\[미결\]", r"M0\s*이후", r"M0\s*에서\s*검증",
    r"NotImplementedError", r"^\s*#\s*TODO\b", r"후보\s*\d+\s*개\s*비교",
]

INFRA_PATH_PATTERNS = [
    "/.claude/harness-state/", "/.claude/harness-logs/",
    "harness-memory.md", "harness.config.json", "/.claude/harness/",
]

READONLY_AGENTS = {"qa", "validator", "pr-reviewer", "security-reviewer",
                    "plan-reviewer", "design-critic"}


# ── 데이터 모델 ────────────────────────────────────────────────────────

@dataclass
class StepRecord:
    idx: int
    ts: str
    agent: str
    mode: Optional[str]
    enum: str
    must_fix: bool
    prose_excerpt: str
    prose_full: str = ""
    elapsed_s: int = 0  # ts diff to next step


@dataclass
class WasteFinding:
    pattern: str
    severity: str  # HIGH / MEDIUM / LOW
    step_idx: int
    agent: str
    detail: str
    fix: str


@dataclass
class GoodFinding:
    pattern: str
    step_idx: int
    agent: str
    detail: str


@dataclass
class RunReport:
    run_id: str
    session_id: str
    run_dir: Path
    steps: list[StepRecord] = field(default_factory=list)
    wastes: list[WasteFinding] = field(default_factory=list)
    goods: list[GoodFinding] = field(default_factory=list)
    total_cost_usd: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    elapsed_s: int = 0
    final_enum: str = ""
    final_clean: bool = False


# ── Run discovery ─────────────────────────────────────────────────────

def list_runs(sessions_root: Path) -> list[Path]:
    """`.sessions/{sid}/runs/{rid}/` 디렉토리 list (mtime 내림차순)."""
    if not sessions_root.exists():
        return []
    runs = []
    for sid_dir in sessions_root.iterdir():
        runs_dir = sid_dir / "runs"
        if not runs_dir.is_dir():
            continue
        for rid_dir in runs_dir.iterdir():
            if (rid_dir / ".steps.jsonl").exists():
                runs.append(rid_dir)
    return sorted(runs, key=lambda p: p.stat().st_mtime, reverse=True)


def find_run_dir(sessions_root: Path, run_id: Optional[str], use_latest: bool) -> Optional[Path]:
    if run_id:
        for rd in list_runs(sessions_root):
            if rd.name == run_id:
                return rd
        return None
    if use_latest:
        runs = list_runs(sessions_root)
        return runs[0] if runs else None
    return None


# ── Step 파싱 ─────────────────────────────────────────────────────────

def _parse_iso(ts: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def parse_steps(run_dir: Path) -> list[StepRecord]:
    steps: list[StepRecord] = []
    jsonl = run_dir / ".steps.jsonl"
    if not jsonl.exists():
        return steps
    raw = []
    for line in jsonl.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            raw.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    for idx, rec in enumerate(raw):
        agent = rec.get("agent", "?")
        mode = rec.get("mode")
        prose_path = run_dir / (f"{agent}-{mode}.md" if mode else f"{agent}.md")
        prose_full = ""
        if prose_path.exists():
            try:
                prose_full = prose_path.read_text(encoding="utf-8")
            except OSError:
                prose_full = ""
        steps.append(StepRecord(
            idx=idx,
            ts=rec.get("ts", ""),
            agent=agent,
            mode=mode,
            enum=rec.get("enum", ""),
            must_fix=bool(rec.get("must_fix")),
            prose_excerpt=rec.get("prose_excerpt", ""),
            prose_full=prose_full,
        ))

    # elapsed 계산 — 다음 step ts 와의 차이
    for i in range(len(steps) - 1):
        a = _parse_iso(steps[i].ts)
        b = _parse_iso(steps[i + 1].ts)
        if a and b:
            steps[i].elapsed_s = int((b - a).total_seconds())
    return steps


# ── Waste 탐지 ────────────────────────────────────────────────────────

def detect_wastes(steps: list[StepRecord]) -> list[WasteFinding]:
    findings: list[WasteFinding] = []

    # RETRY_SAME_FAIL — 연속 동일 FAIL enum
    for i in range(1, len(steps)):
        prev, cur = steps[i - 1], steps[i]
        if prev.agent == cur.agent and prev.enum == cur.enum and prev.enum not in (
            "PASS", "READY_FOR_IMPL", "IMPL_DONE", "TESTS_WRITTEN", "LGTM",
            "SECURE", "DESIGN_REVIEW_PASS", "BUGFIX_PASS", "PLAN_VALIDATION_PASS",
            "UX_REVIEW_PASS", "SYSTEM_DESIGN_READY", "DOCS_SYNCED", "POLISH_DONE",
            "SPEC_GAP_RESOLVED", "LIGHT_PLAN_READY", "PRODUCT_PLAN_READY",
        ):
            findings.append(WasteFinding(
                pattern="RETRY_SAME_FAIL",
                severity="MEDIUM",
                step_idx=i,
                agent=cur.agent,
                detail=f"step {i-1}→{i} 동일 enum 반복: {cur.enum}",
                fix=f"agents/{cur.agent}.md fail 전략 강화 또는 impl 보강",
            ))

    # ECHO_VIOLATION (DCN-30-15) — prose_excerpt 가 너무 짧음
    for s in steps:
        line_count = len([l for l in s.prose_excerpt.splitlines() if l.strip()])
        if line_count < 3 and s.enum != "AMBIGUOUS":
            findings.append(WasteFinding(
                pattern="ECHO_VIOLATION",
                severity="MEDIUM",
                step_idx=s.idx,
                agent=s.agent,
                detail=f"{s.agent} prose 발췌 {line_count}줄 (DCN-30-15 룰 — 5~12줄 의무)",
                fix="agents/{agent}.md / commands/quick.md 가시성 룰 재인용",
            ))

    # PLACEHOLDER_LEAK (DCN-30-18) — Must 직결 placeholder 흔적
    for s in steps:
        for pat in PLACEHOLDER_PATTERNS:
            if re.search(pat, s.prose_full, re.IGNORECASE):
                findings.append(WasteFinding(
                    pattern="PLACEHOLDER_LEAK",
                    severity="HIGH" if s.agent == "architect" else "MEDIUM",
                    step_idx=s.idx,
                    agent=s.agent,
                    detail=f"{s.agent} prose 안 placeholder 발견: `{pat}` (DCN-30-18 — Spike Gate 룰)",
                    fix="agents/architect/system-design.md §Spike Gate 정합 — concrete 구현 + sdk.md 갱신",
                ))
                break

    # MUST_FIX_GHOST — must_fix=true 이후 다음 step 진행
    for i, s in enumerate(steps):
        if s.must_fix and i + 1 < len(steps):
            findings.append(WasteFinding(
                pattern="MUST_FIX_GHOST",
                severity="HIGH",
                step_idx=i,
                agent=s.agent,
                detail=f"step {i} ({s.agent}) MUST_FIX 발견됐는데 step {i+1} 진행 — 멈춤 위반",
                fix="commands/{skill}.md caveat 멈춤 룰 강화",
            ))

    # SPEC_GAP_LOOP — architect SPEC_GAP cycle 한도 초과
    spec_gap_count = sum(1 for s in steps if s.agent == "architect" and s.mode == "SPEC_GAP")
    if spec_gap_count > 2:
        findings.append(WasteFinding(
            pattern="SPEC_GAP_LOOP",
            severity="MEDIUM",
            step_idx=-1,
            agent="architect",
            detail=f"architect SPEC_GAP {spec_gap_count}회 — cycle 한도 2 초과",
            fix="impl batch 자체 보강 또는 product-planner escalate",
        ))

    # INFRA_READ — prose 안 인프라 경로 흔적
    for s in steps:
        for path in INFRA_PATH_PATTERNS:
            if path in s.prose_full:
                findings.append(WasteFinding(
                    pattern="INFRA_READ",
                    severity="HIGH",
                    step_idx=s.idx,
                    agent=s.agent,
                    detail=f"{s.agent} prose 안 인프라 경로 흔적: `{path}`",
                    fix=f"agents/{s.agent}.md 권한 경계 인프라 탐색 금지 강화",
                ))
                break

    # READONLY_BASH — read-only agent 가 Bash 호출 흔적
    for s in steps:
        if s.agent in READONLY_AGENTS and re.search(r"`bash`|Bash tool|```bash", s.prose_full):
            findings.append(WasteFinding(
                pattern="READONLY_BASH",
                severity="HIGH",
                step_idx=s.idx,
                agent=s.agent,
                detail=f"{s.agent} (read-only) prose 안 Bash 흔적",
                fix=f"agents/{s.agent}.md Bash 사용 금지 명시 강화",
            ))

    # EXTERNAL_VERIFIED_MISSING (DCN-30-18) — plan-reviewer prose 에 EXTERNAL_VERIFIED 섹션 부재
    for s in steps:
        if s.agent == "plan-reviewer" and "EXTERNAL_VERIFIED" not in s.prose_full:
            findings.append(WasteFinding(
                pattern="EXTERNAL_VERIFIED_MISSING",
                severity="HIGH",
                step_idx=s.idx,
                agent=s.agent,
                detail="plan-reviewer prose 에 EXTERNAL_VERIFIED 섹션 부재 (DCN-30-18 산출물 의무)",
                fix="agents/plan-reviewer.md §산출물 EXTERNAL_VERIFIED 섹션 의무 재강조",
            ))

    return findings


# ── Good 탐지 ─────────────────────────────────────────────────────────

def detect_goods(steps: list[StepRecord]) -> list[GoodFinding]:
    goods: list[GoodFinding] = []

    # ENUM_CLEAN — 각 step 의 enum 이 expected 정합
    for s in steps:
        expected_map = EXPECTED_FINAL_ENUMS.get(s.agent, {})
        expected = expected_map.get(s.mode) or expected_map.get(None)
        if expected and s.enum == expected and not s.must_fix:
            goods.append(GoodFinding(
                pattern="ENUM_CLEAN",
                step_idx=s.idx,
                agent=s.agent,
                detail=f"{s.agent} enum={s.enum} (expected 정합)",
            ))

    # PROSE_ECHO_OK — prose_excerpt 5~12줄 + must_fix=False
    for s in steps:
        line_count = len([l for l in s.prose_excerpt.splitlines() if l.strip()])
        if 5 <= line_count <= 12:
            goods.append(GoodFinding(
                pattern="PROSE_ECHO_OK",
                step_idx=s.idx,
                agent=s.agent,
                detail=f"{s.agent} prose_excerpt {line_count}줄 (DCN-30-15 룰 정합)",
            ))

    # DDD_PHASE_A — architect SYSTEM_DESIGN prose 안 Domain Model 섹션 존재
    for s in steps:
        if s.agent == "architect" and s.mode == "SYSTEM_DESIGN":
            if re.search(r"##\s*Domain\s*Model|##\s*도메인\s*모델|Phase\s*A", s.prose_full, re.IGNORECASE):
                goods.append(GoodFinding(
                    pattern="DDD_PHASE_A",
                    step_idx=s.idx,
                    agent=s.agent,
                    detail="architect SYSTEM_DESIGN prose 에 Domain Model Phase A 섹션 존재 (DCN-30-16 룰 정합)",
                ))

    # DEPENDENCY_CAUSAL — system-design prose 의존성에 인과관계 표기
    for s in steps:
        if s.agent == "architect" and s.mode == "SYSTEM_DESIGN":
            if re.search(r"→.*\(.*(필요|의존|구독|입력)", s.prose_full):
                goods.append(GoodFinding(
                    pattern="DEPENDENCY_CAUSAL",
                    step_idx=s.idx,
                    agent=s.agent,
                    detail="architect prose 의존성 화살표에 인과관계 1줄 (DCN-30-16 룰 정합)",
                ))

    # EXTERNAL_VERIFIED_PRESENT — plan-reviewer 산출물 의무 충족
    for s in steps:
        if s.agent == "plan-reviewer" and "EXTERNAL_VERIFIED" in s.prose_full:
            goods.append(GoodFinding(
                pattern="EXTERNAL_VERIFIED_PRESENT",
                step_idx=s.idx,
                agent=s.agent,
                detail="plan-reviewer EXTERNAL_VERIFIED 섹션 존재 (DCN-30-18 룰 정합)",
            ))

    return goods


# ── Cost cross-correlation (run-level coarse) ────────────────────────

def encode_repo_path_dcness(repo_path: str) -> str:
    """CC project dir 인코딩 룰 — `/` 와 `.` 모두 `-` 로 (DCN-30-08 fix 정합)."""
    return repo_path.replace("/", "-").replace(".", "-")


def find_session_jsonls(repo_path: Path) -> list[Path]:
    encoded = encode_repo_path_dcness(str(repo_path))
    base = Path.home() / ".claude" / "projects" / encoded
    if not base.exists():
        return []
    return list(base.glob("*.jsonl"))


def compute_run_cost(run_dir: Path, repo_path: Path) -> tuple[float, int, int]:
    """Run timeframe 내 assistant turn 의 cost/input/output 합산. Coarse — Agent 별 분리 X."""
    steps_file = run_dir / ".steps.jsonl"
    if not steps_file.exists():
        return (0.0, 0, 0)

    raw = []
    for line in steps_file.read_text(encoding="utf-8").splitlines():
        try:
            raw.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not raw:
        return (0.0, 0, 0)

    first_ts = _parse_iso(raw[0].get("ts", ""))
    last_ts = _parse_iso(raw[-1].get("ts", ""))
    if not first_ts or not last_ts:
        return (0.0, 0, 0)

    total_cost = 0.0
    total_in = 0
    total_out = 0

    for jsonl in find_session_jsonls(repo_path):
        try:
            for line in jsonl.read_text(encoding="utf-8").splitlines():
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = rec.get("timestamp", "")
                rec_ts = _parse_iso(ts)
                if not rec_ts:
                    continue
                if rec_ts < first_ts or rec_ts > last_ts:
                    continue
                if rec.get("type") != "assistant":
                    continue
                msg = rec.get("message", {})
                model = msg.get("model", "") or ""
                usage = msg.get("usage", {}) or {}
                price = price_for(model)
                inp = usage.get("input_tokens", 0)
                out = usage.get("output_tokens", 0)
                cw = usage.get("cache_creation_input_tokens", 0)
                cr = usage.get("cache_read_input_tokens", 0)
                total_cost += (
                    inp * price["in"] / 1e6 + out * price["out"] / 1e6
                    + cw * price["cw5"] / 1e6 + cr * price["cr"] / 1e6
                )
                total_in += inp + cw + cr
                total_out += out
        except OSError:
            continue

    return (total_cost, total_in, total_out)


# ── Report 생성 ───────────────────────────────────────────────────────

def render_report(report: RunReport) -> str:
    lines = []
    lines.append(f"# Run Review: {report.run_id}")
    lines.append("")
    lines.append("## 요약")
    lines.append("| 항목 | 값 |")
    lines.append("|---|---|")
    lines.append(f"| run_id | `{report.run_id}` |")
    lines.append(f"| session_id | `{report.session_id}` |")
    lines.append(f"| step 수 | {len(report.steps)} |")
    lines.append(f"| 소요 | {report.elapsed_s}s |")
    lines.append(f"| 비용 (run window 내) | ${report.total_cost_usd:.4f} |")
    lines.append(f"| input tokens | {report.total_input_tokens:,} |")
    lines.append(f"| output tokens | {report.total_output_tokens:,} |")
    lines.append(f"| 최종 enum | `{report.final_enum}` |")
    lines.append(f"| clean 판정 | {'✅' if report.final_clean else '❌'} |")
    lines.append("")

    # 호출 흐름
    lines.append("## 호출 흐름")
    lines.append("```")
    for i, s in enumerate(report.steps):
        marker = "└─" if i == len(report.steps) - 1 else "├─"
        mode_str = f" [{s.mode}]" if s.mode else ""
        flag = " ⚠️" if s.must_fix else ""
        lines.append(f"{marker} {s.agent}{mode_str} ({s.elapsed_s}s) → {s.enum}{flag}")
    lines.append("```")
    lines.append("")

    # 단계별 표
    lines.append("## 단계별 상세")
    lines.append("| # | agent | mode | elapsed(s) | enum | must_fix | prose 줄 |")
    lines.append("|---|---|---|---|---|---|---|")
    for s in report.steps:
        line_count = len([l for l in s.prose_excerpt.splitlines() if l.strip()])
        lines.append(
            f"| {s.idx} | {s.agent} | {s.mode or '-'} | {s.elapsed_s} | "
            f"`{s.enum}` | {'⚠️' if s.must_fix else ''} | {line_count} |"
        )
    lines.append("")

    # 잘한 점
    if report.goods:
        lines.append("## 잘한 점 (Good Findings)")
        lines.append("| # | 패턴 | step | agent | 상세 |")
        lines.append("|---|---|---|---|---|")
        for i, g in enumerate(report.goods, 1):
            lines.append(f"| {i} | `{g.pattern}` | {g.step_idx} | {g.agent} | {g.detail} |")
        lines.append("")
    else:
        lines.append("## 잘한 점 — 없음")
        lines.append("")

    # 잘못한 점
    if report.wastes:
        lines.append("## 잘못한 점 (Waste Findings)")
        lines.append("| # | 심각도 | 패턴 | step | agent | 상세 | 수정 |")
        lines.append("|---|---|---|---|---|---|---|")
        sev_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        for i, w in enumerate(sorted(report.wastes, key=lambda x: sev_order.get(x.severity, 9)), 1):
            lines.append(
                f"| {i} | {w.severity} | `{w.pattern}` | {w.step_idx} | {w.agent} "
                f"| {w.detail} | {w.fix} |"
            )
        lines.append("")
    else:
        lines.append("## 잘못한 점 — 없음 ✅")
        lines.append("")

    return "\n".join(lines)


# ── 실행 ──────────────────────────────────────────────────────────────

def build_report(run_dir: Path, repo_path: Path) -> RunReport:
    steps = parse_steps(run_dir)
    wastes = detect_wastes(steps)
    goods = detect_goods(steps)
    cost, in_tok, out_tok = compute_run_cost(run_dir, repo_path)

    elapsed = 0
    if len(steps) >= 2:
        a = _parse_iso(steps[0].ts)
        b = _parse_iso(steps[-1].ts)
        if a and b:
            elapsed = int((b - a).total_seconds())

    final_enum = steps[-1].enum if steps else ""
    has_must_fix = any(s.must_fix for s in steps)
    has_ambiguous = any(s.enum == "AMBIGUOUS" for s in steps)
    final_clean = (final_enum and not has_must_fix and not has_ambiguous
                   and len([w for w in wastes if w.severity == "HIGH"]) == 0)

    sid = run_dir.parent.parent.name
    return RunReport(
        run_id=run_dir.name,
        session_id=sid,
        run_dir=run_dir,
        steps=steps,
        wastes=wastes,
        goods=goods,
        total_cost_usd=cost,
        total_input_tokens=in_tok,
        total_output_tokens=out_tok,
        elapsed_s=elapsed,
        final_enum=final_enum,
        final_clean=final_clean,
    )


def _detect_sessions_root(cwd: Path) -> Optional[Path]:
    """`.claude/harness-state/.sessions/` 위치 자동 탐지 (현재 dir + .git common parent)."""
    cur = cwd / ".claude" / "harness-state" / ".sessions"
    if cur.exists():
        return cur
    # worktree fallback — git common-dir
    try:
        import subprocess
        r = subprocess.run(["git", "rev-parse", "--git-common-dir"],
                            cwd=str(cwd), capture_output=True, text=True, check=False)
        if r.returncode == 0:
            common = Path(r.stdout.strip())
            cand = common.parent / ".claude" / "harness-state" / ".sessions"
            if cand.exists():
                return cand
    except Exception:
        pass
    return None


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="dcness-run-review", description="dcness run 사후 분석")
    p.add_argument("--run-id", help="명시 run_id")
    p.add_argument("--latest", action="store_true", help="최신 run 분석")
    p.add_argument("--list", action="store_true", help="run list 만 출력")
    p.add_argument("--repo", default=".", help="저장소 cwd (default: cwd)")
    p.add_argument("--limit", type=int, default=10, help="--list 시 최대 개수")
    args = p.parse_args(argv)

    repo_path = Path(args.repo).resolve()
    sessions_root = _detect_sessions_root(repo_path)
    if not sessions_root:
        print("[run-review] sessions root 미탐지 — `.claude/harness-state/.sessions/` 부재", file=sys.stderr)
        return 2

    if args.list:
        runs = list_runs(sessions_root)[:args.limit]
        if not runs:
            print("[run-review] runs 없음")
            return 0
        for i, r in enumerate(runs, 1):
            mtime = datetime.fromtimestamp(r.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            print(f"{i}. {r.name}  (sid={r.parent.parent.name}, mtime={mtime})")
        return 0

    run_dir = find_run_dir(sessions_root, args.run_id, args.latest or not args.run_id)
    if not run_dir:
        print(f"[run-review] run_dir 미탐지 (run_id={args.run_id})", file=sys.stderr)
        return 2

    report = build_report(run_dir, repo_path)
    print(render_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
