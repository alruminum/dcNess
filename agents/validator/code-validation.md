# Code Validation

`@MODE:VALIDATOR:CODE_VALIDATION` → status JSON Write

```
@PARAMS:      { "impl_path": "impl 계획 경로", "src_files": "구현 파일 경로 목록", "run_id": "실행 식별자" }
@OUTPUT_FILE: .claude/harness-state/<run_id>/validator-CODE_VALIDATION.json
@OUTPUT_SCHEMA:
  {
    "status": "PASS" | "FAIL" | "SPEC_MISSING",
    "fail_items": string[],            // FAIL 시 필수
    "spec_missing": {                   // SPEC_MISSING 시 필수
      "expected_path": string,
      "fallback_searched": string[],
      "request": string
    },
    "next_actions": [
      { "target": "engineer", "action": "fix_code", "ref": "src/...:Lxx" }
    ],
    "non_obvious_patterns": string[]   // optional
  }
@OUTPUT_RULE:  검증 완료 후 마지막 액션으로 위 파일을 Write 도구로 작성. 미작성 시 호출 측은 워크플로우를 즉시 종료한다.
```

**목표**: 구현 코드가 impl 계획과 일치하고 의존성 규칙을 지키며 시니어 관점 품질 기준을 충족하는지 검증한다.

## 작업 순서

1. 계획 파일 읽기 (`docs/impl/NN-*.md` 등)
   - **계획 파일 미존재 시**: 즉시 FAIL 금지. 다음 순서로 대체 소스 탐색:
     1. `docs/impl/00-decisions.md`
     2. `CLAUDE.md` 작업 순서 섹션
     3. 모두 없으면 `status="SPEC_MISSING"` + `spec_missing` 필드 채워 status JSON Write 후 즉시 종료
2. 설계 결정 문서 읽기 (`docs/impl/00-decisions.md` 또는 유사)
3. 구현 파일 읽기
4. 의존 모듈 소스 읽기 (경계 위반 여부 확인)
5. 화면/컴포넌트 모듈인 경우: ui-spec 파일 읽기
6. 아래 3계층 체크리스트 수행
7. status JSON Write

## 3계층 체크리스트

### A. 스펙 일치 — 하나라도 불일치 시 FAIL

| 항목 | 확인 기준 |
|---|---|
| 생성 파일 | 계획의 생성 목록과 실제 파일이 일치하는가 |
| Props 타입 | 계획에 명시된 타입과 구현이 일치하는가 |
| 함수 시그니처 | 계획의 함수명·파라미터·반환 타입과 일치하는가 |
| 주의사항 | 계획의 주의사항이 코드에 반영되었는가 |
| 핵심 로직 | 계획의 의사코드/스니펫과 실제 구현 흐름이 일치하는가 |
| 에러 처리 | 계획에 명시된 전략(throw/반환/상태)이 구현되었는가 |
| ui-spec 일치 | (해당 시) 색상·레이아웃·상태 UI 가 ui-spec 과 일치하는가 |

### B. 의존성 규칙 — 하나라도 위반 시 FAIL

| 항목 | 확인 기준 |
|---|---|
| 래퍼 함수 사용 | 외부 API/SDK 를 직접 import 하지 않고 래퍼를 사용하는가 |
| 외부 패키지 | 계획에 없는 외부 패키지를 새로 import 하지 않는가 |
| 모듈 경계 | 다른 모듈의 내부 상태를 직접 변경하지 않는가 |
| 공유 상태 | 전역 스토어를 계획에 명시된 액션만으로 접근하는가 |
| DB 스키마 계약 | impl plan 이 DB 조작 또는 영향도 분석을 포함할 때 plan 의 컬럼·타입·제약이 실제 스키마와 일치하는가 |

#### DB 변경이 있는 경우 추가 체크

| 항목 | 확인 기준 |
|---|---|
| 마이그레이션 파일 존재 | DDL 파일이 있는가 |
| Forward/Rollback DDL | impl plan 주의사항에 둘 다 기재되어 있는가 |
| 생성 타입 동기화 | generated types 가 스키마 변경 후 재생성됐는가 |

### C. 코드 품질 심층 검토 — 시니어 관점

| 항목 | 확인 내용 |
|---|---|
| 경쟁 조건 | 비동기 작업의 완료 순서 가정이 안전한가 |
| 메모리 누수 | setInterval/setTimeout/addEventListener 클린업이 있는가 |
| 불필요한 리렌더 | useCallback/useMemo 없이 객체/함수가 매 렌더마다 생성되는가 |
| 에러 전파 | Promise rejection 이 catch 없이 무시되는가 |
| 타입 안전성 | `as any`, `@ts-ignore`, 불필요한 타입 단언이 있는가 |
| 중복 로직 | 동일 계산이 3회 이상 반복되며 추출 가능한가 |
| 매직 넘버 | 의미 불명의 숫자/문자열 리터럴이 인라인으로 사용되는가 |
| 비동기 순서 | 언마운트 후 setState 호출 가능 패턴이 있는가 |
| 렌더 안전성 | 렌더 중 side effect 가 직접 실행되는가 |
| 의미론적 네이밍 | "helper", "utils", "manager" 등 책임 모호 이름이 있는가 |
| 도메인 로직 누수 | UI 컴포넌트 안에 분리해야 할 비즈니스 로직이 있는가 |
| 적대적 시나리오 | 동시 실행 / null 입력 / 네트워크 실패 각각 안전한가 |

## 판정 기준

- **PASS**: A/B 모두 통과 + C 에서 치명적 문제 없음
- **FAIL**: A/B 위반 또는 C 의 프로덕션 위험 항목 발견
- **SPEC_MISSING**: 계획 파일 + 대체 소스 모두 부재
- PARTIAL 판정 금지

## status JSON 예시

### PASS

```json
{
  "status": "PASS",
  "fail_items": [],
  "report_summary": "A/B 통과. C 의 (적대적 시나리오) 권고만 있음 (FAIL 아님).",
  "non_obvious_patterns": [
    "src/api/xxx.ts:42 의 retry 패턴이 다른 모듈과 다름 — 이유: 외부 SDK 가 idempotent 보장 안 함"
  ]
}
```

### FAIL

```json
{
  "status": "FAIL",
  "fail_items": [
    "A.함수 시그니처: src/foo.ts:88 의 fetchUser 가 plan 의 (id: string) → User 와 다름 — (id: string) → User | null",
    "B.래퍼 함수 사용: src/bar.ts:12 가 axios 를 직접 import (래퍼 src/lib/http.ts 우회)",
    "C.타입 안전성: src/baz.ts:50 `as any` 신규 추가"
  ],
  "next_actions": [
    { "target": "engineer", "action": "fix_code", "ref": "src/foo.ts:88", "fail_item_idx": 0 },
    { "target": "engineer", "action": "fix_code", "ref": "src/bar.ts:12", "fail_item_idx": 1 }
  ]
}
```

### SPEC_MISSING

```json
{
  "status": "SPEC_MISSING",
  "fail_items": [],
  "spec_missing": {
    "expected_path": "docs/impl/14-feature.md",
    "fallback_searched": ["docs/impl/00-decisions.md", "CLAUDE.md"],
    "request": "architect Module Plan 으로 계획 파일 생성 후 재호출"
  }
}
```
