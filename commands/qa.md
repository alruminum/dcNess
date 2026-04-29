---
name: qa
description: 버그/이슈를 자연어로 받아 qa 에이전트로 분류하고 다음 액션을 추천하는 스킬. 사용자가 "버그 있다", "이슈", "이상해", "안 돼", "오류", "@qa", "QA", "큐에이" 등의 표현을 쓸 때 반드시 이 스킬을 사용한다. dcNess 컨베이어 패턴 (Task tool + Agent + helper + 훅) 으로 동작. 분류 결과 (FUNCTIONAL_BUG / CLEANUP / DESIGN_ISSUE / KNOWN_ISSUE / SCOPE_ESCALATE) 에 따라 후속 skill 추천.
---

# QA Skill — 버그/이슈 분류 + 라우팅 추천

> 본 skill 은 dcNess `docs/conveyor-design.md` 의 Task tool + helper protocol 으로 동작한다.
> qa agent 호출 → prose 종이 저장 → enum 추출 → 결과 보고. 분류 결과만 사용자에게 보여주고 후속 skill 은 사용자가 결정.

## 언제 사용하는가

- 사용자 발화에 다음 keyword 포함 — "버그", "이슈", "이상해", "안 돼", "안 맞아", "오류", "깨져", "@qa", "QA", "큐에이", "에러"
- 또는 사용자가 어떤 동작/결과가 잘못됐다고 보고
- 분류·라우팅 추천이 목적

## 언제 사용하지 않음

- "간단히 고쳐줘" / "한 줄 수정" → `/quick` (구현 후)
- "새 기능", "피쳐 추가", "기획" → `/product-plan` (구현 후)
- "디자인 바꿔", "레이아웃" → `/ux` (구현 후)
- 코드 변경 의도 명확하고 분류 불필요 → `/quick` 또는 직접 architect 호출

## 가시성 룰 — 매 Agent 호출 후 메인 text echo (필수)

CC collapsed 회피 — Agent 호출 후 메인이 text reply 로 prose 핵심 5~12줄 echo
(DCN-CHG-30-11). prose 의 `## 결론` / `## Summary` 섹션 우선 인용, 부재 시 첫 줄
fallback. 자세한 룰은 `commands/quick.md` "가시성 룰" 절 참조.

## 절차 (Task tool + helper protocol)

### Step 0 — run 시작

```bash
RUN_ID=$("$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" begin-run qa)
echo "[qa] run started: $RUN_ID"
```

`begin-run` 내부 동작:
- sid auto-detect (PPID chain + by-pid lookup)
- run_id 생성 (`run-{token_hex(4)}`)
- `live.json.active_runs[run_id]` 슬롯 추가
- `.by-pid-current-run/{cc_pid}` ← run_id

### Step 1 — Task 생성

```
TaskCreate("qa: 이슈 분류")
```

(단일 task 만. 추가 단계는 사용자 결정 후.)

### Step 2 — 사용자 입력 명확화 (필요 시)

agent 호출 전, 다음 중 하나라도 모호하면 사용자에게 역질문:
- 재현 조건
- 화면/기능/컴포넌트
- 예상/실제 동작 차이
- 에러 메시지/로그
- 발생 범위 (항상 vs 특정 조건)

이미 명확하면 skip. 명확화 안 되면 분석 시작 X (사용자 응답 대기).

### Step 3 — qa Agent 호출

```
TaskUpdate("qa: 이슈 분류", in_progress)
```

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" begin-step qa
```

`Agent` 도구 호출:
```
Agent(
  subagent_type="qa",
  description="<사용자 발화 및 명확화된 컨텍스트>"
)
```

agent prose 가 메인 transcript 에 자동 박힘.

### Step 4 — prose 저장 + enum 추출

메인 transcript 의 prose 본문을 임시 파일에 저장 후 helper 호출:

```bash
# prose 를 here-doc 으로 임시 파일 작성 (메인이 transcript 에서 가져옴)
cat > /tmp/dcness-qa-prose.md << 'PROSE_EOF'
<agent prose 본문 그대로>
PROSE_EOF

# end-step
ENUM=$("$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" end-step qa \
    --allowed-enums "FUNCTIONAL_BUG,CLEANUP,DESIGN_ISSUE,KNOWN_ISSUE,SCOPE_ESCALATE" \
    --prose-file /tmp/dcness-qa-prose.md)
