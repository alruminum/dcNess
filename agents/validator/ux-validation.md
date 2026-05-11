# UX Validation

**모드**: validator 의 UX Flow 검증 호출. ux-architect 가 생성한 UX Flow Doc 이 PRD 요구사항을 충족하는지 검증.
**결론**: prose 마지막 단락에 *결론 + 권장 다음 단계* 자연어 명시. 권장 표현 (형식 강제 X): `UX_REVIEW_PASS` (architect SYSTEM_DESIGN 권고) / `UX_REVIEW_FAIL` (ux-architect 재진입 권고) / `UX_REVIEW_ESCALATE` (사용자 위임).
**호출자가 prompt 로 전달하는 정보**: UX Flow Doc 경로 (`docs/ux-flow.md`), PRD 경로 (`docs/prd.md`), 실행 식별자.

## 작업 흐름 (자율 조정 가능)

PRD → UX Flow Doc → 5 카테고리 체크리스트.

## 5 카테고리 체크리스트

1. **화면 커버리지**: PRD 의 모든 기능이 하나 이상의 화면에 매핑 / 화면 인벤토리에 PRD 범위 밖 화면 X
2. **플로우 완전성**: 모든 화면 간 이동 경로 정의 / 데드엔드 (이동 불가 상태) X / 진입점 (첫 화면) 명확
3. **상태 커버리지**: 각 화면 필수 상태 (로딩·빈 값·에러·정상) 정의 / 에러 상태 복구 경로 존재
4. **인터랙션 정합성**: PRD 유저 시나리오 (Happy path + Edge case) 가 플로우에 반영 / 수용 기준 (Given/When/Then) 과 인터랙션 일치
5. **디자인 테이블 완전성**: 화면 인벤토리의 모든 화면이 디자인 테이블에 포함 / 우선순위 (P0/P1/P2) 할당

## 판정 기준

- **UX_REVIEW_PASS**: 5 카테고리 모두 통과
- **UX_REVIEW_FAIL**: 하나라도 미충족
- **UX_REVIEW_ESCALATE**: ux-architect 재설계 (max 1 회) 후에도 FAIL

## 산출물 정보 의무 (형식 자유)

- 검증 결과 prose
- FAIL 시 Fail Items 별 (카테고리 + 위치 + 문제)
- (선택) Metrics: screen_count, flow_path_count, prd_coverage_pct
- (선택) 다음 행동 권고 (target / action / ref)
