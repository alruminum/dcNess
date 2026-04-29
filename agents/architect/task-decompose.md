# Task Decompose

`@MODE:ARCHITECT:TASK_DECOMPOSE` → prose emit (마지막 단락에 결론 enum)

```
@PARAMS: { "stories_doc": "Epic stories.md 경로", "design_doc": "설계 문서 경로" }
@CONCLUSION_ENUM: READY_FOR_IMPL
```

메인 Claude 또는 product-planner 완료 후 호출.

**목표**: product-planner 가 스토리까지 작성한 epic 파일을 받아, 각 스토리를 기술 구현 단위로 분해하고 impl 파일을 작성한다.

## 작업 순서

1. 스토리 목록 확인:
   - **GitHub Issues 사용 시**: `mcp__github__list_issues` (milestone=Epics, label=현재버전) 로 에픽 이슈 조회 → 본문에서 스토리 목록 확인
   - **로컬 파일 폴백**: `docs/milestones/vNN/epics/epic-NN-*/stories.md` 읽기
2. 프로젝트 루트 `CLAUDE.md` 읽기 (기술 스택, 제약 확인)
3. `docs/impl/00-decisions.md` 또는 유사 파일 읽기 (기존 결정 확인)
4. **Outline-First 절차** (architect.md 자기규율 §TASK_DECOMPOSE 참조):
   - 먼저 impl 목차 만 text 출력 (impl 파일명 + 다룰 스토리 번호 + depth + 1줄 요약 + 의존 관계)
   - 한 파일씩 순차 Write
5. 각 스토리에 대응 기술 태스크 도출 (구현 단위로 쪼개기)
6. 태스크 등록:
   - **GitHub Issues 사용 시**: `mcp__github__update_issue` 로 스토리 이슈 body 에 태스크 체크리스트 추가
   - **로컬 파일 폴백**: `stories.md` 각 스토리 아래 태스크 추가 (체크박스)
7. 각 태스크에 대응 `docs/milestones/vNN/epics/epic-NN-*/impl/NN-*.md` 작성
8. READY_FOR_IMPL 게이트 통과 여부 확인
9. prose 작성 → stdout

## 태스크 도출 기준

- 한 태스크 = engineer 가 한 번 루프로 구현 가능한 단위
- 파일 1~3 개 생성/수정 범위
- 명확한 PASS/FAIL 판단 가능

## 듀얼 모드 가드레일 — 디자인 토큰 우선 (필수 검사)

UI 컴포넌트 포함 epic 분해 시, **`docs/ux-flow.md` 에 §0 디자인 가이드(컬러·타이포·UI 패턴) 존재 + `docs/design-handoff.md` 미존재** = **듀얼 모드**. 디자인 시안 도착 후 컴포넌트 갈아엎지 않으려면 **첫 번째 impl 을 디자인 토큰 시스템으로 강제**.

검사 절차:
1. `docs/ux-flow.md` 존재 + `## 0. 디자인 가이드` 섹션 존재 확인
2. `docs/design-handoff.md` 존재 여부 확인
3. **있고 + 없음 = 듀얼 모드** → 가드레일 적용

가드레일:
- **impl `01-theme-tokens.md` 강제 신설** (다른 UI impl 보다 앞 순번)
  - 생성 파일: `src/theme/colors.ts`, `src/theme/typography.ts`, `src/theme/spacing.ts`, `src/theme/index.ts`
  - 내용: ux-flow §0 의 모든 토큰을 추상 키로 노출 (예: `colors.background.primary`, `colors.accent.gold`, `typography.heading`, `spacing.lg`)
  - 직접 hex/rem/font-name 박는 것 금지 — 모든 컴포넌트는 `theme.*` 경유
- **이후 모든 UI impl 의존성 명시**: `## 의존성` 에 `src/theme/` 1줄
- **수용 기준 추가**: "직접 색상값/폰트명/픽셀값 사용 금지 — 모두 theme.* 경유"

근거: 디자인 시안 도착 후 토큰값만 patch 하면 컴포넌트 갈아엎기 0.

design-handoff.md 있는 경우(B 모드 = 디자인 후 구현) 는 스킵.

## prose 결론 예시

```markdown
## 작업 결과

Epic 03 stories 5개 → impl 7개 분해 완료.

## 추가된 태스크
- Story 1 → impl 01, 02
- Story 2 → impl 03
- ...

## 생성된 impl 파일
- docs/milestones/v1/epics/epic-03-auth/impl/01-theme-tokens.md (depth: simple — 듀얼 모드 가드레일)
- docs/milestones/v1/epics/epic-03-auth/impl/02-login-form.md (depth: std)
- ...

## 결론

READY_FOR_IMPL
```
