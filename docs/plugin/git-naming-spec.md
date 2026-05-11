# Git Naming Spec

> dcNess 기반 프로젝트의 브랜치 / 커밋 / PR 네이밍·메시지 규칙 SSOT.
> dcNess를 사용하는 **일반 프로젝트** 기준. dcNess 자체 레포는 별도 거버넌스 적용.

## 1. 브랜치

| 타입 | 패턴 | 예시 |
|---|---|---|
| 기능 구현 | `feature/epic{N}_story{N}_{desc}` | `feature/epic3_story2_create_mcp_server` |
| 버그픽스 | `fix/issue{N}_{desc}` | `fix/issue32_duplicate_touch` |
| 버그픽스 (복수 이슈) | `fix/issue{N}_{M}_{desc}` | `fix/issue32_45_duplicate_touch` |
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

<!-- issue-lifecycle.md §1.4 키워드 룰:
     - 중간 task → `Part of #N` (default — 본 PR 이 issue 를 끝내지 않으면 이 줄 유지)
     - 마지막 task → `Closes #N` 으로 변경
     - epic 마지막 task → `Closes #story` + `Closes #epic` 둘 다 박음
     under-link 보다 over-close 사고가 더 큼 (#193 → #182 사례) — default 는 안전한 `Part of` -->
Part of #N

## 참고

-
```

## 6. Git 절차

```
1. git checkout -b {브랜치명} main
2. (작업 + 커밋)
3. git push -u origin {브랜치명}
4. gh pr create --title "..." --body "..."
5. "$PLUGIN_ROOT/scripts/pr-finalize.sh"   # 머지 + CI 대기 + main sync 자동 (한 명령)
```

`pr-finalize.sh` 내부:
- `gh pr merge --auto --merge` (auto-merge 토글)
- `gh pr checks --watch` (CI 결과 대기)
- auto-merge 완료 대기 (GitHub 백그라운드 lag)
- `git checkout main && git pull` (자동 sync)

argument 없이 호출 시 current branch 의 open PR 자동 검출. 명시 시 `pr-finalize.sh <PR_NUMBER>`.

- **CI FAIL 시**: pr-finalize 가 exit 1 + 안내. 원인 파악 후 수정 커밋 → 재검증.
- **working tree dirty**: pr-finalize 가 사용자 확인 후 main sync skip 옵션.
- **레거시 패턴** (수동 4 명령) 도 작동 — 단 권장 X (메인 Claude 가 까먹어 main sync 누락 사례).
