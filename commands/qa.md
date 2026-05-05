---
name: qa
description: 버그/이슈를 자연어로 받아 qa 에이전트로 분류하고 다음 액션을 추천하는 스킬. 사용자가 "버그 있다", "이슈", "이상해", "안 돼", "오류", "@qa", "QA", "큐에이" 등의 표현을 쓸 때 반드시 이 스킬을 사용한다. 분류 결과 (FUNCTIONAL_BUG / CLEANUP / DESIGN_ISSUE / KNOWN_ISSUE / SCOPE_ESCALATE) 에 따라 후속 skill 추천.
---

# QA Skill

## Loop
`qa-triage` ([orchestration.md §3.6](../docs/orchestration.md) / [loop-procedure.md §7.5](../docs/loop-procedure.md)).

## Inputs (메인이 사용자에게 받아야 할 정보)
- 이슈 제목 / 발화
- 재현 조건 (있으면)
- 화면·기능 / 예상 vs 실제 / 에러 메시지

명확화 안 되면 분석 시작 X (대기). qa agent 호출 *전* 위 항목 확보.

## 후속 라우팅 추천 (qa enum 별)
- `FUNCTIONAL_BUG` → `quick-bugfix-loop` (`/quick`) 또는 `impl-task-loop` (`/impl`)
- `CLEANUP` → `quick-bugfix-loop` (`/quick`) 또는 engineer 직접
- `DESIGN_ISSUE` → `ux-design-stage` (`/ux` 또는 designer 직접)
- `KNOWN_ISSUE` → 종료
- `SCOPE_ESCALATE` → 사용자 위임 (큰 변경 / 다중 모듈)

후속 skill 자동 진입 X — 사용자 결정.

## 사전 read (skill 진입 즉시)
`docs/orchestration.md` §3.6 + §4.6 + `docs/handoff-matrix.md` read 후 진행.

## 절차
[`docs/loop-procedure.md`](../docs/loop-procedure.md) §1~§6 + §7.5 (`qa-triage` 풀스펙) 따름. 본 파일은 input 명세 + 라우팅 추천만.
