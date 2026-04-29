# Migration Decisions — RWHarness → dcNess

> **Status**: ACTIVE
> **Origin**: `docs/status-json-mutate-pattern.md` §11.2 framework 적용
> **Bootstrap**: DCN-CHG-20260429-05
> **Scope**: RWHarness 의 어느 모듈을 dcNess 로 가져올지 / 폐기할지 / 리팩터할지 module-level 결정 기록

## 0. 목적

`status-json-mutate-pattern.md` §11.2 framework 를 RWHarness 모듈 카탈로그에 적용한 결과를 단일 문서로 박는다. 모듈마다 다음 3 질문 중 하나로 분류:

1. **Catastrophic-prevention 인가?** — 돌이킬 수 없는 사고를 막는가? → **PRESERVE**
2. **발상 변경으로 자연 폐기되는가?** — status JSON mutate / dcNess 메인 직접 작업 모드 적용 시 의미 잃는가? → **DISCARD**
3. **단순화 가능한가?** — 룰 누적·중복 패턴인가? → **REFACTOR**

본 문서는 **결정 기록** 이지 *재작성 금지의 헌법* 이 아니다. 분류가 잘못된 것으로 판명되면 별도 Task-ID 로 정정.

---

## 1. dcNess 정체성 정합 (분류 전 전제)

dcNess 는 RWHarness 와 다른 *모드* 다. 분류 전 다음 전제 박는다 (proposal §10 / §11.4):

- **메인 Claude 직접 작업 모드** — architect/validator/engineer 위임 강제 *없음*
- **RWHarness 가드 미적용** — agent-boundary / commit-gate hook 자체가 본 환경엔 동작 안 함 (사용자 프로젝트 가드 ≠ 본 저장소 가드)
- **Document Sync 거버넌스만 강제** — Task-ID + record/rationale/PROGRESS 동반
- **Plugin 배포 고려** (`DCN-CHG-20260429-04`) — RWHarness 와 공존 가능 설계

따라서 RWHarness 의 *위임 사이클 강제* 모듈군은 dcNess 환경에선 **자연 폐기** (proposal §11.4).

---

## 2. 분류 결과

> 출처: `~/project/RWHarness` (alruminum/realworld-harness@0.1.0-alpha)
> 본 분류는 *현 시점 결정*. RWHarness 가 변하면 본 표도 갱신 필요.

### 2.1 `harness/` (Python 코어)

