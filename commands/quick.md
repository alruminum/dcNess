---
name: quick
description: 작은 버그픽스·코드 정리를 한 줄로 받아 light path 시퀀스 (qa → architect LIGHT_PLAN → engineer simple → validator BUGFIX_VALIDATION → pr-reviewer) 자동 진행하는 스킬. 사용자가 "간단히 해줘", "작은 수정", "한 줄 버그", "/quick", "퀵", "바로 고쳐줘", "오타 고쳐", "간단한 수정" 등을 말할 때 반드시 이 스킬을 사용한다. dcNess 컨베이어 패턴 (Task tool + Agent + helper + 훅) 으로 동작. 분류 결과가 FUNCTIONAL_BUG / CLEANUP 면 자동 진행, 그 외 (DESIGN_ISSUE / KNOWN_ISSUE / SCOPE_ESCALATE) 면 사용자 결정.
---

# Quick Skill — 작은 버그픽스 light path 자동화

> dcNess 컨베이어 패턴. qa 분류 후 FUNCTIONAL_BUG / CLEANUP 만 light path 자동 진행. 다른 분류는 사용자 결정.
> light path = depth=simple, test-engineer 단계 생략, BUGFIX_VALIDATION 사용 (`docs/orchestration.md` §3.5).

## 언제 사용하는가

- 사용자 발화에 다음 keyword — "간단히", "작은 수정", "퀵", "바로 고쳐", "오타", "한 줄"
- 또는 수정 범위가 한 줄 / 한 함수 내부로 명백
- 분류·라우팅 ping-pong 최소화하고 싶을 때

## 언제 사용하지 않음

- "새 기능" / "피쳐 추가" → `/product-plan`
- "리디자인" / "레이아웃" / "시안" → `/ux` (구현 후) 또는 designer 직접 호출
- 코드 변경 범위가 여러 모듈 / 아키텍처 영향 → `/qa` 정석 분류

## 시퀀스 (orchestration.md §3.5 light path)

```
qa (분류) → architect LIGHT_PLAN → engineer IMPL → validator BUGFIX_VALIDATION → pr-reviewer
```

자동 진행 조건: qa 결론이 `FUNCTIONAL_BUG` 또는 `CLEANUP`. 그 외 분류는 fallback.

## yolo 모드 — keyword 트리거

사용자 발화에 다음 keyword 1개 이상 포함 시 yolo 모드 ON:
- `yolo` / `auto` / `끝까지` / `막힘 없이` / `다 알아서` / `자동으로 끝까지`

yolo 시 동작 변화:
- `CLARITY_INSUFFICIENT` / `*_ESCALATE` (soft) / `AMBIGUOUS` 발생 시 사용자 위임 대신 helper `auto-resolve` 호출 → 권장 액션 자동 적용 (재호출 / 폴백 작업).
- Step 7 의 caveat 일부 (NICE TO HAVE 만 있고 MUST FIX 0) 도 자동 진행으로 분류.
- catastrophic 룰 (PreToolUse 훅 §2.3) 은 그대로 — yolo 가 hard safety 우회 못 함.

```bash
# yolo keyword 검출 시 (메인이 사용자 발화 검사)
YOLO=true   # 이후 분기에 활용
```

helper auto-resolve 호출 형식 (yolo 진행 시):
```bash
RESOLVE_JSON=$("$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" auto-resolve "<agent>:<enum_or_mode>")
# JSON: {"action": ..., "hint": ..., "next_enum": ...}
# 메인이 hint 따라 작업 (예: re-invoke 시 prose 작성 + advance, user-delegate 면 사용자 위임)
```

매핑 없으면 (`{"action": "unmapped"}`) yolo 도 사용자 위임 fallback (안전 default).

## 가시성 룰 — 매 Agent 호출 후 메인 text echo (필수)

CC 가 Agent / Bash 출력을 collapsed 표시 (ctrl+o expand 필요). 사용자가 매번 ctrl+o
누르지 않아도 핵심 결과 보이도록, **매 begin-step → Agent → end-step 직후 메인이
text reply 로 prose 핵심 echo** (DCN-CHG-30-11):

