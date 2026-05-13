# Issue Lifecycle

> **Status**: ACTIVE
> **Scope**: GitHub 이슈 생성·완료·미등록 운영 SSOT. dcness plugin 이 적용된 모든 프로젝트가 본 문서를 따른다. 각 agent / skill 은 본 문서를 *참조* 만 한다 (룰 재기술 금지).

## 0. 이슈 계층

```
epic issue ─┬─ story issue ── (task: PR 기반, 이슈 없음)
            └─ story issue ── (task: PR 기반, 이슈 없음)
```

- **epic** = 1개 stories.md 단위
- **story** = stories.md 안의 Story N 단위
- **task** = impl/NN-*.md 단위. PR 1개 = task 1개. GitHub 이슈 X — PR 자체가 추적 단위

## 1. 생성 규칙

### 1.1 시점

메인 Claude 가 PRD/stories.md 작성 + plan-reviewer PASS + PR 머지 완료 후 *사용자 confirm trigger* 로 epic + story 이슈 *연속* 생성 (`commands/product-plan.md` Step 8). 자동화 스크립트 = [`scripts/create_epic_story_issues.sh`](../../scripts/create_epic_story_issues.sh) — stories.md parse + epic/story 이슈 생성 + sub-issue API 연결 한 명령으로 처리. 별도 호출 (구 ISSUE_SYNC) X.

### 1.2 Epic 이슈

- **레이블**: `epic` + `v0N` + `epic-NN-<slug>` (3중)
  - `v0N` = PRD 마일스톤 버전, 소문자 2자리 (예: `v01`)
  - `epic-NN-<slug>` = 에픽 풀네임 라벨 (예: `epic-11-monkey-design-review`). 미존재 시 GitHub 자동 생성
- **마일스톤**: `Epics`
- **제목**: `[epic] <epic 한 줄 요약>`
- **본문**: 목표 + 선행조건 + **완료 기준 (epic 단위 수용 기준 — 검증 가능한 조건, 사용자가 GitHub UI 에서 확인)**. 진척 체크리스트 X (stories.md 가 SSOT)
- **stories.md 기록 (상단)**:
  ```
  **GitHub Epic Issue:** [#NNN](https://github.com/{owner}/{repo}/issues/NNN)
  ```

### 1.3 Story 이슈

- **레이블**: `story` + `v0N` + `epic-NN-<slug>` (3중, epic 과 `epic-NN-<slug>` 공유)
- **마일스톤**: `Story`
- **제목**: `[story] <story 한 줄 요약>`
- **본문**: `As a / I want / So that` 만 (user story). 수용 기준 (Story 단위) / 대상 화면 / 동작 명세 박지 않음 — architecture.md + impl 파일 영역. 태스크 체크리스트 X (stories.md 가 SSOT)
- **순서**: epic 생성 완료 후 story 1, 2, … 순차
- **stories.md 기록**:
  - 각 story 헤더 직하: `**GitHub Issue:** [#MMM](url)`
  - 파일 하단 `## 관련 이슈` 테이블:
    ```
    | 스토리 | GitHub Issue |
    |---|---|
    | Epic | [#NNN](url) |
    | Story 1 | [#MMM](url) |
    ```

### 1.3.1 Sub-issue 연결 (epic ↔ story)

자동화 = [`scripts/create_epic_story_issues.sh`](../../scripts/create_epic_story_issues.sh) — stories.md parse + epic/story 이슈 생성 + sub-issue API 연결 한 명령으로 처리.

수동 호출 시 (script 미사용):

```bash
# story_id = mcp__github__create_issue 응답의 .id 필드 (database id, NOT .number)
gh api -X POST repos/{owner}/{repo}/issues/{epic_number}/sub_issues \
  -F sub_issue_id={story_id}
# 주의: -f (string) 아닌 -F (typed) — -f 시 422 Invalid property
```

멱등성: 재호출 전 `gh api repos/{owner}/{repo}/issues/{epic_number} --jq '.sub_issues_summary.total'` 로 연결 상태 조회. 누락 story 만 추가 (이미 연결된 story 재추가 시 422).

task 는 GitHub 이슈 X — §1.4 PR 트레일러로만 추적.

### 1.4 Task — PR 트레일러

- 중간 task PR: `Part of #story-issue` (Development 섹션 자동 연결 X — 언급만)
- story 의 마지막 task PR: `Closes #story-issue`
- epic 의 마지막 story 의 마지막 task PR: `Closes #story-issue` + `Closes #epic-issue` (한 줄당 1개 또는 comma 분리)

