---
name: quick
description: 작은 버그픽스·코드 정리를 한 줄로 받아 light path 시퀀스 (qa → architect LIGHT_PLAN → engineer simple → validator BUGFIX_VALIDATION → pr-reviewer) 자동 진행하는 스킬. 사용자가 "간단히 해줘", "작은 수정", "한 줄 버그", "/quick", "퀵", "바로 고쳐줘", "오타 고쳐", "간단한 수정" 등을 말할 때 반드시 이 스킬을 사용한다. dcNess 컨베이어 패턴 (Task tool + Agent + helper + 훅) 으로 동작. 분류 결과가 FUNCTIONAL_BUG / CLEANUP 면 자동 진행, 그 외 (DESIGN_ISSUE / KNOWN_ISSUE / SCOPE_ESCALATE) 면 사용자 결정.
---

# Quick Skill — light path 자동화 + 공통 룰 SSOT

> 본 skill 은 light path 자동화 + dcness 컨베이어 공통 룰 (가시성 / AMBIGUOUS / Catastrophic / yolo / worktree) **SSOT**. 다른 skill 은 본 문서 참조.

## 사용

- 트리거: "간단히", "작은 수정", "퀵", "바로 고쳐", "오타", "한 줄"
- 비대상: 새 기능 → `/product-plan` · 디자인 → `/ux` · 다중 모듈 → `/qa` 정석 분류

## 시퀀스 (orchestration §3.5 light path)

```
qa → architect LIGHT_PLAN → engineer IMPL → validator BUGFIX_VALIDATION → pr-reviewer
```

자동 진행 조건: qa 결론이 `FUNCTIONAL_BUG` 또는 `CLEANUP`. 그 외 → 사용자 결정.

## 🚨 가시성 룰 (SSOT — 모든 dcness skill 공통)

> ⚠️ **DCN-CHG-20260430-15 강화**: 본 룰은 **MUST**. 토큰 절약 본능으로 압축/생략 금지. 위반 = bug. 모든 dcness skill (`/qa` `/quick` `/impl` `/impl-loop` `/product-plan`) 의 **모든 step** 의무.

CC 가 Agent / Bash 출력을 collapsed 표시 → 사용자가 매번 ctrl+o 안 눌러도 보이도록, **매 begin-step → Agent → end-step 직후 (TaskUpdate(completed) *전*) 메인이 text reply 로 prose 핵심 echo**:

### 의무 템플릿 — 빈 칸 채우기만 허용 (구조 변경 금지)

```
[<task-id>.<agent>] echo

▎ <prose 의 ## 결론 / ## Summary / ## 변경 요약 섹션 본문 5~12줄>
▎ <섹션 부재 시 prose 첫 5~10줄 fallback>
▎ <필요 시 추가 본문 인용 — 12줄 cap>

결론: <ENUM>
```

- `<task-id>` = standalone 시 step 이름, `/impl-loop` 안 시 `b<i>.<agent>`
- `▎` 글자 (U+258E) 그대로 — 사용자 인식 패턴
- 5줄 미만 / 12줄 초과 = 룰 위반

### 자가 점검 (TaskUpdate(completed) 호출 *전* 4 항)

```
□ Agent prose 종이 (`/tmp/dcness-*.md`) read 했는가?
□ ## 결론 / ## Summary / ## 변경 요약 섹션 우선 추출했는가?
□ 의무 템플릿대로 5~12줄 echo 했는가?
□ 결론 enum 포함됐는가?
```

4개 모두 YES 아니면 echo 추가 후 진행.

### 안티패턴 (절대 금지)

❌ 압축 paraphrase 1~2줄로 끝내기 ("결론: PASS, 다음 진입")
❌ table / code block 통째 생략 (행 수 줄여 인용)
❌ "토큰 아끼려" 결론만 echo
❌ 다음 Agent 호출 직전 echo (늦음 — end-step 직후 즉시)

### 비용 인지

step 당 ~200~300 output tokens (5 step × 5 batch ≈ 5~7k / impl-loop). 전체 batch 처리량 대비 ~3~5%. 비용 인지 + 그래도 의무 (검증·가시성 가치 > 토큰 비용).

## yolo 모드 (SSOT)

발화에 `yolo` / `auto` / `끝까지` / `막힘 없이` / `다 알아서` keyword 시 ON.

