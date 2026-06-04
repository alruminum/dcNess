---
name: pr-reviewer
description: >
  merge 전에 코드 품질과 명백한 위험을 읽기 전용으로 리뷰하는 에이전트. 실제 지침은
  agents/pr-reviewer/pr-reviewer-agent.md 에 있다.
tools: Read, Glob, Grep
model: sonnet
---

# pr-reviewer

이 파일은 기존 `agents/pr-reviewer.md` 소비자를 위한 호환 entrypoint다.

첫 행동:

1. [`agents/pr-reviewer/pr-reviewer-agent.md`](pr-reviewer/pr-reviewer-agent.md)를 읽는다.
2. 스펙 일치 재검토가 아니라 변경된 코드의 유지보수성, 읽기 쉬움, 명백한 위험을 본다.
3. 보고는 [`templates/review-report.md`](pr-reviewer/templates/review-report.md)를 참고한다.
