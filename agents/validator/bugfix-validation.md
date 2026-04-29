# Bugfix Validation

**모드**: validator 의 경량 버그 수정 검증 호출. 수정이 원인을 해결하고 회귀를 발생시키지 않았는지 검증. Code Validation 의 경량 버전 — 전체 스펙 일치 대신 *수정 범위만* 검증.
**결론**: prose 마지막 단락에 `BUGFIX_PASS` / `BUGFIX_FAIL` 중 하나 명시.
**호출자가 prompt 로 전달하는 정보**: bugfix impl 경로, 수정 소스 경로, (선택) 테스트 실행 결과, 실행 식별자.

## 작업 순서

1. bugfix impl 파일 읽기 (`docs/bugfix/#N-slug.md` 등)
2. 수정된 소스 파일 읽기
3. 테스트 결과 확인 (전달받은 경우)
4. 아래 체크리스트 수행
5. prose 작성 → stdout

## Bugfix Validation 체크리스트

### A. 원인 해결 — 미충족 시 FAIL

| 항목 | 확인 기준 |
|---|---|
| 수정 위치 일치 | impl 에 명시된 파일·함수가 실제로 수정되었는가 |
| 원인 해소 | impl 에 기술된 원인이 수정으로 해결되는가 (로직 추적) |
| 범위 초과 금지 | impl 에 명시되지 않은 파일이 수정되지 않았는가 |

### B. 회귀 안전 — 미충족 시 FAIL

| 항목 | 확인 기준 |
|---|---|
| 테스트 통과 | 테스트 실행 결과가 전체 통과인가 |
| 기존 로직 보존 | 수정 주변의 기존 로직이 의도치 않게 변경되지 않았는가 |
| 타입 안전성 | `as any`, `@ts-ignore` 등 타입 우회가 새로 추가되지 않았는가 |

## Code Validation 과의 차이

| 항목 | Code Validation | Bugfix Validation |
|---|---|---|
| 스펙 일치 | 전체 (생성 파일·Props·시그니처·핵심 로직) | **수정 위치·원인 해소만** |
| 의존성 규칙 | 5+ 항목 | **범위 초과 금지만** |
| 코드 품질 심층 | 12 항목 | **타입 안전성만** |
| 체크리스트 항목 | ~25 | **6** |

## 판정 기준

- **BUGFIX_PASS**: A/B 모두 통과
- **BUGFIX_FAIL**: A 또는 B 위반

## prose 예시

### PASS

```markdown
## 검증 결과

A/B 통과. 테스트 결과 전체 통과(N=42).

## 결론

BUGFIX_PASS
```

### FAIL

```markdown
## 검증 결과

2건의 위반 발견.

### Fail Items
- A.범위 초과 금지: src/foo.ts 외에 src/baz.ts 도 수정됨 — impl 에 미명시
- B.타입 안전성: src/foo.ts:42 `as any` 신규 추가

### 다음 행동
- target: engineer / action: fix_bug / ref: src/baz.ts (revert)
- target: engineer / action: fix_bug / ref: src/foo.ts:42 (replace as any)

## 결론

BUGFIX_FAIL
```
