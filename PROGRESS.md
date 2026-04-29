# PROGRESS

## 현재 상태

- 거버넌스 시스템 부트스트랩 완료 (`DCN-CHG-20260429-01`, PR #1 머지)
- 프로젝트 루트 `CLAUDE.md` + 루트 정책 파일 게이트 분류 추가 (`DCN-CHG-20260429-02`)
- **Plugin 배포 인프라**: `.claude-plugin/{plugin,marketplace}.json` (`DCN-CHG-20260429-04`)
  - 이름 = `dcness`, 버전 = `0.1.0-alpha`. RWHarness 와 공존 가능 설계.
- **모듈 분류 framework 적용**: `docs/migration-decisions.md` (`DCN-CHG-20260429-05`)
- **CI 게이트 3종**: Document Sync (`-08`) / Python tests (`-09`) / Plugin manifest (`-10`)
- **README + AGENTS 보강**: `-11`, `-12`
- **🔄 Phase 1 재정렬 — Prose-Only Pattern** (`DCN-CHG-20260429-13`):
  - **proposal 갱신**: `docs/status-json-mutate-pattern.md` 가 *Prose-Only Pattern* 으로 정정. 형식 강제 자체가 사다리를 부른다는 자각 — JSON schema 도 형식 사다리의 한 형태. harness 강제 = 작업 순서 + 접근 영역만, 그 외는 agent 자율.
  - **폐기**: `harness/state_io.py` (~290 LOC) + `tests/test_state_io.py` (32) + `tests/test_validator_schemas.py` (9). JSON schema 강제 자체가 형식 사다리 잠재.
  - **신규**: `harness/signal_io.py` (~290 LOC) — `write_prose` / `read_prose` / `interpret_signal` (휴리스틱 + DI swap) / `MissingSignal` (3 reason).
  - **테스트**: `tests/test_signal_io.py` 29 PASS — round-trip / path 화이트리스트 / 휴리스틱 (단어경계·case-insensitive·다중매칭) / DI / clear_run_state.
  - **validator agent docs 6 재작성**: `@OUTPUT_*` 형식 강제 제거 → prose writing guide. 각 모드별 결론 enum 만 명시 (PASS / FAIL / SPEC_MISSING / ESCALATE 등).
  - 메타 LLM (haiku) 통합은 `interpreter=` DI swap point 로 남김 — 후속 Task-ID.

## TODO

### Phase 1 — Foundation (prose-only) ✅
모든 acceptance 항목 완료. dcNess 메인 작업 모드(`status-json-mutate-pattern.md` §11.4) 정합으로 RWHarness `harness/core.py` 의 parse_marker 호출지 / agent-boundary hook ALLOW_MATRIX / `_AGENT_DISALLOWED` 변경은 본 저장소엔 미도입 (plugin 배포 시점 사용자 프로젝트 가드용).

### Phase 2 — 메타 LLM 통합 + 다른 12 agent docs (선택)
- [ ] Anthropic SDK 통합 — `interpret_signal` 의 메타 LLM interpreter 구현 (haiku, cycle 당 비용 측정 — proposal R8)
- [ ] ambiguous prose 카탈로그 — `MissingSignal(ambiguous)` raise 시 `.metrics/ambiguous-prose.jsonl` 누적 (proposal R1 acceptance)
- [ ] 다른 12 agent docs 를 prose writing guide 로 변환:
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

### Phase 3 — Plugin 배포 dry-run (선택)
- [ ] RWHarness 와 공존 시나리오 검증 (proposal §12.3.2)
- [ ] 1 프로젝트 1 cycle 도그푸딩
- [ ] 휴리스틱 interpreter hit rate 측정 (단어경계 매칭 vs ambiguous 빈도)

### 인프라 / CI 보강
- [ ] branch protection 룰 추가 (사용자 수동, GitHub Settings)
- [ ] CLAUDE.md §6 환경변수 — 도입 시 갱신

## Blockers
- 없음
