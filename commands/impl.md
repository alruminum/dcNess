---
name: impl
description: impl task (feature-build-loop §4.2 Step 7 architect MODULE_PLAN × N 산출물) 1개를 받아 정식 impl 루프 (default = test-engineer → engineer → validator CODE_VALIDATION → pr-reviewer · fallback = architect MODULE_PLAN 선두 추가) 자동 진행하는 스킬. 사용자가 "구현해줘", "/impl <task>", "이 task 구현", "impl 루프" 등을 말할 때 반드시 이 스킬을 사용한다. /product-plan 의 후속 — feature-build-loop 가 `impl/NN-*.md` 본문 detail 까지 채운 산출물의 task list 1개씩 처리. /quick 보다 무거움 (test-engineer + CODE_VALIDATION 포함).
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

## 진입 모드 — default vs fallback (위치 도장)
- task 경로 매치 + 정식 위치 (`docs/milestones/v\d+/epics/epic-\d+-*/impl/\d+-*.md`) 파일 존재 → **default**: test-engineer 직진 (architect MODULE_PLAN skip).
- 매치 실패 / 파일 부재 → **fallback**: architect MODULE_PLAN 1번 호출 후 test-engineer 진입.
- 근거: feature-build-loop §4.2 의 Step 7 (MODULE_PLAN × N) 이 정식 위치 impl 파일 본문 detail 까지 채움. 정식 경로 + 파일 존재 = 통과 보장. (옛 `MODULE_PLAN_READY` 마커 grep 룰 폐기 — 위치 자체가 도장.)

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