```
## <step 이름> 결과 — <enum>

<prose 의 ## 결론 / ## Summary / ## 변경 요약 섹션의 본문 5~12줄 그대로 인용,
markdown 정합 보존. 결론 헤더 부재 시 prose 첫 5~10줄 fallback>

<선택: 1줄 다음 step 안내>
```

text reply 는 collapsed 안 됨 — 사용자 가시성 ↑. helper stderr 자동 요약 (DCN-CHG-30-2,
30-11 cap 확장) 과 동시 — 두 channel 가시성 보장.

verbose 회피: 매 step 5~12줄 cap. 그 이상은 사용자가 ctrl+o 또는 prose 종이
(`.claude/harness-state/.sessions/{sid}/runs/{rid}/<agent>[-<MODE>].md`) 직접 read.

## 절차 (Task tool + helper protocol)

### Step 0a — worktree 격리 진입 (선택, keyword 트리거)

사용자 발화에 다음 keyword 가 포함된 경우에만 worktree 진입 (옵션 C — 명시 트리거):
- `worktree`, `wt`, `격리`, `isolate`

해당 keyword 없으면 본 step 통째로 skip → 바로 Step 0b 진행 (main repo cwd).

```
EnterWorktree(name="quick-{rid_prefix}")
```

`{rid_prefix}` = 곧 발급될 run_id 의 prefix 추정 (예: `q1`, `q2` 같은 짧은 토큰). 실 run_id 는
Step 0b 에서 발급되니, worktree 이름은 `quick-{ts_short}` 처럼 시간 토큰으로 채워도 무방.

진입 후 cwd = `.claude/worktrees/quick-.../`.

`harness/session_state.py` 의 `_default_base()` 가 `git rev-parse --git-common-dir` 로 main
repo `.git` 를 추출 → main repo `.claude/harness-state/` 가 단일 source. SessionStart 훅이
main repo 에서 박은 by-pid / live.json 을 worktree 안 helper 도 그대로 읽는다 (`docs/conveyor-design.md` §13 참조).

사용자에게 진입 사실 1줄 보고:
```
[quick] worktree 격리 진입 — cwd: .claude/worktrees/quick-...
```

### Step 0b — run 시작 + 사용자 확인

```bash
RUN_ID=$("$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" begin-run quick)
echo "[quick] run started: $RUN_ID"
```

사용자에게 한 번 확인:
```
[quick] 실행 설정
- 요청: <유저 원문>
- 이슈 제목 (한 줄, 70자 이내): <뽑은 제목>
- depth: simple (light path 고정)

진행할까요?
```

확인 못 받으면 대기. 자동 진행 금지.

### Step 1 — 5 task 생성

```
TaskCreate("qa: 이슈 분류")
TaskCreate("architect: LIGHT_PLAN")
TaskCreate("engineer: IMPL (simple)")
TaskCreate("validator: BUGFIX_VALIDATION")
TaskCreate("pr-reviewer: 검토")
```

(commit/PR 은 사용자 결정 — Task 에 안 넣음)

### Step 2 — qa 분류

```
TaskUpdate("qa: 이슈 분류", in_progress)
```

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" begin-step qa
```

```
Agent(
  subagent_type="qa",
  description="<유저 원문>. [Quick 모드] depth=simple 고정, architect LIGHT_PLAN 진입 예정. 5 결론 enum 중 하나로 분류해줘."
)
```

prose 받으면:
```bash
cat > /tmp/dcness-quick-qa.md << 'PROSE_EOF'
<agent prose>
PROSE_EOF

ENUM=$("$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" end-step qa \
    --allowed-enums "FUNCTIONAL_BUG,CLEANUP,DESIGN_ISSUE,KNOWN_ISSUE,SCOPE_ESCALATE" \
    --prose-file /tmp/dcness-quick-qa.md)
