# Design Validation

**모드**: validator 의 시스템 설계 검증 호출. architect 가 작성한 시스템 설계가 실제로 구현 가능하고 빈틈 없는지 엔지니어 관점에서 검증.
**결론**: prose 마지막 단락에 `DESIGN_REVIEW_PASS` / `DESIGN_REVIEW_FAIL` / `DESIGN_REVIEW_ESCALATE` 중 하나 명시.
**호출자가 prompt 로 전달하는 정보**: SYSTEM_DESIGN_READY 문서 경로, 실행 식별자.

## 작업 흐름 (자율 조정 가능)

SYSTEM_DESIGN_READY 문서 → 프로젝트 `CLAUDE.md` (기술 스택 제약) → 3 계층 체크리스트.

## 3 계층 체크리스트

**A. 구현 가능성** (하나라도 문제 시 FAIL):
- 기술 스택 실현 가능성 (선택 스택이 요구사항 충족 가능, 버전·생태계)
- 외부 의존성 해결 가능 (명시된 외부 API/SDK 가 실재 + 사용 가능)
- 데이터 흐름 완결성 (입력 → 처리 → 출력 누락 단계 없음)
- 모듈 경계 명확성 (각 모듈 책임 명확 + 중복/충돌 없음)
- **Placeholder Leak 룰 (DCN-CHG-20260430-18)** — `docs/sdk.md` / `docs/reference.md` / `docs/architecture.md` / impl batch 파일들 안에 `[미기록]` / `[미결]` / `M0 이후 구현` / `NotImplementedError` / `# TODO` 등의 placeholder 발견 시:
  - 해당 placeholder 가 **PRD Must 기능 핵심 가치 직결** → 즉시 **DESIGN_REVIEW_FAIL** + 본문에 (placeholder 위치 / 어느 PRD Must 기능 직결 / spike 1개 실측 권고).
  - PRD Should/Could 직결 → WARN.
  - 부가 영역 (로깅·통계·관리자 도구) 직결 → 통과 가능.
- **Spike Gate 정합 (DCN-CHG-20260430-18)** — `agents/architect/system-design.md` §Spike Gate 정합. architect 가 추상 ABC + Mock 만으로 통과시킨 흔적 (concrete 구현 0 + sdk.md 의 API signature 부재) 발견 시 FAIL.

**B. 스펙 완결성** (하나라도 미흡 시 FAIL):
- 인터페이스 정의 (모듈 간 타입·API 충분히 명시)
- 에러 처리 방식 (각 모듈 전략 명시)
- 엣지케이스 커버리지 (null·네트워크 실패·동시 요청)
- 상태 초기화 순서 (해당 시 앱 시작·화면 전환 시)

**C. 리스크 평가** (치명적 항목 시 FAIL):
- 기술 리스크 커버리지 (명시된 리스크가 실제 주요 위험 포괄)
- 구현 순서 의존성 (실제 의존 관계 반영)
- 성능 병목 가능성 (N+1, 대용량 동기 처리 등 명백한 병목)

## 판정 기준

- **DESIGN_REVIEW_PASS**: A/B/C 모두 통과
- **DESIGN_REVIEW_FAIL**: 위반
- **DESIGN_REVIEW_ESCALATE**: architect 재설계 (max 1 회) 후에도 FAIL

## 산출물 정보 의무 (형식 자유)

- 검증 결과 prose
- FAIL 시 Fail Items 별 (계층 + 위치 + 문제)
- (선택) 다음 행동 권고 (target / action / ref)
