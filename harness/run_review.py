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

# DCN-CHG-20260501-10: must_fix retroactive recompute.
# .steps.jsonl 의 must_fix 는 *기록 시점* helper regex 산출물 — DCN-CHG-20260501-09
# 이전 데이터는 단순 단어경계 매칭의 false positive 포함. parser 가 prose_full 보유 시
# 신규 negation-aware regex 로 재계산. prose_full 부재 시 jsonl fallback.
try:
    from harness.session_state import _has_positive_must_fix
except Exception:
    def _has_positive_must_fix(_prose: str) -> bool:  # type: ignore
        return False

# ── 상수 ───────────────────────────────────────────────────────────────

EXPECTED_FINAL_ENUMS = {
    "architect": {"MODULE_PLAN": "READY_FOR_IMPL", "SYSTEM_DESIGN": "SYSTEM_DESIGN_READY",
                   "TASK_DECOMPOSE": "READY_FOR_IMPL", "LIGHT_PLAN": "LIGHT_PLAN_READY",
                   "SPEC_GAP": "SPEC_GAP_RESOLVED", "DOCS_SYNC": "DOCS_SYNCED"},
    "test-engineer": {None: "TESTS_WRITTEN"},
    "engineer": {"IMPL": "IMPL_DONE", "POLISH": "POLISH_DONE"},
    "code-validator": {None: "PASS"},
    "architecture-validator": {None: "PASS"},
    "pr-reviewer": {None: "LGTM"},
    "qa": {None: None},  # qa 다양 (FUNCTIONAL_BUG / CLEANUP / etc.)
    "plan-reviewer": {None: "PLAN_REVIEW_PASS"},
}

PLACEHOLDER_PATTERNS = [
    r"\[미기록\]", r"\[미결\]", r"M0\s*이후", r"M0\s*에서\s*검증",
    r"NotImplementedError", r"^\s*#\s*TODO\b", r"후보\s*\d+\s*개\s*비교",
]

# 이슈 #321 C STRAY_DIR_LEAK — known infra dir 와 fuzzy match (typo 의심)
# 예: `.claire` (실측 jajang run-dbd49faf task 1/2/3 사례) → `.claude` 의 typo
KNOWN_INFRA_DIR_NAMES = [".claude", ".git", ".github"]

INFRA_PATH_PATTERNS = [
    "/.claude/harness-state/", "/.claude/harness-logs/",
    "harness-memory.md", "harness.config.json", "/.claude/harness/",
]

READONLY_AGENTS = {"qa", "code-validator", "architecture-validator", "pr-reviewer",
                    "plan-reviewer"}

# DCN-CHG-20260430-20: Phase 2 — per-Agent budget for THINKING_LOOP detection.
# elapsed_s: 정상 sub-agent 한 번 호출 한도 (초).
# min_output_tokens: 정상 sub-agent 가 emit 할 최소 output token (이하 = stall 의심).
EXPECTED_AGENT_BUDGETS: dict[str, dict[str, int]] = {
    "architect":       {"elapsed_s": 600, "min_output_tokens": 1500},
    "engineer":        {"elapsed_s": 900, "min_output_tokens": 2000},
    "test-engineer":   {"elapsed_s": 600, "min_output_tokens": 1500},
    "code-validator":  {"elapsed_s": 300, "min_output_tokens": 800},
    "architecture-validator": {"elapsed_s": 300, "min_output_tokens": 800},
    "pr-reviewer":     {"elapsed_s": 180, "min_output_tokens": 600},
    "qa":              {"elapsed_s": 300, "min_output_tokens": 600},
    "plan-reviewer":   {"elapsed_s": 300, "min_output_tokens": 1000},
    "designer":        {"elapsed_s": 600, "min_output_tokens": 1000},
    "ux-architect":    {"elapsed_s": 600, "min_output_tokens": 1000},
}

DCNESS_AGENT_NAMES = set(EXPECTED_AGENT_BUDGETS.keys())

# DCN-CHG-20260430-38: engineer self-verify echo anchor 옵션 (DCN-30-34 강제 → DCN-30-38 자율화).
# prose 끝에 *어느 한 anchor* 라도 있으면 통과. 형식 자율 + substance 의무.
# heading 라인에 검증 / verification / self-verify 단어가 *포함* 되면 매칭 (issue #249 — `## 수용 기준 검증` 같은 변형 허용).
SELF_VERIFY_ANCHORS = [
    r"^\s*#{1,6}[^\n]*검증",
    r"^\s*#{1,6}[^\n]*verification",
    r"^\s*#{1,6}[^\n]*self[-\s]?verify",
]


