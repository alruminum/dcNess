---
name: impl
description: impl batch (architect TASK_DECOMPOSE 산출물) 1개를 받아 정식 impl 루프 (architect MODULE_PLAN → test-engineer → engineer → validator CODE_VALIDATION → pr-reviewer) 자동 진행하는 스킬. 사용자가 "구현해줘", "/impl <batch>", "이 batch 구현", "module plan 부터 진행", "impl 루프" 등을 말할 때 반드시 이 스킬을 사용한다. /product-plan 의 후속 — TASK_DECOMPOSE 의 batch list 1개씩 처리. /quick 보다 무거움 (test-engineer + CODE_VALIDATION 포함). dcNess 컨베이어 패턴 (Task tool + Agent + helper + 훅) 으로 동작.
---

# Impl Skill — per-batch 정식 impl 루프

> 공통 룰 (가시성 / AMBIGUOUS / Catastrophic / yolo / worktree / Step 7 commit-PR) SSOT = `commands/quick.md`. 본 skill 은 시퀀스 + 분기 + 4.5 sync + 2.0 마커 검사만 명세.

## 사용

- 트리거: "구현해줘", "/impl", "이 batch 구현", "module plan", "impl 루프"
- 비대상: 한 줄 → `/quick` · spec/design → `/product-plan` · multi-batch → `/impl-loop` · batch 부재 → `/quick`

## 시퀀스 (orchestration §2.1)

```
architect MODULE_PLAN → test-engineer → engineer IMPL → validator CODE_VALIDATION → pr-reviewer
```

## 절차

### Step 0 — worktree (선택, SSOT)

배치 = src/ 다중 수정 → 충돌 위험 시 권장.

### Step 0b — run 시작

```bash
HELPER="$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper"
RUN_ID=$("$HELPER" begin-run impl)
echo "[impl] run started: $RUN_ID"
```

batch 경로 추출 (예: `docs/milestones/v0.2/epics/epic-01-*/impl/01-*.md`). 사용자 확인 (batch / 이슈 제목 / 시퀀스 / attempt 한도 — engineer 3 / POLISH 2 / SPEC_GAP cycle 2 / 진행할까요).

### Step 1 — 5 sub-task 등록 (의무, skip 금지 DCN-CHG-30-12)

⚠️ inline skip 금지. begin-step → Agent 직행 X.

**standalone**:
```
TaskCreate("architect: MODULE_PLAN")
TaskCreate("test-engineer: TDD attempt 0")
TaskCreate("engineer: IMPL")
TaskCreate("validator: CODE_VALIDATION")
TaskCreate("pr-reviewer: 검토")
```

**`/impl-loop` inner**: prefix `b<i>.` (예: `b1.architect: MODULE_PLAN`). `commands/impl-loop.md` Step 2 참조.

### Step 2 — architect MODULE_PLAN (state-aware skip 가능)

#### 2.0 batch 마커 검사 (DCN-CHG-30-13)

```bash
if grep -q "MODULE_PLAN_READY" "<batch path>"; then
    echo "[impl] batch 자체 MODULE_PLAN_READY 박힘 — Step 2.1 skip"
    SKIP_MODULE_PLAN=true
else
    SKIP_MODULE_PLAN=false
fi
```

조건: `architect TASK_DECOMPOSE` 가 batch 산출 시 ## 생성/수정 파일 / ## 인터페이스 / ## 의사코드 / ## 결정 근거 박고 마지막 줄에 `MODULE_PLAN_READY` 마커 박음.

**SKIP 시**:
- TaskUpdate("architect: MODULE_PLAN", completed) + label "skipped (batch 자체 MODULE_PLAN_READY)"
- catastrophic §2.3.3 통과 위해 prose 종이 복사:
  ```bash
  cp "<batch path>" "$RUN_DIR/architect-MODULE_PLAN.md"
  ```
- Step 3 직진

#### 2.1 정상 호출 (마커 부재 시)

```
TaskUpdate("architect: MODULE_PLAN", in_progress)
"$HELPER" begin-step architect MODULE_PLAN
Agent(subagent_type="architect", mode="MODULE_PLAN",
      description="impl batch 파일: <batch path>. 모듈 plan — 생성/수정 파일 + 인터페이스 + 의사코드 + 결정 근거. 결론 enum: READY_FOR_IMPL / SPEC_GAP_FOUND / TECH_CONSTRAINT_CONFLICT.")
# DCN-30-21: prose-file 을 run-dir 안 격리 (멀티세션 안전)
RUN_DIR=$("$HELPER" run-dir)
mkdir -p "$RUN_DIR/.prose-staging"
PROSE_PATH="$RUN_DIR/.prose-staging/architect-MODULE_PLAN.md"
# (메인이 sub-agent prose 를 위 경로에 Write)
ENUM=$("$HELPER" end-step architect MODULE_PLAN \
       --allowed-enums "READY_FOR_IMPL,SPEC_GAP_FOUND,TECH_CONSTRAINT_CONFLICT" \
       --prose-file "$PROSE_PATH")
# 가시성 룰 의무 echo
```

### Step 3~6 — 단계 표

매 단계 골격 동일 (TaskUpdate(in_progress) → begin-step → Agent → end-step → 의무 echo → TaskUpdate(completed)):

