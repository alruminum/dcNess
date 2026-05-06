---
name: impl
description: impl task (architect TASK_DECOMPOSE 산출물) 1개를 받아 정식 impl 루프 (architect MODULE_PLAN → test-engineer → engineer → validator CODE_VALIDATION → pr-reviewer) 자동 진행하는 스킬. 사용자가 "구현해줘", "/impl <task>", "이 task 구현", "module plan 부터 진행", "impl 루프" 등을 말할 때 반드시 이 스킬을 사용한다. /product-plan 의 후속 — TASK_DECOMPOSE 의 task list 1개씩 처리. /quick 보다 무거움 (test-engineer + CODE_VALIDATION 포함).
---

# Impl Skill

## Loop
`impl-task-loop` ([orchestration.md §2.1 / §4.3](../docs/plugin/orchestration.md)).
UI 디자인 mid-loop 필요 시 → `impl-ui-design-loop` (orchestration §4.4) 자동 전환.

## Inputs (메인이 사용자에게 받아야 할 정보)
- task 경로 (필수, 예: `docs/milestones/v0.2/epics/epic-01-*/impl/01-*.md`)
- 이슈 번호 (있으면)
- attempt 한도 확인 (engineer 3 / POLISH 2 / SPEC_GAP cycle 2 — 기본값)

## 비대상 (다른 skill 추천)
- 한 줄 / 작은 버그 → `/quick` (`quick-bugfix-loop`)
- spec / design 단계 → `/product-plan` (`feature-build-loop`)
- 다중 task 자동 chain → `/impl-loop`
- task 부재 (계획 X) → `/quick` 또는 `/product-plan`

## State-aware skip (DCN-30-13)
task 파일 끝에 `MODULE_PLAN_READY` 마커 박혀있으면 Step 2 (architect:MODULE_PLAN) skip. 상세 = orchestration §4.3 풀스펙.

## 후속 라우팅
- 본 loop clean → 자동 commit/PR (branch prefix = orchestration §4.3 decision rule: feat/chore/fix)
- caveat → 사용자 결정 (수동 7b)
- multi-task chain 필요 → `/impl-loop`

## 사전 read (skill 진입 즉시)
`docs/plugin/loop-procedure.md` + `docs/plugin/orchestration.md` §4.3 + `docs/plugin/handoff-matrix.md` + `docs/plugin/issue-lifecycle.md` read 후 진행.

## Pre-flight gate (Step 0 직후)
[`docs/plugin/issue-lifecycle.md`](../docs/plugin/issue-lifecycle.md) §6 매치 강제 — 부모 epic stories.md 상단 `**GitHub Epic Issue:** [#\d+]` 또는 `미등록 (사유: …)` 매치 0건 시 즉시 STOP + 사용자 보고. silent skip 금지.

## 절차
[`docs/plugin/loop-procedure.md`](../docs/plugin/loop-procedure.md) §1~§6 + [`docs/plugin/orchestration.md`](../docs/plugin/orchestration.md) §4.3 (`impl-task-loop` 풀스펙, Step 4.5 stories sync 포함) 따름. UI 감지 시 §4.4 (`impl-ui-design-loop`).