| 상황 | 비-yolo | yolo |
|------|---------|------|
| `CLARITY_INSUFFICIENT` / `*_ESCALATE` (soft) / `AMBIGUOUS` | 사용자 위임 | `auto-resolve` 적용 |
| `SPEC_GAP_FOUND` | 사용자 위임 | architect SPEC_GAP cycle (≤2) |
| `TESTS_FAIL` / validator FAIL | 재시도 (≤3) | 동일 |
| `CHANGES_REQUESTED` | 사용자 위임 | engineer POLISH (cycle ≤2) |
| Step 7 caveat (NICE TO HAVE only, MUST FIX 0) | 사용자 위임 | 7a 자동 |
| catastrophic 룰 (PreToolUse §2.3) | hard safety | hard safety (yolo 우회 X) |

```bash
RESOLVE_JSON=$("$HELPER" auto-resolve "<agent>:<enum_or_mode>")
# JSON: {"action":..., "hint":..., "next_enum":...}
# unmapped 시 yolo 도 사용자 위임 fallback
```

## AMBIGUOUS cascade (SSOT)

`end-step` stdout = `AMBIGUOUS` 시:
1. 재호출 1회 (결론 enum 명시 요청)
2. 재호출도 AMBIGUOUS → 사용자 위임 (enum 후보 + prose 발췌)

## worktree 격리 (SSOT — Step 0a 패턴)

발화에 `worktree` / `wt` / `격리` / `isolate` keyword 시:

```
EnterWorktree(name="<skill>-{ts_short}")
```

`harness/session_state.py._default_base()` 가 main repo `.git` 를 단일 source 로 — SessionStart 훅 by-pid / live.json 정합 (`docs/conveyor-design.md` §13).

종료 시 squash 흡수 검사 후 자동:
```bash
UNMERGED_DIFF=$(git diff "main..$WORKTREE_BRANCH" -- ':^.claude' 2>/dev/null)
if [ -z "$UNMERGED_DIFF" ]; then
  ExitWorktree(action="remove", discard_changes=true)
else
  ExitWorktree(action="keep")
fi
```

## 절차

### Step 0a — worktree (선택, 위 SSOT 참조)

### Step 0b — run 시작

```bash
HELPER="$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper"
RUN_ID=$("$HELPER" begin-run quick)
echo "[quick] run started: $RUN_ID"
```

사용자 확인 (요청 / 이슈 제목 / depth=simple / 진행할까요).

### Step 1 — 5 task 등록

```
TaskCreate("qa: 이슈 분류")
TaskCreate("architect: LIGHT_PLAN")
TaskCreate("engineer: IMPL (simple)")
TaskCreate("validator: BUGFIX_VALIDATION")
TaskCreate("pr-reviewer: 검토")
```

(commit/PR 은 사용자 결정 — Task 외)

### Step 2~6 — 각 단계 표

매 단계 골격 (`<>` 부분만 step 별 차이):

```
TaskUpdate("<task>", in_progress)
"$HELPER" begin-step <agent> [<MODE>]
Agent(subagent_type="<agent>", mode="<MODE>", description="...")
ENUM=$("$HELPER" end-step <agent> [<MODE>] --allowed-enums "<list>" --prose-file /tmp/dcness-quick-<n>.md)
# 가시성 룰 의무 echo → advance 시 TaskUpdate(completed)
```

| Step | agent | mode | allowed-enums | advance |
|------|-------|------|---------------|---------|
| 2 | qa | — | `FUNCTIONAL_BUG,CLEANUP,DESIGN_ISSUE,KNOWN_ISSUE,SCOPE_ESCALATE` | `FUNCTIONAL_BUG` / `CLEANUP` |
| 3 | architect | LIGHT_PLAN | `LIGHT_PLAN_READY,SPEC_GAP_FOUND,TECH_CONSTRAINT_CONFLICT` | `LIGHT_PLAN_READY` |
| 4 | engineer | IMPL | `IMPL_DONE,SPEC_GAP_FOUND,TESTS_FAIL,IMPLEMENTATION_ESCALATE` | `IMPL_DONE` |
| 5 | validator | BUGFIX_VALIDATION | `PASS,FAIL` | `PASS` |
| 6 | pr-reviewer | — | `LGTM,CHANGES_REQUESTED` | `LGTM` |

### qa 분기 (Step 2 advance 외)

| ENUM | 처리 |
|------|------|
| `DESIGN_ISSUE` | 종료 + `/ux` (구현 후) 추천 |
| `KNOWN_ISSUE` | 종료 |
| `SCOPE_ESCALATE` | 사용자 위임 (분류 모호) |