```

분기:
- **FUNCTIONAL_BUG / CLEANUP** → 다음 step 진행
- **DESIGN_ISSUE** → 종료 + `/ux` (구현 후) 또는 designer 직접 호출 추천
- **KNOWN_ISSUE** → 종료 (이미 알려진 이슈)
- **SCOPE_ESCALATE** → 사용자 위임 (분류 모호)
- **AMBIGUOUS** → /qa 의 cascade 패턴 (재호출 → 사용자) 적용

advance 시:
```
TaskUpdate("qa: 이슈 분류", completed)
```

### Step 3 — architect LIGHT_PLAN

```
TaskUpdate("architect: LIGHT_PLAN", in_progress)
```

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" begin-step architect LIGHT_PLAN
```

```
Agent(
  subagent_type="architect",
  mode="LIGHT_PLAN",
  description="qa 분류 = $ENUM. 이슈: <원문>. light path. depth=simple. impl 계획 prose 로 짜줘. 결론 enum: LIGHT_PLAN_READY / SPEC_GAP_FOUND / TECH_CONSTRAINT_CONFLICT 중 하나."
)
```

```bash
ENUM=$("$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" end-step architect LIGHT_PLAN \
    --allowed-enums "LIGHT_PLAN_READY,SPEC_GAP_FOUND,TECH_CONSTRAINT_CONFLICT" \
    --prose-file /tmp/dcness-quick-light-plan.md)
```

advance 조건: `LIGHT_PLAN_READY`. 그 외:
- `SPEC_GAP_FOUND` → architect SPEC_GAP 끼우거나 사용자 위임
- `TECH_CONSTRAINT_CONFLICT` → 사용자 위임 (escalate)
- `AMBIGUOUS` → cascade

```
TaskUpdate("architect: LIGHT_PLAN", completed)
```

### Step 4 — engineer IMPL

```
TaskUpdate("engineer: IMPL (simple)", in_progress)
```

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" begin-step engineer IMPL
```

PreToolUse 훅 검사 (catastrophic-gate.sh):
- §2.3.3 — `architect-LIGHT_PLAN.md` 안 `LIGHT_PLAN_READY` 확인 → 통과 (Step 3 에서 박힘)

```
Agent(
  subagent_type="engineer",
  mode="IMPL",
  description="architect LIGHT_PLAN 완료. 계획 prose: <agent transcript 의 직전 architect prose>. 구현해줘. 결론 enum: IMPL_DONE / SPEC_GAP_FOUND / TESTS_FAIL / IMPLEMENTATION_ESCALATE."
)
```

engineer 가 src/ 수정. PreToolUse Write 훅 (있다면) 이 ALLOW path 검증.

```bash
ENUM=$("$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" end-step engineer IMPL \
    --allowed-enums "IMPL_DONE,SPEC_GAP_FOUND,TESTS_FAIL,IMPLEMENTATION_ESCALATE" \
    --prose-file /tmp/dcness-quick-impl.md)
```

advance 조건: `IMPL_DONE`. 그 외:
- `SPEC_GAP_FOUND` → architect SPEC_GAP 진입 (별도 cycle)
- `TESTS_FAIL` → engineer 재호출 (depth=simple 이라 보통 안 발생)
- `IMPLEMENTATION_ESCALATE` → 사용자 위임
- `AMBIGUOUS` → cascade

### Step 5 — validator BUGFIX_VALIDATION

```
TaskUpdate("validator: BUGFIX_VALIDATION", in_progress)
```

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" begin-step validator BUGFIX_VALIDATION
```

```
Agent(
  subagent_type="validator",
  mode="BUGFIX_VALIDATION",
  description="engineer IMPL 완료. 변경: <transcript 의 engineer prose>. 검증해줘. 결론 enum: PASS / FAIL."
)
```

```bash
ENUM=$("$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" end-step validator BUGFIX_VALIDATION \
    --allowed-enums "PASS,FAIL" \
    --prose-file /tmp/dcness-quick-bugfix.md)
```

advance 조건: `PASS`. `FAIL` 면 engineer 재호출 또는 사용자 위임.

### Step 6 — pr-reviewer

```
TaskUpdate("pr-reviewer: 검토", in_progress)
```

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" begin-step pr-reviewer
```

PreToolUse 훅 검사:
- §2.3.1 — `validator-BUGFIX_VALIDATION.md` 안 `PASS` 확인 → 통과

```
Agent(
  subagent_type="pr-reviewer",
  description="engineer IMPL + validator BUGFIX_VALIDATION PASS. 검토해줘. 결론 enum: LGTM / CHANGES_REQUESTED."
)
```

```bash
ENUM=$("$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" end-step pr-reviewer \
    --allowed-enums "LGTM,CHANGES_REQUESTED" \
    --prose-file /tmp/dcness-quick-pr.md)
