---
name: impl
description: impl batch (architect TASK_DECOMPOSE 산출물) 1개를 받아 정식 impl 루프 (architect MODULE_PLAN → test-engineer → engineer → validator CODE_VALIDATION → pr-reviewer) 자동 진행하는 스킬. 사용자가 "구현해줘", "/impl <batch>", "이 batch 구현", "module plan 부터 진행", "impl 루프" 등을 말할 때 반드시 이 스킬을 사용한다. /product-plan 의 후속 — TASK_DECOMPOSE 의 batch list 1개씩 처리. /quick 보다 무거움 (test-engineer + CODE_VALIDATION 포함). dcNess 컨베이어 패턴 (Task tool + Agent + helper + 훅) 으로 동작.
---

# Impl Skill — per-batch 정식 impl 루프

> dcNess 컨베이어 패턴. /product-plan TASK_DECOMPOSE 산출 batch 1개를 정식 impl 루프로 처리. orchestration §2.1 정합.

## 언제 사용

- 사용자 발화: "구현해줘", "/impl", "이 batch 구현", "module plan", "정식 루프", "impl 루프"
- /product-plan 종료 후 batch list 1개씩 진행할 때
- 단순 한 줄 수정 (`/quick` 영역) 보다 *모듈 단위 + 테스트* 가 필요한 경우

## 언제 사용하지 않음

- 한 줄 / 한 함수 수정 → `/quick` (light path, test-engineer 생략)
- 새 기능 spec/design 단계 → `/product-plan`
- 다중 batch 자동 chain → `/impl-loop`
- impl batch 가 부재 (TASK_DECOMPOSE 안 거침) → `/quick` 또는 architect MODULE_PLAN 직접 호출

## 시퀀스 (orchestration.md §2.1)

```
architect MODULE_PLAN → test-engineer → engineer IMPL → validator CODE_VALIDATION → pr-reviewer
```

각 단계 결론 enum:
- architect MODULE_PLAN → `READY_FOR_IMPL` (또는 `SPEC_GAP_FOUND` / `TECH_CONSTRAINT_CONFLICT`)
- test-engineer → `TESTS_WRITTEN` (또는 `SPEC_GAP_FOUND`)
- engineer IMPL → `IMPL_DONE` (또는 `SPEC_GAP_FOUND` / `TESTS_FAIL` / `IMPLEMENTATION_ESCALATE`)
- validator CODE_VALIDATION → `PASS` (또는 `FAIL` / `SPEC_MISSING`)
- pr-reviewer → `LGTM` (또는 `CHANGES_REQUESTED`)

## yolo 모드 — keyword 트리거

`/quick` `/product-plan` 과 동일. 사용자 발화에 `yolo` / `auto` / `끝까지` / `막힘 없이` / `다 알아서` 시 yolo ON.

yolo 시:
- `SPEC_GAP_FOUND` → architect SPEC_GAP cycle 자동 진입 (단 cycle 한도 2 — 초과 시 사용자 위임)
- `TESTS_FAIL` → engineer 재시도 (attempt < 3)
- `CODE_VALIDATION FAIL` → engineer 재시도
- `CHANGES_REQUESTED` → engineer POLISH 자동 호출 (cycle 한도 2)
- `*_ESCALATE` / `AMBIGUOUS` → `auto-resolve` 매핑 적용 후 fallback (사용자 위임)

catastrophic 룰 (PreToolUse 훅 §2.3) hard safety 보존.

## 가시성 룰 — 매 Agent 호출 후 메인 text echo (필수)

`commands/quick.md` 와 동일 — Agent 호출 후 메인이 text reply 로 prose 핵심 5~12줄
echo (DCN-CHG-30-11). MODULE_PLAN / TESTS_WRITTEN / IMPL_DONE / CODE_VALIDATION /
LGTM 5 step 모두 적용.

## 절차 (Task tool + helper protocol)

### Step 0a — worktree 격리 진입 (선택, keyword 트리거)

`/quick` 동일 — `worktree` / `wt` / `격리` / `isolate` keyword 시:

