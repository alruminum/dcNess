# UX Validation

`@MODE:VALIDATOR:UX_VALIDATION` → status JSON Write

```
@PARAMS:      { "ux_flow_doc": "docs/ux-flow.md 경로", "prd_path": "prd.md 경로", "run_id": "실행 식별자" }
@OUTPUT_FILE: .claude/harness-state/<run_id>/validator-UX_VALIDATION.json
@OUTPUT_SCHEMA:
  {
    "status": "UX_REVIEW_PASS" | "UX_REVIEW_FAIL" | "UX_REVIEW_ESCALATE",
    "fail_items": string[],
    "next_actions": [
      { "target": "ux-architect", "action": "rework_flow", "ref": "docs/ux-flow.md§..." }
    ],
    "metrics": {                       // optional
      "screen_count": number,
      "flow_path_count": number,
      "prd_coverage_pct": number
    },
    "non_obvious_patterns": string[]
  }
@OUTPUT_RULE:  검증 완료 후 마지막 액션으로 위 파일을 Write 도구로 작성. 미작성 시 호출 측은 워크플로우를 즉시 종료한다.
```

**목표**: ux-architect 가 생성한 UX Flow Doc 이 PRD 요구사항을 충족하는지 검증한다.

## 작업 순서

1. PRD (`prd.md`) 읽기
2. UX Flow Doc (`docs/ux-flow.md`) 읽기
3. 아래 체크리스트 수행
4. status JSON Write

## 검증 체크리스트

### 1. 화면 커버리지

- [ ] PRD 의 모든 기능이 하나 이상의 화면에 매핑되어 있는가?
- [ ] 화면 인벤토리에 PRD 범위 밖 화면이 포함되어 있지 않은가?

### 2. 플로우 완전성

- [ ] 모든 화면 간 이동 경로가 정의되어 있는가?
- [ ] 데드엔드(이동 불가 상태)가 없는가?
- [ ] 진입점(첫 화면)이 명확한가?

### 3. 상태 커버리지

- [ ] 각 화면의 필수 상태(로딩·빈 값·에러·정상)가 모두 정의되어 있는가?
- [ ] 에러 상태에서의 복구 경로가 있는가?

### 4. 인터랙션 정합성

- [ ] PRD 의 유저 시나리오(Happy path + Edge case)가 플로우에 반영되어 있는가?
- [ ] 수용 기준(Given/When/Then)과 인터랙션 정의가 일치하는가?

### 5. 디자인 테이블 완전성

- [ ] 화면 인벤토리의 모든 화면이 디자인 테이블에 포함되어 있는가?
- [ ] 우선순위(P0/P1/P2)가 할당되어 있는가?

## 판정 기준

- **UX_REVIEW_PASS**: 5 카테고리 모두 통과
- **UX_REVIEW_FAIL**: 하나라도 미충족
- **UX_REVIEW_ESCALATE**: ux-architect 재설계(max 1회) 후에도 FAIL

## status JSON 예시

### PASS

```json
{
  "status": "UX_REVIEW_PASS",
  "fail_items": [],
  "metrics": {
    "screen_count": 12,
    "flow_path_count": 28,
    "prd_coverage_pct": 100
  },
  "report_summary": "5 카테고리 통과. 화면 12, 플로우 28, PRD 100% 매핑.",
  "non_obvious_patterns": []
}
```

### FAIL

```json
{
  "status": "UX_REVIEW_FAIL",
  "fail_items": [
    "1.화면 커버리지: PRD §3.4 'export 기능' 매핑 화면 부재",
    "3.상태 커버리지: ScreenA 의 에러 상태 미정의",
    "4.인터랙션 정합성: PRD §5 Edge case '네트워크 실패' 가 ScreenB 인터랙션에 미반영"
  ],
  "next_actions": [
    {
      "target": "ux-architect",
      "action": "rework_flow",
      "ref": "docs/ux-flow.md — export 화면 추가",
      "fail_item_idx": 0
    },
    {
      "target": "ux-architect",
      "action": "rework_flow",
      "ref": "docs/ux-flow.md§ScreenA 에러 상태",
      "fail_item_idx": 1
    }
  ],
  "metrics": {
    "screen_count": 11,
    "flow_path_count": 24,
    "prd_coverage_pct": 87
  }
}
```

### ESCALATE

```json
{
  "status": "UX_REVIEW_ESCALATE",
  "fail_items": [
    "재검에도 1.화면 커버리지: export 화면 미추가",
    "재검에도 3.상태 커버리지: ScreenA 에러 상태 미정의"
  ],
  "next_actions": [
    { "target": "main_claude", "action": "user_decision", "ref": "rework limit 1회 초과" }
  ]
}
```
