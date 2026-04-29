---
name: impl-loop
description: impl batch list (architect TASK_DECOMPOSE 산출물) 를 순차 자동 chain 으로 처리하는 스킬. 사용자가 "전부 구현", "/impl-loop", "batch 다 돌려", "epic 전체 구현", "/product-plan 후 자동", "끝까지 구현" 등을 말할 때 반드시 이 스킬을 사용한다. 각 batch 마다 /impl skill 의 정식 루프를 실행 + clean run 만 자동 진행 + caveat 시 사용자 위임. /product-plan 종료 후 N 개 batch 한 번에 처리하고 싶을 때.
---

# Impl Loop Skill — multi-batch sequential auto chain

> dcNess 컨베이어 패턴. `/impl` 의 multi-batch 래퍼 — batch list 1~N 개 순차 처리. clean 시 자동 진행 + caveat 시 멈춤.

## 언제 사용

- 사용자 발화: "/impl-loop", "전부 구현", "다 돌려", "epic 전체", "끝까지 구현", "/product-plan 후 자동"
- /product-plan TASK_DECOMPOSE 산출 batch N 개 한 번에 처리할 때
- yolo 모드 + 사용자가 잠시 자리 비울 때 (각 batch clean 진행 시 무인)

## 언제 사용하지 않음

- batch 1 개만 처리 → `/impl` (단일 batch)
- batch 별로 사용자가 검토하고 싶음 → `/impl` 1개씩 수동 호출
- 한 줄 / 한 함수 수정 → `/quick`
- 새 기능 spec/design 단계 → `/product-plan`

## 핵심 동작

각 batch 에 대해 `/impl` skill 의 시퀀스 (architect MODULE_PLAN → test-engineer → engineer → validator CODE_VALIDATION → pr-reviewer) 실행. clean 시 자동 commit/PR + 다음 batch 진행. caveat (FAIL / AMBIGUOUS / MUST FIX) 시 멈춤 + 사용자 위임.

## 가시성 룰 — 매 batch 의 inner /impl 진행 시 echo

각 batch 의 inner /impl 은 자기 가시성 룰 적용 (5 step 별 5~12줄 echo). loop level 추가:
- 매 batch 시작/종료 시 batch progress 1줄 echo (`[impl-loop] batch i/N — <status>`)
- caveat 멈춤 시 *전체 진행 요약* echo (몇 batch 처리 / 남은 batch / 멈춤 사유)

자세한 룰은 `commands/quick.md` "가시성 룰" 참조.

## 절차

### Step 0 — batch list 추출 + 사용자 확인

사용자 발화 또는 architect TASK_DECOMPOSE 산출물에서 batch 파일 list 추출:

```bash
# 예시 — TASK_DECOMPOSE prose 가 박은 임프로젝트 디렉토리 패턴
BATCH_LIST=$(ls docs/milestones/v*/epics/epic-*/impl/*.md 2>/dev/null | sort)
echo "발견된 batch:"
echo "$BATCH_LIST"
```

또는 사용자가 직접 list 명시 (예: `/impl-loop epic-01/01.md epic-01/02.md`).

```bash
HELPER="$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper"
RUN_ID=$("$HELPER" begin-run impl-loop)
echo "[impl-loop] run started: $RUN_ID"
```

사용자에게:
```
[impl-loop] 실행 설정
- 처리할 batch (N 개):
  1. <batch 1 경로>
  2. <batch 2 경로>
  ...
- 시퀀스: 각 batch 마다 /impl 의 정식 루프 (architect MODULE_PLAN → test-engineer → engineer IMPL → validator CODE_VALIDATION → pr-reviewer)
- 분기 정책:
  - clean → 자동 commit/PR + 다음 batch 진행
  - caveat → 멈춤 + 사용자 위임
- yolo 모드: <yes/no — 사용자 발화 keyword 검출 결과>

진행할까요?
```

### Step 1 — task 등록 (batch 별 1개)

