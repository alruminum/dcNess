---
name: product-plan
description: 새 기능 / PRD 변경 / 큰 기획을 받아 product-planner → plan-reviewer → ux-architect → validator UX_VALIDATION → architect SYSTEM_DESIGN → validator DESIGN_VALIDATION → architect TASK_DECOMPOSE 시퀀스로 spec/design 단계까지 진행하는 스킬. 사용자가 "기획자야", "새 기능", "피쳐 추가", "이런 기능이 필요할 것 같아", "기획해줘", "프로덕트 플랜", "/product-plan" 등을 말할 때 반드시 이 스킬을 사용한다. 구현 진입은 별도 (`/quick` 또는 `/impl` / `/impl-loop`).
---

# Product Plan Skill

## Loop
`feature-build-loop` ([orchestration.md §3.1 / §4.2](../docs/orchestration.md)).

## Inputs (메인이 사용자에게 받아야 할 정보)
- 요구사항 / 문제 정의 (한 단락)
- 사용자 시나리오 (Who / When / What / Why)
- 제약 (기술 / 일정 / 리소스, 있으면)
- 우선순위 (M0 / M1 / nice-to-have, 있으면)
- 변경인지 신규인지 (PRD 변경 시 어떤 부분)

명확화 안 되면 product-planner 호출 X (`CLARITY_INSUFFICIENT` 회피 — 메인이 사전 정형화).

## 비대상 (다른 skill 추천)
- 버그 → `/qa` (`qa-triage`)
- 한 줄 수정 → `/quick` (`quick-bugfix-loop`)
- 디자인만 → `/ux` (`ux-design-stage`)

## 후속 라우팅
- `READY_FOR_IMPL` → `/impl-loop` (multi-task) 또는 `/impl` (per-task) 또는 architect MODULE_PLAN 직접
- `PRODUCT_PLAN_UPDATED` → plan-reviewer skip + ux-architect 직행 (orchestration §4.2 분기)
- `UX_REFINE_READY` → `ux-refine-stage` 진입 (`/ux`)
- escalate enum → 사용자 위임 (orchestration §4.2 분기 표 참조)

## 사전 read (skill 진입 즉시)
`docs/loop-procedure.md` + `docs/orchestration.md` §2~§3 + §4.2 + `docs/handoff-matrix.md` read 후 진행.

## 절차
[`docs/loop-procedure.md`](../docs/loop-procedure.md) §1~§6 + [`docs/orchestration.md`](../docs/orchestration.md) §4.2 (`feature-build-loop` 풀스펙) 따름. 본 파일은 input 명세 + 라우팅만.