| 모듈 | 결정 | 사유 |
|---|---|---|
| `core.py:551-680` `MARKER_ALIASES` + `parse_marker` + `diagnose_marker_miss` | **DISCARD** | 발상 변경으로 자연 폐기. `signal_io.interpret_signal` 이 대체. proposal §3 |
| `core.py:2040-2200` `generate_handoff` + `write_handoff` | **DISCARD** | prose 자체가 handoff. 별도 형식 없음. proposal §4.3 / §3 (Handoff) |
| `core.py:175-210` `class Flag` (enum) | **DISCARD** | 형식 강제의 한 형태 (boolean flag). proposal §1·§4.4 — recovery state 는 별도 카운터 (`.attempts.json`) 로 분리 |
| `core.py:1024-1043` `_AGENT_DISALLOWED` 매트릭스 | **DISCARD (dcNess 한정)** | `agent_call` subprocess 의 일부. dcNess 메인 직접 작업 모드엔 의미 없음 |
| `core.py` `agent_call` subprocess (claude CLI 격리) | **DISCARD (dcNess 한정)** | 메인 직접 작업 모드라 subagent 호출은 메인 Claude 의 `Agent` 도구 또는 `Task` 도구가 담당. RWHarness 의 별도 subprocess 격리는 ceremony |
| `core.py` `RunLogger` (JSONL 이벤트 로그) | **PRESERVE (검토)** | 도그푸딩 측정에 유용. dcNess 가 도그푸딩 환경 도입 시 같은 형식 채택. 단 Phase 1 진입 전엔 *보류* (불필요한 LOC) |
| `core.py` `StateDir` (path 추상) | **PARTIAL** | path 추상은 `signal_io.py` 에 이미 흡수. RWHarness `StateDir` 자체는 폐기, 신규 `signal_io.signal_path` 가 대체 |
| `core.py` `kill_check` / `HARNESS_KILL` | **PRESERVE (검토)** | 무한 루프 차단 catastrophic-prevention. 단 dcNess 가 subprocess 루프 안 돌리면 의미 없음. 후속 Task 검토 |
| `executor.py` (agent subprocess executor) | **DISCARD (dcNess 한정)** | `agent_call` 폐기와 동반 |
| `path_resolver.py` (claude CLI 경로 결정) | **DISCARD (dcNess 한정)** | 메인 작업 모드엔 메인 Claude 가 자기 CLI 안에서 동작 → 외부 CLI path 결정 불필요 |
| `providers.py` (provider config) | **DISCARD (dcNess 한정)** | 위 동일 |
| `config.py` `HarnessConfig` | **DISCARD (dcNess 한정)** | 위 동일. dcNess 는 환경변수 + plugin manifest 로 충분 |
| `notify.py` (알림 send) | **DISCARD (dcNess 한정)** | 메인 작업 모드라 사용자가 직접 인지 |
| `tracker.py` (Issue tracker integration) | **DISCARD (dcNess 한정)** | 본 저장소 거버넌스가 GitHub Issue 직접 사용 (`gh` CLI) — 별도 추상 불필요 |
| `helpers.py` (utility) | **검토** | 일부 함수 (`format_ref` 등) 는 유용. 필요 시 cherry-pick |
| `impl_loop.py` (validator → engineer → pr-reviewer 시퀀스) | **DISCARD (dcNess 한정)** | proposal §11.4 — "impl_loop subprocess 시퀀스 강제" 도입 안 함 |
| `impl_router.py` (모드 분기) | **DISCARD (dcNess 한정)** | impl_loop 동반 폐기 |
| `plan_loop.py` (checkpoint hash + planning 시퀀스) | **DISCARD (dcNess 한정)** | 위 동일 |
| `review_agent.py` (review 분기) | **DISCARD (dcNess 한정)** | 위 동일 |

### 2.2 `hooks/` (Claude Code hook)

| 모듈 | 결정 | 사유 |
|---|---|---|
| `agent-boundary.py` (ALLOW_MATRIX / READ_DENY_MATRIX / HARNESS_INFRA_PATTERNS) | **DISCARD (dcNess 한정)** | proposal §11.4 — "가드 자체가 신규 프로젝트엔 미적용". 본 저장소가 다른 사용자 프로젝트의 가드가 되려면 *plugin 배포* 후 사용자 프로젝트에서 활성화. 현재 dcNess 자체 작업 시엔 미적용 |
| `commit-gate.py` (Gate 1/4/5) | **DISCARD (dcNess 한정)** | 위 동일. 본 저장소는 git pre-commit + Claude Code PreToolUse hook (이미 도입) 으로 충분 |
| `plugin-write-guard.py` (plugin 디렉토리 보호) | **PRESERVE (전역)** | 전역 hook (~/.claude). dcNess 자체는 영향 안 줌. RWHarness 와 공존 시 동시 활성. 본 저장소가 *복사* 할 필요 없음 |
| `harness-session-start.py` (session bootstrap) | **DISCARD (dcNess 한정)** | RWHarness 활성 화이트리스트 검사 — dcNess 자체엔 무관 |
| `skill-stop-protect.py` (skill stop 차단) | **PRESERVE (전역)** | 전역 hook. 동일 |
| `harness_common.py` (hook utility) | **DISCARD (dcNess 한정)** | RWHarness hook 들의 공통 utility. dcNess hook 미도입이라 불필요 |
| `session_state.py` (live.json SSOT) | **DISCARD (dcNess 한정)** | 위 동일 |
| 기타 review/router/drift hook | **DISCARD (dcNess 한정)** | 위 동일 |