```
for i in 1..N:
  TaskCreate(f"impl-{i}: <batch 파일명 + 짧은 제목>")
```

각 batch = 1 외부 task. 각 batch 안의 5 sub-task 는 batch 진행 시 `/impl` 가 만듦 — 외부 시각엔 배 N 개 task progress 보임.

### Step 2 — 각 batch 순차 처리 (1 부터 N 까지)

```
for batch in BATCH_LIST:
  TaskUpdate(f"impl-{i}: ...", in_progress)
  → /impl skill 의 Step 1~7 시퀀스 호출 (인자 = batch path, 단 begin-run 은 본 outer run 안 별도 inner run 으로):

      INNER_RUN=$("$HELPER" begin-run "impl-batch-$i")
      → /impl 의 Step 1~7 (batch 1개 처리)
      → /impl Step 7 의 finalize-run 으로 status 받음
      → clean 판정:
          - clean → 자동 commit/PR (graceful degrade) → INNER_RUN end
          - caveat → 사용자 위임 → 본 loop 멈춤

  TaskUpdate(f"impl-{i}: ...", completed) # clean 만
```

### Step 2.5 — caveat 발생 시 멈춤

clean 아닌 batch 만나면:

```
[impl-loop] batch <i> 에서 멈춤 — caveat 발생
- batch: <batch 경로>
- caveat: <FAIL / AMBIGUOUS / MUST FIX 등>
- 처리한 batch: <i-1>/<N>
- 남은 batch: <list>

옵션:
1. 사용자가 batch <i> 수동 처리 후 `/impl-loop` 재호출 (남은 batch 만 인자로)
2. yolo + cycle 한도 내 재시도 (yolo ON 일 때만)
3. 종료
```

사용자 응답 받으면 그에 따라.

### Step 3 — 모든 batch 완료 시 보고

```
[impl-loop] 전체 완료 ✅
- run_id: $RUN_ID
- 처리한 batch: <N>/<N>
- 각 batch 의 inner run_id + 변경 파일 + PR URL (생성된 경우)

prose 종이 트리: <main repo>/.claude/harness-state/.sessions/{sid}/runs/$RUN_ID/
                 + 각 inner run dir 들

다음 단계 (선택):
- 추가 batch 가 발생하면 /impl-loop 재호출
- 또는 epic 전체 완료 시 /product-plan 다음 epic 진입
```

## yolo 모드

`/impl` 의 yolo 와 동일 + multi-batch 한정 추가 동작:
- 각 batch 의 caveat 도 yolo 매트릭스 적용 — `auto-resolve` 권장 액션 자동 적용
- 단 매 3 batch 마다 또는 1 시간마다 사용자에게 progress 보고 (장시간 무인 운영 시 안전)

## 한계 / 후속

- **batch 간 의존성 처리 X (v1)** — batch 들이 병렬 가능한지, 직렬 의존인지 자동 판단 X. v1 = 무조건 직렬. 사용자가 list 순서로 의존 표현.
- **재시도 시 cycle 누적** — batch B 에서 재시도 5회 후 실패 → 그 시점까지의 commit 들은 보존. rollback X (안전 가드).
- **inner run 의 .steps.jsonl 분리** — 각 batch 가 자기 inner run dir 사용. outer run dir 엔 batch 진행 메타만 (별도 jsonl).
- **multi-batch resume 미구현 (v1)** — caveat 멈춤 후 재실행 시 처음부터 다시. 단 이미 commit 된 batch 는 architect MODULE_PLAN 단계 자가 검출 (SPEC_GAP_FOUND 분기) 로 skip 가능.

## 참조

- `commands/impl.md` — 단일 batch 처리 (본 skill 의 inner)
- `commands/product-plan.md` — TASK_DECOMPOSE 산출 batch list 출처
- `docs/orchestration.md` §2.1 — 정식 impl 루프
- `docs/orchestration.md` §3.1 — /product-plan → /impl-loop 진입 흐름
- `commands/quick.md` — 한 줄 수정 (light path, multi-batch 무관)
