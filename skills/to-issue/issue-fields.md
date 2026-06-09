# /to-issue Field SSOT

This file is the single source of truth for `/to-issue` issue classification fields. `SKILL.md` must reference this file instead of duplicating these option lists. The broader Project lifecycle SSOT is [`../../docs/plugin/github-project.md`].

When GitHub Project field options or repo labels diverge from this file, stop before creating the issue and report the setup gap. Do not guess option ids or create labels implicitly. repo label 6종은 IssueType 축과 같은 의미로 쓴다.

## Status

| Value | Meaning |
| --- | --- |
| `Todo` | Issue has been registered but no target workflow has started yet. |
| `In progress` | A target workflow such as `/spec`, `/design`, `/impl`, or `/ux` has started for the issue. |
| `Done` | The issue was completed by a merged PR that actually closes/fixes/resolves it. |

## IssueType

| Value | Repo label | Meaning |
| --- | --- | --- |
| `epic` | `epic` | Large outcome that groups multiple features or stories. |
| `feature` | `feature` | User-facing or operator-facing capability. |
| `story` | `story` | End-to-end vertical slice that can be implemented and verified independently. |
| `task` | `task` | Non-user-facing work item with a concrete completion condition. |
| `subTask` | `subTask` | Child work item that only makes sense under a parent issue. |
| `bug` | `bug` | Broken or regressed behavior that should be restored. |

## Priority

| Value | Meaning | 추론 신호 (단발 `/to-issue`) |
| --- | --- | --- |
| `blocker` | Prevents dependent work or release from moving forward. | 다른 작업·릴리스가 이 이슈 때문에 막혀 있다. merge/release/복구를 차단. |
| `critical` | High-risk or time-sensitive issue that should be handled before normal major work. | 보안·데이터 손실·실사용자 영향 장애처럼 고위험·시급. `major` 보다 먼저 다뤄야 한다. |
| `major` | Normal important work with meaningful product, workflow, or maintenance value. | 위 둘에 안 걸리고 아래 둘만큼 작지도 않은 표준 기능·버그·개선. |
| `minor` | Useful but lower urgency work. | 있으면 좋지만 급하지 않다. 우회 가능하거나 영향이 국소적. |
| `trivial` | Small cleanup or polish with limited impact. | 오타·문구·소규모 정리처럼 동작 영향이 거의 없다. |

### Priority 추론 (단발 `/to-issue`)

- 단발 `/to-issue` 에는 Priority 기본값이 없다. 명시되지 않았다고 `major` 로 자동 수렴시키지 않는다.
- 명시가 없으면 발화 맥락에서 추론한다. 이슈 성격을 위 "추론 신호" 에 대응시켜 값을 정한다. `Status=Todo` 가 고정값인 것과 달리 Priority 는 케이스별 추론값이다.
- 매번 사용자에게 Priority 를 되묻지 않는다. 추론한 값과 근거를 Issue Brief 초안에 함께 제시하고, 사용자는 원하면 초안에서 교정한다. 교정값이 있으면 그 값을 그대로 따른다.
- epic/story 일괄 생성(`create_epic_story_issues.sh`)은 전부 `major` 고정이며 별도 정책이다 — 본 추론 가이드 대상이 아니다 (의도된 결정, 유지).

## Usage Rules

- Use the selected `IssueType` value as the repo label.
- Set Project `IssueType` and Project `Priority` to the exact values above.
- Set Project `Status` to `Todo` when registering the issue.
- Move Project `Status` to `In progress` when a target workflow starts.
- Move Project `Status` to `Done` only from `Closes`, `Fixes`, `Resolves`, or GitHub closing references after default-branch merge. `Part of #N` is not a Done signal.
- If a parent issue exists, reference it only. `/to-issue` does not close or rewrite the parent.
