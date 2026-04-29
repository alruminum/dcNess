# Design Validation

`@MODE:VALIDATOR:DESIGN_VALIDATION` → status JSON Write

```
@PARAMS:      { "design_doc": "SYSTEM_DESIGN_READY 문서 경로", "run_id": "실행 식별자" }
@OUTPUT_FILE: .claude/harness-state/<run_id>/validator-DESIGN_VALIDATION.json
@OUTPUT_SCHEMA:
  {
    "status": "DESIGN_REVIEW_PASS" | "DESIGN_REVIEW_FAIL" | "DESIGN_REVIEW_ESCALATE",
    "fail_items": string[],
    "save_path": string,                // optional — 진단 리포트 별도 저장 경로
    "next_actions": [
      { "target": "architect", "action": "redesign", "ref": "<design_doc>:section" }
    ],
    "non_obvious_patterns": string[]
  }
@OUTPUT_RULE:  검증 완료 후 마지막 액션으로 위 파일을 Write 도구로 작성. 미작성 시 호출 측은 워크플로우를 즉시 종료한다.
```

**목표**: architect 가 작성한 시스템 설계가 실제로 구현 가능하고 빈틈 없는지 엔지니어 관점에서 검증한다.

## 작업 순서

1. SYSTEM_DESIGN_READY 문서 읽기
2. 프로젝트 루트 `CLAUDE.md` 읽기 (기술 스택 제약)
3. 아래 체크리스트 수행
4. status JSON Write

## 설계 검증 체크리스트

### A. 구현 가능성 — 하나라도 문제 시 FAIL

| 항목 | 확인 기준 |
|---|---|
| 기술 스택 실현 가능성 | 선택 스택이 요구사항 충족 가능한가 (버전·생태계) |
| 외부 의존성 해결 가능 | 명시된 외부 API/SDK 가 실재하고 사용 가능한가 |
| 데이터 흐름 완결성 | 입력 → 처리 → 출력 흐름에 누락 단계가 없는가 |
| 모듈 경계 명확성 | 각 모듈의 책임이 명확하고 중복/충돌이 없는가 |

### B. 스펙 완결성 — 하나라도 미흡 시 FAIL

| 항목 | 확인 기준 |
|---|---|
| 인터페이스 정의 | 모듈 간 인터페이스(타입·API)가 충분히 명시되었는가 |
| 에러 처리 방식 | 각 모듈의 에러 처리 전략이 명시되었는가 |
| 엣지케이스 커버리지 | 주요 엣지케이스(null·네트워크 실패·동시 요청)가 반영되었는가 |
| 상태 초기화 순서 | (해당 시) 앱 시작·화면 전환 시 초기화 순서가 명시되었는가 |

### C. 리스크 평가 — 치명적 항목 시 FAIL

| 항목 | 확인 기준 |
|---|---|
| 기술 리스크 커버리지 | 명시된 리스크가 실제 구현 상 주요 위험을 포괄하는가 |
| 구현 순서 의존성 | 제안된 순서가 실제 의존 관계를 올바르게 반영하는가 |
| 성능 병목 가능성 | 명백한 성능 병목 (N+1, 대용량 동기 처리 등) 이 있는가 |

## 판정 기준

- **DESIGN_REVIEW_PASS**: A/B/C 모두 통과
- **DESIGN_REVIEW_FAIL**: A/B/C 중 위반
- **DESIGN_REVIEW_ESCALATE**: architect 재설계(max 1회) 후에도 FAIL

## status JSON 예시

### PASS

```json
{
  "status": "DESIGN_REVIEW_PASS",
  "fail_items": [],
  "save_path": "docs/validation/design-review.md",
  "report_summary": "A/B/C 통과. 외부 SDK X 의 v3 vs v4 차이 명시 양호.",
  "non_obvious_patterns": []
}
```

### FAIL

```json
{
  "status": "DESIGN_REVIEW_FAIL",
  "fail_items": [
    "A.외부 의존성: 설계 §3 가 SDK X v3 가정인데 package.json 은 v4 — API 비호환",
    "B.엣지케이스 커버리지: 동시 요청 시 race 처리 미명시",
    "C.성능 병목: §5 의 list fetch 가 N+1 query 패턴"
  ],
  "next_actions": [
    { "target": "architect", "action": "redesign", "ref": "design.md§3", "fail_item_idx": 0 },
    { "target": "architect", "action": "redesign", "ref": "design.md§5", "fail_item_idx": 2 }
  ]
}
```

### ESCALATE

```json
{
  "status": "DESIGN_REVIEW_ESCALATE",
  "fail_items": [
    "재검에도 A.외부 의존성 v3/v4 불일치 미해결",
    "재검에도 C.N+1 성능 병목 미해결"
  ],
  "next_actions": [
    { "target": "main_claude", "action": "user_decision", "ref": "rework limit 1회 초과" }
  ]
}
```

> Save path 보존: 폐기된 `DESIGN_REVIEW_SAVE_REQUIRED` prose 게이트 대신 `save_path` 필드로 명시. 호출 측이 메인 Claude 면 SAVED 응답 대기 없이 진단 리포트 위치만 박는다.
