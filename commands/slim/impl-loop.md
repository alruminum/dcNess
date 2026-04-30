---
name: impl-loop
description: impl batch list (architect TASK_DECOMPOSE 산출물) 를 순차 자동 chain 으로 처리하는 스킬. 사용자가 "전부 구현", "/impl-loop", "batch 다 돌려", "epic 전체 구현", "/product-plan 후 자동", "끝까지 구현" 등을 말할 때 반드시 이 스킬을 사용한다. 각 batch 마다 /impl skill 의 정식 루프를 실행 + clean run 만 자동 진행 + caveat 시 사용자 위임. /product-plan 종료 후 N 개 batch 한 번에 처리하고 싶을 때.
---

# Impl Loop Skill — multi-batch sequential auto chain

> `/impl` 의 multi-batch 래퍼. 공통 룰 SSOT = `commands/quick.md`. inner /impl 시퀀스 = `commands/impl.md`.

## 사용

- 트리거: "/impl-loop", "전부 구현", "다 돌려", "epic 전체", "끝까지 구현"
- 비대상: batch 1개 → `/impl` · 한 줄 → `/quick` · spec/design → `/product-plan`

## 핵심 동작

각 batch → `/impl` 시퀀스 (architect MODULE_PLAN → test-engineer → engineer → validator CODE_VALIDATION → pr-reviewer). clean → 자동 commit/PR + 다음 batch. caveat → 멈춤 + 사용자 위임.

## 가시성 (SSOT = quick.md)

inner /impl 의 5 step 모두 `b<i>.<agent>` prefix 로 의무 echo (의무 템플릿 = quick.md). loop level 추가:
- 매 batch 시작/종료 시 `[impl-loop] batch i/N — <status>` 1줄
- caveat 멈춤 시 전체 진행 요약 echo (처리 / 남은 / 멈춤 사유)

inner echo 5 의무 ✓ 안 되면 다음 batch 진입 금지.

## 절차

### Step 0 — batch list 추출 + run 시작

```bash
# TASK_DECOMPOSE 산출 dir 패턴
BATCH_LIST=$(ls docs/milestones/v*/epics/epic-*/impl/*.md 2>/dev/null | sort)
echo "발견된 batch:"; echo "$BATCH_LIST"

HELPER="$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper"
RUN_ID=$("$HELPER" begin-run impl-loop)
echo "[impl-loop] run started: $RUN_ID"
```

또는 사용자가 list 직접 명시. 사용자 확인 (batch N 개 / 시퀀스 / 분기 정책 / yolo 여부 / 진행).

### Step 1 — outer task 등록 (batch 별 1개)

```
for i in 1..N:
  TaskCreate(f"impl-{i}: <batch 파일명 + 짧은 제목>")
```

### Step 2 — 각 batch 순차 처리 (inner sub-task 등록 의무)

⚠️ **inline skip 금지 (DCN-CHG-30-12)**: 각 batch 진입 시 `/impl` 의 5 sub-task 의무 등록. inline begin-step → Agent 직행 X.

```
for i in 1..N:
  TaskUpdate(f"impl-{i}: ...", in_progress)
  INNER_RUN=$("$HELPER" begin-run "impl-batch-$i")
  echo "[impl-loop] batch $i/$N → INNER_RUN=$INNER_RUN"

  # inner 5 sub-task 의무 등록 (b{i}. prefix)
  TaskCreate(f"b{i}.architect: MODULE_PLAN")
  TaskCreate(f"b{i}.test-engineer: TDD attempt 0")
  TaskCreate(f"b{i}.engineer: IMPL")
  TaskCreate(f"b{i}.validator: CODE_VALIDATION")
  TaskCreate(f"b{i}.pr-reviewer: 검토")

  # /impl Step 2~7 진행 (commands/impl.md 참조)
  if clean:
    자동 commit/PR (graceful degrade) → INNER_RUN end
    TaskUpdate(f"impl-{i}: ...", completed)
  else:
    Step 2.5 (caveat 멈춤)
```

가시성 표시 형식:
```
◼ impl-1: epic-01 greet lang
◻ impl-2: epic-02 calc.multiply
◼ b1.architect: MODULE_PLAN     ← 현재 batch 1 inner step
◻ b1.test-engineer: TDD attempt 0
◻ b1.engineer: IMPL
◻ b1.validator: CODE_VALIDATION
◻ b1.pr-reviewer: 검토
```

### Step 2.5 — caveat 멈춤

```
[impl-loop] batch <i> 멈춤 — caveat
- batch: <경로> · caveat: <FAIL / AMBIGUOUS / MUST FIX>
- 처리: <i-1>/<N> · 남은: <list>

옵션:
1. 사용자 batch <i> 수동 처리 후 /impl-loop 재호출 (남은 batch 인자)
2. yolo + cycle 한도 내 재시도 (yolo ON 일 때만)
3. 종료
```

### Step 3 — 전체 완료 시 보고

```
[impl-loop] 전체 완료 ✅
- run_id: $RUN_ID · 처리: <N>/<N>
- inner run_id + 변경 + PR URL

다음 (선택):
- 추가 batch → /impl-loop 재호출
- epic 전체 완료 → /product-plan 다음 epic
```

## yolo 모드

`/impl` yolo (commands/quick.md SSOT) + multi-batch 추가:
- 각 batch caveat 도 `auto-resolve` 매핑 적용
- 매 3 batch 또는 1시간마다 progress 보고 (장시간 무인 안전)

## 한계

- batch 의존성 자동 판단 X (v1 = 무조건 직렬, list 순서가 의존 표현)
- 재시도 5회 후 실패 시 그 시점까지 commit 보존 (rollback X — 안전 가드)
- inner run dir 분리, outer 는 batch 진행 메타만
- multi-batch resume 미구현 — caveat 후 재실행 시 처음부터, 단 commit 된 batch 는 MODULE_PLAN_READY 자가 검출 (impl.md Step 2.0) 로 skip

## 참조

- `commands/impl.md` (inner 단일 batch 처리) · `commands/product-plan.md` (TASK_DECOMPOSE 산출 = 입력) · `commands/quick.md` (가시성 / yolo / 공통 룰 SSOT)
- `docs/orchestration.md` §2.1 / §3.1