> **반드시 PR body 에 박는다 (commit message 아님)** — 본 프로젝트는 regular merge 채택 (`docs/plugin/git-naming-spec.md` §6, squash 금지). regular merge 시 GitHub auto-close 는 *PR body* 또는 *squash merge commit message* 만 인식. commit message 안 `Closes #N` 은 머지 commit 에 들어가도 auto-close 발동 X. 본 룰 mechanical 강제 = `scripts/check_pr_body.mjs` + `.github/workflows/pr-body-validation.yml` (init-dcness Step 2.6 으로 사용자 repo 배포).
>
> 예외 — issue 없는 infra-only / follow-up split PR 등은 PR body 에 `Document-Exception-PR-Close: <사유>` line 박으면 게이트 우회.

#### 통합 브랜치 케이스 — base ≠ main sub-PR 의 auto-close 한계 (MUST)

stories.md 상단에 `**Base Branch:** feature/<slug>` 마커 박힌 epic (= 통합 브랜치 모드, `commands/product-plan.md` Step 6.5/7) 의 sub-PR 은 *base = `feature/<slug>`* 로 머지된다. **GitHub auto-close 는 base = default branch (main) 인 PR 만 인식** — base ≠ main sub-PR 의 PR body `Closes #N` 은 머지 시 발동 X.

흐름:

1. **각 sub-PR (base = `feature/<slug>`)** — PR body 에 평소대로 `Part of #<story>` / `Closes #<story>` 박되 머지 시 *발동 안 됨* 전제. `Document-Exception-PR-Close: 통합 브랜치 sub-PR — main 머지 시 일괄 close` 박아 `check_pr_body.mjs` 게이트 우회 가능 (자유 선택).
2. **마지막 통합 → main 머지 PR (base = main)** — PR body 에 **모든 story + epic 을 일괄 close**:
   ```
   Closes #<story1>
   Closes #<story2>
   ...
   Closes #<storyN>
   Closes #<epic>
   ```
   main 머지 시 GitHub 가 일괄 처리. *bulk close = epic atomic transaction 의도와 정합* — main 입장에선 epic 전체가 한 시점에 들어옴.

근거: GitHub 의 [linking-a-pull-request-to-an-issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue) 문서 — *"The pull request must be on the default branch."* 통합 브랜치 base sub-PR 은 미충족.

> 별도 자동화 (sub-issue API 기반 base 무관 close 정책) 는 *추후* 자매 이슈에서 다룸. 본 단락은 *최소 명문화* — 통합 브랜치 모드 진입 사용자가 *마지막 머지 PR 에 bulk close* 박는 패턴만 인지하면 충분.

#### 적용 절차 — PR 생성 직전 사전 체크 (impl 파일 frontmatter 기반)

판정 입력 = **impl 파일 frontmatter `task_index: <i>/<total>` + `story: <N>`**. module-architect × K 시점 (architect-loop §4.2 Step 4) 에 박힘. stories.md `[ ]` 카운트 룰 폐기 (2026-05-12) — 새 stories.md 양식엔 task `[ ]` 자체 없음 (user story 만, [`commands/product-plan.md`](../../commands/product-plan.md) §stories.md 산출물).

1. **task 파일 frontmatter read** — `task_index: 3/3` + `story: 1`
2. **본 task 가 Story 마지막인지 판정** — `i == total` 이면 마지막
3. **본 Story 가 epic 마지막인지 판정** — gh API 1 회: `gh issue list --label "epic-NN-<slug>" --milestone Story --state open --json number --jq 'length'` 가 1 (= 본 Story 만 OPEN) 이면 본 task 머지 시 epic 도 close 예정
4. **분기**:
   - i == total + epic 마지막 story → `Closes #${STORY_ISSUE}` + `Closes #${EPIC_ISSUE}`
   - i == total + epic 중간 story → `Closes #${STORY_ISSUE}`
   - i < total → `Part of #${STORY_ISSUE}`

bash one-liner ([`loop-procedure.md`](loop-procedure.md) §3.4 commit3 단계 안):

```bash
TASK_FILE="docs/milestones/.../impl/NN-*.md"
TASK_INDEX=$(awk '/^task_index:/ {gsub(/[",]/,""); print $2; exit}' "$TASK_FILE")
I="${TASK_INDEX%/*}"
TOTAL="${TASK_INDEX#*/}"
```

