# Handoff Matrix — Agent Routing 가이드 / Retry / Escalate / 권한

> **Status**: ACTIVE
> **Scope**: dcness 컨베이어의 *agent 측 강제 영역* SSOT — agent 결론 prose 를 보고 메인 Claude 가 다음 단계 결정할 때 참조하는 자연어 routing 가이드 / retry 한도 / escalate 카탈로그 / 접근 권한.
> **Cross-ref**: 시퀀스 spec + 8 loop 행별 풀스펙 = [`orchestration.md`](orchestration.md) §2~§4. 절차 mechanics = [`loop-procedure.md`](loop-procedure.md).

---

## 1. Agent 결론 → 다음 agent 결정 가이드 (자연어)

> agent 13 종 (architect 는 system-architect + module-architect 두 에이전트로 평탄화, validator 는 code-validator + architecture-validator 두 에이전트로 평탄화, security-reviewer 는 pr-reviewer §F-Security + architect 의 위협 모델 가정·invariant 로 흡수). agent 가 자기 prose 에 결론 + 권장 다음 단계를 자유롭게 박는다. 메인 Claude 는 그 prose 와 본 가이드를 비교해 다음 호출을 결정한다. 본 가이드는 형식 강제가 아니라 *판단 보조*. 가능한 결론 표현은 agent 별로 다양 — 의미만 맞으면 OK ([`dcness-rules.md`](dcness-rules.md) §1 원칙 2 자율 정합).

> **이슈 #280 정착 후 작동 모델**:
> - agent 는 prose 마지막 단락에 *어떤 결과로 끝났는지 + 메인이 누구를 부르는 게 적절한지* 자기 언어로 명시.
> - 메인은 prose + 본 §1 가이드만으로 routing 결정. enum 형식 검증 없음.
> - prose 가 모호하거나 결론을 추출 못 하면 메인이 사용자에게 위임 (cascade — `harness/routing_telemetry.py:record_cascade`).

### 1.1 product-planner

PRD 작성 / 변경 / 동기화 hub. 일반적으로 다음 4 결과 중 하나로 종료:

- **PRD 신규 또는 변경안 준비 완료** → plan-reviewer 호출 (변경분만이면 review 도 변경분 한정).
- **사용자 입력이 모호해 추가 질문 필요** → 사용자에게 역질문하고 응답 대기 (자동 진행 금지).
- **변경된 PRD 가 UX 영향** → ux-architect 로 변경 반영.
- **issue tracker 동기화 완료** → 후속 단계 없음.

### 1.2 plan-reviewer

PRD 심사 (`FULL` 모드 default / `PRE_CHECK` 모드 — `/product-plan` 스킬의 Spike Pre-Check 단계). 세 가지 결과:

- **PRD 승인** (`PLAN_REVIEW_PASS`) → 다음 단계는 ux-architect (UX_FLOW). `PRE_CHECK` 모드면 product-planner 호출 진입.
- **PRD 변경 요청** (`PLAN_REVIEW_FAIL`) → product-planner 재진입 (cycle ≤ 2). `PRE_CHECK` 모드면 사용자 입력 재정리 후 진입.
- **판정 불가** (`PLAN_REVIEW_ESCALATE`) → 사용자 위임. 4 트리거: 외부 검증 실행 불가 / 권한 경계 밖 정보 의존 / cycle 한도 직전 동일 finding 반복 / `EXTERNAL_VERIFIED` URL 부재 PASS 시도.

### 1.3 ux-architect

UX Flow 정의 / 변경 / refine. 산출 *전* 5 카테고리 self-check 의무 (외부 validator 부재 — 자가검증). 다음 4 결과:

- **UX Flow 신규 완성 / 변경분 patch 완료 + self-check PASS** → system-architect.
- **UI refine 완료 (기존 디자인 다듬기)** → 사용자 승인 후 designer SCREEN.
- **Flow 정의 불가 (PRD 모순 등) 또는 self-check 2 cycle 후에도 FAIL** → escalate (사용자 위임).

### 1.4 system-architect

전체 시스템 설계 hub — 도메인 모델 + 모듈 구조 + 기술 스택 + Story → impl 매핑 표 + Spike Gate. 기술 에픽 (기술 부채/인프라/리팩토링) 도 동일 모드로 처리 (호출자 prompt 에 "기술 에픽" 명시 시 추가로 epic+story 이슈 등록).

- **READY** — 시스템 설계 산출 (`docs/architecture.md` + `## impl 목차` 표) 완료 → architecture-validator (Placeholder Leak + Spike Gate 외부 검증).
- **ESCALATE** — 기술 제약 충돌 / Spike FAIL / PRD 위반 → 사용자 또는 product-planner 위임.

### 1.4b module-architect