echo "[qa] classification: $ENUM"
```

`end-step` 내부 동작:
- prose 를 `.sessions/{sid}/runs/{rid}/qa.md` 로 atomic write
- `interpret_with_fallback` (heuristic only — no haiku)
- 휴리스틱이 prose 마지막 영역에서 enum 단어 매칭
- stdout: 추출된 enum 1단어, 또는 `"AMBIGUOUS"` (실패 시)

### Step 5 — AMBIGUOUS 처리 (실패 시 cascade)

`end-step` stdout 이 `"AMBIGUOUS"` 면 다음 순서로 처리:

#### 5-1. agent 재호출 (1회)

```
Agent(
  subagent_type="qa",
  description="직전 응답에서 결론 enum 미명시. FUNCTIONAL_BUG / CLEANUP / DESIGN_ISSUE / KNOWN_ISSUE / SCOPE_ESCALATE 중 하나로 prose 마지막 단락에 명시해서 다시 분석해줘. 원본 이슈: <사용자 발화>"
)
```

재호출 prose 받으면 Step 4 반복. enum 추출되면 Step 6 진행.

#### 5-2. 재호출도 AMBIGUOUS 면 사용자 위임

```
사용자에게:
"qa 가 결론을 명확히 안 적었습니다. 본문 발췌:
   <prose tail 발췌>

다음 중 어느 분류로 진행할까요?
1) FUNCTIONAL_BUG  (기능 버그 — impl 루프)
2) CLEANUP         (코드 정리 — impl 루프 light)
3) DESIGN_ISSUE    (디자인 이슈 — designer)
4) KNOWN_ISSUE     (이미 알려진 — 종료)
5) SCOPE_ESCALATE  (분류 모호 — 사용자 결정)
6) 종료"
```

사용자 응답 받으면 그 enum 으로 진행.

### Step 6 — 결과 보고 + 후속 skill 추천

```
TaskUpdate("qa: 이슈 분류", completed)
```

분류 결과 + 라우팅 추천 출력:

```
[qa 분류 결과] $ENUM

prose 종이: .claude/harness-state/.sessions/{sid}/runs/{rid}/qa.md

다음 추천:
- FUNCTIONAL_BUG → /quick (구현 후) 또는 architect LIGHT_PLAN 직접 호출
- CLEANUP        → /quick (구현 후) 또는 engineer 직접 호출
- DESIGN_ISSUE   → /ux (구현 후) 또는 designer 직접 호출
- KNOWN_ISSUE    → 종료 (이미 알려진 이슈)
- SCOPE_ESCALATE → 사용자 결정 필요 (분류 모호)

진행할까요? 사용자 결정 대기.
```

후속 skill 자동 진입 안 함 (사용자가 결정). FUNCTIONAL_BUG / CLEANUP 의 경우 `/quick` 미구현 시 architect 직접 호출 가이드 제공.

### Step 7 — run 종료

사용자 응답에 따라:
- 후속 진행 → run 유지 (다음 step 시작 — 다른 skill 진입)
- 종료 → `"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" end-run`

```bash
"$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)/scripts/dcness-helper" end-run
```

`end-run` 내부:
- `live.json.active_runs[rid].completed_at` 채움 (soft tombstone)
- `.by-pid-current-run/{cc_pid}` 삭제

## Catastrophic 룰 정합

본 skill 은 catastrophic 위반 없음:
- qa agent 는 HARNESS_ONLY_AGENTS 미해당 — run 컨텍스트 없어도 호출 가능 (단 본 skill 은 begin-run 으로 컨텍스트 만듦 — prose 저장 / live.json 갱신 위해)
- §2.3 4룰 모두 qa 무관

`docs/conveyor-design.md` §8 의 catastrophic-gate.sh 가 자동 통과.

## 한계 / 후속

- **`/quick`, `/ux` 미구현** — 본 skill 은 분류만 하고 다음 skill 자동 진입 안 함. 별도 Task 에서 후속 skill 추가 시 자동 라우팅 활성.
- **재현 검증 안 함** — qa agent 가 분류 + 추적 ID 발급. 실제 재현은 다음 단계 (engineer/designer) 책임.
- **휴리스틱 fail rate 측정** — `.metrics/heuristic-calls.jsonl` 누적. fail rate 30%+ 면 agent prose writing guide 정정 (haiku fallback 폐기 — DCN-CHG-20260430-04 heuristic-only 정착).

## 참조

- `agents/qa.md` — qa 에이전트 system prompt (5 결론 enum 출처)
- `docs/orchestration.md` §3.6 — qa 라우팅 시퀀스
- `docs/orchestration.md` §4.11 — qa 결론 enum → 다음 trigger 결정표
- `docs/conveyor-design.md` §2 / §3 / §7 — Task tool + helper protocol + 훅 책임
- `harness/session_state.py` — begin-run / begin-step / end-step / end-run helpers
