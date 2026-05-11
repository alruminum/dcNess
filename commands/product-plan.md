---
name: product-plan
description: 새 기능 / PRD 변경 / 큰 기획을 받아 product-planner → plan-reviewer → ux-architect (5 카테고리 self-check) → system-architect (self-check + impl 목차 표 산출) → architecture-validator (Placeholder Leak + Spike Gate) → module-architect × N (impl 본문 detail) 시퀀스로 spec/design 단계까지 진행하는 스킬. 사용자가 "기획자야", "새 기능", "피쳐 추가", "이런 기능이 필요할 것 같아", "기획해줘", "프로덕트 플랜", "/product-plan" 등을 말할 때 반드시 이 스킬을 사용한다. 구현 진입은 별도 (`/impl` / `/impl-loop`).
---

# Product Plan Skill

## Loop
`feature-build-loop` ([orchestration.md §3.1 / §4.2](../docs/plugin/orchestration.md)).

## Inputs (메인이 사용자에게 받아야 할 정보)
- 요구사항 / 문제 정의 (한 단락)
- 사용자 시나리오 (Who / When / What / Why)
- 제약 (기술 / 일정 / 리소스, 있으면)
- 우선순위 (M0 / M1 / nice-to-have, 있으면)
- 변경인지 신규인지 (PRD 변경 시 어떤 부분)

명확화 안 되면 product-planner 호출 X (`CLARITY_INSUFFICIENT` 회피 — 메인이 사전 정형화).

## Pre-Check Trigger (Spike Pre-Check)

사용자 입력 또는 1차 정형화 결과에 다음 *spike 의심 신호* 1개 이상 포함 시 product-planner 호출 *전* plan-reviewer 를 `PRE_CHECK` 모드로 1회 먼저 호출 ([`agents/plan-reviewer.md`](../agents/plan-reviewer.md) "호출 모드" 섹션):

- **외부 의존 명시**: 외부 모델 / API / SDK 이름 (예: "OpenVoice", "ElevenLabs", "Replicate API", "Suno API", "Apple IAP", "Google Cloud TTS")
- **조건부 약속 패턴**: "M0 에서 검증" / "마일스톤 0 결정" / "후보 N개 비교 후 선정" / "X 안 되면 Y 로 fallback"
- **사용자 의문문**: "이거 진짜 되나?", "X 가 Y 를 지원하는지", "API 키 / 쿼터 확인 필요"

플로우:
- `PLAN_REVIEW_PASS` → product-planner 호출. 검증 결과 (`EXTERNAL_VERIFIED` 섹션) 를 prompt 에 첨부.
- `PLAN_REVIEW_FAIL` → 사용자에게 결과 보고 + 입력 재정리 요청. product-planner 호출 보류.
- `PLAN_REVIEW_ESCALATE` → 사용자 위임 (WebFetch 차단 / 공식 문서 부재 / 권한 부족).

신호 없으면 pre-call 스킵 — 기존 시퀀스 그대로 (product-planner 직접 호출).

## 비대상 (다른 skill 추천)
- 버그 → `/qa` (`qa-triage`)
- 한 줄 수정 / 버그픽스 → `/qa` (분류 후 impl-task-loop fallback)
- 디자인만 → `/ux` (`ux-design-stage`)

## 후속 라우팅
- `READY` → `/impl-loop` (multi-task) 또는 `/impl` (per-task) 또는 module-architect 직접
- `PRODUCT_PLAN_UPDATED` → plan-reviewer 변경분 재심사 (skip 분기 폐기 — 변경의 성격 무관 항상 호출) → PASS 시 ux-architect
- `UX_REFINE_READY` → `ux-refine-stage` 진입 (`/ux`)
- `PLAN_REVIEW_ESCALATE` → 사용자 위임 (외부 검증 불가 / 권한 경계 밖 정보 / 동일 finding 반복 / URL 부재 PASS 시도)
- 기타 escalate enum → 사용자 위임 (orchestration §4.2 분기 표 참조)

## 사전 read (skill 진입 즉시)
`docs/plugin/loop-procedure.md` + `docs/plugin/orchestration.md` §2~§3 + §4.2 + `docs/plugin/handoff-matrix.md` read 후 진행.

## 워크트리 (X)
`/product-plan` 은 워크트리 자동 진입 안 함. 기획·설계는 동시 다중 batch 충돌 회피 목적 부재 — 메인 working tree 에서 별 branch 따고 직접 진행. 자세히 = [`docs/plugin/loop-procedure.md`](../docs/plugin/loop-procedure.md) §1.1.

## 절차
[`docs/plugin/loop-procedure.md`](../docs/plugin/loop-procedure.md) §1~§6 + [`docs/plugin/orchestration.md`](../docs/plugin/orchestration.md) §4.2 (`feature-build-loop` 풀스펙) 따름. 본 파일은 input 명세 + 라우팅만.
