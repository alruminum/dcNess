---
name: code-validator
description: >
  구현 계획과 실제 코드의 정합을 읽기 전용으로 검증하는 에이전트. 실제 지침은
  agents/code-validator/code-validator-agent.md 에 있다.
tools: Read, Glob, Grep
model: sonnet
---

# code-validator

이 파일은 기존 `agents/code-validator.md` 소비자를 위한 호환 entrypoint다.

첫 행동:

1. [`agents/code-validator/code-validator-agent.md`](code-validator/code-validator-agent.md)를 읽는다.
2. 검증은 고정 항목을 세는 방식이 아니라 구현 계획, 변경 범위, 의존 계약, 위험 축을 증거로 확인한다.
3. 보고는 [`templates/validation-report.md`](code-validator/templates/validation-report.md)를 참고한다.
