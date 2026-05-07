---
name: quick
description: 작은 버그픽스·코드 정리를 한 줄로 받아 light path (qa → architect LIGHT_PLAN → engineer simple → validator BUGFIX_VALIDATION → pr-reviewer) 자동 진행하는 스킬. 사용자가 "간단히 해줘", "작은 수정", "한 줄 버그", "/quick", "퀵", "바로 고쳐줘", "오타 고쳐", "간단한 수정" 등을 말할 때 반드시 이 스킬을 사용한다. 분류 결과가 FUNCTIONAL_BUG / CLEANUP 면 자동 진행, 그 외 (DESIGN_ISSUE / KNOWN_ISSUE / SCOPE_ESCALATE) 면 사용자 결정.
---

# Quick Skill

## Loop
`quick-bugfix-loop` ([orchestration.md §3.5 / §4.5](../docs/plugin/orchestration.md)).

## Inputs (메인이 사용자에게 받아야 할 정보)
- 이슈 요약 (한 줄 — 무엇이 잘못됐나)
- 영향 파일 / 위치 (있으면)
- 재현 조건 (있으면)
- 원하는 방향 (있으면)

명확화 안 되면 분석 시작 X (대기). qa agent 호출 *전* 위 항목 확보.

## 비대상 (다른 skill 추천)
- 새 기능 → `/product-plan` (`feature-build-loop`)
- 디자인 → `/ux` (`ux-design-stage`)
- 다중 모듈 / 큰 변경 → `/qa` 정석 분류 또는 `/impl`

## 후속 라우팅 (qa enum 별)
- `FUNCTIONAL_BUG` → 본 loop advance · branch prefix `fix/`
- `CLEANUP` → 본 loop advance · branch prefix `chore/`
- `DESIGN_ISSUE` → 종료 + `/ux` 추천
- `KNOWN_ISSUE` → 종료
- `SCOPE_ESCALATE` → 사용자 위임 (큰 변경 / 다중 모듈)

## 사전 read (skill 진입 즉시)
`docs/plugin/loop-procedure.md` + `docs/plugin/orchestration.md` §4.5 + `docs/plugin/handoff-matrix.md` read 후 진행.

## 워크트리 (기본 켜짐)
Step 0 진입 시 자동 `EnterWorktree(name="quick-{ts_short}")`. 사용자 발화에 정규식 `워크트리\s*(빼|없|말)` 매치 시에만 건너뜀. 자세히 = [`docs/plugin/loop-procedure.md`](../docs/plugin/loop-procedure.md) §1.1.

## 절차
[`docs/plugin/loop-procedure.md`](../docs/plugin/loop-procedure.md) §1~§6 + [`docs/plugin/orchestration.md`](../docs/plugin/orchestration.md) §4.5 (`quick-bugfix-loop` 풀스펙) 따름. 본 파일은 input 명세 + 라우팅만.
