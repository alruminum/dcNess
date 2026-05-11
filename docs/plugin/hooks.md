# Hooks SSOT — dcness 코드 강제 백본

> **Status**: ACTIVE
> **Scope**: dcness plug-in 이 활성 프로젝트에 적용하는 6 hook 의 시점 / 역할 / 차단 동작 / 우회 메커니즘 SSOT.
> **Cross-ref**: [`orchestration.md`](orchestration.md) §2.3 (catastrophic 5 룰), [`handoff-matrix.md`](handoff-matrix.md) §4 (권한 매트릭스), [`dcness-rules.md`](dcness-rules.md) §1 (대원칙).

---

## 0. 정체성 — hook 은 dcness 의 *유일한* 코드 강제 백본

dcness 가 강제하는 영역은 단 2가지 ([`dcness-rules.md`](dcness-rules.md) §1):
1. **작업 순서** — agent 시퀀스 + retry 정책
2. **접근 영역** — 파일 경계 (ALLOW/READ_DENY) + 외부 시스템 mutation 차단

그 *외* 모든 영역 = agent 자율 / 권고 / 측정. hook 은 위 2 영역의 *유일한 코드 구현*. 다른 모든 SSOT (orchestration / handoff-matrix / loop-procedure / dcness-rules) 는 hook 동작을 *문서화* 한 자연어 spec 이며, 위반 시 실제로 *차단* 하는 주체는 본 문서가 다루는 6 hook.

---

## 1. CC hook event 모델

dcness 가 사용하는 CC hook event 3종:

| Event | 시점 | 차단 권한 | dcness 사용 hook |
|---|---|---|---|
| `SessionStart` | CC 새 conversation 시작 시 (resume / `/clear` 포함). user 첫 prompt 처리 *전*. | X (inject 만) | session-start.sh |
| `PreToolUse` | tool 호출 *직전*. matcher 매치 시 fire. | ✓ (`exit 1` 또는 `permissionDecision: deny` 로 차단) | catastrophic-gate / file-guard / tdd-guard |
| `PostToolUse` | tool 호출 *직후* (결과 반환 후, 메인 다음 turn 시작 전). | X (inject 만) | post-agent-clear / post-file-op-trace |

**사용 안 하는 event** (dcness 가 미사용):
- `UserPromptSubmit` — user prompt 검사. dcness 는 prompt 단계 강제 0.
- `PreCompact` — context compact 직전. compact 는 CC 내장 동작이라 dcness 개입 X.
- `Stop` / `SubagentStop` — 종료 hook. dcness 는 PostToolUse 로 충분.
- `Notification` / `SessionEnd` — 보조 event. dcness 미사용.

**차단 권한 비대칭**:
- PreToolUse 만 *차단* 가능 → catastrophic-gate / file-guard / tdd-guard 가 실제 강제 백본.
- SessionStart + PostToolUse 는 `hookSpecificOutput.additionalContext` 로 *컨텍스트 inject* — 메인 Claude 의 다음 turn 에 system reminder 로 보임.

---

## 2. 공통 패턴 (전 6 hook 공유)

모든 hook 의 bash wrapper 가 동일한 부트스트랩 4 단계 수행:

```bash
set -uo pipefail

# 1. plug-in root 를 PYTHONPATH 에 prepend — cross-project 시나리오 대응
export PYTHONPATH="${CLAUDE_PLUGIN_ROOT:-.}:${PYTHONPATH:-}"

# 2. 활성화 게이트 — dcness whitelist 외 프로젝트면 즉시 pass-through
python3 -m harness.session_state is-active >/dev/null 2>&1 || exit 0

# 3. CC PID 추출 (bash 의 PPID = CC main process)
CC_PID=$PPID

# 4. Python dispatch
python3 -m harness.hooks <handler> --cc-pid "$CC_PID"
```

**활성화 게이트 메커니즘**:
- `harness/session_state.py is-active` 가 현재 프로젝트가 dcness 활성 여부 판정 (`/init-dcness` 로 등록된 whitelist + marker 검사)
- 미활성 프로젝트 → hook 즉시 `exit 0` (no-op). plug-in 설치만 했고 활성화 안 한 프로젝트엔 영향 X.

**Python handler dispatch**: 모든 차단 / inject 로직은 [`harness/hooks.py`](../../harness/hooks.py) 안. bash wrapper 는 thin shim.

---

## 3. 6 hook 상세

### 3.1 session-start.sh

**Event**: `SessionStart`
**시점**: CC 가 새 conversation 시작 시. user 첫 prompt 처리 *전*.

