# Light Plan

**모드**: architect 의 경량 계획 호출 — 아키텍처 변경 없는 국소적 수정. Module Plan 의 경량 버전.
**결론**: prose 마지막 단락에 `LIGHT_PLAN_READY` 명시.
**호출자가 prompt 로 전달하는 정보**: 관련 파일 경로 (grep 결과 또는 DESIGN_HANDOFF 대상), GitHub 이슈 제목+본문, 라벨 목록, 이슈 번호.

## 적용 범위

- **버그 수정** (FUNCTIONAL_BUG): QA 가 특정한 원인 파일 기반 수정
- **디자인 반영** (DESIGN_HANDOFF): designer 시안을 코드에 적용하는 국소 변경
- **REVIEW_FIX**: pr-reviewer MUST FIX 피드백 재반영 (아키텍처 변경 없는 국소 수정)
- **DOCS_UPDATE**: 텍스트/스타일 등 behavior 불변 변경 (depth=simple 자동)

공통 성격: 아키텍처 변경 없음, 국소적 (1~4 파일), 새 설계 결정 없음. 새 설계 필요 시 MODULE_PLAN 으로 승격.

## 작업 흐름 (자율 조정 가능)

이슈에서 변경 대상 파일·컴포넌트 확인 (버그: qa 리포트 원인 파일·함수·라인 / 디자인: DESIGN_HANDOFF 패키지 대상) → 해당 소스 직접 읽기 (변경 범위 검증) → **관련 테스트 파일 탐색 + 수정 범위 포함** (필수) → 경량 impl 파일 작성.

**테스트 누락 = 루프 실패** — scope_violation autocheck 이 impl 에 없는 파일 변경 차단. 수정 대상 함수/모듈의 테스트를 Glob/Grep 으로 탐색 → 변경 동작을 assert 하면 반드시 `## 수정 파일` 에 포함.

## impl 파일 정보 의무 (형식 자유)

- frontmatter `depth: simple`
- 변경 대상 (파일 / 컴포넌트·함수 + line / 1~2 문장 요약)
- **분기 enumeration**: 수정 대상 함수/클래스의 모든 호출 사이트 + 모든 내부 분기 빠짐없이 나열. 표 형식 (분기 / 위치 / fix 적용 여부 YES/NO / 회귀 가능성 또는 out-of-scope 사유). **최소 2 행** (단일 분기면 `single-branch` 라벨 + 사유). out-of-scope 분기도 반드시 명시 — "안 봤다" 가 아니라 "보고 의도적으로 제외" 를 문서화.
- 수정 내용 (구체적 변경)
- 수용 기준 (1~2 행 — REQ-NNN + 검증 방법 태그 + 통과 조건)

## Module Plan 과의 차이

| 항목 | Module Plan | Light Plan |
|---|---|---|
| 설계 문서 읽기 | 필수 | **불필요** (대상 파일만) |
| 인터페이스 정의 | 필수 | **불필요** (기존 유지) |
| 핵심 로직 | 의사코드/스니펫 필수 | 수정 내용만 |
| DB 영향도 | 필수 | **불필요** |
| 이슈 생성 | 조건부 | **하지 않음** |
| CLAUDE.md / trd.md 업데이트 | 필수/조건부 | **불필요** |
| 수용 기준 | 다수 | **1~2 개** |

## LIGHT_PLAN_READY 게이트 (5 항목)

- 변경 대상 파일·컴포넌트 특정 완료
- 수정 내용 명시
- 변경 동작을 assert 하는 테스트 파일이 수정 범위에 포함 (또는 관련 테스트 없음 확인)
- 수용 기준 섹션 존재 + 태그 있음
- 분기 enumeration 섹션 존재 + 최소 2 행 (또는 single-branch 라벨)

## impl 파일 위치

- `docs/bugfix/#{이슈번호}-{슬러그}.md` (예: `docs/bugfix/#42-flushsync-timing.md`)
