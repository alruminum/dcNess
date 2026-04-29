# dcNess

> **Status**: `0.1.0-alpha` — Phase 1 (validator 단위) 완료
> **Origin**: [`alruminum/realworld-harness`](https://github.com/alruminum/realworld-harness) fork-and-refactor
> **Spec**: [`docs/status-json-mutate-pattern.md`](docs/status-json-mutate-pattern.md)

Lightweight harness — **status JSON mutate 결정론** + **4 기둥 정합** + **함정 회피 5원칙** 기반의 RWHarness 후속.

## 무엇이 다른가

| 항목 | RWHarness | dcNess |
|---|---|---|
| 결정론 메커니즘 | `parse_marker` regex + `MARKER_ALIASES` 사다리 (~180 LOC) | `state_io.read_status` (~290 LOC) — agent 가 외부 status JSON 을 *mutate*, harness 는 그 파일만 *read* |
| 컨텍스트 layer | 5 layer (CLAUDE.md + agents + agent-config + preamble + sub-doc) | 2 layer (CLAUDE.md + agents) — preamble / agent-config 자동 주입 폐기 |
| 게이트 | hook 7+ (agent-boundary / commit-gate / etc.) | 거버넌스 + 3 CI workflow (Document Sync + Python tests + Plugin manifest) |
| LOC 목표 | 5000 | 2500 ~ 3000 |

핵심 발상 (proposal §2):

> "agent 의 자유 텍스트를 신뢰하지 않는다.
>  agent 에게 외부 상태 파일 mutate 책임 부여.
>  orchestrator 는 그 파일만 read."

## 1차 구현 (Phase 1) 현황

✅ **완료** — validator 단일 agent 단위로 status-JSON-mutate 패턴 검증.

| 컴포넌트 | 위치 | 상태 |
|---|---|---|
| Status I/O 모듈 | [`harness/state_io.py`](harness/state_io.py) | 32 단위 테스트 통과 (R8 5 failure modes 단일 normalize) |
| Validator agent docs | [`agents/validator.md`](agents/validator.md) + [`agents/validator/*.md`](agents/validator) (5 모드) | `@OUTPUT_FILE` / `@OUTPUT_SCHEMA` / `@OUTPUT_RULE` 형식 |
| Schema round-trip 검증 | [`tests/test_validator_schemas.py`](tests/test_validator_schemas.py) | 9 단위 테스트 통과 |
| Plugin manifest | [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) + [marketplace.json](.claude-plugin/marketplace.json) | RWHarness 와 공존 가능 (`name=dcness`) |
| Governance | [`docs/process/governance.md`](docs/process/governance.md) | Document Sync 게이트 SSOT |
| CI workflows | [`.github/workflows/`](.github/workflows) | 3 종 (document-sync / python-tests / plugin-manifest) |

자세한 현황: [`PROGRESS.md`](PROGRESS.md)

## Quick Start (개발자)

### 의존성

- Python 3.11+ (테스트 실행)
- Node.js 20+ (governance 게이트)
- 외부 패키지 0 (표준 라이브러리만)

### 셋업

```sh
git clone https://github.com/alruminum/dcNess.git
cd dcNess

# git pre-commit hook 설치 (1회)
cp scripts/hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### 검증

```sh
# 단위 테스트 (state_io + validator schemas)
python3 -m unittest discover -s tests -v

# Document Sync 게이트 (수동 실행 — commit 시 자동 호출)
node scripts/check_document_sync.mjs

# Plugin manifest 검증
node scripts/check_plugin_manifest.mjs
```

### 코드 사용 예 (`state_io`)

```python
from harness.state_io import write_status, read_status, MissingStatus

# Agent 측 — status JSON Write
write_status(
    "validator", "run_001",
    {
        "status": "PLAN_VALIDATION_PASS",
        "fail_items": [],
        "non_obvious_patterns": ["impl 6.2 의 retry 횟수 명세 일치"],
    },
    mode="PLAN_VALIDATION",
)

# Orchestrator 측 — 결정론 read
try:
    result = read_status(
        "validator", "run_001",
        mode="PLAN_VALIDATION",
        allowed_status={"PLAN_VALIDATION_PASS", "PLAN_VALIDATION_FAIL"},
    )
    if result["status"] == "PLAN_VALIDATION_PASS":
        # 다음 단계 진입
        ...
except MissingStatus as e:
    # 5 failure modes 단일 catch — e.reason 으로 retry 정책 분기
    if e.reason in ("empty", "race"):
        ...  # 100ms 후 1회 재read
    else:
        ...  # 즉시 fail (not_found / malformed_json / schema_violation)
```

## 거버넌스 (필수)

본 저장소의 모든 변경은 [`docs/process/governance.md`](docs/process/governance.md) 에 따른다 (SSOT).

- **Task-ID**: `DCN-CHG-YYYYMMDD-NN` 형식. 모든 작업은 단 하나의 ID.
- **3중 강제**: git pre-commit hook + Claude Code PreToolUse hook + AGENTS.md (외부 에이전트 지침)
- **CI 게이트**: PR 단위로 base..head diff 검사 — local 우회 차단

PR 절차: [`CLAUDE.md`](CLAUDE.md) §5.

## 다음 단계 (Phase 2 ~ )

[`PROGRESS.md`](PROGRESS.md) §TODO 참조. 핵심 후보:

- 다른 12 agent docs 변환 (architect / engineer / designer / ...)
- branch protection 룰 추가 (사용자 수동, GitHub Settings)
- 실 plugin 설치 dry-run — RWHarness 와 공존 검증 (proposal §12.3.2)

## 참조 문서

| 문서 | 역할 |
|---|---|
| [`docs/status-json-mutate-pattern.md`](docs/status-json-mutate-pattern.md) | proposal — Goal / Mechanism / Phase / Risks / Plugin 전환 절차 |
| [`docs/migration-decisions.md`](docs/migration-decisions.md) | RWHarness 모듈 PRESERVE / DISCARD / REFACTOR 분류 |
| [`docs/process/governance.md`](docs/process/governance.md) | Document Sync SSOT |
| [`docs/process/document_update_record.md`](docs/process/document_update_record.md) | WHAT 로그 (Task-ID 별 변경 파일) |
| [`docs/process/change_rationale_history.md`](docs/process/change_rationale_history.md) | WHY 로그 (Task-ID 별 동기·대안·결정·후속) |
| [`PROGRESS.md`](PROGRESS.md) | 현재 상태 / TODO / Blockers |
| [`AGENTS.md`](AGENTS.md) | 외부 에이전트(Codex 등) 지침 |
| [`CLAUDE.md`](CLAUDE.md) | 메인 Claude 작업 지침 |

## License

MIT — see [`LICENSE`](LICENSE) (TBD).