```
EnterWorktree(name="impl-{ts_short}")
```

batch 단위 작업이라 worktree 격리 권장. 사용자 발화에 keyword 없어도 batch 작업 = src/ 다중 파일 수정 → conflict 위험 있을 시 메인이 자체 판단으로 권유 가능.

### Step 0b — run 시작 + 사용자 확인

사용자 발화에서 impl batch 경로 추출 (예: `docs/milestones/v0.2/epics/epic-01-greet-i18n/impl/01-greetings-data.md`).

```bash
HELPER="$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper"
RUN_ID=$("$HELPER" begin-run impl)
echo "[impl] run started: $RUN_ID"
```

사용자에게 한 번 확인:
```
[impl] 실행 설정
- batch: <batch 파일 경로>
- 이슈 제목 (한 줄, 70자 이내): <impl batch 의 ## 제목 줄 추출>
- 시퀀스: architect MODULE_PLAN → test-engineer → engineer IMPL → validator CODE_VALIDATION → pr-reviewer
- attempt 한도: engineer 3 / POLISH 2 / SPEC_GAP cycle 2

진행할까요?
```

### Step 1 — 5 sub-task 등록 (의무, skip 금지)

⚠️ **inline skip 금지 (DCN-CHG-30-12)**: 본 step 은 *반드시 수행*. begin-step → Agent 직행 X. Step 2~6 의 각 단계에서 TaskUpdate 가 본 task 를 in_progress / completed 변환하므로 사전 등록 필수.

**standalone 호출** (`/impl <batch>` 단독):
```
TaskCreate("architect: MODULE_PLAN")
TaskCreate("test-engineer: TDD attempt 0")
TaskCreate("engineer: IMPL")
TaskCreate("validator: CODE_VALIDATION")
TaskCreate("pr-reviewer: 검토")
```

**`/impl-loop` 안 inner 호출**: 호출자 (`/impl-loop`) 가 batch index `i` 와 함께 호출 시 prefix 컨벤션 — `b<i>.<agent>` (예: `b1.architect: MODULE_PLAN`). 자세한 컨벤션 = `commands/impl-loop.md` Step 2 참조. 본 skill standalone 시 prefix 없음.

### Step 2 — architect MODULE_PLAN (state-aware skip 가능)

#### 2.0 batch 마커 검사 (DCN-CHG-20260430-13)

batch 파일 안 `MODULE_PLAN_READY` 마커 검사:

```bash
if grep -q "MODULE_PLAN_READY" "<batch path>"; then
    echo "[impl] batch 자체에 MODULE_PLAN_READY 박힘 — architect MODULE_PLAN step skip"
    SKIP_MODULE_PLAN=true
else
    SKIP_MODULE_PLAN=false
fi
```

조건: `architect TASK_DECOMPOSE` (`/product-plan` Step 7) 가 batch 산출 시 ## 생성/수정 파일 / ## 인터페이스 / ## 의사코드 / ## 결정 근거 박고 마지막 줄에 `MODULE_PLAN_READY` 마커 박음 (`agents/architect/task-decompose.md` 컨벤션).

**SKIP_MODULE_PLAN=true 시**:
- TaskUpdate("architect: MODULE_PLAN", completed) + label 정정 → "skipped (batch 자체 MODULE_PLAN_READY)"
- batch 파일 자체를 MODULE_PLAN prose 로 사용 (architect-MODULE_PLAN.md 자리에 batch path symlink 또는 cp)
- catastrophic 훅 §2.3.3 (engineer 직전 plan READY 검사) 통과 위해 prose 종이 필요:
  ```bash
  cp "<batch path>" "$RUN_DIR/architect-MODULE_PLAN.md"
  ```
- → Step 3 (test-engineer) 직진

**SKIP_MODULE_PLAN=false 시**: 정상 호출 (아래 2.1).

근거: RWHarness 의 plan_loop 가 의도했던 "산출물 있으면 통과 + 없으면 다시 호출". dcness 가 분기 폐기로 일관성 회피하느라 잃었던 효율성 복원. 분기 추가 0 — skill prompt 의 grep 1줄 + 메인 자율.

