# Handoff Matrix — Agent 결정 / Retry / Escalate / 권한

> **Status**: ACTIVE
> **Scope**: dcness 컨베이어의 *agent 측 강제 영역* SSOT — 결론 enum 별 다음 trigger / retry 한도 / escalate 카탈로그 / 접근 권한 (호출 / Write / Read / 인프라 패턴).
> **Cross-ref**: 시퀀스 spec + 8 loop 행별 풀스펙 = [`orchestration.md`](orchestration.md) §2~§4. 절차 mechanics = [`loop-procedure.md`](loop-procedure.md).

---

## 1. 결론 enum → 다음 agent trigger 결정표

> 13 agent (validator/architect 의 mode 펼침). 본 표가 [`orchestration.md`](orchestration.md) §2/§3 시퀀스의 *상세 분기 spec*.

### 1.1 product-planner

| 결론 | 다음 trigger |
|---|---|
| `PRODUCT_PLAN_READY` | plan-reviewer |
| `CLARITY_INSUFFICIENT` | 사용자 (역질문) |
| `PRODUCT_PLAN_CHANGE_DIFF` | plan-reviewer (변경 분만 재심사) |
| `PRODUCT_PLAN_UPDATED` | ux-architect (변경 반영) |
| `ISSUES_SYNCED` | (다음 단계 없음, 동기화 완료) |

### 1.2 plan-reviewer

| 결론 | 다음 trigger |
|---|---|
| `PLAN_REVIEW_PASS` | ux-architect (UX_FLOW) |
| `PLAN_REVIEW_CHANGES_REQUESTED` | product-planner 재진입 |

### 1.3 ux-architect

| 결론 | 다음 trigger |
|---|---|
| `UX_FLOW_READY` | validator (UX_VALIDATION) |
| `UX_FLOW_PATCHED` | validator (UX_VALIDATION, 변경 부분만) |
| `UX_REFINE_READY` | 사용자 승인 → designer SCREEN |
| `UX_FLOW_ESCALATE` | 사용자 (escalate) |

### 1.4 architect (master, 7 mode)

| Mode | 결론 | 다음 trigger |
|---|---|---|
| SYSTEM_DESIGN | `SYSTEM_DESIGN_READY` | architect TASK_DECOMPOSE |
| TASK_DECOMPOSE | `READY_FOR_IMPL` | impl 루프 (architect MODULE_PLAN per impl) |
| MODULE_PLAN | `READY_FOR_IMPL` | validator PLAN_VALIDATION |
| SPEC_GAP | `SPEC_GAP_RESOLVED` | engineer 재진입 |
| SPEC_GAP | `PRODUCT_PLANNER_ESCALATION_NEEDED` | product-planner |
| SPEC_GAP | `TECH_CONSTRAINT_CONFLICT` | 사용자 (escalate) |
| TECH_EPIC | `SYSTEM_DESIGN_READY` | architect TASK_DECOMPOSE |
| LIGHT_PLAN | `LIGHT_PLAN_READY` | engineer simple |
| DOCS_SYNC | `DOCS_SYNCED` | (완료) |
| DOCS_SYNC | `SPEC_GAP_FOUND` | architect SPEC_GAP |
| DOCS_SYNC | `TECH_CONSTRAINT_CONFLICT` | 사용자 |

### 1.5 engineer

| 결론 | 다음 trigger |
|---|---|
| `IMPL_DONE` | validator CODE_VALIDATION |
| `IMPL_PARTIAL` | engineer 재호출 (split < 3, 새 context window — DCN-30-34) |
| `SPEC_GAP_FOUND` | architect SPEC_GAP (attempt < 2) / escalate (attempt ≥ 2) |
| `TESTS_FAIL` | engineer 재시도 (attempt < 3) / `IMPLEMENTATION_ESCALATE` (≥ 3) |
| `IMPLEMENTATION_ESCALATE` | 사용자 |
| `POLISH_DONE` | pr-reviewer (재호출) |

### 1.6 test-engineer

| 결론 | 다음 trigger |
|---|---|
| `TESTS_WRITTEN` | engineer (attempt 0 진입) |
| `SPEC_GAP_FOUND` | architect SPEC_GAP |

### 1.7 designer

| 결론 | 다음 trigger |
|---|---|
| `DESIGN_READY_FOR_REVIEW` | (THREE_WAY) design-critic / (ONE_WAY) 사용자 PICK |
| `DESIGN_LOOP_ESCALATE` | 사용자 |

### 1.8 design-critic

| 결론 | 다음 trigger |
|---|---|
| `VARIANTS_APPROVED` | 사용자 PICK → 다음 단계 (test 또는 impl) |
| `VARIANTS_ALL_REJECTED` | designer 재진입 (round < 3) |
| `UX_REDESIGN_SHORTLIST` | ux-architect UX_REFINE (round ≥ 3) |