> **요약**: dcNess 는 *자체 hook 없음*. RWHarness 의 hook 은 *사용자 프로젝트* 보호용으로, dcNess 가 plugin 으로 배포돼 다른 프로젝트에 활성화될 때 의미가 있음. 본 저장소 `hooks/` 디렉토리는 만들지 않는다 (proposal §11.4 정합).

### 2.3 `agents/` (agent prompt + 모드 sub-doc)

| 모듈 | 결정 | 사유 |
|---|---|---|
| `validator.md` + `validator/*.md` (5 모드) | **REFACTOR (Phase 1) ✅** | `DCN-CHG-20260429-13` — prose writing guide 형식. 결론 + 이유만 가이드, 형식 강제 0 (proposal §3) |
| `architect.md` + `architect/*.md` (7 모드) | **REFACTOR (Phase 2)** | 동일 prose writing guide 적용 |
| `engineer.md` | **REFACTOR (Phase 2)** | 동일 |
| `designer.md` + `designer/*.md` (4 모드) | **REFACTOR (Phase 2)** | 동일 |
| `design-critic.md` | **REFACTOR (Phase 2)** | 동일 |
| `qa.md` | **REFACTOR (Phase 2)** | 동일 |
| `ux-architect.md` | **REFACTOR (Phase 2)** | 동일 |
| `product-planner.md` | **REFACTOR (Phase 2)** | 동일 |
| `plan-reviewer.md` | **REFACTOR (Phase 2)** | 동일 |
| `pr-reviewer.md` | **REFACTOR (Phase 2)** | 동일 |
| `security-reviewer.md` | **REFACTOR (Phase 2)** | 동일 |
| `test-engineer.md` | **REFACTOR (Phase 2)** | 동일 |
| `preamble.md` (자동 주입 헤더) | **DISCARD** | 점진 공개로 대체 (proposal §5 Phase 1.3 / Phase 2). dcNess 가 plugin 으로 배포될 때도 동일 |

> **dcNess 메인 작업 모드 vs Plugin 배포 모드**:
> - **메인 작업 모드 (본 저장소 내부)**: agent prompt 가 *자료* 일 뿐 의무 호출 없음. 메인 Claude 가 `Task` 도구로 호출 시에만 활성화.
> - **Plugin 배포 모드 (사용자 프로젝트에서 활성화)**: agent prompt 가 *실 호출 대상*. status JSON mutate 형식 강제.
>
> 두 모드 다 같은 agent docs 형식 사용 → 변환은 한 번만.

### 2.4 `agent-config/` (프로젝트별 agent 컨텍스트)

| 모듈 | 결정 | 사유 |
|---|---|---|
| `agent-config/*.md` (project context) | **DISCARD** | proposal §5 Phase 1: "별 layer 폐기, agents/*.md 통합". dcNess 에 도입 안 함 |

### 2.5 `scripts/` (build/test/governance)

| 모듈 | 결정 | 사유 |
|---|---|---|
| RWHarness `setup-harness.sh` / `setup-agents.sh` | **DISCARD (dcNess 한정)** | RWHarness 부트스트랩 — dcNess 는 이미 거버넌스 부트스트랩 완료 (`DCN-CHG-20260429-01`) |
| RWHarness 기타 운영 script | **검토** | cherry-pick 후보. 필요 시 별도 Task |

### 2.6 `orchestration/` (changelog + rationale)

| 모듈 | 결정 | 사유 |
|---|---|---|
| `orchestration/changelog.md` 형식 + Task-ID 패턴 | **PRESERVE → 이미 흡수** | dcNess 의 `docs/process/document_update_record.md` + `change_rationale_history.md` 가 동일 역할. Task-ID 형식 (`DCN-CHG-YYYYMMDD-NN`) 도 RWHarness `HARNESS-CHG-*` 패턴 정합 |
| Document-Exception 토큰 룰 | **PRESERVE → 이미 흡수** | governance §2.4 |