**역할**:
- (a) sid 추출 + `.by-pid-current-run` 작성 + `live.json` 초기화 (state machine bootstrap)
- (b) **BLOCKING GATE inject** — `hookSpecificOutput.additionalContext` 로 [`dcness-rules.md`](dcness-rules.md) 강제 read 지시
  - 메인 Claude 첫 응답 첫 줄에 토큰 `[dcness-rules 로드 완료]` 출력 의무
  - 토큰 부재 시 사용자가 즉시 룰 위반 확인 가능
- (c) `dcness-rules.md` path resolve 3단계:
  1. `${CLAUDE_PLUGIN_ROOT}/docs/plugin/dcness-rules.md`
  2. `~/.claude/plugins/cache/dcness/dcness/<latest>/docs/plugin/dcness-rules.md`
  3. 사용자 repo legacy `${CLAUDE_PROJECT_DIR}/docs/plugin/dcness-rules.md`

**차단 동작**: SessionStart 는 차단 권한 X. `additionalContext` inject 만.
**실패 시**: silent (`exit 0`) — CC 동작 방해 X.

**외부 사용자 영향**: 활성 프로젝트의 매 세션 시작 시 메인 Claude 가 dcness-rules 강제 read + 토큰 출력. 미활성 프로젝트는 영향 0.

---

### 3.2 catastrophic-gate.sh

**Event**: `PreToolUse`
**Matcher**: `Agent`
**시점**: 메인 Claude 가 sub-agent 호출 (Task tool with `subagent_type`) *직전*.

**역할**: [`orchestration.md`](orchestration.md) §2.3 catastrophic 시퀀스 강제

| 룰 | 차단 조건 |
|---|---|
| §2.3.1 | src/ 변경 후 code-validator PASS 없이 pr-reviewer 호출 |
| §2.3.3 | engineer 가 module-architect `PASS` 없이 src/ 작성 |

**차단 동작**: `exit 1` → CC 가 Agent 호출 거부 + stderr 메시지 사용자 노출.
**외부 사용자 영향**: 활성 프로젝트의 시퀀스 위반 시 sub-agent 호출 자체가 막힘. 메인 Claude 가 직접 회복 시도하거나 사용자 위임.

---

### 3.3 file-guard.sh

**Event**: `PreToolUse`
**Matcher**: `Edit|Write|NotebookEdit|Read|Bash|mcp__.*`
**시점**: 모든 file / bash / mcp tool 호출 *직전* (sub-agent 활성 시 + 메인 직접 모두).

**역할**: [`handoff-matrix.md`](handoff-matrix.md) §4 권한 매트릭스 강제

| § | 룰 | 영향 |
|---|---|---|
| §4.3 | `DCNESS_INFRA_PATTERNS` | 전 sub-agent 의 인프라 path 차단 (`.claude/`, `hooks/`, `harness/*.py`, `docs/plugin/*.md`, `scripts/*.mjs`) |
| §4.1 | `ALLOW_MATRIX` | agent 별 Write 허용 path (예 engineer = `src/**`, designer = `design-variants/**`) |
| §4.2 | `READ_DENY_MATRIX` | agent 별 Read 금지 (예 designer 는 `src/` 못 읽음) |
| §4.4 | `is_infra_project()` | dcness 자체 작업 시 위 모두 해제 |

**메인 Claude turn** (sub-agent 비활성): pass-through. governance Document Sync 가 별도 보호.
**mcp__.* tool**: `file_path` 인자 부재 → boundary 검사 skip, trace 만.
**차단 동작**: `exit 1` → CC 가 tool 호출 거부.

**외부 사용자 영향**: 활성 프로젝트의 sub-agent 가 권한 외 path 시도 시 자동 차단. ALLOW_MATRIX 정의 안 된 agent 가 새로 호출되면 차단되므로, custom agent 추가 시 §4.1 행 등록 의무.

**코드 SSOT**: [`harness/agent_boundary.py`](../../harness/agent_boundary.py) `DCNESS_INFRA_PATTERNS` (handoff-matrix §4.3 와 동기 의무).

---

### 3.4 tdd-guard.sh

