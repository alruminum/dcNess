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

`product-planner` 가 PRODUCT_PLAN_READY 산출 직후 stories.md Write → epic + story 이슈 *연속* 생성. 별도 호출 (구 ISSUE_SYNC) X.

### 1.2 Epic 이슈

- **레이블**: `epic` + `v0N` + `epic-NN-<slug>` (3중)
  - `v0N` = PRD 마일스톤 버전, 소문자 2자리 (예: `v01`)
  - `epic-NN-<slug>` = 에픽 풀네임 라벨 (예: `epic-11-monkey-design-review`). 미존재 시 GitHub 자동 생성
- **마일스톤**: `Epics`
- **제목**: `[epic] <epic 한 줄 요약>`
- **본문**: 목표 + 선행조건 + 완료 기준만. 진척 체크리스트 X (stories.md 가 SSOT)
- **stories.md 기록 (상단)**:
  ```
  **GitHub Epic Issue:** [#NNN](https://github.com/{owner}/{repo}/issues/NNN)
  ```

### 1.3 Story 이슈

- **레이블**: `story` + `v0N` + `epic-NN-<slug>` (3중, epic 과 `epic-NN-<slug>` 공유)
- **마일스톤**: `Story`
- **제목**: `[story] <story 한 줄 요약>`
- **본문**: 수용 기준 (Given/When/Then) 만. 태스크 체크리스트 X (stories.md 가 SSOT)
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

GitHub native sub-issue API 로 epic 과 story 를 부모-자식 관계로 연결. 본문 체크리스트 (`- [ ] #M — Story N: …`) 만으로는 `sub_issues_summary.total: 0` 이라 GitHub UI 의 progress bar / sub-issues 패널이 작동하지 않음.

- **시점**: §1.3 의 story 이슈 N 개 *전부* 생성 완료 후 일괄 호출.
- **호출 주체**: 메인 Claude — product-planner / architect tech-epic 등 agent 종료 직후 메인이 prose 에서 epic 번호 + story id 목록을 받아 호출. agent 자체는 `gh api` 호출 X (권한 최소화 — agent tools 에 Bash 추가하지 않음).
- **API**: 현재 `mcp__github__*` 툴셋엔 sub-issue 추가 도구 없음 — `gh api` 직접 호출 필수. 장래 MCP 툴 추가되면 본 § 갱신.

  ```bash
  # story_id = mcp__github__create_issue 응답의 .id 필드 (database id, NOT .number)
  gh api -X POST repos/{owner}/{repo}/issues/{epic_number}/sub_issues \
    -F sub_issue_id={story_id}
  ```

  주의: `-f` (string) 가 아닌 `-F` (typed) 사용. `-f` 시 `422 Invalid property: sub_issue_id is not of type integer`.

- **멱등성**: 재호출 전 현재 연결 상태 조회:

  ```bash
  gh api repos/{owner}/{repo}/issues/{epic_number} --jq '.sub_issues_summary.total'
  ```

  값이 기대 story 수와 같으면 skip. 부족 시 누락 story 만 추가 (이미 연결된 story 재추가 시 422 가능).

- **task PR 과의 분리**: task 는 GitHub 이슈 X (§1.4 PR 트레일러로만 추적). sub-issue API 호출 X.

### 1.4 Task — PR 트레일러

- 중간 task PR: `Part of #story-issue` (Development 섹션 자동 연결 X — 언급만)
- story 의 마지막 task PR: `Closes #story-issue`
- epic 의 마지막 story 의 마지막 task PR: `Closes #story-issue` + `Closes #epic-issue` (한 줄당 1개 또는 comma 분리)

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
- **Close**: 마지막 task PR 의 commit/PR body `Closes #story-issue` → GitHub 자동 close
- 메인 Claude 사후 작업: stories.md Story `[x]` 체크 (`engineer.md` §1 task = 1 PR 정합 — 본 문서 추가 룰 X)

### 2.2 Epic 완료

- **조건**: epic 의 모든 story closed
- **Close 시점**: 마지막 story 의 마지막 task PR — 메인이 PR 생성 *직전* 1회 사전 체크:
  ```bash
  gh issue list --label epic-NN-<slug> --milestone Story --state open
  ```
  → 이 task merge 시 마지막 story close 예정이면, PR body 에 `Closes #epic-issue` 도 동봉
- 메인 Claude 사후 작업: 마지막 task PR stage 에 `backlog.md` 추가 (Epic NN `[x]` 체크)
- 별도 wrap-up PR 만들지 않음

### 2.3 API 직접 close 절대금지

- `mcp__github__update_issue` state:closed 호출 X (epic / story / 모두)
- 반드시 PR commit message 의 `Closes #N` 으로만 close

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

`/impl` / `/impl-loop` / `architect SYSTEM_DESIGN` (impl 목차 산출 시) / `architect MODULE_PLAN × N` (feature-build-loop §4.2 Step 7) 진입 시 부모 epic stories.md 상단 매치 강제:

- `**GitHub Epic Issue:** [#\d+]` (정식 등록), 또는
- `**GitHub Epic Issue:** 미등록 (사유: …)` (§3 허용 모드)

매치 0건 → 즉시 STOP + 사용자 보고. silent skip ("이슈 번호 없음 — 생략하고 진행") 금지.

story 이슈 부재 시 동일 패턴 (Story N 헤더 직하 `**GitHub Issue:** [#\d+]` 매치).

## 7. 참조

- 시퀀스 / 핸드오프: [`orchestration.md`](orchestration.md)
- loop spec (8 loop 행별 풀스펙): [`orchestration.md`](orchestration.md) §4
- product-planner: [`../../agents/product-planner.md`](../../agents/product-planner.md) §PRODUCT_PLAN
- system-design (impl 목차 표 SSOT): [`../../agents/architect/system-design.md`](../../agents/architect/system-design.md)
- module-plan (impl 본문 detail per task): [`../../agents/architect/module-plan.md`](../../agents/architect/module-plan.md)
- engineer: [`../../agents/engineer.md`](../../agents/engineer.md) §1 task = 1 PR
