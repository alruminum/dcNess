# Document Update Record (WHAT log)

> 본 파일은 dcNess 프로젝트 모든 변경 작업의 **WHAT** (무엇을 바꿨나) 로그.
> 규칙 정의: [`governance.md`](governance.md) §2.3 / §2.6 (재기술 금지).

## 형식

```
### {Task-ID}
- **Date**: YYYY-MM-DD
- **Change-Type**: spec | agent | harness | hooks | ci | test | docs-only (복수 가능)
- **Files Changed**:
  - path/to/file.md
  - path/to/code.ts
- **Summary**: 한 줄 요약
- **Document-Exception** (있을 때만): 예외 사유
```

---

## Records

### DCN-CHG-20260429-01
- **Date**: 2026-04-29
- **Change-Type**: ci, docs-only
- **Files Changed**:
  - `docs/process/governance.md` (신규)
  - `docs/process/document_update_record.md` (신규)
  - `docs/process/change_rationale_history.md` (신규)
  - `docs/process/document_impact_matrix.md` (신규)
  - `scripts/check_document_sync.mjs` (신규)
  - `scripts/hooks/pre-commit` (신규)
  - `scripts/hooks/cc-pre-commit.sh` (신규)
  - `.claude/settings.json` (신규)
  - `.github/PULL_REQUEST_TEMPLATE.md` (신규)
  - `AGENTS.md` (신규)
  - `PROGRESS.md` (신규)
- **Summary**: 거버넌스 시스템 초기 구축 — Document Sync 게이트(`check_document_sync.mjs`) + 3중 pre-commit 강제(git hook + Claude Code hook + AGENTS 지침) + SSOT(`governance.md`).
- **Document-Exception**: bootstrap commit — 거버넌스 자체 도입이라 이전 산출물 없음. 본 항목 자체가 self-record.

### DCN-CHG-20260429-02
- **Date**: 2026-04-29
- **Change-Type**: agent, ci, docs-only
- **Files Changed**:
  - `CLAUDE.md` (신규 — 메인 Claude 작업 지침)
  - `docs/process/governance.md` (§2.2 agent 패턴에 `^CLAUDE\.md$`, `^AGENTS\.md$` 추가)
  - `scripts/check_document_sync.mjs` (CATEGORY_RULES agent 토큰에 동일 패턴 추가)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: 프로젝트 루트 CLAUDE.md 신규 + 게이트 룰에 루트 정책 파일(`CLAUDE.md` / `AGENTS.md`) `agent` 카테고리 분류 추가.

### DCN-CHG-20260429-03
- **Date**: 2026-04-29
- **Change-Type**: harness, test, agent, docs-only
- **Files Changed**:
  - `harness/state_io.py` (신규 — Phase 1 핵심 모듈)
  - `tests/test_state_io.py` (신규 — 32 케이스, 5 failure modes 검증)
  - `CLAUDE.md` (§4 개발 명령어에 테스트 실행 명령 추가)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: Phase 1 foundation — `harness/state_io.py` 신규(write/read/clear + R8 5 failure modes 단일 normalize) + 테스트 32 케이스 전부 PASS. `parse_marker` 사다리 폐기를 위한 첫 모듈.

### DCN-CHG-20260429-05
- **Date**: 2026-04-29
- **Change-Type**: docs-only
- **Files Changed**:
  - `docs/migration-decisions.md` (신규 — RWHarness 모듈 분류표)
  - `docs/process/document_update_record.md` (본 항목)
- **Summary**: `status-json-mutate-pattern.md` §11.2 framework 적용 — RWHarness 의 `harness/` / `hooks/` / `agents/` / `scripts/` / `orchestration/` / `.claude-plugin/` 모듈을 PRESERVE / DISCARD / REFACTOR 로 분류. dcNess 메인 작업 모드(§11.4) 정합으로 hook/impl_loop 류는 자연 폐기, agent docs 변환 + state_io.py 만 net-new.
- **Document-Exception**: 본 변경은 분류 *결정 기록* 이라 추가 deliverable 부재. heavy 카테고리 미해당 — `docs-only` 단독.

### DCN-CHG-20260429-11
- **Date**: 2026-04-29
- **Change-Type**: docs-only
- **Files Changed**:
  - `README.md` (대폭 보강 — 정체성·차이점·Phase 1 현황·Quick Start·코드 예·거버넌스·후속)
  - `docs/process/document_update_record.md` (본 항목)
