---
name: next
description: GitHub Project 보드에서 현재 In progress 항목과 다음 Todo 후보를 조회하는 read-only 유틸리티. 사용자가 "/next", "다음 작업", "뭐부터 하지", "진행 중 작업", "콜드스타트 시작점" 등을 말할 때 사용한다.
---

# Next — 다음 작업 read-only 조회

> GitHub Project Status 를 읽어 cold-start 세션의 시작점을 확인한다. Project/issue 상태를 쓰거나 변경하지 않는다.

## 언제 사용

- 새 세션에서 다음 작업이나 시작점을 확인할 때
- 현재 In progress 항목과 Todo 후보를 빠르게 보고 싶을 때
- `docs/index.md` 의 정적 포인터만으로는 live 상태를 알 수 없을 때

## 절차

```bash
SCRIPT="$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | sort -V | tail -1)/scripts/github_project_lifecycle.mjs"
node "$SCRIPT" next
```

사용자가 repo / Project 좌표를 명시한 경우에만 flag 를 그대로 전달한다.

```bash
node "$SCRIPT" next --repo OWNER/REPO --owner OWNER --project PROJECT_NUMBER
```

## 동작 계약

- read-only: `--apply` 를 쓰지 않고, Project/issue/PR 상태를 변경하지 않는다.
- 좌표 해석: flag → `DCNESS_PROJECT_*` env → repo variable → repo owner fallback 순서.
- Project 좌표가 없으면 실패로 끝내지 않고 `/init-dcness` bootstrap 안내를 출력한다.
- 출력은 `In progress` 와 `Next Todo` 요약이다. 필요하면 사용자는 GitHub Project 보드에서 live 상태를 직접 확인한다.

## 참조

- [`issue-lifecycle.md` Project lifecycle](../docs/plugin/issue-lifecycle.md#github-project-status-lifecycle)
- [`positioning.md` Utility 공개 노출 범위](../docs/plugin/positioning.md#utility-공개-노출-범위)
