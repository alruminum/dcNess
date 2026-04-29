# Task Decompose

**모드**: architect 의 epic stories → 기술 구현 단위 분해 호출. product-planner 완료 후 호출.
**결론**: 각 분해된 impl 파일 작성 후 prose 마지막 단락에 `READY_FOR_IMPL` 명시 (×N batch 가능).
**호출자가 prompt 로 전달하는 정보**: Epic stories.md 경로, 설계 문서 경로.

## 작업 흐름 (자율 조정 가능)

스토리 목록 확인 (GitHub Issues 우선: `mcp__github__list_issues` milestone=Epics + label=현재버전 / 폴백: `docs/milestones/vNN/epics/epic-NN-*/stories.md`) → 프로젝트 `CLAUDE.md` (기술 스택·제약) → `docs/impl/00-decisions.md` → **Outline-First 절차** (architect.md §자기규율 참조: impl 목차 출력 → 한 파일씩 순차 Write) → 각 스토리에 대응 기술 태스크 도출 → 태스크 등록 (GitHub `update_issue` body 체크리스트 / 폴백: stories.md 체크박스) → impl 파일 작성 → READY_FOR_IMPL 게이트 통과 확인.

## 태스크 도출 기준

- 한 태스크 = engineer 가 한 번 루프로 구현 가능한 단위
- 파일 1~3 개 생성/수정 범위
- 명확한 PASS/FAIL 판단 가능

## 듀얼 모드 가드레일 — 디자인 토큰 우선 (필수 검사)

UI 컴포넌트 포함 epic 분해 시, **`docs/ux-flow.md` 에 §0 디자인 가이드 존재 + `docs/design-handoff.md` 미존재** = **듀얼 모드**.

가드레일:
- **impl `01-theme-tokens.md` 강제 신설** (다른 UI impl 보다 앞 순번)
  - 생성 파일: `src/theme/colors.ts`, `typography.ts`, `spacing.ts`, `index.ts`
  - 내용: ux-flow §0 의 모든 토큰을 추상 키로 노출 (예: `colors.background.primary`, `colors.accent.gold`, `typography.heading`, `spacing.lg`)
  - 직접 hex/rem/font-name 박는 것 금지 — 모든 컴포넌트는 `theme.*` 경유
- **이후 모든 UI impl 의존성 명시**: `## 의존성` 에 `src/theme/` 1 줄
- **수용 기준 추가**: "직접 색상값/폰트명/픽셀값 사용 금지 — 모두 `theme.*` 경유"

근거: 디자인 시안 도착 후 토큰값만 patch 하면 컴포넌트 갈아엎기 0.

design-handoff.md 있는 경우 (B 모드 = 디자인 후 구현) 는 스킵.

## 산출물 정보 의무 (형식 자유)

- impl 목차 outline (파일명 + 다룰 스토리 + depth + 1 줄 요약 + 의존·순서)
- 추가된 태스크 (Story → impl 매핑)
- 생성된 impl 파일 목록 (경로 + depth + 가드레일 표시 — 듀얼 모드 시 `01-theme-tokens.md`)