**Event**: `PreToolUse`
**Matcher**: `Edit|Write|NotebookEdit`
**도입**: release 0.2.16 (PR #339 / #340)
**시점**: Edit / Write tool 호출 *직전*.

**역할**: TS / JS 파일 (`*.ts|*.tsx|*.js|*.jsx`) Edit / Write 시 매칭 test 파일 *존재* 검사. 없으면 deny.

**skip 대상** (no-op, exit 0):
- test 파일 자체 — `*test*`, `*spec*`, `*__tests__*`
- 설정 / 비-코드 — `*.json`, `*.css`, `*.scss`, `*.md`, `*.yml`, `*.yaml`, `*.env*`, `*.config.*`, `*tailwind*`, `*postcss*`, `*next.config*`, `*tsconfig*`
- 타입 — `*/types/*`, `*/types.ts`, `*/types.d.ts`, `*.d.ts`
- Next.js 특수 — `*/layout.tsx`, `*/page.tsx`, `*/loading.tsx`, `*/error.tsx`, `*/not-found.tsx`, `*/globals.css`
- 시드 / 시안 — `*/templates/*`, `*/design-variants/*`
- 그 외 확장자 (`*.py`, `*.go` 등) — silent skip

**매칭 test 파일 검사 8 location**:
```
<dir>/<name>.{test,spec}.{ts,tsx,js,jsx}
<dir>/__tests__/<name>.{test,spec}.{ts,tsx,js,jsx}
<parent>/__tests__/<name>.{test,spec}.{ts,tsx,js,jsx}
<root>/src/__tests__/<name>.{test,spec}.{ts,tsx,js,jsx}
```

**차단 동작**: `permissionDecision: deny` JSON 출력 + 한국어 안내 메시지 (테스트 부재 + 검사 위치 8곳 명시).
**파급 사례**: `/quick` 스킬 폐기 직접 원인 (PR #349) — quick-bugfix-loop 에 test-engineer 부재라 engineer 의 src 작성이 자동 deny.

**외부 사용자 영향**: 활성 프로젝트의 TS / JS src 작성 시 test 동반 강제. TDD 미이행 환경에선 plug-in 활성화 후 광범위한 deny 발생 가능.

---

### 3.5 post-agent-clear.sh

**Event**: `PostToolUse`
**Matcher**: `Agent`
**시점**: sub-agent 호출 *직후* (Task tool 결과 반환 후, 메인 다음 turn 시작 전).

**역할**:
- (a) `live.json.active_agent / active_mode` clear — 메인 Claude 복귀 표시
- (b) **sub-agent prose 자동 저장** — `tool_response.text` → `<run_dir>/<agent>[-<MODE>].md` + `live.json.current_step.prose_file` 기록. 메인이 직접 Write 불필요.
- (c) agent-trace 집계 → tool histogram + anomaly 검출
- (d) **`additionalContext` inject** (`hookSpecificOutput` JSON) — 메인 다음 turn 의 Agent tool result 옆에 system reminder 로 보임
- (e) `redo_log` 1줄 자동 append — 메인이 잊는 행동 자동화

**차단 동작**: X (PostToolUse).
**stdout**: JSON (`hookSpecificOutput`) — CC 가 메인 컨텍스트 inject.
**stderr**: `/tmp/dcness-hook-stderr.log` 보존 (디버그용).

**외부 사용자 영향**: 메인 Claude 가 sub-agent prose 를 직접 Write 안 해도 자동 저장됨. trace + anomaly 가 다음 turn 의 컨텍스트로 inject 되어 메인이 review 정보 자동 인지.

---

### 3.6 post-file-op-trace.sh

**Event**: `PostToolUse`
**Matcher**: `Edit|Write|NotebookEdit|Read|Bash|mcp__.*`
**시점**: file / bash / mcp tool 호출 *직후*.

**역할**: 활성 sub-agent 가 있을 때만 `agent-trace.jsonl` 에 post phase 1줄 append.
- 메인 Claude turn (active_agent 미설정) = noop
- 비활성 프로젝트 = noop

**차단 동작**: X.
**용도**: agent 별 행동 trace 누적 → review report ([`harness/run_review.py`](../../harness/run_review.py)) 의 tool histogram + anomaly 검출 입력.

**외부 사용자 영향**: 직접 가시 영향 0. sub-agent 행동 trace 가 누적되어 `dcness-review` / `/run-review` 출력에 반영.

---

## 4. 등록 메커니즘

**[`hooks/hooks.json`](../../hooks/hooks.json)**: CC plug-in 의 hook 등록 표준 형식. event 별 matcher + 실행 스크립트 정의.

```json
{
  "hooks": {
    "SessionStart": [{ "hooks": [{ "type": "command", "command": "bash \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh\"" }] }],
    "PreToolUse": [
      { "matcher": "Agent", "hooks": [...] },
      { "matcher": "Edit|Write|NotebookEdit|Read|Bash|mcp__.*", "hooks": [...] },
      { "matcher": "Edit|Write|NotebookEdit", "hooks": [...] }
    ],
    "PostToolUse": [
      { "matcher": "Agent", "hooks": [...] },
      { "matcher": "Edit|Write|NotebookEdit|Read|Bash|mcp__.*", "hooks": [...] }
    ]
  }
}
```

**[`.claude-plugin/plugin.json`](../../.claude-plugin/plugin.json)**: plug-in 메타데이터 (`name`, `version`, `description`, `homepage`, `repository`). hook 등록은 본 파일에 없음 — `hooks/hooks.json` 가 별도 SSOT.

**자동 로딩**: CC 가 plug-in 활성 시 `hooks/hooks.json` 표준 경로를 자동 인식해 등록.

**`${CLAUDE_PLUGIN_ROOT}`**: CC 가 plug-in hook 실행 시 자동 설정하는 환경변수. plug-in 의 cache 경로 (`~/.claude/plugins/cache/dcness/dcness/<version>/`) 를 가리킴.

---

## 5. 우회 / opt-out

| 메커니즘 | 적용 범위 | 효과 |
|---|---|---|
| **미활성 프로젝트** | 자동 | `is-active` 게이트가 즉시 통과 — 모든 hook no-op |
| **`.no-dcness-guard`** (cwd marker 파일) | 임시 | file-guard 만 우회. cwd 에 본 빈 파일 두면 boundary 검사 건너뜀 |
| **`DCNESS_INFRA=1`** (환경변수) | 영구 | dcness 자체 작업 모드 — DCNESS_INFRA_PATTERNS 해제 (자기 인프라 편집 가능) |
| **`~/.claude/.dcness-infra`** (marker 파일) | 영구 | `DCNESS_INFRA=1` 동일 효과 |
| **`CLAUDE_PLUGIN_ROOT` non-empty** | 영구 | dcness 자체 plug-in 실행 시 자동 — `is_infra_project()` true |
| **cwd whitelist 매칭** | 영구 | `/Users/<user>/project/dcness` 또는 화이트리스트 매칭 시 인프라 모드 |

**우회 불가**:
- `--no-verify` 등 git hook bypass — [`CLAUDE.md`](../../CLAUDE.md) §2 명시 금지
- catastrophic-gate / tdd-guard 우회 marker 없음 (의도적 — 잘못된 시퀀스는 회복 비용 ↑)

---

## 6. 한눈 요약

| # | Hook | Event | Matcher | 차단 | 핵심 역할 |
|---|---|---|---|---|---|
| 1 | session-start | SessionStart | — | X (inject) | dcness-rules 강제 read + 토큰 의무 + state bootstrap |
| 2 | catastrophic-gate | PreToolUse | Agent | ✓ | orchestration §2.3 5 룰 위반 시 Agent 호출 차단 |
| 3 | file-guard | PreToolUse | Edit/Write/Read/Bash/mcp__.* | ✓ | handoff-matrix §4 경계 (ALLOW/READ_DENY/INFRA) 강제 |
| 4 | tdd-guard | PreToolUse | Edit/Write/NotebookEdit | ✓ | TS / JS src 변경 시 매칭 test 부재면 deny |
| 5 | post-agent-clear | PostToolUse | Agent | X (inject) | sub-agent prose 자동 저장 + trace inject |
| 6 | post-file-op-trace | PostToolUse | Edit/Write/Read/Bash/mcp__.* | X | sub-agent 활성 시 tool trace 누적 |

---

## 7. 참조

**자연어 SSOT (본 hook 들이 강제하는 룰의 spec)**:
- [`dcness-rules.md`](dcness-rules.md) §1 — 대원칙 (강제 영역 2가지)
- [`orchestration.md`](orchestration.md) §2.3 — catastrophic 5 룰 (catastrophic-gate 강제 대상)
- [`handoff-matrix.md`](handoff-matrix.md) §4 — 권한 매트릭스 (file-guard 강제 대상)
- [`loop-procedure.md`](loop-procedure.md) — Step 0~8 mechanics (hook 시점이 절차 어디에 끼는지)

**코드 SSOT**:
- [`harness/hooks.py`](../../harness/hooks.py) — 모든 hook handler dispatch
- [`harness/session_state.py`](../../harness/session_state.py) — `is-active` 게이트 + run state machine
- [`harness/agent_boundary.py`](../../harness/agent_boundary.py) — `DCNESS_INFRA_PATTERNS` + ALLOW/READ_DENY 코드 SSOT

**등록 manifest**:
- [`hooks/hooks.json`](../../hooks/hooks.json) — hook 등록 표준 형식
- [`.claude-plugin/plugin.json`](../../.claude-plugin/plugin.json) — plug-in 메타데이터
