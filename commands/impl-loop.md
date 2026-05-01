---
name: impl-loop
description: impl batch list (architect TASK_DECOMPOSE 산출물) 를 순차 자동 chain 으로 처리하는 스킬. 사용자가 "전부 구현", "/impl-loop", "batch 다 돌려", "epic 전체 구현", "/product-plan 후 자동", "끝까지 구현" 등을 말할 때 반드시 이 스킬을 사용한다. 각 batch 마다 /impl 의 정식 루프 실행 + clean run 만 자동 진행 + caveat 시 사용자 위임. /product-plan 종료 후 N 개 batch 한 번에 처리하고 싶을 때.
---

# Impl Loop Skill

## Loop
`impl-batch-loop × N` ([loop-catalog.md §10](../docs/loop-catalog.md) — 다중 batch chain).
inner = `impl-batch-loop` (catalog §3) per batch.

## Inputs (메인이 사용자에게 받아야 할 정보)
- batch list 또는 epic 경로 (예: `docs/milestones/v0.2/epics/epic-01-*/impl/*.md` glob)
- 진행 정책 — clean 자동 / caveat 멈춤 (default) 또는 yolo (catalog §3 sub_cycles 자동 시도)
- attempt 한도 확인 (`/impl` 와 동일 default)

## 비대상 (다른 skill 추천)
- batch 1개 → `/impl`
- 한 줄 → `/quick`
- spec / design → `/product-plan`

## Outer / inner 컨벤션 (DCN-30-12)
- outer task: `impl-<i>: <batch 파일명>` (batch list 길이 만큼 등록)
- inner sub-task: `b<i>.<agent>` prefix 의무 (loop-procedure.md §2 inner skip 금지)

## 후속 라우팅
- 각 batch clean → 자동 7a + 다음 batch
- caveat → 멈춤 + 사용자 위임 (재호출 또는 수동 처리)
- 전체 완료 → 보고 (처리 N/N + 각 PR URL)

## 사전 read (skill 진입 즉시)
`docs/loop-procedure.md` + `docs/loop-catalog.md` §3 + §10 + `docs/handoff-matrix.md` read 후 진행.

## 절차
[`docs/loop-procedure.md`](../docs/loop-procedure.md) §1~§6 + [`docs/loop-catalog.md`](../docs/loop-catalog.md) §3 (inner) + §10 (chain 정책) 따름.

## 한계
- batch 의존성 자동 판단 X (v1 = 무조건 직렬, list 순서 = 의존 표현)
- multi-batch resume 미구현 — caveat 후 재실행 시 처음부터 (단 commit 된 batch 는 `MODULE_PLAN_READY` 자가 검출로 Step 2 skip)