### advance 외 분기 공통

- `SPEC_GAP_FOUND` → architect SPEC_GAP 또는 사용자 위임
- `TECH_CONSTRAINT_CONFLICT` / `IMPLEMENTATION_ESCALATE` → 사용자 위임
- validator `FAIL` → engineer 재호출 또는 사용자 위임
- `CHANGES_REQUESTED` → engineer POLISH 호출 (cycle ≤2) 또는 사용자 위임
- `AMBIGUOUS` → 위 SSOT cascade

### Step 7 — finalize-run + clean 자동 commit/PR

#### 7.1 status 집계

```bash
STATUS=$("$HELPER" finalize-run)
"$HELPER" end-run
echo "$STATUS"
```

JSON 구조: `{run_id, session_id, steps[{agent, mode, enum, must_fix, prose_excerpt}], has_ambiguous, has_must_fix, step_count}`.

#### 7.2 clean 판정

다음 모두 충족 → **clean**:
- `has_ambiguous == false` && `has_must_fix == false`
- step enum 매트릭스: `qa ∈ {FUNCTIONAL_BUG, CLEANUP}` · `architect:LIGHT_PLAN == LIGHT_PLAN_READY` · `engineer:IMPL == IMPL_DONE` · `validator:BUGFIX_VALIDATION == PASS` · `pr-reviewer == LGTM`
- git 안전 가드:
  - `git status --porcelain` 에 `.env` / `secrets.*` / `credentials.*` 없음
  - unstaged + untracked ≤ 10
  - submodule 변경 없음

clean 아니면 **7b**.

#### 7a — Clean 자동 commit/PR

자동 진행 (사용자 확인 X):

1. 변경 + remote 확인:
   ```bash
   CHANGED=$(git diff --name-only HEAD)
   HAS_REMOTE=$(git remote get-url origin >/dev/null 2>&1 && echo yes || echo no)
   ```

2. branch + commit (분류별 prefix — `FUNCTIONAL_BUG` → `fix/`, `CLEANUP` → `chore/`):
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

3. remote 있으면 push + PR + squash merge:
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
     echo "[quick] remote 없음 — local commit only"
   fi
   ```

4. worktree 정리 (위 SSOT — squash 흡수 검사).

5. 사용자 보고:
   ```
   [quick] 완료 + 자동 commit/PR ✅
   - run_id: $RUN_ID · branch: $BRANCH · PR: <URL>
   - 변경: <changed files 요약>
   ```

#### 7b — Caveat 확인 (clean 아닐 때)

```
[quick] 완료 (caveat)
- run_id: $RUN_ID · 변경: <src/ 변경 파일>
- prose 종이: .claude/harness-state/.sessions/{sid}/runs/$RUN_ID/

⚠️ Caveat: <has_ambiguous / has_must_fix / unexpected enum / sensitive untracked>

커밋/PR 진행할까요? (수동 — branch → PR → squash merge)
```

worktree 처리도 사용자 결정.

**yolo 시**: `has_must_fix == false` + enum unexpected 만 (CHANGES_REQUESTED 1건 등) → 자동 7a 시도. `has_must_fix` 또는 `has_ambiguous` true 면 yolo 도 7b.

## Catastrophic 룰 정합

본 시퀀스는 `docs/conveyor-design.md` §2.3 정합:
- §2.3.1 (pr-reviewer 직전 validator PASS) — Step 5 충족
- §2.3.3 (engineer 직전 plan READY) — Step 3 충족
- §2.3.4 (architect SD/TD 직전 PRD 검토) — light path 비대상

PreToolUse 훅 자동 통과.

## 한계

- depth=simple 고정 — 큰 변경은 `/product-plan` 또는 `/impl` 정식 루프
- SPEC_GAP_FOUND 자동 처리 미구현 (사용자 위임)

## 참조

- `agents/{qa,architect,engineer,pr-reviewer,validator}.md` + `agents/architect/light-plan.md` + `agents/validator/bugfix-validation.md`
- `docs/orchestration.md` §3.5 (light path) / §4 (enum 결정표)
- `docs/conveyor-design.md` §2 / §3 / §7 / §8 / §13
- `commands/qa.md` (분류만) · `commands/product-plan.md` (spec/design) · `commands/impl.md` (정식 루프)