#### 2.1 architect MODULE_PLAN 정상 호출 (마커 부재 시)

```
TaskUpdate("architect: MODULE_PLAN", in_progress)
```

```bash
"$HELPER" begin-step architect MODULE_PLAN
```

```
Agent(
  subagent_type="architect",
  mode="MODULE_PLAN",
  description="impl batch 파일: <batch path>. 모듈 plan 작성 — 생성/수정 파일 + 인터페이스 + 의사코드 + 결정 근거. 결론 enum: READY_FOR_IMPL / SPEC_GAP_FOUND / TECH_CONSTRAINT_CONFLICT."
)
```

```bash
ENUM=$("$HELPER" end-step architect MODULE_PLAN \
    --allowed-enums "READY_FOR_IMPL,SPEC_GAP_FOUND,TECH_CONSTRAINT_CONFLICT" \
    --prose-file /tmp/dcness-impl-mp.md)
```

advance: `READY_FOR_IMPL`. 그 외:
- `SPEC_GAP_FOUND` → architect SPEC_GAP 진입 (cycle < 2) 또는 사용자 위임
- `TECH_CONSTRAINT_CONFLICT` → 사용자 위임
- `AMBIGUOUS` → cascade

### Step 3 — test-engineer (TDD attempt 0)

```
TaskUpdate("test-engineer: TDD attempt 0", in_progress)
```

```bash
"$HELPER" begin-step test-engineer
```

PreToolUse 훅:
- §2.3.3 — `architect-MODULE_PLAN.md` 안 `READY_FOR_IMPL` 확인 → 통과.

```
Agent(
  subagent_type="test-engineer",
  description="MODULE_PLAN 완료. impl 의 ## 생성/수정 파일 경로만 사용 (src/ 읽기 금지 — catastrophic-prevention). 테스트 코드 작성. 결론 enum: TESTS_WRITTEN / SPEC_GAP_FOUND."
)
```

```bash
ENUM=$("$HELPER" end-step test-engineer \
    --allowed-enums "TESTS_WRITTEN,SPEC_GAP_FOUND" \
    --prose-file /tmp/dcness-impl-test.md)
```

advance: `TESTS_WRITTEN`. `SPEC_GAP_FOUND` 면 architect SPEC_GAP 또는 사용자 위임.

### Step 4 — engineer IMPL (attempt 0..3)

```
TaskUpdate("engineer: IMPL", in_progress)
```

```bash
"$HELPER" begin-step engineer IMPL
```

PreToolUse 훅:
- §2.3.3 — `architect-MODULE_PLAN.md` 안 `READY_FOR_IMPL` 확인 → 통과.

```
Agent(
  subagent_type="engineer",
  mode="IMPL",
  description="MODULE_PLAN + TESTS_WRITTEN 완료. 구현해줘. 결론 enum: IMPL_DONE / SPEC_GAP_FOUND / TESTS_FAIL / IMPLEMENTATION_ESCALATE."
)
```

```bash
ENUM=$("$HELPER" end-step engineer IMPL \
    --allowed-enums "IMPL_DONE,SPEC_GAP_FOUND,TESTS_FAIL,IMPLEMENTATION_ESCALATE" \
    --prose-file /tmp/dcness-impl-impl.md)
```

advance: `IMPL_DONE`. 그 외:
- `SPEC_GAP_FOUND` → architect SPEC_GAP cycle (한도 2) 또는 사용자 위임
- `TESTS_FAIL` → engineer 재시도 (attempt < 3, 재호출 시 attempt 카운터 ↑)
- `IMPLEMENTATION_ESCALATE` → 사용자 위임
- `AMBIGUOUS` → cascade

### Step 4.5 — stories.md / backlog.md 체크박스 동기화 (DCN-CHG-20260430-14)

engineer IMPL 의 `IMPL_DONE` 직후, validator 진입 *전* 메인이 직접 mechanical edit 수행. agent 위임 X (engineer 는 `src/**` 만, architect 는 spec doc 만 — stories.md/backlog.md 체크박스는 도메인 외).