### 2.7 `.claude-plugin/` (plugin manifest)

| 모듈 | 결정 | 사유 |
|---|---|---|
| `plugin.json` + `marketplace.json` 형식 | **PRESERVE → 이미 흡수** | dcNess 는 자체 manifest (`name=dcness`) 작성 (`DCN-CHG-20260429-04`). RWHarness 와 plugin name 충돌 0 |

---

## 3. 신규 net-new (RWHarness 에 없음)

| 모듈 | 상태 | 위치 |
|---|---|---|
| `harness/state_io.py` (status JSON schema) | **DISCARDED** | `DCN-CHG-20260429-03` 도입 → `DCN-CHG-20260429-13` 폐기 (proposal 갱신: 형식 강제 = 사다리) |
| `tests/test_state_io.py` (32 케이스) | **DISCARDED** | 위 동일 |
| `tests/test_validator_schemas.py` (9 round-trip) | **DISCARDED** | 위 동일 |
| `harness/signal_io.py` (prose I/O + interpret_signal + DI swap) | **DONE** | `DCN-CHG-20260429-13` |
| `tests/test_signal_io.py` (29 케이스) | **DONE** | 위 동일 |
| `agents/validator*.md` prose writing guide | **DONE** | 위 동일 |
| `.github/workflows/document-sync.yml` (CI 게이트) | **DONE** | `DCN-CHG-20260429-08` |
| `.github/workflows/python-tests.yml` | **DONE** | `DCN-CHG-20260429-09` |
| `.github/workflows/plugin-manifest.yml` | **DONE** | `DCN-CHG-20260429-10` |
| 메타 LLM (haiku) interpreter 통합 | **TODO** | Phase 2 — `interpret_signal(..., interpreter=anthropic_haiku_call)` |

---

## 4. 보류 / 미정 (decision pending)

다음 항목은 *후속 Task* 에서 결정:

- **dcNess 가 메인 Claude 의 `Task` 도구로 agent 호출 시 prose 강제 여부** — 현 모드(메인 직접 작업) 에선 의무 아님. plugin 배포 후 사용자 프로젝트에서 메타 LLM interpreter 가 동작.
- **`harness/core.py` 의 `RunLogger` / `kill_check` 도입 여부** — 도그푸딩 측정 또는 무한루프 차단 필요 시 cherry-pick.
- **`harness/helpers.py` 의 utility 함수 cherry-pick** — 사용 시점에 필요한 함수만 가져옴.
- **메타 LLM interpreter 의 cache 전략** — 같은 prose 결과 caching 으로 비용 절감 가능 (proposal R8). 운영 데이터 누적 후 결정.

---

## 5. 분류 변경 절차

분류 결정이 잘못된 것으로 판명 시:

1. 별도 Task-ID 발급 (`DCN-CHG-YYYYMMDD-NN`)
2. 본 표의 해당 row 갱신
3. `change_rationale_history.md` 에 변경 사유·근거·후속 기록
4. 영향 받는 모듈 동반 작업

> 예: validator.md 변환을 시작했는데 RWHarness 의 mode sub-doc 구조가 dcNess 정체성과 맞지 않다고 판명 → REFACTOR → DISCARD + 신규 작성.

---

## 6. 참조

- `docs/status-json-mutate-pattern.md` §11.2 — framework 출처
- `docs/status-json-mutate-pattern.md` §11.4 — 도입할 것 / 도입 안 할 것 / 안전망
- `docs/status-json-mutate-pattern.md` §12 — RWHarness → 신규 Plugin 전환 절차
- `docs/process/governance.md` — Task-ID + Document Sync 룰
- `~/project/RWHarness` — 분류 대상 코드베이스