```

advance 조건: `LGTM`. `CHANGES_REQUESTED` 면 engineer POLISH 호출 또는 사용자 위임.

```
TaskUpdate("pr-reviewer: 검토", completed)
```

### Step 7 — finalize-run + clean 자동 commit/PR (또는 caveat 확인)

#### 7.1 helper 로 status 집계

```bash
HELPER="$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper"
STATUS=$("$HELPER" finalize-run)
"$HELPER" end-run
echo "$STATUS"
```

JSON 구조:
```json
{
  "run_id": "run-...",
  "session_id": "...",
  "steps": [
    {"agent": "qa", "mode": null, "enum": "FUNCTIONAL_BUG", "must_fix": false, "prose_excerpt": "..."},
    {"agent": "architect", "mode": "LIGHT_PLAN", "enum": "LIGHT_PLAN_READY", ...},
    {"agent": "engineer", "mode": "IMPL", "enum": "IMPL_DONE", ...},
    {"agent": "validator", "mode": "BUGFIX_VALIDATION", "enum": "PASS", ...},
    {"agent": "pr-reviewer", "mode": null, "enum": "LGTM", ...}
  ],
  "has_ambiguous": false,
  "has_must_fix": false,
  "step_count": 5
}
```

#### 7.2 clean 판정

다음 모두 충족 → **clean**:
- `has_ambiguous == false`
- `has_must_fix == false`
- step enum 매트릭스:
  - `qa.enum ∈ {FUNCTIONAL_BUG, CLEANUP}`
  - `architect:LIGHT_PLAN.enum == LIGHT_PLAN_READY`
  - `engineer:IMPL.enum == IMPL_DONE`
  - `validator:BUGFIX_VALIDATION.enum == PASS`
  - `pr-reviewer.enum == LGTM`
- git 안전 가드:
  - `git status --porcelain` 에 `.env` / `secrets.*` / `credentials.*` 패턴 없음
  - unstaged + untracked 파일 합 ≤ 10
  - submodule 변경 (m flag) 없음

clean 아니면 → **7b (caveat 확인)** 으로.

#### 7a — Clean 자동 commit/PR

자동 진행 (사용자 확인 X):

1. **changed files 확인** + **git 상태**:
   ```bash
   CHANGED=$(git diff --name-only HEAD)
   HAS_REMOTE=$(git remote get-url origin >/dev/null 2>&1 && echo yes || echo no)
   ```

2. **branch + commit** (분류별 prefix — FUNCTIONAL_BUG → `fix/`, CLEANUP → `chore/`):
   ```bash
   BRANCH="fix/<short-slug>"   # 또는 chore/
   git checkout -b "$BRANCH" main
   git add $CHANGED
   git commit -m "$(cat <<'EOF'
   <한 줄 제목 — Step 0 의 이슈 제목 재사용>

   <2~3 줄 본문 — engineer prose_excerpt + run_id 참조>

   Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
   EOF
   )"
   ```

3. **remote 있으면 push + PR + squash merge**:
   ```bash
   if [ "$HAS_REMOTE" = "yes" ]; then
     git push -u origin "$BRANCH"
     gh pr create --title "<제목>" --body "$(cat <<'EOF'
   ## Summary
   <변경 요약>

   ## Test
   - validator BUGFIX_VALIDATION: PASS
   - pr-reviewer: LGTM
   - run_id: $RUN_ID

   🤖 Generated by /quick (dcNess)
   EOF
   )"
     gh pr merge --squash --auto 2>/dev/null || gh pr merge --squash || \
       echo "[quick] PR merge 차단 — branch protection / CI 대기"
     git checkout main && git pull --ff-only 2>/dev/null || true
   else
     echo "[quick] git remote 없음 — local commit 까지만"
   fi
   ```

4. **worktree 정리** (Step 0a 진입했으면):
   ```bash
   # squash merge 후 worktree branch tip 이 main 에 unreachable 해도 변경은 흡수됨.
   # 검사: git diff main..<worktree-branch> -- :^.claude  결과 비면 안전 → discard_changes=true.
   if [ -n "$WORKTREE_BRANCH" ]; then
     UNMERGED_DIFF=$(git diff "main..$WORKTREE_BRANCH" -- ':^.claude' 2>/dev/null)
     if [ -z "$UNMERGED_DIFF" ]; then
       # 변경 main 에 흡수됨
       ExitWorktree(action="remove", discard_changes=true)
     else
       ExitWorktree(action="keep")  # 변경 안 흡수 — 보존
     fi
   fi
   ```

5. **사용자 보고**:
   ```
   [quick] 완료 + 자동 commit/PR ✅
   - run_id: $RUN_ID
   - branch: $BRANCH
   - PR: <URL or "remote 없음 — local commit only">
   - 변경: <changed files 요약>
   ```

#### 7b — Caveat 확인 (clean 아닐 때)

사용자 확인 받음:
```
[quick] 완료 (caveat)
- run_id: $RUN_ID
- 변경: <src/ 변경 파일 요약>
- prose 종이: .claude/harness-state/.sessions/{sid}/runs/$RUN_ID/