근거: 글로벌 `~/.claude/CLAUDE.md` "태스크 완료 → stories.md 체크. 에픽 완료 → backlog.md 체크" 룰의 *완료* 시점 = IMPL 완료 시점. impl.md 시퀀스에 step 으로 박지 않으면 매 batch 마다 누락.

#### 4.5.1 batch → epic 경로 추출

batch 파일 경로에서 epic dir 추출:
```bash
# 예: docs/milestones/v0.3/epics/epic-01-greet-lang-apply/impl/01-*.md
EPIC_DIR=$(dirname $(dirname "<batch path>"))
STORIES_FILE="$EPIC_DIR/stories.md"
BACKLOG_FILE="$(dirname $(dirname $EPIC_DIR))/../backlog.md"  # milestone root + ..
```

(실제 경로는 milestone 구조에 따라 메인이 자체 판단 — `find` / `Glob` 으로 stories.md 위치 확인 후 진행.)

#### 4.5.2 stories.md 체크박스 갱신

batch 가 다룬 Story 의 `[ ]` → `[x]`. batch 파일 안 `## 관련 Story` 또는 `## 적용 범위` 등의 메타로 어느 Story 인지 식별. 없으면 batch 파일명/제목으로 매칭.

```
Edit(STORIES_FILE, "- [ ] Story X: ...", "- [x] Story X: ...")
```

batch 가 1 Story 의 일부 task 만 처리한 경우 → 해당 task 만 `[x]`. Story 하위 task 모두 `[x]` 면 Story 자체도 `[x]`.

#### 4.5.3 backlog.md 체크박스 갱신 (epic 완료 시만)

stories.md 의 모든 Story 가 `[x]` 면 backlog.md 의 epic 라인도 `[x]`:

```
if all stories checked:
    Edit(BACKLOG_FILE, "- [ ] epic-NN-...", "- [x] epic-NN-...")
```

부분 진행이면 backlog.md 손대지 않음.

#### 4.5.4 가시성

```
[impl] step 4.5 — stories.md / backlog.md sync
- stories.md: Story 1 [ ] → [x] (8 task 모두 완료)
- backlog.md: epic-01 라인 [ ] → [x] (epic 전체 Story 완료)
```

다음 step (validator) 은 src/ 만 검증 — stories.md 변경 무시. pr-reviewer 가 코드 + doc 같이 검토 (잘못 체크된 항목 catch).

### Step 5 — validator CODE_VALIDATION

```
TaskUpdate("validator: CODE_VALIDATION", in_progress)
```

```bash
"$HELPER" begin-step validator CODE_VALIDATION
```

```
Agent(
  subagent_type="validator",
  mode="CODE_VALIDATION",
  description="engineer IMPL 완료. 코드 검증해줘. 결론 enum: PASS / FAIL / SPEC_MISSING."
)
```

```bash
ENUM=$("$HELPER" end-step validator CODE_VALIDATION \
    --allowed-enums "PASS,FAIL,SPEC_MISSING" \
    --prose-file /tmp/dcness-impl-cv.md)
```

advance: `PASS`. 그 외:
- `FAIL` → engineer 재시도 (attempt < 3)
- `SPEC_MISSING` → architect SPEC_GAP

### Step 6 — pr-reviewer

```
TaskUpdate("pr-reviewer: 검토", in_progress)
```

```bash
"$HELPER" begin-step pr-reviewer
```

PreToolUse 훅:
- §2.3.1 — `validator-CODE_VALIDATION.md` 안 `PASS` 확인 → 통과.

```
Agent(
  subagent_type="pr-reviewer",
  description="engineer IMPL + validator CODE_VALIDATION PASS. 검토. 결론 enum: LGTM / CHANGES_REQUESTED."
)
```

```bash
ENUM=$("$HELPER" end-step pr-reviewer \
    --allowed-enums "LGTM,CHANGES_REQUESTED" \
    --prose-file /tmp/dcness-impl-pr.md)
```