- **Summary**: README.md 보강 — Phase 1 완료 외부 공개. RWHarness vs dcNess 차이 표 + 1차 구현 컴포넌트 매핑 + Quick Start (의존성 / 셋업 / 검증 / 코드 사용 예) + 거버넌스 / 다음 단계 / 참조 문서 지도.

### DCN-CHG-20260429-10
- **Date**: 2026-04-29
- **Change-Type**: ci
- **Files Changed**:
  - `scripts/check_plugin_manifest.mjs` (신규 — manifest 무결성 validator)
  - `.github/workflows/plugin-manifest.yml` (신규 — CI workflow)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: Plugin manifest 무결성 검증 — `plugin.json` + `marketplace.json` 의 required 필드 + name regex + 두 파일 간 name 정합 검증. `claude plugin validate` (CLI 의존) 대신 Node-only minimum guard.

### DCN-CHG-20260429-09
- **Date**: 2026-04-29
- **Change-Type**: ci
- **Files Changed**:
  - `.github/workflows/python-tests.yml` (신규)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: Python unittest 자동 회귀 차단 — `tests/test_state_io.py` (32) + `tests/test_validator_schemas.py` (9) 자동 실행. paths 필터로 `harness/` / `tests/` / `agents/` 변경 시만 발동(docs-only PR 면제).

### DCN-CHG-20260429-08
- **Date**: 2026-04-29
- **Change-Type**: ci
- **Files Changed**:
  - `.github/workflows/document-sync.yml` (신규 — Document Sync 게이트 CI workflow)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: Document Sync 게이트 CI level 추가 — PR 단위로 base..head diff 를 검사. 로컬 게이트(git pre-commit + Claude Code PreToolUse) 가 우회된 경우(`--no-verify` 등) CI 가 *최후 차단*. proposal 4-pillar #2 (CI 게이트) 정합.

### DCN-CHG-20260429-07
- **Date**: 2026-04-29
- **Change-Type**: test
- **Files Changed**:
  - `tests/test_validator_schemas.py` (신규 — 9 케이스)
  - `docs/process/document_update_record.md` (본 항목)
- **Summary**: validator agent docs 의 모든 ```json``` 예시 status JSON 이 `state_io.read_status` 와 round-trip 통과하는지 자동 검증. 마스터의 매트릭스 정합 + 폐기 컨벤션(`---MARKER:X---` 결정 원천) / preamble 자동 주입 의존 부재 검증 포함. 향후 docs 변경 시 schema 깨지면 즉시 fail.
- **Document-Exception**: `test` 단독 카테고리 — heavy 미해당으로 rationale 면제. 본 변경은 DCN-CHG-20260429-06 의 *follow-up acceptance* 항목 직접 구현이라 rationale 동반은 잉여.

### DCN-CHG-20260429-06
- **Date**: 2026-04-29
- **Change-Type**: agent
- **Files Changed**:
  - `agents/validator.md` (신규 — 마스터 + 5 모드 인덱스)
  - `agents/validator/plan-validation.md` (신규)
  - `agents/validator/code-validation.md` (신규)
  - `agents/validator/design-validation.md` (신규)
  - `agents/validator/bugfix-validation.md` (신규)
  - `agents/validator/ux-validation.md` (신규)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
- **Summary**: validator agent docs 6개 신규 — RWHarness 의 `agents/validator*.md` 를 status JSON Write 형식으로 변환. `@OUTPUT_FILE` / `@OUTPUT_SCHEMA` / `@OUTPUT_RULE` 컨벤션 채택. `---MARKER:X---` 텍스트 컨벤션 + preamble.md 자동 주입 의존 + agent-config 별 layer 모두 폐기.

### DCN-CHG-20260429-04
- **Date**: 2026-04-29
- **Change-Type**: agent, ci, docs-only
- **Files Changed**:
  - `.claude-plugin/plugin.json` (신규 — plugin 메타)
  - `.claude-plugin/marketplace.json` (신규 — marketplace 정의)
  - `docs/process/governance.md` (§2.2 agent 패턴에 `^\.claude-plugin/` 추가)
  - `scripts/check_document_sync.mjs` (CATEGORY_RULES agent 토큰 동기 갱신)
  - `docs/process/document_update_record.md` (본 항목)
  - `docs/process/change_rationale_history.md`
  - `PROGRESS.md`
- **Summary**: Plugin 배포 인프라 — `dcness@dcness` plugin/marketplace manifest 신규. `status-json-mutate-pattern.md` §12 (RWHarness → 신규 Plugin 전환 절차) 정합. governance §2.2 의 `agent` 카테고리에 `.claude-plugin/` 패턴 추가하여 plugin manifest 변경에도 record/rationale 동반 강제.
