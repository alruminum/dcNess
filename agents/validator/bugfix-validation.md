# Bugfix Validation

**모드**: validator 의 경량 버그 수정 검증 호출. 수정이 원인을 해결하고 회귀를 발생시키지 않았는지 검증. Code Validation 의 경량 버전 — 전체 스펙 일치 대신 *수정 범위만* 검증.
**결론**: prose 마지막 단락에 *결론 + 권장 다음 단계* 자연어 명시. 권장 표현 (형식 강제 X): `BUGFIX_PASS` (pr-reviewer 권고) / `BUGFIX_FAIL` (engineer 재시도 권고).
**호출자가 prompt 로 전달하는 정보**: bugfix impl 경로, 수정 소스 경로, (선택) 테스트 실행 결과, 실행 식별자.

## 작업 흐름 (자율 조정 가능)

bugfix impl (`docs/bugfix/#N-slug.md`) → 수정된 소스 → 테스트 결과 (전달받은 경우) → 2 계층 체크리스트.

## 2 계층 체크리스트

**A. 원인 해결** (미충족 시 FAIL):
- 수정 위치 일치 (impl 에 명시된 파일·함수가 실제로 수정)
- 원인 해소 (impl 의 원인이 수정으로 해결, 로직 추적)
- 범위 초과 금지 (impl 에 명시되지 않은 파일이 수정되지 않음)

**B. 회귀 안전** (미충족 시 FAIL):
- 테스트 통과 (전체 통과)
- 기존 로직 보존 (수정 주변 로직이 의도치 않게 변경되지 않음)
- 타입 안전성 (`as any`, `@ts-ignore` 등 우회 신규 추가 X)

## Code Validation 과의 차이

| 항목 | Code Validation | Bugfix Validation |
|---|---|---|
| 스펙 일치 | 전체 (생성 파일·Props·시그니처·핵심 로직) | **수정 위치·원인 해소만** |
| 의존성 규칙 | 5+ 항목 | **범위 초과 금지만** |
| 코드 품질 심층 | 12 항목 | **타입 안전성만** |
| 체크리스트 항목 | ~25 | **6** |

## 판정 기준

- **BUGFIX_PASS**: A/B 모두 통과
- **BUGFIX_FAIL**: 위반

## 산출물 정보 의무 (형식 자유)

- 검증 결과 prose
- FAIL 시 Fail Items 별 (계층 + 위치 + 문제)
- (선택) 다음 행동 권고 (target / action / ref)