advance: `LGTM`. `CHANGES_REQUESTED` 면 engineer POLISH 호출 (cycle 한도 2) 또는 사용자 위임.

#### POLISH 사이드 사이클 (CHANGES_REQUESTED)

```
Agent(
  subagent_type="engineer",
  mode="POLISH",
  description="pr-reviewer CHANGES_REQUESTED. 지적 사항 반영. 결론 enum: POLISH_DONE / IMPLEMENTATION_ESCALATE."
)
```

POLISH_DONE 후 pr-reviewer 재호출. cycle 한도 2.

### Step 7 — finalize-run + clean 자동 commit/PR (또는 caveat 확인)

`/quick` 의 Step 7 와 동일 패턴. 차이점은 enum 매트릭스만:

#### 7.1 helper 로 status 집계

```bash
STATUS=$("$HELPER" finalize-run)
"$HELPER" end-run
echo "$STATUS"
```

#### 7.2 clean 판정

다음 모두 충족 → **clean**:
- `has_ambiguous == false`
- `has_must_fix == false`
- step enum 매트릭스:
  - `architect:MODULE_PLAN.enum == READY_FOR_IMPL`
  - `test-engineer.enum == TESTS_WRITTEN`
  - `engineer:IMPL.enum == IMPL_DONE`
  - `validator:CODE_VALIDATION.enum == PASS`
  - `pr-reviewer.enum == LGTM`
- git 안전 가드 (`/quick` Step 7.2 동일)

#### 7a — Clean 자동 commit/PR

`/quick` Step 7a 와 동일. branch prefix = `feat/<batch-slug>` 또는 `chore/<batch-slug>` (impl 분류에 따라).

#### 7b — Caveat 확인

`/quick` Step 7b 와 동일.

worktree 처리도 동일 — squash 흡수 검사 자동.

## AMBIGUOUS 처리 — 매 step 동일

`/quick` 의 cascade 패턴 정합:
1. 재호출 1회
2. 재호출도 AMBIGUOUS → 사용자 위임 (yolo 시 auto-resolve fallback)

## Catastrophic 룰 — 자동 정합

본 시퀀스는 §2.3 4룰 + §2.3.5 정합:
- §2.3.1 (pr-reviewer 직전 validator PASS) — Step 5 CODE_VALIDATION PASS 충족
- §2.3.3 (engineer/test-engineer 직전 plan READY) — Step 2 MODULE_PLAN READY_FOR_IMPL 충족
- §2.3.4 (architect SD/TD 직전 PRD 검토) — MODULE_PLAN 은 SD/TD 아님 → 비대상
- §2.3.5 (TD 직전 DESIGN_REVIEW_PASS) — TD 본 시퀀스 안 없음 → 비대상

PreToolUse 훅이 매 Agent 직전 자동 검사. 시퀀스 정합 시 통과.

## 한계 / 후속

- **batch list 자동 chain X** — 본 skill 은 batch 1개 처리. multi-batch 자동 chain 은 `/impl-loop` (별도 skill).
- **attempt counter 메인 추적** — engineer 재시도 횟수 메인이 자체 카운팅 (현재 helper 미지원, 향후 follow-up 가능).
- **POLISH cycle 한도 2** — 초과 시 사용자 위임.

## 참조

- `agents/architect/module-plan.md` — MODULE_PLAN system prompt
- `agents/test-engineer.md` — test-engineer system prompt
- `agents/engineer.md` — engineer (IMPL / POLISH)
- `agents/validator/code-validation.md` — CODE_VALIDATION
- `agents/pr-reviewer.md` — pr-reviewer
- `docs/orchestration.md` §2.1 — 정식 impl 루프
- `docs/orchestration.md` §4 — agent 별 결론 enum 결정표
- `docs/conveyor-design.md` — Task tool + helper + 훅
- `commands/quick.md` — light path (test-engineer 생략, BUGFIX_VALIDATION 사용)
- `commands/product-plan.md` — spec/design (TASK_DECOMPOSE 산출 = 본 skill 입력)
- `commands/impl-loop.md` — multi-batch sequential auto chain (별도 skill)