| Step | agent | mode | allowed-enums | advance |
|------|-------|------|---------------|---------|
| 3 | test-engineer | — | `TESTS_WRITTEN,SPEC_GAP_FOUND` | `TESTS_WRITTEN` |
| 4 | engineer | IMPL | `IMPL_DONE,SPEC_GAP_FOUND,TESTS_FAIL,IMPLEMENTATION_ESCALATE` | `IMPL_DONE` |
| 5 | validator | CODE_VALIDATION | `PASS,FAIL,SPEC_MISSING` | `PASS` |
| 6 | pr-reviewer | — | `LGTM,CHANGES_REQUESTED` | `LGTM` |

### 분기 표

| ENUM | 처리 |
|------|------|
| `SPEC_GAP_FOUND` | architect SPEC_GAP cycle (≤2) 또는 사용자 위임 |
| `TESTS_FAIL` / validator `FAIL` | engineer 재시도 (attempt < 3) |
| `SPEC_MISSING` | architect SPEC_GAP |
| `TECH_CONSTRAINT_CONFLICT` / `IMPLEMENTATION_ESCALATE` | 사용자 위임 |
| `CHANGES_REQUESTED` | engineer POLISH cycle (≤2) |
| `AMBIGUOUS` | `commands/quick.md` cascade |

#### POLISH 사이드 사이클

```
Agent(subagent_type="engineer", mode="POLISH",
      description="pr-reviewer CHANGES_REQUESTED. 지적 사항 반영. 결론 enum: POLISH_DONE / IMPLEMENTATION_ESCALATE.")
```

`POLISH_DONE` 후 pr-reviewer 재호출. cycle ≤ 2.

### Step 4.5 — stories.md / backlog.md 체크박스 sync (DCN-CHG-30-14)

engineer `IMPL_DONE` 직후, validator 진입 *전*. 메인 직접 mechanical edit (agent 위임 X — 도메인 외).

**근거**: 글로벌 `~/.claude/CLAUDE.md` "태스크 완료 → stories.md 체크" 룰. impl.md 시퀀스에 step 으로 박지 않으면 매 batch 누락.

#### 4.5.1 epic 경로 추출

```bash
EPIC_DIR=$(dirname $(dirname "<batch path>"))
STORIES_FILE="$EPIC_DIR/stories.md"
BACKLOG_FILE="$(dirname $(dirname $EPIC_DIR))/../backlog.md"  # milestone root + ..
```

(실제 경로는 milestone 구조에 따라 메인이 자체 판단 — `find` / `Glob` 으로 확인.)

#### 4.5.2 stories.md 갱신

batch 가 다룬 Story `[ ]` → `[x]`. batch 의 ## 관련 Story / ## 적용 범위 메타로 식별. 부분 task 만 처리 → 해당 task 만 `[x]`. Story 하위 모두 `[x]` 면 Story 자체 `[x]`.

```
Edit(STORIES_FILE, "- [ ] Story X: ...", "- [x] Story X: ...")
```

#### 4.5.3 backlog.md 갱신 (epic 완료 시만)

stories.md 의 모든 Story `[x]` 면:
```
Edit(BACKLOG_FILE, "- [ ] epic-NN-...", "- [x] epic-NN-...")
```

부분 진행이면 backlog 손대지 않음.

#### 4.5.4 가시성

```
[impl] step 4.5 — stories.md / backlog.md sync
- stories.md: Story 1 [ ] → [x] (8 task 모두 완료)
- backlog.md: epic-01 라인 [ ] → [x]
```

다음 step (validator) 은 src/ 만 검증 — stories.md 무시. pr-reviewer 가 코드 + doc 같이 검토.

### Step 7 — finalize-run + clean commit/PR

`commands/quick.md` Step 7 동일. 차이점:

**finalize-run 호출** (DCN-30-25 step 안전망):
```bash
STATUS=$("$HELPER" finalize-run --expected-steps 5)  # architect/test-engineer/engineer/validator/pr-reviewer
```
미달 시 stderr WARN — inner step 누락 즉시 인지.

**clean 매트릭스**:
- `architect:MODULE_PLAN.enum == READY_FOR_IMPL`
- `test-engineer.enum == TESTS_WRITTEN`
- `engineer:IMPL.enum == IMPL_DONE`
- `validator:CODE_VALIDATION.enum == PASS`
- `pr-reviewer.enum == LGTM`

**branch prefix**: `feat/<batch-slug>` 또는 `chore/<batch-slug>`.

worktree 흡수 검사 / commit / PR / merge / 보고 모두 quick.md SSOT.

## Catastrophic 룰 정합

`docs/conveyor-design.md` §2.3 정합:
- §2.3.1 (pr-reviewer 직전 validator PASS) — Step 5 충족
- §2.3.3 (engineer/test-engineer 직전 plan READY) — Step 2 (또는 batch 자체 MODULE_PLAN_READY) 충족
- §2.3.4 / §2.3.5 — TD 본 시퀀스 안 없음 → 비대상

## 한계

- batch list 자동 chain X — `/impl-loop` 사용
- attempt counter 메인 자체 카운팅 (helper 미지원)
- POLISH cycle ≤ 2

## 참조

- `agents/architect/{module-plan,task-decompose}.md` · `agents/{test-engineer,engineer,pr-reviewer,validator}.md` · `agents/validator/code-validation.md`
- `docs/orchestration.md` §2.1 / §4
- `commands/quick.md` (가시성 / Step 7 / 공통 룰 SSOT) · `commands/product-plan.md` (TASK_DECOMPOSE 산출 = 본 skill 입력) · `commands/impl-loop.md` (multi-batch chain)
