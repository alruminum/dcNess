# 병렬 wave 실행 정책 (parallel wave execution policy)

> impl chain 의 **opt-in 병렬 확장** 정책 SSOT. 기본은 직렬 chain 이고, 병렬은 독립 task 가 명확히 판정될 때만 켜지는 예외다. 상위 doctrine = [`CLAUDE.md` dcness 강제 원칙](../../CLAUDE.md#dcness-강제-원칙-룰-추가설계-시-가드레일). lane/shape 판정 = [`workflow-router.md`](workflow-router.md). chain mechanics = [`loop-procedure.md`](loop-procedure.md).
>
> 🔴 **범위 주의** — 본 문서는 *정책*(허용/금지 조건 · 권한 경계 · 판정 입력 스키마)을 고정한다. 병렬 wave 를 실제로 오케스트레이션하는 **driver 구현은 본 문서 범위 밖**이며 후속 작업이다. 현재 [`impl-loop`](../../skills/impl-loop/SKILL.md) chain 은 **직렬로만 동작**한다.

## 1. doctrine — 직렬이 기본, 병렬은 조건부 예외

- **기본은 현행 직렬 chain.** impl chain (N task) 은 task 한 개씩 직렬 진행이 default 다. 한 task 가 완전히 끝난(PR 머지 + 이슈 close) 뒤에만 다음 task 에 진입한다.
- **병렬은 opt-in.** 서로 독립인 task 가 명확히 판정되고 wave 로 묶을 수 있을 때만 켜진다. 모호하면 켜지 않는다.
- **leader-owned governance 보존.** run ledger / PR 생성·머지 / issue close / final checkpoint 는 leader(메인)만 소유한다. 병렬은 처리량 최적화지 governance 완화가 아니다.
- **위험 경계는 그대로.** 병렬은 사전 ceremony(직렬 대기)를 줄이는 것이지, branch / PR / test / review / CI / false-clean 방지 같은 safety gate 를 줄이는 것이 아니다.

## 2. 실행모델 — worktree 격리 fan-in

병렬은 **build 단계만 병렬**이고, governance 단계(PR·merge·close)는 **leader-owned 직렬 fan-in**으로 유지한다.

```text
[build 단계 — 병렬]                       [fan-in gate]              [merge 단계 — 직렬]
worker A ─ worktree A ─ patch/evidence ─┐
worker B ─ worktree B ─ patch/evidence ─┤→ leader: 별도 fan-in     → PR_A → merge → close
worker C ─ worktree C ─ patch/evidence ─┘   worktree 서 patch 합쳐    PR_B → merge → close
   (PR/merge/issue/ledger 권한 없음)          aggregate tree test        PR_C → merge → close
                                              + scope/conflict 검증
                                              PASS 필요
```

- worker 의 병렬 단계는 **산출물 생산만** 한다: code diff/patch, 테스트·검증 명령 결과, evidence prose.
- worker 가 transport 용도의 로컬 checkpoint commit 을 남길 수는 있어도 그것은 **authoritative commit 이 아니다**. authoritative commit / PR / merge / issue close / ledger checkpoint 는 leader 만 만든다. (문서·핸드오프에서는 `commit` 대신 **patch/evidence** 로 표기해 혼선을 막는다.)
- leader 는 별도 fan-in worktree 에서 wave patch 들을 합쳐 aggregate tree 를 만들고 전체 테스트를 1회 이상 돌린다.
- **aggregate gate PASS 는 merge 단계 진입 허가일 뿐, PR 별 검증을 생략하는 면허가 아니다.** 각 task 의 PR 은 기존 규칙대로 pr-reviewer 와 CI 를 그대로 탄다.

### 2.1 왜 "한 세션 안 병렬 Agent" 가 아닌가

active conveyor run 안의 `Agent` 호출은 직전 `begin-step` 의 단일 `current_step` 슬롯과 일치해야 통과한다(strict conveyor gate). 한 세션에서 sub-agent 를 동시에 발사하면 이 "step 당 agent 1개 순차 전제"를 위반한다 — 자세히 = [`hooks.md`](hooks.md). 한 세션 병렬을 정식 실행모델로 삼으려면 `current_step` 단일 슬롯 / ledger / run-review / ROI marker 상태모델을 한꺼번에 재설계해야 하므로, 본 정책 범위를 넘는 별도 대형 설계로 분리한다. 따라서 병렬 단위는 **worktree/session 격리**다.

## 3. 독립성 판정 — 어떤 task 가 같은 wave 에 묶이나

```text
같은 wave 병렬 가능 = depends_on 위상상 서로 선후 없음   (DAG)
                   AND Scope 파일집합 disjoint           (충돌 그래프)
```

판정은 **두 축**을 함께 본다. 둘은 종류가 다른 그래프라 하나로 합치지 않는다.

| 축 | 방향성 | 의미 | 입력 위치 |
|---|---|---|---|
| `depends_on` | directed (선후) | task 실행 선후. **contract produces/consumes 와 ordering 을 모두 흡수한 단일 SSOT** | impl task frontmatter ([`impl-task.md`](../../agents/module-architect/templates/impl-task.md)) |
| Scope 파일집합 | undirected (동시 금지) | 두 task 의 `수정 허용` 파일 경로 교집합 ≠ ∅ → 같은 wave 금지 | impl task `Scope > 수정 허용` |

- **방향 있는 의존(contract 사슬·ordering·명시 선후)은 `depends_on` 하나로 통합**한다. 같은 정보를 여러 칸에 중복 기재하지 않는다. contract produces→consumes 사슬은 `depends_on` 간선으로 유도된다.
- **파일 충돌은 `depends_on` 에 합치지 않는다.** `depends_on` 은 "누가 먼저"(순서)인데 파일 충돌은 "동시에 금지, 순서는 무관"(상호배제)이라 성질이 다르다. 억지로 합치면 (a) 없는 순서를 강제하고 (b) 의미를 왜곡한다. 대신 별도 필드를 신설하지 않고 이미 적는 `수정 허용` 파일 목록의 교집합으로 자동 계산한다.

### 3.1 빈 값은 "독립" 이 아니라 "미상"

`depends_on` 이나 Scope 가 비어 있으면 그것은 "독립이라서"가 아니라 "기록이 없어서"다. 미상(unknown)은 독립(independent)이 아니다. 독립 확신이 서지 않는 task 는 병렬 후보에서 빼고 직렬로 강등한다(아래 "병렬 금지 조건"). 병렬은 두 축이 모두 disjoint 라고 확신될 때만 켜진다.

## 4. 병렬 금지 조건 (fallback → 직렬 강등)

다음 중 하나라도 해당하면 해당 task(또는 wave 전체)를 직렬 chain 으로 강등한다.

- `depends_on` 이 불명확하거나 미기재.
- `수정 허용` 이 파일 경로 단위로 정규화되지 않음(자유 서술).
- 다른 task 와 Scope 파일집합이 겹침.
- fan-in 시 diff 충돌 발생.
- worker evidence 가 부족해 검증 불가.
- fan-in 검증(aggregate test / scope·conflict) 실패.
- migration / destructive / security / 도메인 invariant 변경 같은 고위험 task.

## 5. 권한 경계 — leader-owned vs worker

| 행위 | leader (메인) | worker |
|---|---|---|
| run ledger 이벤트 (run/step/next-task/checkpoint marker) | ✅ 소유 | ❌ 금지 |
| authoritative commit / PR 생성 / PR body trailer | ✅ | ❌ |
| pr-reviewer 호출 / merge / issue close | ✅ | ❌ |
| final checkpoint | ✅ | ❌ |
| 격리 worktree 안 code diff/patch 생산 | — | ✅ |
| 테스트·검증 명령 실행 + 결과 반환 | — | ✅ |
| evidence prose 반환 | — | ✅ |
| transport 용 로컬 checkpoint commit (non-authoritative) | — | ✅ |

병렬 worker 완료가 곧 task 완료가 아니다. task 완료는 leader 의 PR merge + issue close 로만 성립한다.

## 6. fan-in 검증 최소 절차 (leader)

1. 각 worker worktree 의 diff + evidence 를 수집한다.
2. 별도 fan-in worktree 에서 wave 의 patch 들을 합친다.
3. scope 준수(각 patch 가 자기 Scope 안인가)와 diff 충돌 여부를 확인한다.
4. aggregate tree 전체 테스트를 1회 이상 돌린다.
5. PASS → merge 단계 진입(각 task PR 은 기존 pr-reviewer·CI 그대로). FAIL → 충돌/실패 worker 산출물만 폐기하고 해당 task 직렬 fallback.

> wave-level integration validator 의 자동화 구현은 후속이다. 본 정책은 leader 가 위 절차를 수행한다는 최소 골격만 고정한다.

## 7. 비용가드

- **`max_parallel_workers = 2`** (첫 버전). 상향은 실측 후 별도 이슈로 결정한다.
- 근거: 직렬을 default 로 둔 사유 중 하나가 동시 실행 시 컨텍스트 누적 비용(cache 재독)이다. 병렬은 worker 별 격리로 메인 컨텍스트 누적은 피하지만, 동시 worker 수가 늘면 총비용이 다시 커진다. 낮은 상한에서 시작해 측정으로 올린다.

## 8. 측정·분석 단위 보존

- run-review / ROI marker 의 분석 단위는 **task 별 직렬 merge 단계** 기준으로 유지된다. build 가 병렬이어도 merge 가 직렬이라 `1 task = 1 run = 1 review` 단위가 깨지지 않는다.
- ledger 가 wave 구조(어느 task 가 같은 wave 였는지)를 인지하도록 하는 확장은 후속이다.

## 9. agent_boundary 검토 결론

현재 [`agent_boundary.py`](../../harness/agent_boundary.py) 는 sub-agent 의 `git push` 와 `gh` mutation 만 차단하고, `git commit` / 내부 helper / ledger 이벤트는 통과시킨다.

- 위 "실행모델"에서 worker 는 **격리 worktree sub-agent** 라 leader 의 ledger helper 에 구조적으로 접근하기 어렵다 → 본 정책 단계에서는 **prompt-only 권한 명시**(agent 지침 + 본 문서 "권한 경계")로 1차 충분하다.
- 다만 fallback 경로 등에서 worker 가 leader-owned mutation 을 호출할 수 있는 통로가 생기면, `agent_boundary.py` 에 worker→leader-mutation 차단을 추가할지 검토한다. 이 결정은 driver 의 실행모델 확정값에 종속되므로 **driver 구현 이슈에서 확정**한다.

## 10. 범위 경계 — 본 정책 vs 후속

| 본 정책(고정 완료) | 후속 이슈(범위 밖) |
|---|---|
| 병렬 허용/금지 조건 | 병렬 wave driver 오케스트레이션 구현 |
| leader/worker 권한 목록 | wave-level integration validator 자동화 |
| fan-in 검증 최소 절차 | ledger 의 wave 구조 인지 |
| 판정 입력 스키마 (`depends_on` · Scope 파일집합) | `max_parallel_workers` 상한 상향 |
| 직렬 chain default 명시 | `agent_boundary.py` worker 차단 코드(실행모델 확정 후) |