### 1.9 validator (5 mode 펼침)

| Mode | 결론 | 다음 trigger |
|---|---|---|
| PLAN_VALIDATION | `PASS` | test-engineer |
| PLAN_VALIDATION | `FAIL` | architect MODULE_PLAN 재진입 |
| PLAN_VALIDATION | `SPEC_MISSING` | product-planner / architect SPEC_GAP |
| CODE_VALIDATION | `PASS` | pr-reviewer |
| CODE_VALIDATION | `FAIL` | engineer 재시도 (attempt < 3) |
| CODE_VALIDATION | `SPEC_MISSING` | architect SPEC_GAP |
| DESIGN_VALIDATION | `DESIGN_REVIEW_PASS` | architect TASK_DECOMPOSE |
| DESIGN_VALIDATION | `DESIGN_REVIEW_FAIL` | architect SYSTEM_DESIGN 재진입 (cycle 한도 2) |
| DESIGN_VALIDATION | `DESIGN_REVIEW_ESCALATE` | 사용자 위임 |
| UX_VALIDATION | `PASS` | architect SYSTEM_DESIGN |
| UX_VALIDATION | `FAIL` | ux-architect 재진입 |
| BUGFIX_VALIDATION | `PASS` | pr-reviewer |
| BUGFIX_VALIDATION | `FAIL` | engineer 재시도 |

### 1.10 pr-reviewer

| 결론 | 다음 trigger |
|---|---|
| `LGTM` | 사용자 승인 → squash merge |
| `CHANGES_REQUESTED` | engineer POLISH |

### 1.11 qa

| 결론 | 다음 trigger |
|---|---|
| `FUNCTIONAL_BUG` | architect LIGHT_PLAN |
| `CLEANUP` | engineer 직접 (light) |
| `DESIGN_ISSUE` | designer / ux-architect (REFINE) |
| `KNOWN_ISSUE` | (종료) |
| `SCOPE_ESCALATE` | 사용자 |

### 1.12 security-reviewer

| 결론 | 다음 trigger |
|---|---|
| `SECURE` | (다음 단계 없음, 검증 완료) |
| `VULNERABILITIES_FOUND` | engineer (수정 요청) |

---

## 2. Retry 한도

> RWHarness `harness-architecture.md` §4.3 핵심 상수 + impl_loop 정책 정합. dcNess 는 boolean Flag 대신 `.claude/harness-state/<run_id>/.attempts.json` 카운터로 표현.

| 항목 | 한도 | 초과 시 |
|---|---|---|
| engineer attempt (TESTS_FAIL → 재시도) | 3 | `IMPLEMENTATION_ESCALATE` |
| engineer split (IMPL_PARTIAL → 재호출, DCN-30-34) | 3 | `IMPLEMENTATION_ESCALATE` (작업 분해 부족 — architect TASK_DECOMPOSE 재진입 권고) |
| engineer SPEC_GAP_FOUND → architect.spec-gap → engineer 재진입 | 2 | `IMPLEMENTATION_ESCALATE` |
| validator FAIL → 직전 agent 재진입 | (validator 종속) | 직전 agent 의 retry 한도에 흡수 |
| design THREE_WAY VARIANTS_ALL_REJECTED 라운드 | 3 | `UX_REDESIGN_SHORTLIST` (ux-architect REFINE) |
| pr-reviewer CHANGES_REQUESTED → POLISH 라운드 | 2 | 사용자 escalate |
| product-planner CLARITY_INSUFFICIENT 라운드 | 무제한 (사용자 응답 대기) | (해당 없음) |
| ESCALATE 누적 (동일 fail_type) | 2 | architect SPEC_GAP 자동 호출 |

`.attempts.json` 형식 (예시):
```json
{
  "plan_validation": 1,
  "code_validation": 2,
  "spec_gap": 1,
  "design_round": 0
}
```