⚠️ Caveat:
<caveat 항목 — has_ambiguous / has_must_fix / unexpected enum / sensitive untracked 등>

커밋/PR 진행할까요? (수동 — branch → PR → squash merge)
```

worktree 처리도 사용자 결정 (`keep` / `remove`).

**yolo 모드 시**: caveat 가 has_must_fix == false 이고 enum 만 unexpected (예: pr-reviewer CHANGES_REQUESTED 1건) 인 경우 자동으로 7a 시도. has_must_fix 또는 has_ambiguous true 면 yolo 도 7b fallback.

## AMBIGUOUS 처리 — 매 step 동일

`end-step` stdout 이 `AMBIGUOUS` 면:

1. **재호출 (1회)** — agent 한테 결론 enum 명시 요청 후 재실행
2. 재호출도 AMBIGUOUS → **사용자 위임** (현재 step 의 enum 후보 + prose 발췌 보여주고 결정 받음)
3. 사용자 응답 → 그 enum 으로 진행 또는 종료

`/qa` 의 cascade 패턴 정합.

## Catastrophic 룰 — 자동 정합

본 시퀀스는 §2.3 4룰 모두 정합:
- §2.3.1 (pr-reviewer 직전 validator PASS) — Step 5 BUGFIX_VALIDATION PASS 가 충족
- §2.3.3 (engineer 직전 plan READY) — Step 3 LIGHT_PLAN_READY 가 충족
- §2.3.4 (architect SD/TD 직전 PRD 검토) — light path 는 architect SD/TD 안 써서 비대상

PreToolUse 훅이 매 Agent 호출 직전 자동 검사. 시퀀스 정합 시 자동 통과.

## 한계 / 후속

- **depth=simple 고정** — 한 줄 / 한 함수 수정 외엔 부적합. test-engineer 단계 없어 회귀 위험. 큰 변경은 `/product-plan` 또는 정식 impl 루프.
- **SPEC_GAP_FOUND 자동 처리 미구현** — 별도 cycle 진입 X. v1 은 사용자 위임.
- **commit/PR 자동화 X** — Step 7 에서 사용자 결정. 자동 commit 은 위험 (governance §2.5 doc-sync gate 위배 가능).

## 참조

- `agents/qa.md` — qa system prompt
- `agents/architect/light-plan.md` — LIGHT_PLAN system prompt
- `agents/engineer.md` — engineer (IMPL / POLISH)
- `agents/validator/bugfix-validation.md` — BUGFIX_VALIDATION system prompt
- `agents/pr-reviewer.md` — pr-reviewer
- `docs/orchestration.md` §3.5 — light path 시퀀스
- `docs/orchestration.md` §4 — agent 별 결론 enum 결정표
- `docs/conveyor-design.md` §2 / §3 / §7 / §8 — Task tool + helper + 훅
- `commands/qa.md` — `/qa` skill (분류만 하는 진입점)