def _has_self_verify_anchor(prose: str) -> bool:
    """engineer prose 에 self-verify anchor 중 하나라도 있는지 (DCN-30-38)."""
    if not prose:
        return False
    for pat in SELF_VERIFY_ANCHORS:
        if re.search(pat, prose, re.MULTILINE | re.IGNORECASE):
            return True
    return False


def _detect_stray_infra_dirs(prose: str) -> list[tuple[str, str, float]]:
    """이슈 #321 C STRAY_DIR_LEAK — `.claude` / `.git` / `.github` 와 typo 의심 디렉토리.

    prose 안 `.<word>(/|\\b)` 매치 + KNOWN_INFRA_DIR_NAMES 와 difflib similarity ≥ 0.78
    이지만 정확 매치 아닌 후보 → typo 의심.

    Returns list of (typo_name, intended_name, similarity_ratio).
    """
    if not prose:
        return []
    import difflib  # 표준 라이브러리. 모듈 top import 와 분리 (사용 시점 import 비용 무시).
    # 4~10 문자 word — `.claude` (7자) / `.git` (4자) / `.github` (7자) 모두 커버
    candidates = re.findall(r'(?<![./\w])\.([a-zA-Z][a-zA-Z0-9_-]{3,9})(?=[/\s\b]|$)', prose)
    leaks: list[tuple[str, str, float]] = []
    seen = set()
    for cand in candidates:
        full = "." + cand
        full_lower = full.lower()
        if full_lower in {n.lower() for n in KNOWN_INFRA_DIR_NAMES}:
            continue
        if full_lower in seen:
            continue
        seen.add(full_lower)
        for known in KNOWN_INFRA_DIR_NAMES:
            ratio = difflib.SequenceMatcher(None, full_lower, known).ratio()
            # 0.70 = .claire/.claude 케이스 (실측 0.714) 커버, .vscode/.cargo/.cache
            # 등 false positive 0건 (실측 모두 0.57 이하)
            if ratio >= 0.70:
                leaks.append((full, known, ratio))
                break
    return leaks


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
    # DCN-CHG-20260430-20: per-Agent metrics from CC session JSONL toolUseResult.
    duration_ms: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    matched_invocation: bool = False
    # DCN-CHG-20260430-37: tool_use_count — TOOL_USE_OVERFLOW 검출 + DCN-30-36 hint 짝.
    tool_use_count: int = 0


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
        # .steps.jsonl 없는 run 도 직접 탐색 (prose staging 실패 등 부분 완료 run)
        for sid_dir in sessions_root.iterdir():
            runs_dir = sid_dir / "runs"
            if not runs_dir.is_dir():
                continue
            cand = runs_dir / run_id
            if cand.is_dir():
                return cand
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
        prose_full = ""

        # prose_file: end-step 이 기록한 절대 경로 → 직접 읽기
        prose_file = rec.get("prose_file")
        if prose_file:
            p = Path(prose_file)
            if p.exists():
                try:
                    prose_full = p.read_text(encoding="utf-8")
                except OSError:
                    pass

        # legacy fallback: prose_file 없는 옛 records → outer <agent>[-mode].md
        if not prose_full:
            suffix = f"{agent}-{mode}.md" if mode else f"{agent}.md"
            legacy = run_dir / suffix
            if legacy.exists():
                try:
                    prose_full = legacy.read_text(encoding="utf-8")
                except OSError:
                    pass

        if prose_full:
            must_fix = _has_positive_must_fix(prose_full)
        else:
            must_fix = bool(rec.get("must_fix"))

        steps.append(StepRecord(
            idx=idx,
            ts=rec.get("ts", ""),
            agent=agent,
            mode=mode,
            enum=rec.get("enum", ""),
            must_fix=must_fix,
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

def _scan_main_sed_misdiagnosis(
    repo_path: Optional[Path],
    window: Optional[tuple],
) -> list[str]:
    """CC session JSONL within run window 에서 메인 self-correction 패턴 검출
    (DCN-CHG-20260430-37). I5 회귀 추적 — "정정 — 변경 0" / "잘못 진단" 등.

    return: 매칭된 assistant text excerpt list (최대 3).
    """
    if not repo_path or not window:
        return []
    first_ts, last_ts = window
    keyword_filter = ["정정", "잘못 진단", "실측 시", "misdiagnosis", "변경사항 0"]
    patterns = [
        r"정정[^\n]{0,80}(0개|0\s*변경|실제\s*0|변경사항\s*0)",
        r"sed[^\n]{0,80}변경[^\n]{0,20}0",
        r"실측\s*시\s*0",
        r"잘못\s*진단",
        r"misdiagnosis",
    ]
    hits: list[str] = []
    try:
        for jsonl in find_session_jsonls(repo_path):
            try:
                lines = jsonl.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            for line in lines:
                if not any(kw in line for kw in keyword_filter):
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("type") != "assistant":
                    continue
                ts = _parse_iso(rec.get("timestamp", ""))
                if not ts:
                    continue
                ts_naive = ts.replace(tzinfo=None)
                if ts_naive < first_ts.replace(tzinfo=None) or ts_naive > last_ts.replace(tzinfo=None):
                    continue
                content = rec.get("message", {}).get("content", [])
                matched = False
                for blk in content:
                    if blk.get("type") != "text":
                        continue
                    text = blk.get("text", "")
                    for pat in patterns:
                        if re.search(pat, text):
                            hits.append(text[:300].replace("\n", " "))
                            matched = True
                            break
                    if matched:
                        break
                if len(hits) >= 3:
                    return hits
    except Exception:
        pass
    return hits


def detect_wastes(
    steps: list[StepRecord],
    invocations: Optional[list[dict]] = None,
    repo_path: Optional[Path] = None,
    window: Optional[tuple] = None,
) -> list[WasteFinding]:
    findings: list[WasteFinding] = []

    # RETRY_SAME_FAIL — 연속 동일 FAIL enum
    # 이슈 #302 #1: prose-only mode (#284) 정착 후 PROSE_LOGGED 가 표준 advance enum.
    # 또한 같은 (agent, mode) 가 N task 순회 정상 호출 (예: architect MODULE_PLAN × 4)
    # 시 동일 enum 반복은 *retry 가 아닌 정상 호출* — prose 내용이 다르면 다른 step.
    ADVANCE_ENUMS = {
        "PASS", "READY_FOR_IMPL", "IMPL_DONE", "TESTS_WRITTEN", "LGTM",
        "SECURE", "SYSTEM_DESIGN_READY", "DOCS_SYNCED", "POLISH_DONE",
        "SPEC_GAP_RESOLVED", "LIGHT_PLAN_READY", "PRODUCT_PLAN_READY",
        "PLAN_REVIEW_PASS", "UX_FLOW_READY",
        "PROSE_LOGGED",  # #284 prose-only mode default sentinel — 정상 종료
    }
    for i in range(1, len(steps)):
        prev, cur = steps[i - 1], steps[i]
        if prev.agent != cur.agent or prev.enum != cur.enum:
            continue
        if prev.enum in ADVANCE_ENUMS:
            continue
        # prose 내용이 *다르면* 같은 enum 이라도 다른 invocation (N task 순회 등)
        # — retry 아님. prose_excerpt 가 동일할 때만 진짜 retry 후보.
        prev_prose = prev.prose_full or prev.prose_excerpt
        cur_prose = cur.prose_full or cur.prose_excerpt
        if prev_prose and cur_prose and prev_prose != cur_prose:
            continue
        findings.append(WasteFinding(
            pattern="RETRY_SAME_FAIL",
            severity="MEDIUM",
            step_idx=i,
            agent=cur.agent,
            detail=f"step {i-1}→{i} 동일 enum 반복: {cur.enum}",
            fix=f"agents/{cur.agent}.md fail 전략 강화 또는 impl 보강",
        ))

    # ECHO_VIOLATION — prose 전체 줄 수 기준 (prose_full). prose_full 없는 레코드는 skip.
    for s in steps:
        if not s.prose_full:
            continue
        line_count = len([l for l in s.prose_full.splitlines() if l.strip()])
        if line_count < 5 and s.enum != "AMBIGUOUS":
            findings.append(WasteFinding(
                pattern="ECHO_VIOLATION",
                severity="MEDIUM",
                step_idx=s.idx,
                agent=s.agent,
                detail=f"{s.agent} prose {line_count}줄 (5줄 미만 — 충분한 분석 필요)",
                fix=f"agents/{s.agent}.md 가시성 룰 강화 또는 prose 내용 보강",
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

    # STRAY_DIR_LEAK — `.claude` 와 typo 의심 디렉토리 흔적 (#321 C)
    # 실측: jajang run-dbd49faf task 1/2/3 `.claire` 3 회 연속.
    for s in steps:
        if not s.prose_full:
            continue
        for typo, intended, ratio in _detect_stray_infra_dirs(s.prose_full):
            findings.append(WasteFinding(
                pattern="STRAY_DIR_LEAK",
                severity="MEDIUM",
                step_idx=s.idx,
                agent=s.agent,
                detail=f"{s.agent} prose 안 `{typo}/` 흔적 — `{intended}/` typo 의심 (similarity {ratio:.2f})",
                fix=f"agents/{s.agent}.md 디렉토리명 정확 인지 룰 보강 또는 사용자 환경 검증",
            ))

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

    # THINKING_LOOP (DCN-30-20) — sub-agent 가 오래 돌았는데 output token 적음 = stall / thinking 무한 loop
    # 사용자 사례 (jajang product-planner): 6분 elapsed + ↓624 tokens.
    for s in steps:
        if not s.matched_invocation:
            continue
        budget = EXPECTED_AGENT_BUDGETS.get(s.agent)
        if not budget:
            continue
        duration_s = s.duration_ms / 1000 if s.duration_ms else 0
        out_tok = s.output_tokens
        # 조건 — duration 이 expected × 1.5 초과 AND output token 이 기대치 30% 미만
        # OR duration > 5분 + output < 1k (절대 한도)
        thinking_loop = False
        reason = ""
        if duration_s > budget["elapsed_s"] * 1.5 and out_tok < budget["min_output_tokens"] * 0.3:
            thinking_loop = True
            reason = (f"duration {duration_s:.0f}s > budget {budget['elapsed_s']}s × 1.5 + "
                      f"output {out_tok} < min {budget['min_output_tokens']} × 0.3")
        elif duration_s > 300 and out_tok < 1000:
            thinking_loop = True
            reason = f"duration {duration_s:.0f}s > 300s + output {out_tok} < 1000"
        if thinking_loop:
            findings.append(WasteFinding(
                pattern="THINKING_LOOP",
                severity="HIGH",
                step_idx=s.idx,
                agent=s.agent,
                detail=f"{s.agent} stall 의심 — {reason}",
                fix=(f"agents/{s.agent}.md 'thinking 본문 드래프트 금지' 룰 ⚠️ CRITICAL banner 격상 + "
                      "Agent description 에 'extended thinking 의사결정 분기만, prose 즉시 emit' 추가"),
            ))

    # TOOL_USE_OVERFLOW (DCN-CHG-20260430-37) — step 의 tool_use_count ≥ 100.
    # 자장 epic-08/09 실측 — 102/119/153/170/223 모두 PR PARTIAL 회귀.
    # DCN-30-36 hint 와 짝 — 사후 측정.
    for s in steps:
        if not s.matched_invocation or s.tool_use_count < 100:
            continue
        findings.append(WasteFinding(
            pattern="TOOL_USE_OVERFLOW",
            severity="HIGH",
            step_idx=s.idx,
            agent=s.agent,
            detail=f"{s.agent} step {s.idx} tool_use_count={s.tool_use_count} (≥ 100). "
                   f"context overflow / IMPL_PARTIAL 회귀 위험 (자장 실측 임계).",
            fix="DCN-30-36 prior count hint 활용 + agent prompt 분할 자율 판단 강화. "
                "임계 ≥ 100 = 자장 실측 5건 모두 PR PARTIAL.",
        ))

    # PARTIAL_LOOP (DCN-CHG-20260430-37) — IMPL_PARTIAL ≥ 3 in same run.
    # 자장 패턴 "overflow → PARTIAL → 추가 epic → 또 overflow → 무한 반복".
    partial_count = sum(1 for s in steps if s.enum == "IMPL_PARTIAL")
    if partial_count >= 3:
        findings.append(WasteFinding(
            pattern="PARTIAL_LOOP",
            severity="HIGH",
            step_idx=-1,
            agent="engineer",
            detail=f"IMPL_PARTIAL {partial_count}회 — 같은 run 무한 분할 의심.",
            fix="task 자체 split 필요 (epic 단위 재계획). architect TASK_DECOMPOSE 재진입 또는 "
                "사용자 위임. DCN-30-34 권고 cycle ≤ 3 정합.",
        ))

    # END_STEP_SKIP (DCN-CHG-20260430-37) — sub-agent invocation > .steps.jsonl row.
    # 메인 distract → end-step 호출 skip → .steps.jsonl 누락. DCN-30-25 STEP COUNT WARN /
    # DCN-30-33 STALE STEP WARN 의 사후 측정 보완.
    if invocations:
        from collections import Counter
        inv_count_per_agent = Counter(i["agent"] for i in invocations)
        step_count_per_agent = Counter(s.agent for s in steps)
        for agent_name, inv_n in inv_count_per_agent.items():
            step_n = step_count_per_agent.get(agent_name, 0)
            # margin 1 — sub-agent self-recurse 등 false positive 회피.
            if inv_n > step_n + 1:
                findings.append(WasteFinding(
                    pattern="END_STEP_SKIP",
                    severity="HIGH",
                    step_idx=-1,
                    agent=agent_name,
                    detail=f"{agent_name} invocations={inv_n} > steps={step_n} "
                           f"(diff={inv_n-step_n}) — end-step 호출 누락 의심.",
                    fix="commands/<skill>.md begin/end-step 1:1 의무 (DCN-30-25 / DCN-30-33). "
                        "메인 distract 회피 — Agent 직후 즉시 end-step.",
                ))

    # MISSING_SELF_VERIFY (DCN-CHG-20260430-38) — engineer prose 에 self-verify anchor 부재.
    # DCN-30-34 의무 (anchor 자율, substance 의무) 회귀 검출. prose_full 부재 시 skip.
    # POLISH_DONE 은 제외 (#252) — POLISH 결과 prose 는 짧은 정리 보고 (테스트 N passed 본문 서술)
    # 자체가 검증 substance. heading anchor 강제는 잉여 형식 + 회귀 false positive.
    for s in steps:
        if s.agent != "engineer":
            continue
        if s.enum not in ("IMPL_DONE", "IMPL_PARTIAL"):
            continue
        if not s.prose_full:
            continue
        if not _has_self_verify_anchor(s.prose_full):
            findings.append(WasteFinding(
                pattern="MISSING_SELF_VERIFY",
                severity="MEDIUM",
                step_idx=s.idx,
                agent="engineer",
                detail=f"engineer step {s.idx} ({s.enum}) prose 에 자가 검증 anchor 부재 — "
                       f"DCN-30-34 의무 (anchor 자율: `## 자가 검증` / `## Verification` / "
                       f"`## 검증` / `## 수용 기준 검증` / `## Self-Verify` 등 — heading 에 "
                       f"검증/verification/self-verify 단어 포함하면 OK).",
                fix="agents/engineer.md § 자가 검증 echo 의무 — prose 끝에 anchor 추가 + "
                    "실측 명령 + 결과 수치 인용. substance (검증 결과) 만 의무.",
            ))

    # MAIN_SED_MISDIAGNOSIS (DCN-CHG-20260430-37) — 메인 self-correction 패턴.
    # I5 회귀 — "130개 fix" → 실측 0개 → 정정. CC JSONL 텍스트 검출.
    sed_hits = _scan_main_sed_misdiagnosis(repo_path, window)
    if sed_hits:
        findings.append(WasteFinding(
            pattern="MAIN_SED_MISDIAGNOSIS",
            severity="HIGH",
            step_idx=-1,
            agent="main",
            detail=f"메인 self-correction 패턴 {len(sed_hits)}회 — 추측 진단 → 사용자 알림 → "
                   f"실측 시 0 발견 → 정정. 첫 발췌: {sed_hits[0][:120]}...",
            fix="dcness-rules.md §10 self-verify 원칙 — Bash sed/awk 후 "
                "*전·후* 실측 의무 (git diff --stat / 결과 grep). 글로벌 ~/.claude/CLAUDE.md "
                "제1룰 정합.",
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

    # PROSE_ECHO_OK — prose 충분 (5줄 이상)
    for s in steps:
        check_text = s.prose_full or s.prose_excerpt
        line_count = len([l for l in check_text.splitlines() if l.strip()])
        if line_count >= 5:
            goods.append(GoodFinding(
                pattern="PROSE_ECHO_OK",
                step_idx=s.idx,
                agent=s.agent,
                detail=f"{s.agent} prose {line_count}줄 (충분한 분석 포함)",
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


# ── Per-Agent invocation extraction (DCN-CHG-20260430-20, Phase 2) ────


def _normalize_agent_type(agent_type: Optional[str]) -> Optional[str]:
    """`dcness:architect:system-design` → `architect`. None / 비-dcness → 원형 그대로."""
    if not agent_type:
        return None
    if agent_type.startswith("dcness:"):
        parts = agent_type.split(":")
        return parts[1] if len(parts) > 1 else agent_type
    return agent_type


def _compute_invocation_cost(model: str, usage: dict) -> float:
    """toolUseResult.usage 의 token breakdown 으로 USD 계산. price_for util 재사용."""
    if not usage:
        return 0.0
    price = price_for(model)
    inp = usage.get("input_tokens", 0)
    out = usage.get("output_tokens", 0)
    cw = usage.get("cache_creation_input_tokens", 0)
    cr = usage.get("cache_read_input_tokens", 0)
    cw_detail = usage.get("cache_creation", {}) or {}
    cw5 = cw_detail.get("ephemeral_5m_input_tokens", 0)
    cw1h = cw_detail.get("ephemeral_1h_input_tokens", 0)
    if cw5 + cw1h == 0 and cw > 0:
        cw5 = cw
    return (
        inp * price["in"] / 1e6
        + out * price["out"] / 1e6
        + cw5 * price["cw5"] / 1e6
        + cw1h * price["cw1h"] / 1e6
        + cr * price["cr"] / 1e6
    )


def extract_agent_invocations(repo_path: Path, run_window: tuple[datetime, datetime]) -> list[dict]:
    """CC session JSONL 의 toolUseResult 에서 dcness sub-agent 호출만 추출.

    return: [{ts, agent, duration_ms, output_tokens, total_tokens, cost_usd, ...}, ...] (ts 오름차순).
    """
    first_ts, last_ts = run_window
    invocations: list[dict] = []

    for jsonl in find_session_jsonls(repo_path):
        try:
            for line in jsonl.read_text(encoding="utf-8").splitlines():
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                tur = rec.get("toolUseResult")
                if not isinstance(tur, dict):
                    continue
                # totalTokens 또는 totalDurationMs 가 있어야 sub-agent result.
                if "totalTokens" not in tur and "totalDurationMs" not in tur:
                    continue
                rec_ts = _parse_iso(rec.get("timestamp", ""))
                if not rec_ts:
                    continue
                # 날짜 비교를 위해 timezone 통일 — naive 만 비교.
                rec_ts_naive = rec_ts.replace(tzinfo=None)
                if rec_ts_naive < first_ts.replace(tzinfo=None) or rec_ts_naive > last_ts.replace(tzinfo=None):
                    continue
                agent_type = tur.get("agentType") or ""
                normalized = _normalize_agent_type(agent_type)
                if normalized not in DCNESS_AGENT_NAMES:
                    continue
                usage = tur.get("usage", {}) or {}
                # iterations[].* 의 model 정보가 있으면 우선. 없으면 default opus.
                model = ""
                iters = usage.get("iterations") or []
                if iters and isinstance(iters[0], dict):
                    model = iters[0].get("model", "") or ""
                cost = _compute_invocation_cost(model, usage)
                invocations.append({
                    "ts": rec_ts_naive,
                    "agent": normalized,
                    "agent_type_raw": agent_type,
                    "duration_ms": tur.get("totalDurationMs", 0),
                    "total_tokens": tur.get("totalTokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "input_tokens": usage.get("input_tokens", 0),
                    "cache_read": usage.get("cache_read_input_tokens", 0),
                    "cost_usd": cost,
                    "tool_use_count": tur.get("totalToolUseCount", 0),
                })
        except OSError:
            continue

    invocations.sort(key=lambda r: r["ts"])
    return invocations


def assign_invocations_to_steps(steps: list[StepRecord], invocations: list[dict]) -> None:
    """각 step 에 대응 invocation 매칭 — timestamp proximity 기반 (DCN-30-21 fix).

    이전 algo (단순 순서 + agent name) 결함: step 0 invocation 누락 시 (다른 세션
    호출 등) cascade 로 후속 step 매칭 모두 어긋남. jajang 실측에서 9 step 중
    2 만 매칭, 7 미매칭. fix — 각 step 의 ts 와 가장 가까운 invocation 을 매칭
    window 안에서 선택. 1 invocation = 1 step (used set).

    매칭 룰:
    - inv.ts < step.ts (sub-agent 가 end-step 직전에 끝남)
    - step.ts - inv.ts ≤ 600s (10 분 — sub-agent budget 한도)
    - inv.agent == step.agent
    - 같은 agent 후보 여럿이면 가장 최근 inv (closest before step.ts)
    """
    if not steps or not invocations:
        return
    used: set[int] = set()

    for step in steps:
        step_ts = _parse_iso(step.ts)
        if not step_ts:
            continue
        step_ts_naive = step_ts.replace(tzinfo=None)
        best_idx = -1
        best_diff_s = float("inf")
        for i, inv in enumerate(invocations):
            if i in used:
                continue
            if inv["agent"] != step.agent:
                continue
            inv_ts = inv["ts"]
            if isinstance(inv_ts, datetime):
                inv_ts_naive = inv_ts.replace(tzinfo=None) if inv_ts.tzinfo else inv_ts
            else:
                continue
            diff_s = (step_ts_naive - inv_ts_naive).total_seconds()
            if 0 <= diff_s <= 600 and diff_s < best_diff_s:
                best_idx = i
                best_diff_s = diff_s
        if best_idx >= 0:
            inv = invocations[best_idx]
            step.duration_ms = inv["duration_ms"]
            step.output_tokens = inv["output_tokens"]
            step.total_tokens = inv["total_tokens"]
            step.cost_usd = inv["cost_usd"]
            step.matched_invocation = True
            step.tool_use_count = inv.get("tool_use_count", 0)
            used.add(best_idx)


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

    # 단계별 표 (DCN-30-20: per-Agent metrics + DCN-30-24: local time 시작 컬럼
    #            + DCN-CHG-20260430-39: tool_uses 컬럼 — TOOL_USE_OVERFLOW 가시성)
    lines.append("## 단계별 상세")
    lines.append("| # | 시작(local) | agent | mode | elapsed(s) | duration(s) | out_tok | total_tok | tool_uses | cost($) | enum | must_fix | prose줄 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for s in report.steps:
        line_count = len([l for l in (s.prose_full or s.prose_excerpt).splitlines() if l.strip()])
        dur_s = f"{s.duration_ms / 1000:.0f}" if s.matched_invocation else "-"
        out_tok = f"{s.output_tokens:,}" if s.matched_invocation else "-"
        tot_tok = f"{s.total_tokens:,}" if s.matched_invocation else "-"
        cost = f"{s.cost_usd:.4f}" if s.matched_invocation else "-"
        if s.matched_invocation:
            # ≥ 100 시 **bold** — TOOL_USE_OVERFLOW 임계와 동일 (run_review.py:465)
            tu_str = f"**{s.tool_use_count}**" if s.tool_use_count >= 100 else str(s.tool_use_count)
        else:
            tu_str = "-"
        ts_local = "-"
        ts_dt = _parse_iso(s.ts)
        if ts_dt:
            # UTC ISO → system local time (Mac 기본: 한국 KST)
            ts_local = ts_dt.astimezone().strftime("%H:%M:%S")
        lines.append(
            f"| {s.idx} | {ts_local} | {s.agent} | {s.mode or '-'} | {s.elapsed_s} | "
            f"{dur_s} | {out_tok} | {tot_tok} | {tu_str} | {cost} | "
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

    # DCN-CHG-20260430-20: per-Agent invocation 매칭 — wastes 탐지 *전*에 enrichment.
    invocations: list[dict] = []
    window: Optional[tuple] = None
    if steps:
        first_ts = _parse_iso(steps[0].ts)
        last_ts = _parse_iso(steps[-1].ts)
        if first_ts and last_ts:
            window = (first_ts, last_ts)
            invocations = extract_agent_invocations(repo_path, window)
            assign_invocations_to_steps(steps, invocations)

    # DCN-CHG-20260430-37: detect_wastes 에 invocations + repo_path + window 전달
    # (END_STEP_SKIP / MAIN_SED_MISDIAGNOSIS run-level 패턴 검출 위해).
    wastes = detect_wastes(steps, invocations=invocations, repo_path=repo_path, window=window)
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