모듈/태스크 단위 설계 hub. 호출자 컨텍스트 (신규 story / 버그픽스 / 기존 impl 보강 / 문서 동기화) 에 따라 분량·범위 자율 판단.

- **READY** — impl 설계문서 작성/수정 완료. 다음 단계는 컨텍스트:
  - feature-build-loop 안 = impl 목차 다음 행 있으면 module-architect 재호출, 마지막 행이면 loop 종료 → impl-task-loop 진입
  - impl-task-loop fallback = test-engineer
  - 버그픽스 케이스 = engineer (simple)
  - 보강 케이스 = engineer 재진입
  - 문서 동기화 케이스 = 후속 없음
- **ESCALATE** — PRD 변경 필요 (product-planner) / 기술 제약 충돌 (사용자) / 권한·도구 부족 (사용자).

> Note: 이전 6 mode (SYSTEM_DESIGN / MODULE_PLAN / SPEC_GAP / LIGHT_PLAN / DOCS_SYNC / TECH_EPIC) → 2 agent 통합. 이전 mode 별 결론 enum (SYSTEM_DESIGN_READY / READY_FOR_IMPL / LIGHT_PLAN_READY / SPEC_GAP_RESOLVED / DOCS_SYNCED / TECH_CONSTRAINT_CONFLICT / PRODUCT_PLANNER_ESCALATION_NEEDED) → 단순 `READY` / `ESCALATE` 2종. 옛 TASK_DECOMPOSE 의 가치 (Story → impl 매핑 / NN-slug 명명 / 의존 순서) 는 system-architect 의 `## impl 목차` 표로 흡수. impl 본문 detail 은 module-architect × N 가 채움.

### 1.5 engineer

구현 hub. 결과 종류:

- **구현 완료 (기능 검증 가능)** → code-validator (impl 파일 경로로 full/bugfix scope 자동 분기).
- **부분 구현 (분량 초과로 split 필요)** → engineer 재호출 (split 한도 3, 새 context window — DCN-30-34).
- **SPEC GAP 발견 (스펙 모호 / 부족)** → module-architect (보강 케이스, attempt < 2). 한도 초과면 escalate.
- **테스트 실패 (재구현 필요)** → engineer 재시도 (attempt < 3). 한도 초과면 escalate.
- **POLISH 단계 마무리** → pr-reviewer 재호출.
- **escalate** (구현 불가 / 한도 초과) → 사용자 위임.

### 1.6 test-engineer

테스트 코드 선작성 (TDD). 결과:

- **테스트 준비 완료** → engineer (attempt 0 진입).
- **스펙 부족해 테스트 작성 불가** → module-architect (보강 케이스).

### 1.7 designer

UI variant 생성. 결과:

- **variant 준비 완료** → THREE_WAY 면 design-critic, ONE_WAY 면 사용자 PICK.
- **variant 생성 불가** → escalate (사용자 위임).

### 1.8 design-critic

variant 심사. 결과:

- **1+ variant 승인** → 사용자 PICK → 다음 단계 (test 또는 impl).
- **모두 reject** → designer 재진입 (round < 3).
- **3 round 누적 reject** → ux-architect UX_REFINE.

### 1.9 code-validator

impl 계획 ↔ 구현 코드 일치 검증. impl 파일 경로 (`docs/impl/NN-*.md` 또는 `docs/bugfix/#N-slug.md`) 로 full/bugfix scope 자동 분기. 결론 3종:

- **PASS** → pr-reviewer.
- **FAIL** → engineer 재시도 (attempt < 3).
- **ESCALATE** → impl 계획 + 대체 소스 모두 부재 / 재시도 한도 초과. 본문 사유 명시 → 메인이 사유 보고 module-architect (보강 케이스) 호출 또는 사용자 위임.

### 1.10 architecture-validator

system-architect 산출물의 자가검증 사각지대 (Placeholder Leak + Spike Gate 2 항목) 외부 reviewer. 결론 3종:

- **PASS** → module-architect × N (impl 목차 첫 행부터 순차).
- **FAIL** → system-architect 재진입 (cycle 한도 2). 본문에 placeholder 위치 / Must 기능 직결 / spike 권고 명시.
- **ESCALATE** → system-architect 재설계 1 cycle 후에도 동일 FAIL → 사용자 위임.

