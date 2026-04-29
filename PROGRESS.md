# PROGRESS

## 현재 상태
- 거버넌스 시스템 부트스트랩 완료 (`DCN-CHG-20260429-01`, PR #1 머지)
- 프로젝트 루트 `CLAUDE.md` + 루트 정책 파일 게이트 분류 추가 (`DCN-CHG-20260429-02`)
- **Phase 1 foundation 진입**: `harness/state_io.py` 신규 + 테스트 32 PASS (`DCN-CHG-20260429-03`, PR #3 머지)
  - R8 5 failure modes (not_found/empty/race/malformed_json/schema_violation) 단일 normalize 검증 완료
  - atomic write (POSIX rename) + path traversal self-check (R1 layer 1) 포함
  - 적용 범위 = 모듈 단독. validator 호출지 / agent docs / hook ALLOW_MATRIX 변환은 후속 Task-ID
- **Plugin 배포 인프라**: `.claude-plugin/{plugin,marketplace}.json` 신규 (`DCN-CHG-20260429-04`)
  - 이름 = `dcness`, 버전 = `0.1.0-alpha`. RWHarness 와 공존 가능 설계 (proposal §12.3.2).
  - governance §2.2 의 `agent` 카테고리에 `^\.claude-plugin/` 패턴 추가하여 plugin manifest 변경도 heavy 카테고리 강제.
- **모듈 분류 framework 적용**: `docs/migration-decisions.md` (`DCN-CHG-20260429-05`)
  - DISCARD: parse_marker / generate_handoff / impl_loop / agent_call / agent-boundary hook / preamble.md
  - PRESERVE: 거버넌스 / plugin manifest
  - REFACTOR: agents/*.md @OUTPUT 변환 / class Flag → Phase 3.2
- **validator agent docs 변환 완료**: `agents/validator*.md` 6개 + 9 schema round-trip tests (`DCN-CHG-20260429-06,07`)
  - `@OUTPUT_FILE` / `@OUTPUT_SCHEMA` / `@OUTPUT_RULE` 형식 + 5 모드 mode-specific status enum
  - preamble / agent-config 의존 제거
  - 자동 검증: docs 변경 시 schema 깨지면 fail
- **CI 게이트 추가**: `.github/workflows/document-sync.yml` (`DCN-CHG-20260429-08`)
  - PR + push to main 시 base..head diff 검사 → local hook 우회 차단
- **Python 테스트 CI**: `.github/workflows/python-tests.yml` (`DCN-CHG-20260429-09`)
  - paths 필터(`harness/` / `tests/` / `agents/`) 로 docs-only PR 면제
  - state_io 32 케이스 + validator schemas 9 케이스 자동 회귀 차단

## TODO
### Phase 1 — validator 단위 완성 ✅
모든 acceptance 항목 완료 (state_io / agent docs 변환 / round-trip 검증). dcNess 메인 작업 모드(§11.4) 정합으로 RWHarness `harness/core.py` 의 7 parse_marker 호출지 / agent-boundary hook ALLOW_MATRIX / `_AGENT_DISALLOWED` 변경은 *plugin 배포 시점* 의 사용자 프로젝트 가드용 → 본 저장소엔 미도입.

### Phase 2 — 다른 12 agent docs 변환 (선택)
plugin 배포 시 사용자 프로젝트에서 각 agent 가 status JSON Write 하도록.
- [ ] `agents/architect.md` + 7 mode sub-doc (System Design / Module Plan / SPEC_GAP / Task Decompose / Technical Epic / Light Plan / Docs Sync)
- [ ] `agents/engineer.md`
- [ ] `agents/designer.md` + 4 mode sub-doc
- [ ] `agents/design-critic.md`
- [ ] `agents/qa.md`
- [ ] `agents/ux-architect.md`
- [ ] `agents/product-planner.md`
- [ ] `agents/plan-reviewer.md`
- [ ] `agents/pr-reviewer.md`
- [ ] `agents/security-reviewer.md`
- [ ] `agents/test-engineer.md`

### 인프라 / CI 보강
- [ ] `.github/workflows/plugin-validate.yml` (별도 Task)
- [ ] `.github/workflows/python-tests.yml` — agent docs schema round-trip 자동
- [ ] branch protection 룰 추가 (사용자 수동, GitHub Settings)
- [ ] CLAUDE.md §6 환경변수 — 도입 시 갱신

## Blockers
- 없음
