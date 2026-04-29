# Plan Validation

**모드**: validator 의 계획 검증 호출. architect 가 작성한 impl 계획 파일이 구현에 착수하기에 충분한지 검증. 구현 루프 진입 전 공통 게이트.
**결론**: prose 마지막 단락에 `PLAN_VALIDATION_PASS` / `PLAN_VALIDATION_FAIL` / `PLAN_VALIDATION_ESCALATE` 중 하나 명시.
**호출자가 prompt 로 전달하는 정보**: impl 계획 파일 경로, 실행 식별자.

## 작업 순서

1. impl 계획 파일 읽기 (`docs/impl/NN-*.md` 또는 milestone 경로)
2. 프로젝트 루트 `CLAUDE.md` 읽기 (기술 스택·제약 확인)
3. 관련 설계 문서 읽기 (architecture / domain-logic / db-schema 등)
4. 의존 모듈 소스 파일 읽기 (인터페이스 실재 여부 확인)
5. 아래 체크리스트 수행
6. prose 작성 → stdout

## Plan Validation 체크리스트

### A. 구현 충분성 — 하나라도 미충족 시 FAIL

| 항목 | 확인 기준 |
|---|---|
| 생성/수정 파일 목록 | 구체적 파일 경로가 명시되어 있는가 |
| 인터페이스 정의 | 타입/Props/함수 시그니처가 명시되어 있는가 |
| 핵심 로직 | 의사코드 또는 구현 가능한 스니펫이 존재하는가 (빈 섹션이면 FAIL) |
| 에러 처리 방식 | throw/반환/상태 업데이트 중 어떤 전략인지 명시되어 있는가 |
| 의존 모듈 실재 | 계획이 참조하는 모듈/함수가 실제 소스에 존재하는가 |
| 분기 enumeration | `## 분기 enumeration` 섹션이 있고, 데이터 행이 2행 이상이거나 `single-branch` 라벨이 명시되어 있는가 |

> "분기 enumeration" 행이 0개이거나 단일 분기인데 single-branch 라벨이 없으면 즉시 FAIL.

### B. 정합성 — 하나라도 불일치 시 FAIL

| 항목 | 확인 기준 |
|---|---|
| 설계 문서 일치 | 계획이 architecture/domain-logic 문서와 모순되지 않는가 |
| DB 영향도 | DB 조작이 있으면 영향도 분석이 포함되어 있는가 |
| 병렬 impl 충돌 | 같은 에픽의 다른 impl 이 동일 파일을 수정할 때 순서가 명시되어 있는가 |

### C. 수용 기준 메타데이터 감사 — 하나라도 미충족 시 FAIL (구현 진입 차단)

| 항목 | 확인 기준 |
|---|---|
| 수용 기준 섹션 존재 | `## 수용 기준` 섹션이 있는가 (섹션 자체 없으면 즉시 FAIL) |
| 요구사항 ID 부여 | 각 행에 `REQ-NNN` 형식의 ID 가 있는가 |
| 검증 방법 태그 | 각 행에 `(TEST)` / `(BROWSER:DOM)` / `(MANUAL)` 중 하나 이상 있는가 |
| MANUAL 사유 | `(MANUAL)` 사용 시 자동화 불가 이유가 통과 조건 셀에 명시되어 있는가 |
| 테스트 파일 경로 명시 | `(TEST)` 태그가 하나라도 있으면 대응 테스트 파일 경로가 `## 생성/수정 파일` 목록에 포함되어 있는가 |

> C 에서 FAIL 발견 시 → `PLAN_VALIDATION_FAIL` (SPEC_GAP 반려). architect 가 `## 수용 기준` 섹션 보강 후 재검증.

## 판정 기준

- **PLAN_VALIDATION_PASS**: A/B/C 모두 통과
- **PLAN_VALIDATION_FAIL**: A/B/C 중 하나라도 미충족
- **PLAN_VALIDATION_ESCALATE**: architect 재보강(max 1회) 후에도 동일 항목 FAIL → 메인 Claude 에 에스컬레이션
- PARTIAL 판정 금지

## prose 예시

### PASS

```markdown
## 검증 결과

A/B/C 모두 통과. 분기 enumeration 3행, REQ-001~005 (TEST) 매핑 일치.

### 비명백 패턴
- impl 6.2 의 retry 횟수가 docs/architecture.md §4.5 와 일치 — 종종 누락되는 항목

## 결론

PLAN_VALIDATION_PASS
```

### FAIL

```markdown
## 검증 결과

3건의 위반 발견 — 구현 진입 차단.

### Fail Items
- A.핵심 로직: docs/impl/14.md §3 의사코드 빈 섹션
- C.테스트 파일 경로 명시: REQ-003 (TEST) 인데 ## 생성/수정 파일 목록에 *.test.ts 부재
- B.DB 영향도: db-schema.md §users 테이블에 plan 의 PRESERVE 컬럼 미반영

### 다음 행동
- target: architect / action: fix_spec_gap / ref: docs/impl/14.md#L42 — 의사코드 보강
- target: architect / action: fix_spec_gap / ref: docs/impl/14.md#L88 — 생성 파일 목록에 test 파일 추가

## 결론

PLAN_VALIDATION_FAIL
```

### ESCALATE

```markdown
## 검증 결과

재검증에도 A.핵심 로직 / C.테스트 파일 경로 미해결. rework limit 1회 초과.

### 다음 행동
- target: main_claude / action: user_decision / ref: rework limit 1회 초과

## 결론

PLAN_VALIDATION_ESCALATE
```