> Note: 옛 validator 5 모드 (CODE/DESIGN/UX/BUGFIX/PLAN) 폐기 (validator 단순화).
> - PLAN_VALIDATION 은 컨베이어 task_list 에 *원래부터* 빠져있던 drift (issue #247) — 정합 회복.
> - UX_VALIDATION 은 ux-architect self-check 흡수 (5 카테고리, FAIL 시 재고려).
> - DESIGN_VALIDATION 의 자가검증 가능 항목 (인터페이스/에러/엣지케이스/리스크/성능) 은 system-architect self-check 흡수. *자가검증 사각지대* (Placeholder Leak + Spike Gate) 만 architecture-validator 가 외부 검증.
> - BUGFIX_VALIDATION 은 code-validator 의 bugfix scope (impl 파일 경로 `docs/bugfix/`) 로 통합.

### 1.11 pr-reviewer

merge 직전 코드 품질 심사:

- **LGTM** → CI PASS 후 메인이 즉시 regular merge.
- **변경 요청** → engineer POLISH 재호출.

### 1.12 qa

이슈 분류 hub. 5 결과:

- **기능 버그** → module-architect (버그픽스 케이스).
- **간단 cleanup** → engineer 직접 (light).
- **디자인 이슈** → designer 또는 ux-architect (REFINE).
- **알려진 이슈** → 후속 없음.
- **분류 불가 (escalate)** → 사용자 위임.

---

## 2. Retry 한도

> RWHarness `harness-architecture.md` §4.3 핵심 상수 + impl_loop 정책 정합. dcNess 는 boolean Flag 대신 `.claude/harness-state/<run_id>/.attempts.json` 카운터로 표현.

| 항목 | 한도 | 초과 시 |
|---|---|---|
| engineer attempt (TESTS_FAIL → 재시도) | 3 | `IMPLEMENTATION_ESCALATE` |
| engineer split (IMPL_PARTIAL → 재호출, DCN-30-34) | 3 | `IMPLEMENTATION_ESCALATE` (작업 분해 부족 — system-architect 재진입 권고 / impl 목차 분할 재검토) |
| engineer SPEC_GAP_FOUND → module-architect (보강) → engineer 재진입 | 2 | `IMPLEMENTATION_ESCALATE` |
| code-validator FAIL → engineer 재진입 | engineer attempt 흡수 | engineer attempt 한도 (3) 도달 시 escalate |
| architecture-validator FAIL → system-architect 재진입 | 2 cycle | 사용자 위임 |
| design THREE_WAY VARIANTS_ALL_REJECTED 라운드 | 3 | `UX_REDESIGN_SHORTLIST` (ux-architect REFINE) |
| pr-reviewer CHANGES_REQUESTED → POLISH 라운드 | 2 | 사용자 escalate |
| product-planner CLARITY_INSUFFICIENT 라운드 | 무제한 (사용자 응답 대기) | (해당 없음) |
| ESCALATE 누적 (동일 fail_type) | 2 | module-architect (보강 케이스) 자동 호출 |

`.attempts.json` 형식 (예시):
```json
{
  "code_validation": 2,
  "spec_gap": 1,
  "design_round": 0
}
```

force-retry 시 카운터 리셋 (RWHarness PR #11 패턴 정합).

---

## 3. Escalate 조건 카탈로그

다음 결론 enum 수신 시 **메인 Claude / driver 가 즉시 사용자 보고 후 대기** ([`dcness-rules.md`](dcness-rules.md) §1 §2 원칙 2 정합 — 자동 복구 금지):

| Enum | 출처 agent | 의미 |
|---|---|---|
| `IMPLEMENTATION_ESCALATE` | engineer | 재시도 한도 초과 또는 구현 불가 |
| `UX_FLOW_ESCALATE` | ux-architect | UX Flow 정의 불가 (PRD 모순 등) |
| `DESIGN_LOOP_ESCALATE` | designer | variant 생성 불가 또는 critic 3 round 후 |
| `SCOPE_ESCALATE` | qa | 이슈 범위가 분류 enum 5개 모두 해당 안 됨 |
| `ESCALATE` | system-architect / module-architect | 기술 제약 충돌 / PRD 변경 필요 / Spike FAIL / 권한 부족 (본문 사유 명시) |
| `UX_REDESIGN_SHORTLIST` | design-critic | 3 round 누적 reject |
| `CLARITY_INSUFFICIENT` | product-planner | 사용자 입력 모호 (역질문 필요) |

자동 재시도 / 우회 금지. 사용자 명시 결정 후만 진행.

---

## 4. 접근 권한 매트릭스

> RWHarness `harness-architecture.md` §3 의 dcNess 변환. dcness 의 두 번째 강제 영역 = "접근 영역" ([`dcness-rules.md`](dcness-rules.md) §1 §1 정합).

### 4.1 호출 권한 (HARNESS_ONLY_AGENTS)

`HARNESS_ONLY_AGENTS = ("engineer",)` — 메인 Claude 가 Agent 도구로 직접 호출 차단. 코드 driver (impl_driver) 경유 필수.

| Agent | 케이스 | 직접 호출 허용 | 비고 |
|---|---|---|---|
| system-architect | (전체) | ✅ | 메인 직접 |
| module-architect | 신규 story (feature-build-loop §4.2 Step 7) / 보강 (engineer SPEC_GAP_FOUND) | ❌ | impl_driver / plan_driver 경유 |
| module-architect | 버그픽스 (qa 후) / 문서 동기화 | ✅ | 메인 직접 |
| architecture-validator | — | ✅ | 메인 직접 |
| code-validator | — | ❌ | impl_driver 경유 |
| 그 외 9 agent | — | ✅ | designer, ux-architect, qa, pr-reviewer, design-critic, product-planner, test-engineer, plan-reviewer, security-reviewer 모두 메인 직접 |
| engineer | — | ❌ | impl_driver 경유 필수 |

### 4.2 Write/Edit 허용 경로 (ALLOW_MATRIX)

| 에이전트 | 허용 경로 |
|---|---|
| engineer | `src/**` |
| system-architect / module-architect | `docs/**`, `backlog.md` |
| designer | `design-variants/**`, `docs/ui-spec*` |
| test-engineer | `src/__tests__/**`, `*.test.*`, `*.spec.*` |
| product-planner | `docs/prd.md`, `stories.md` |
| ux-architect | `docs/ux-flow.md` |
| qa | (Issue tracker mutation 만, 파일 X) |
| code-validator / architecture-validator / design-critic / pr-reviewer / plan-reviewer | (없음 — 판정 전용) |

### 4.3 Read 금지 경로 (READ_DENY_MATRIX)

| 에이전트 | 금지 |
|---|---|
| product-planner | `src/`, `docs/impl/`, `docs/architecture.md` |
| designer | `src/` |
| test-engineer | `src/` (impl 외), 도메인 문서 |
| plan-reviewer | `src/`, `docs/impl/`, `docs/architecture.md` |

### 4.4 인프라 패턴 (전 에이전트 공통 차단)

> **코드 SSOT**: 실제 강제 패턴은 `harness/agent_boundary.py:DCNESS_INFRA_PATTERNS`. 본 §4.4 와 코드는 항상 동기 — 변경 시 양쪽 함께.

```python
DCNESS_INFRA_PATTERNS = [
    r'(^|/)\.claude/',
    r'(^|/)hooks/',
    r'(^|/)harness/(signal_io|interpret_strategy|hooks|session_state|agent_boundary)\.py$',
    r'(^|/)docs/plugin/orchestration\.md$',
    r'(^|/)docs/plugin/handoff-matrix\.md$',
    r'(^|/)docs/plugin/loop-procedure\.md$',
    r'(^|/)docs/plugin/dcness-rules\.md$',
    r'(^|/)scripts/(setup_branch_protection|analyze_metrics)\.mjs$',
]
```

> RWHarness 의 `HARNESS_INFRA_PATTERNS` 안 `r'orchestration-rules\.md'` 잔재는 dcness 가 정정 — 파일명은 `docs/plugin/orchestration.md` + `docs/plugin/handoff-matrix.md` (split 후 양쪽). loop-procedure / dcness-rules / hooks·session_state·agent_boundary 도 dcness 가 추가 보호.

인프라 프로젝트(`is_infra_project()` True) 에선 위 패턴 해제 (dcness 자체 작업 시 본 SSOT 들도 편집 가능해야 함).

### 4.5 인프라 프로젝트 판정

RWHarness 4 신호 OR 정합:

1. `DCNESS_INFRA=1` 환경변수
2. 마커 파일 `~/.claude/.dcness-infra` 존재
3. `CLAUDE_PLUGIN_ROOT` 환경변수 non-empty
4. `cwd.resolve() == Path("/Users/<user>/project/dcness")` (또는 화이트리스트 매칭)

> **코드 강제**: `harness/agent_boundary.py` 가 본 spec 의 SSOT 구현. `hooks/file-guard.sh` (PreToolUse Edit/Write/Read/Bash) + `hooks/post-agent-clear.sh` (PostToolUse Agent) 가 활성화. opt-out 마커 = `.no-dcness-guard` (cwd) — 사용자 임시 우회.

---

## 5. 참조

- [`orchestration.md`](orchestration.md) — 시퀀스 catalog (§2 게이트 + §3 진입 경로 + §4 8 loop 행별 풀스펙)
- [`loop-procedure.md`](loop-procedure.md) — Step 0~8 mechanics
- [`dcness-rules.md`](dcness-rules.md) §1 — Prose-Only 원칙 현행 SSOT (대 원칙 + Anti-Pattern 5원칙)
- [`../archive/status-json-mutate-pattern.md`](../archive/status-json-mutate-pattern.md) — Prose-Only 원전 proposal (역사 자료)
- `agents/*.md` — 각 agent 의 결론 prose 표현 가이드
- `harness/routing_telemetry.py` — prose-only routing 회귀 검증 telemetry (이슈 #281)
- `harness/signal_io.py` / `harness/interpret_strategy.py` — 옛 enum 추출 인프라 (이슈 #284 폐기 진행 중)
