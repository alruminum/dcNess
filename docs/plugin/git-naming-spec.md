# Git Naming Spec

> dcNess 기반 프로젝트의 브랜치 / 커밋 / PR 네이밍·메시지 규칙 SSOT.
> dcNess를 사용하는 **일반 프로젝트** 기준. dcNess 자체 레포는 별도 거버넌스 적용.

## 1. 브랜치

| 타입 | 패턴 | 예시 |
|---|---|---|
| 기능 구현 | `feature/epic{N}_story{N}_{desc}` | `feature/epic3_story2_create_mcp_server` |
| 버그픽스 | `fix/issue{N}_{desc}` | `fix/issue32_duplicate_touch` |
| 문서 | `docs/{desc}` | `docs/update_api_spec` |

- `{desc}`: 소문자 + `_` 구분자. 공백·특수문자 금지.
- main 직접 push 금지. 항상 branch → PR → merge.
- 브랜치는 merge 후에도 삭제하지 않는다.

## 2. 커밋 제목

| 타입 | 형식 | 예시 |
|---|---|---|
| 기능 구현 | `[epic{N}][story{N}] {설명}` | `[epic4][story3] mcp 세팅` |
| 버그픽스 | `[issue-{N}] {설명}` | `[issue-32] 중복 터치 수정` |
| 문서 | `[docs] {설명}` | `[docs] API 스펙 업데이트` |

- `{설명}`: 명사형 또는 동사원형으로 간결하게 한 줄.

## 3. 커밋 메시지 본문

빈 섹션은 `-` 로 채운다.

```
## 관련 이슈 번호

-

## 배경 및 문제

-

## 원인

-

## 작업 내용

-

## 참고

-
```

## 4. PR 제목

| 타입 | 형식 | 예시 |
|---|---|---|
| 기능 구현 | `[epic{N}][story{N}] {설명}` | `[epic4][story3] mcp서버를 생성합니다.` |
| 버그픽스 | `[issue-{N}] {설명}` | `[issue-32] 중복터치 개선` |
| 문서 | `[docs] {설명}` | `[docs] API 스펙 업데이트` |

## 5. PR 본문

커밋이 여러 개면 커밋별로 섹션 반복. 단일 커밋은 하나만.

```markdown
## 변경 요약

### {커밋 제목}
- **What**: 
- **Why**: 

## 결정 근거

<!-- 검토한 대안, 선택 이유. 단순 변경이면 `-` -->
-

## 관련 이슈

<!-- issue-lifecycle.md §1.4: 중간 task → `Part of #N` / 마지막 task → `Closes #N` / epic 마지막 task → `Closes #story` + `Closes #epic` -->
Closes #N

## 참고

-
```

## 6. Git 절차

```
1. git checkout -b {브랜치명} main
2. (작업 + 커밋)
3. git push -u origin {브랜치명}
4. gh pr create --title "..." --body "..."
5. gh pr merge   # regular merge — 커밋 히스토리 보존 (squash 금지)
6. git checkout main && git pull
```
