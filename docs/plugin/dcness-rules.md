# dcness Rules

> dcness plugin 활성 프로젝트 (`init-dcness` 등록) 의 매 세션에 SessionStart 훅이 본 내용을 system-reminder 로 inject.
> 대원칙 + 라우팅 가이드 + 특히 중요한 운영 룰 강조.

## 1. 대원칙

**harness 가 강제하는 것은 단 2가지:**
1. **작업 순서** — 에이전트 시퀀스 (validator → engineer → pr-reviewer 등) + retry 정책
2. **접근 영역** — 파일 경계 (agent-boundary ALLOW/READ_DENY) + 외부 시스템 mutation 차단

**그 외 모두 에이전트 자율.** 출력 형식 / prose 구조 / handoff 형식 / 판단 방식 = 강제 없음.

**에이전트의 prose 가 작업의 유일한 증거다.** harness 는 prose 마지막 영역에서 결과 enum 을 heuristic 추출하고, 메인 Claude 는 그걸 사용자에게 echo 한다 (§3.3).

### 안티패턴

**1. 룰이 룰을 부르는 reactive cycle** — 신규 룰 추가 전 기존 룰 제거 가능성 먼저 검토. 추가→제거 비대칭이 기술 부채.

**2. 강제 vs 권고 혼동**
- 강제(block): catastrophic 만 (plugin-write-guard, agent-boundary)
- 권고(warn): 그 외 — 형식 위반 / 비용 폭증 등은 측정 + 경고 + 사용자 개입
- 권고 → 강제 자동 승격 금지

**3. 에이전트 자율성 침해** — agent prompt 에 강제 형식 박기 금지. 결론 + 이유 명확히 쓰도록 가이드만 (형식이 아니라 의미).

**4. 불필요한 흐름 강제** — 시퀀스 보존은 catastrophic 만. 시퀀스 내부 행동 = 에이전트 자율.

### 도입 안 할 것

- 출력 형식 강제 (marker / status JSON / @OUTPUT_SCHEMA)
- handoff 형식 강제 (next_actions[] 등 구조)
- Flag 시스템 (boolean flag 파일)
- preamble 자동 주입

### 메인 Claude 필수 준수

**파일 경로 표기 — MUST**: 파일을 언급할 때는 반드시 클릭 가능한 풀 경로로 쓴다. 파일명 뒤에 공백을 둬야 링크가 깨지지 않는다.
- ❌ `dcness-rules.md 에서 확인` → ✅ `docs/plugin/dcness-rules.md 에서 확인`

**진행 불가 시 — MUST**: 도구·권한·정보 부족으로 목표 달성이 불가할 때 추측 진행하지 않고 사용자에게 명시 요청:
- (a) 무엇이 부족한지
- (b) 왜 필요한지
- (c) 어떻게 얻을 수 있는지

사용자 권한 부여 받은 후 진행.

---

## 2. 라우팅 가이드

세션 시작 시 이 테이블 외 추가 read 하지 말 것 — skill 트리거 시 해당 skill 파일의 `## 사전 read` 섹션이 정확한 경로와 섹션 번호를 안내한다.

| 상황 | 읽어야 할 문서 | 섹션 |
|---|---|---|
| 루프 진입 / 시퀀스 결정 | [`orchestration.md`](orchestration.md) | §3 mini-graph + §4 해당 loop |
| Step 0~8 실행 절차 | [`loop-procedure.md`](loop-procedure.md) | 전체 |
| agent 호출 분기 / retry / escalate 한도 | [`handoff-matrix.md`](handoff-matrix.md) | §1~§3 |
| agent 접근 권한 (Write/Read 경계) | [`handoff-matrix.md`](handoff-matrix.md) | §4 |
| 실존 검증 룰 + dcness 특화 안티패턴 | [`../internal/self-guidelines.md`](../internal/self-guidelines.md) | §2 |
| dcness 자체 작업 룰 (300줄 cap 등) | [`../internal/self-guidelines.md`](../internal/self-guidelines.md) | §1 |
| yolo 모드 / worktree 격리 상세 | [`loop-procedure.md`](loop-procedure.md) | §3.3 yolo / §1.1 worktree |

skill 들은 input 정형화 + Loop 추천만, 절차는 loop-procedure, loop spec 은 orchestration §4.

## 3. 에이전트 루프 개요

에이전트 1회 호출의 최소 실행 단위:

```
TaskUpdate(in_progress)
  begin-step <agent>              § 3.1
  Agent(subagent_type=<agent>)    § 3.2
  end-step <agent>                § 3.3
TaskUpdate(completed)
```

## 3.1 begin-step

```bash
"$HELPER" begin-step <agent> [<MODE>]
```

`begin-step` stdout 에 `[INSIGHTS: <agent>/<mode>]` 섹션이 있으면 Agent 프롬프트 끝에 그대로 추가한다. 해당 에이전트의 이전 루프 학습 내용("하지 말 것" / "잘 됐던 것")이 프로젝트 레벨로 누적된 것.