**Development 섹션 역방향 업데이트** (story 마지막 PR 생성 시 필수):

`Closes #story-issue` PR 생성과 동시에, 이전 `Part of #story-issue` PR 들을 찾아 body 앞에 `Fixes #story-issue` 를 추가한다. 이미 머지된 PR body 업데이트는 issue close 를 재발동하지 않으며 Development 섹션에 소급 반영된다.

```bash
ISSUE=<story-issue-number>
REPO=<owner>/<repo>
gh search prs --repo "$REPO" "Part of #$ISSUE" --json number --jq '.[].number' \
  | while read num; do
      cur=$(gh pr view "$num" --repo "$REPO" --json body --jq '.body')
      gh pr edit "$num" --repo "$REPO" --body "Fixes #$ISSUE
$cur"
    done
```

## 2. 완료 규칙

### 2.1 Story 완료

- **조건**: story 의 모든 impl task PR merge
- **Close**: 마지막 task PR body `Closes #story-issue` → GitHub 자동 close (regular merge auto-close)
- 메인 Claude 사후 작업 없음 — stories.md `[x]` 체크 룰 폐기 (2026-05-12, [`loop-procedure.md`](loop-procedure.md) §4)

### 2.2 Epic 완료

- **조건**: epic 의 모든 story closed
- **Close 시점**: 마지막 story 의 마지막 task PR — 메인이 PR 생성 *직전* 1회 사전 체크:
  ```bash
  gh issue list --label epic-NN-<slug> --milestone Story --state open
  ```
  → 이 task merge 시 마지막 story close 예정이면, PR body 에 `Closes #epic-issue` 도 동봉
- 메인 Claude 사후 작업 없음 — `backlog.md` 자체 폐기 (2026-05-12, GitHub epic issue close 가 SSOT)
- 별도 wrap-up PR 만들지 않음

### 2.3 API 직접 close 절대금지

`mcp__github__update_issue state:closed` 호출 금지 (epic / story 모두). 반드시 PR body `Closes #N` — §1.4 참조 (regular merge auto-close 인식 한계).

## 3. 미등록 허용 모드

프로젝트가 미등록 모드 (spike / 잡탕 epic 등) 채택 시 stories.md 상단:

```
**GitHub Epic Issue:** 미등록 (사유: <spike / 잡탕 / …>)
```

명시 없는 미등록 = 위반. 발견 시 backfill 의무 — 메인이 §1 따라 `mcp__github__create_issue` 1회 호출 + stories.md 번호 patch.

## 4. 멱등성

`mcp__github__create_issue` 전: stories.md 의 `**GitHub Epic Issue:**` / `**GitHub Issue:**` 매치 검사. 링크 있으면 skip. stories.md 가 이슈 등록 상태의 SSOT.

## 5. 마일스톤 number 조회

`mcp__github__create_issue` 의 `milestone` 파라미터는 **이름이 아닌 숫자(number)** 요구. 매 세션 1회 조회:

```bash
gh api repos/{owner}/{repo}/milestones --jq '.[] | {number, title}'
```

프로젝트별 number 다를 수 있음 — 캐싱 X.

## 6. mid-flow 누락 차단 (pre-flight gate)

`/impl` / `/impl-loop` / `/architect-loop` (ux-architect / system-architect / module-architect × K) 진입 시 부모 epic stories.md 상단 매치 강제:

- `**GitHub Epic Issue:** [#\d+]` (정식 등록), 또는
- `**GitHub Epic Issue:** 미등록 (사유: …)` (§3 허용 모드)

매치 0건 → 즉시 STOP + 사용자 보고. silent skip ("이슈 번호 없음 — 생략하고 진행") 금지.

story 이슈 부재 시 동일 패턴 (Story N 헤더 직하 `**GitHub Issue:** [#\d+]` 매치).

## 7. 참조

- 시퀀스 / 핸드오프: [`orchestration.md`](orchestration.md)
- loop spec (8 loop 행별 풀스펙): [`orchestration.md`](orchestration.md) §4
- product-plan skill (메인 직접): [`../../commands/product-plan.md`](../../commands/product-plan.md)
- system-architect (impl 목차 표 SSOT): [`../../agents/system-architect.md`](../../agents/system-architect.md)
- module-architect (impl 본문 detail per task): [`../../agents/module-architect.md`](../../agents/module-architect.md)
- engineer: [`../../agents/engineer.md`](../../agents/engineer.md) §1 task = 1 PR
