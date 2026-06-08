# /to-issue Field SSOT

This file is the single source of truth for `/to-issue` issue classification fields. `SKILL.md` must reference this file instead of duplicating these option lists.

When GitHub Project field options or repo labels diverge from this file, stop before creating the issue and report the setup gap. Do not guess option ids or create labels implicitly.

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

| Value | Meaning |
| --- | --- |
| `blocker` | Prevents dependent work or release from moving forward. |
| `critical` | High-risk or time-sensitive issue that should be handled before normal major work. |
| `major` | Normal important work with meaningful product, workflow, or maintenance value. |
| `minor` | Useful but lower urgency work. |
| `trivial` | Small cleanup or polish with limited impact. |

## Usage Rules

- Use the selected `IssueType` value as the repo label.
- Set Project `IssueType` and Project `Priority` to the exact values above.
- Set Project `Status` to `Todo` when registering the issue.
- If a parent issue exists, reference it only. `/to-issue` does not close or rewrite the parent.
