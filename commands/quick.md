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

## 공통 룰 (SSOT 외부)

dcness 범용 룰 (가시성 / Step 기록 / yolo / AMBIGUOUS / worktree / 루프 종료 시 /run-review / 결과 출력 / 권한 요청) 은 **`docs/process/dcness-guidelines.md`** 단일 SSOT.

활성 프로젝트의 매 세션 SessionStart 훅이 본 가이드라인을 system-reminder 로 자동 inject (DCN-30-26). skill 측은 본 SSOT 인용만.

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
# DCN-30-21: prose-file 을 run-dir 안 격리 (멀티세션 안전, /tmp 결함 fix)
RUN_DIR=$("$HELPER" run-dir)
mkdir -p "$RUN_DIR/.prose-staging"
PROSE_PATH="$RUN_DIR/.prose-staging/<step>.md"
# (메인이 sub-agent prose 를 위 경로에 Write)
ENUM=$("$HELPER" end-step <agent> [<MODE>] --allowed-enums "<list>" --prose-file "$PROSE_PATH")
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
STATUS=$("$HELPER" finalize-run --expected-steps 5)  # DCN-30-25: 5 = qa+architect+engineer+validator+pr-reviewer
"$HELPER" end-run
echo "$STATUS"
```

`--expected-steps` 미달 시 helper 가 stderr WARN — 메인이 즉시 인지 + `/run-review` 로 진단.

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
