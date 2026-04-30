# SPEC_GAP

> ⚠️ **CRITICAL — extended thinking 본문 드래프트 금지** (DCN-CHG-20260430-39). thinking = 의사결정 분기만. 갭 분석 / 계획 보강 patch 본문 = thinking 종료 *후* 즉시 emit 또는 `Edit/Write` 입력값 안에서만. THINKING_LOOP 회귀 회피 (DCN-30-20). master 룰: `agents/architect.md` §자기규율.

**모드**: architect 의 SPEC_GAP 해결 호출 — engineer/test-engineer 가 SPEC_GAP_FOUND emit 후 진입.
**결론**: prose 마지막 단락에 `SPEC_GAP_RESOLVED` / `PRODUCT_PLANNER_ESCALATION_NEEDED` / `TECH_CONSTRAINT_CONFLICT` 중 하나 명시.
**호출자가 prompt 로 전달하는 정보**: SPEC_GAP_FOUND 갭 목록, 영향 받는 impl 경로, 현재 depth (`simple` / `std` / `deep`).

## 작업 흐름 (자율 조정 가능)

갭 목록 분석 → 해당 소스 파일 직접 확인 → 계획 파일 보강 (갭 발생 섹션 수정) → READY_FOR_IMPL 게이트 재체크 → **설계 문서 동기화** → 결론 emit.

## 설계 문서 동기화 (필수)

SPEC_GAP 처리로 로직·스키마·인터페이스 변경 시 아래 문서를 반드시 확인 + 불일치 시 즉시 수정:

| 변경 유형 | 동기화 대상 |
|---|---|
| **도메인 모델 변경** (entity/VO/aggregate/invariant) **(DCN-CHG-20260430-16)** | **`docs/domain-model.md` (architect 단독 수정 권한)** |
| 시스템 구조·모듈 의존성 변경 | `docs/architecture.md` + 분리된 detail 파일 |
| 게임 로직·알고리즘·수치 변경 | `docs/game-logic.md` (또는 프로젝트 해당 문서) |
| 핵심 로직·상태머신·알고리즘 | `trd.md` §3 |
| DB 스키마 변경 | `docs/db-schema.md` + `trd.md` §4 |
| SDK 연동 방식 | `docs/sdk.md` + `trd.md` §5 |
| store 인터페이스 | `trd.md` §6 |
| 화면·컴포넌트 스펙 | `trd.md` §7 |

## Domain Model 변경 사이클 (DCN-CHG-20260430-16)

engineer / test-engineer 가 SPEC_GAP_FOUND 보고 시 도메인 모델 변경 필요 (entity 신규, invariant 변경, aggregate 경계 조정 등) 면:

1. **architect 단독 수정** — engineer/test-engineer 직접 수정 절대 금지 (catastrophic 룰)
2. 변경 영향 분석:
   - 기존 invariant 깨지는 코드 있는가? → 영향 받는 impl batch list
   - aggregate 경계 변경 시 트랜잭션 단위 재검토
   - 의존성 그래프 변경 → `docs/architecture.md` 도 갱신
3. 300줄 cap 초과 시 별도 .md 분리 (예: `docs/domain/<aggregate>.md`)
4. 변경 사유 + 영향 범위를 prose 결론에 명시 (`SPEC_GAP_RESOLVED` + domain model 변경 표시)

## 분기 판정

**1. prd.md 불일치 발견 시** → architect 직접 수정 X. 결론 `PRODUCT_PLANNER_ESCALATION_NEEDED` + 본문에 (현재 prd.md 내용 / 실제 구현 / 권고) 명시.

**2. 기술 제약 vs 비즈니스 요구 충돌 시** ("현재 기술 스택/제약으로 PRD 요구사항 구현 불가"):
- 즉시 구현 중단
- 결론 `TECH_CONSTRAINT_CONFLICT` + 본문에 (충돌 내용: PRD 요구사항 / 기술 제약 / 영향 범위) + 옵션 (A. PRD 축소 / B. 기술 스택 변경 / C. 임시 우회 구현 + 기술 부채 명시) + 권고 (A/B/C 중 하나 + 이유)
- 메인 Claude 가 product-planner escalate 여부 결정. architect 가 직접 PRD 수정·"일단 하겠다" 진행 금지.

**3. 정상 해결** → 결론 `SPEC_GAP_RESOLVED` + 산출물 (impl_path / depth).

## depth 재판정 (상향만 허용)

SPEC_GAP 처리 중 작업 범위가 커지면 depth 상향 가능 (simple → std → deep). **하향 금지**. prose 산출물 섹션에 `depth:` 변경 사실 명시.