force-retry 시 카운터 리셋 (RWHarness PR #11 패턴 정합).

---

## 3. Escalate 조건 카탈로그

다음 결론 enum 수신 시 **메인 Claude / driver 가 즉시 사용자 보고 후 대기** ([`status-json-mutate-pattern.md`](status-json-mutate-pattern.md) §2.5 정합 — 자동 복구 금지):

| Enum | 출처 agent | 의미 |
|---|---|---|
| `IMPLEMENTATION_ESCALATE` | engineer | 재시도 한도 초과 또는 구현 불가 |
| `UX_FLOW_ESCALATE` | ux-architect | UX Flow 정의 불가 (PRD 모순 등) |
| `DESIGN_LOOP_ESCALATE` | designer | variant 생성 불가 또는 critic 3 round 후 |
| `SCOPE_ESCALATE` | qa | 이슈 범위가 분류 enum 5개 모두 해당 안 됨 |
| `PRODUCT_PLANNER_ESCALATION_NEEDED` | architect.spec-gap | PRD 변경 필요 |
| `TECH_CONSTRAINT_CONFLICT` | architect.spec-gap / docs-sync | 기술 제약 충돌 |
| `UX_REDESIGN_SHORTLIST` | design-critic | 3 round 누적 reject |
| `CLARITY_INSUFFICIENT` | product-planner | 사용자 입력 모호 (역질문 필요) |

자동 재시도 / 우회 금지. 사용자 명시 결정 후만 진행.

---

## 4. 접근 권한 매트릭스

> RWHarness `harness-architecture.md` §3 의 dcNess 변환. dcness 의 두 번째 강제 영역 = "접근 영역" ([`status-json-mutate-pattern.md`](status-json-mutate-pattern.md) §2.5 정합).

### 4.1 호출 권한 (HARNESS_ONLY_AGENTS)

`HARNESS_ONLY_AGENTS = ("engineer",)` — 메인 Claude 가 Agent 도구로 직접 호출 차단. 코드 driver (impl_driver) 경유 필수.

| Agent | Mode | 직접 호출 허용 | 비고 |
|---|---|---|---|
| architect | SYSTEM_DESIGN, TASK_DECOMPOSE, TECH_EPIC, LIGHT_PLAN, DOCS_SYNC | ✅ | 메인 직접 |
| architect | MODULE_PLAN, SPEC_GAP | ❌ | impl_driver / plan_driver 경유 |
| validator | DESIGN_VALIDATION, UX_VALIDATION | ✅ | 메인 직접 |
| validator | PLAN_VALIDATION, CODE_VALIDATION, BUGFIX_VALIDATION | ❌ | 루프 경유 |
| 그 외 11 agent | — | ✅ | designer, ux-architect, qa, pr-reviewer, design-critic, security-reviewer, product-planner, test-engineer, plan-reviewer 모두 메인 직접 |
| engineer | — | ❌ | impl_driver 경유 필수 |

### 4.2 Write/Edit 허용 경로 (ALLOW_MATRIX)

| 에이전트 | 허용 경로 |
|---|---|
| engineer | `src/**` |
| architect | `docs/**`, `backlog.md`, `trd.md` |
| designer | `design-variants/**`, `docs/ui-spec*` |
| test-engineer | `src/__tests__/**`, `*.test.*`, `*.spec.*` |
| product-planner | `prd.md`, `stories.md` |
| ux-architect | `docs/ux-flow.md` |
| qa | (Issue tracker mutation 만, 파일 X) |
| validator / design-critic / pr-reviewer / security-reviewer / plan-reviewer | (없음 — 판정 전용) |

### 4.3 Read 금지 경로 (READ_DENY_MATRIX)

| 에이전트 | 금지 |
|---|---|
| product-planner | `src/`, `docs/impl/`, `trd.md` |
| designer | `src/` |
| test-engineer | `src/` (impl 외), 도메인 문서 |
| plan-reviewer | `src/`, `docs/impl/`, `trd.md` |

### 4.4 인프라 패턴 (전 에이전트 공통 차단)

> **코드 SSOT**: 실제 강제 패턴은 `harness/agent_boundary.py:DCNESS_INFRA_PATTERNS`. 본 §4.4 와 코드는 항상 동기 — 변경 시 양쪽 함께.

```python
DCNESS_INFRA_PATTERNS = [
    r'(^|/)\.claude/',
    r'(^|/)hooks/',
    r'(^|/)harness/(signal_io|interpret_strategy|hooks|session_state|agent_boundary)\.py$',
    r'(^|/)docs/orchestration\.md$',
    r'(^|/)docs/handoff-matrix\.md$',
    r'(^|/)docs/loop-procedure\.md$',
    r'(^|/)docs/process/(governance|dcness-guidelines)\.md$',
    r'(^|/)scripts/(check_document_sync|check_task_id|setup_branch_protection|analyze_metrics)\.mjs$',
]
```

> RWHarness 의 `HARNESS_INFRA_PATTERNS` 안 `r'orchestration-rules\.md'` 잔재는 dcness 가 정정 — 파일명은 `docs/orchestration.md` + `docs/handoff-matrix.md` (split 후 양쪽). loop-procedure / dcness-guidelines / hooks·session_state·agent_boundary 도 dcness 가 추가 보호 (DCN-30-30/31/32 split + loop-catalog 흡수 산출물).

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
- [`status-json-mutate-pattern.md`](status-json-mutate-pattern.md) — proposal SSOT (정체성 / 원칙)
- `agents/*.md` — 각 agent 의 결론 enum 출처
- `harness/signal_io.py` / `harness/interpret_strategy.py` — enum 추출 인프라
