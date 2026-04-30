---
name: qa
description: 버그/이슈를 자연어로 받아 qa 에이전트로 분류하고 다음 액션을 추천하는 스킬. 사용자가 "버그 있다", "이슈", "이상해", "안 돼", "오류", "@qa", "QA", "큐에이" 등의 표현을 쓸 때 반드시 이 스킬을 사용한다. dcNess 컨베이어 패턴 (Task tool + Agent + helper + 훅) 으로 동작. 분류 결과 (FUNCTIONAL_BUG / CLEANUP / DESIGN_ISSUE / KNOWN_ISSUE / SCOPE_ESCALATE) 에 따라 후속 skill 추천.

---

# QA Skill — 버그/이슈 분류 + 라우팅 추천

> 공통 룰 (가시성 / AMBIGUOUS / Catastrophic) SSOT = `commands/quick.md`. qa agent 호출 → enum 추출 → 결과 보고. 후속 skill 자동 진입 X.

## 사용

- 트리거: "버그", "이슈", "이상해", "안 돼", "오류", "에러", "@qa", "QA"
- 비대상: 한 줄 수정 명확 → `/quick` · 새 기능 → `/product-plan` · 디자인 → `/ux`

## 절차

### Step 0 — run 시작

```bash
HELPER="$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper"
RUN_ID=$("$HELPER" begin-run qa)
echo "[qa] run started: $RUN_ID"
```

`begin-run` 동작: sid auto-detect (PPID + by-pid) · run_id 생성 · `live.json.active_runs` 슬롯 + `.by-pid-current-run/{cc_pid}` 박음.

### Step 1 — Task 등록

```
TaskCreate("qa: 이슈 분류")
```

### Step 2 — 입력 명확화 (필요 시)

agent 호출 전 다음 모호 시 역질문: 재현 조건 / 화면·기능 / 예상 vs 실제 / 에러 메시지 / 발생 범위. 명확화 안 되면 분석 시작 X (대기).

### Step 3 — qa Agent 호출 + enum 추출

```
TaskUpdate("qa: 이슈 분류", in_progress)
"$HELPER" begin-step qa
Agent(subagent_type="qa", description="<사용자 발화 + 명확화 컨텍스트>")
```

prose 받으면:
```bash
cat > /tmp/dcness-qa-prose.md << 'PROSE_EOF'
<agent prose 본문>
PROSE_EOF

ENUM=$("$HELPER" end-step qa \
       --allowed-enums "FUNCTIONAL_BUG,CLEANUP,DESIGN_ISSUE,KNOWN_ISSUE,SCOPE_ESCALATE" \
       --prose-file /tmp/dcness-qa-prose.md)
echo "[qa] classification: $ENUM"
```

`end-step` 동작: prose `.sessions/{sid}/runs/{rid}/qa.md` atomic write · `interpret_with_fallback` (heuristic-only, no haiku — DCN-CHG-30-04) · stdout = enum 또는 `AMBIGUOUS`.

가시성 룰 의무 echo (commands/quick.md 의무 템플릿).

### Step 4 — AMBIGUOUS cascade

`commands/quick.md` SSOT 와 동일:
1. **재호출 1회** — 결론 enum 명시 요청
2. **재호출도 AMBIGUOUS** → 사용자 위임:

```
qa 가 결론을 명확히 안 적었습니다. 본문 발췌:
   <prose tail>

다음 중 어느 분류로 진행할까요?
1) FUNCTIONAL_BUG  (기능 버그 — impl 루프)
2) CLEANUP         (코드 정리 — impl 루프 light)
3) DESIGN_ISSUE    (디자인 이슈 — designer)
4) KNOWN_ISSUE    (이미 알려진 — 종료)
5) SCOPE_ESCALATE  (분류 모호 — 사용자 결정)
6) 종료
```

### Step 5 — 결과 보고 + 라우팅 추천

```
TaskUpdate("qa: 이슈 분류", completed)
```

```
[qa 분류 결과] $ENUM
prose 종이: .claude/harness-state/.sessions/{sid}/runs/{rid}/qa.md

다음 추천:
- FUNCTIONAL_BUG → /quick 또는 architect LIGHT_PLAN 직접
- CLEANUP        → /quick 또는 engineer 직접
- DESIGN_ISSUE   → /ux 또는 designer 직접
- KNOWN_ISSUE    → 종료
- SCOPE_ESCALATE → 사용자 결정 필요

진행할까요? 사용자 결정 대기.
```

후속 skill 자동 진입 X — 사용자 결정.

### Step 6 — run 종료

후속 진행 → run 유지. 종료 → `"$HELPER" end-run` (live.json 의 `completed_at` 채움 + `.by-pid-current-run/{cc_pid}` 삭제).

## Catastrophic 룰 정합

qa 는 HARNESS_ONLY_AGENTS 미해당 — run 컨텍스트 없어도 호출 가능. §2.3 4룰 모두 qa 무관 → catastrophic-gate.sh 자동 통과.

## 한계

- 후속 skill 자동 진입 X (사용자 결정)
- 재현 검증 X — 다음 단계 (engineer/designer) 책임
- 휴리스틱 fail rate `.metrics/heuristic-calls.jsonl` 누적 — 30%+ 면 agent prose writing guide 정정

## 참조

- `agents/qa.md` (5 결론 enum 출처)
- `docs/orchestration.md` §3.6 / §4.11
- `docs/conveyor-design.md` §2 / §3 / §7
- `harness/session_state.py` (begin-run / begin-step / end-step / end-run)
- `commands/quick.md` (가시성 / AMBIGUOUS cascade SSOT)