## 3.2 에이전트 호출

```
Agent(subagent_type=<agent>, mode=<MODE>, description="...")
```

begin-step 에서 전달된 INSIGHTS 가 있으면 prompt 에 포함.

## 3.3 end-step

```bash
ENUM=$("$HELPER" end-step <agent> [<MODE>] --allowed-enums "<csv>")
```

**시점**: Agent 완료 직후 → TaskUpdate(completed) 전

### 결과 echo + 평가 — MUST (5~12줄)

```
[<task-id>.<agent>] echo

▎ <prose 의 ## 결론 / ## Summary / ## 변경 요약 섹션 본문 5~12줄>
▎ <섹션 부재 시 prose 첫 5~10줄 fallback>
▎ <필요 시 추가 본문 인용 — 12줄 cap>

결론: <ENUM>
평가: PASS / REDO_SAME / REDO_BACK / REDO_DIFF — <사유>
```

- `<task-id>` = standalone 시 step 이름, `/impl-loop` 안 시 `b<i>.<agent>`
- `▎` 글자 (U+258E) 그대로 — 사용자 인식 패턴
- 5줄 미만 / 12줄 초과 = 룰 위반

**평가 기준**: 에이전트 결과를 받으면 바로 다음 step으로 넘어가지 않고 충분한지 먼저 판단한다. 미진한 결과를 통과시키면 다음 step이 그 위에 쌓여 나중에 더 큰 redo 비용이 발생한다.

| 평가 | 의미 |
|---|---|
| `PASS` | 결과 충분, 다음 step 진입 |
| `REDO_SAME` | 같은 접근으로 재시도 |
| `REDO_BACK` | 이전 step으로 돌아가 재실행 |
| `REDO_DIFF` | 다른 접근 / 다른 에이전트로 재시도 |

REDO 판단 신호: 결과가 질문에 제대로 답하지 못함 / 같은 tool 5회+ 반복 / boundary 위반 stderr / 기대 enum 불일치.

루프 순서 변경도 자유 — architect 재실행, 다른 에이전트 호출 등 적극.

**echo 안티패턴**:
- ❌ 압축 paraphrase 1~2줄로 끝내기
- ❌ table / code block 통째 생략
- ❌ "토큰 아끼려" 결론만 echo
- ❌ 평가 줄 빠뜨리기

### 자가 점검 (TaskUpdate(completed) 전)

```
□ prose read 했는가?
□ ## 결론 / ## Summary / ## 변경 요약 섹션 우선 추출했는가?
□ 5~12줄 echo 했는가?
□ 결론 enum + 평가 포함됐는가?
```

### AMBIGUOUS 처리

`end-step` stdout = `AMBIGUOUS` 시:
1. 재호출 1회 (결론 enum 명시 요청)
2. 재호출도 AMBIGUOUS → 사용자 위임 (enum 후보 + prose 발췌)

### helper 안전망 (자동 검출)

- **drift WARN**: live.json `current_step` 과 `args.agent` 불일치 → stderr WARN
- **step count WARN**: `finalize-run --expected-steps N` row count 미달 → stderr WARN
- 자동 보정 X — 메인이 사후 인지 + `/run-review` 진단

## 3.4 step 명명 규칙

같은 에이전트를 재호출할 때 begin/end-step 쌍의 이름:

| 상황 | 이름 패턴 |
|---|---|
| POLISH 사이클 | `engineer:POLISH-1`, `engineer:POLISH-2` |
| TESTS_FAIL 재시도 | `engineer:IMPL-RETRY-1`, `engineer:IMPL-RETRY-2` |

재호출마다 별도 begin/end-step 1쌍 필수.

**안티패턴** (begin/end-step 쌍 누락):
- ❌ engineer commit/PR 후 git status 확인 → end-step skip
- ❌ CHANGES_REQUESTED 후 POLISH Agent 호출 시 begin/end-step 미포함
- ❌ end-step 보류 중 다음 step 진입으로 망각
- ❌ task 간 보고 작성 후 begin-step 재호출 누락

## 4. 루프 종료 후 리뷰 출력

`finalize-run --auto-review` 로 자동 출력된다. `--auto-review` 없이 실행됐을 경우 수동으로:

```bash
"$(dirname "$HELPER")/dcness-review" --run-id "$RUN_ID" --repo "$(pwd)"
```

skip 금지 — 사용자 보고 전 1회 의무.

### 세션에 직접 출력 — MUST

Bash stdout 은 CC UI 에서 collapsed (펼쳐야 보임). 리뷰 결과를 **텍스트 응답으로 그대로 복사**해서 출력한다.

- 섹션 생략 / 축약 / 재배치 금지
- 자체 해석 ("핵심은~", "정리하면~") 본문 사이 삽입 금지

### 개선점 코멘트 — MUST

리뷰 출력 끝에 메인 Claude 가 1~3줄 코멘트 추가:

```
💡 이번 run 개선점:
- <이번 run 에서 발견된 반복 실수 / 낭비 요약>
- <다음 run 에서 주의할 점>
```


