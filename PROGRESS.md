# PROGRESS

## 현재 상태

- 거버넌스 시스템 부트스트랩 완료 (`DCN-CHG-20260429-01`, PR #1 머지)
- 프로젝트 루트 `CLAUDE.md` + 루트 정책 파일 게이트 분류 추가 (`DCN-CHG-20260429-02`)
- **Plugin 배포 인프라**: `.claude-plugin/{plugin,marketplace}.json` (`DCN-CHG-20260429-04`)
  - 이름 = `dcness`, 버전 = `0.1.0-alpha`. RWHarness 와 공존 가능 설계.
- **모듈 분류 framework 적용**: `docs/migration-decisions.md` (`DCN-CHG-20260429-05`)
- **CI 게이트 3종**: Document Sync (`-08`) / Python tests (`-09`) / Plugin manifest (`-10`)
- **README + AGENTS 보강**: `-11`, `-12`
- **🚀 Phase 2 iter 4 — designer + design-critic prose-only** (`DCN-CHG-20260429-18`):
  - `agents/designer.md` (DESIGN_READY_FOR_REVIEW / DESIGN_LOOP_ESCALATE) — 2×2 매트릭스 (SCREEN/COMPONENT × ONE_WAY/THREE_WAY) 4 모드 + Phase 0 (이슈 생성, Pencil 캔버스) + Phase 1 (variant 생성) + Phase 4 (DESIGN_HANDOFF, outline-first) + 차별화 의무 + View 전용 원칙
  - `agents/design-critic.md` (VARIANTS_APPROVED / VARIANTS_ALL_REJECTED / UX_REDESIGN_SHORTLIST) — 4 기준 (UX 명료성·미적 독창성·컨텍스트 적합성·구현 실현성) 각 10점, 총 40점, PASS 28+ 기준
- **🚀 Phase 2 iter 3 — engineer + test-engineer prose-only** (`DCN-CHG-20260429-17`):
  - `agents/engineer.md` (IMPL_DONE / SPEC_GAP_FOUND / IMPLEMENTATION_ESCALATE / TESTS_FAIL / POLISH_DONE) — Phase 1 스펙 검토 + Phase 2 구현 + 듀얼 모드 + DESIGN_HANDOFF + 재시도 한도 + 커밋 단위 룰
  - `agents/test-engineer.md` (TESTS_WRITTEN / SPEC_GAP_FOUND) — TDD attempt 0 전용, src/ 읽기 금지 (catastrophic-prevention), impl `## 생성/수정 파일` 경로만 사용
- **🚀 Phase 2 iter 2 — architect 8 docs prose-only** (`DCN-CHG-20260429-16`):
  - `agents/architect.md` (마스터, 7 모드 인덱스 + Outline-First 자기규율 + TRD 현행화 룰)
  - `agents/architect/system-design.md` (SYSTEM_DESIGN_READY)
  - `agents/architect/module-plan.md` (READY_FOR_IMPL — depth/design frontmatter, DB 영향도 분석, 듀얼 모드 가드레일)
  - `agents/architect/spec-gap.md` (SPEC_GAP_RESOLVED / PRODUCT_PLANNER_ESCALATION_NEEDED / TECH_CONSTRAINT_CONFLICT)
  - `agents/architect/task-decompose.md` (READY_FOR_IMPL — Outline-First, 듀얼 모드 가드레일)
  - `agents/architect/tech-epic.md` (SYSTEM_DESIGN_READY)
  - `agents/architect/light-plan.md` (LIGHT_PLAN_READY — bugfix / DESIGN_HANDOFF / REVIEW_FIX / DOCS_UPDATE)
  - `agents/architect/docs-sync.md` (DOCS_SYNCED / SPEC_GAP_FOUND / TECH_CONSTRAINT_CONFLICT)
  - 모두 prose writing guide. `---MARKER:X---` 텍스트 마커 + `@OUTPUT` JSON schema + preamble / agent-config 별 layer 의존 폐기.
- **🚀 Phase 2 iter 1 — 4 read-only agents prose-only** (`DCN-CHG-20260429-15`):
  - `agents/pr-reviewer.md` (LGTM / CHANGES_REQUESTED) — validator 와 역할 분리, 스코프 매트릭스, 레거시 처리
  - `agents/plan-reviewer.md` (PLAN_REVIEW_PASS / PLAN_REVIEW_CHANGES_REQUESTED) — 8 차원 (현실성·MVP·제약·UX·숨은가정·경쟁·BM·기술실현)
  - `agents/qa.md` (FUNCTIONAL_BUG / CLEANUP / DESIGN_ISSUE / KNOWN_ISSUE / SCOPE_ESCALATE) — 역질문 루프, MCP+tracker CLI 폴백
  - `agents/security-reviewer.md` (SECURE / VULNERABILITIES_FOUND) — OWASP Top 10 + WebView 특화
  - 모두 prose writing guide 형식. `---MARKER:X---` 텍스트 마커 + `@OUTPUT_*` JSON schema + preamble 자동주입 / agent-config 별 layer 의존 모두 폐기.
- **🧹 stale 참조 sweep** (`DCN-CHG-20260429-14`): CLAUDE.md test 명령어 + python-tests.yml 헤더 + marketplace.json description/tags + .gitignore 코멘트 + migration-decisions framework 표현을 prose-only 로 정정. history record 항목은 governance §2.4 스코핑 정합으로 미수정.
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

### Phase 2 — 메타 LLM 통합 + 다른 12 agent docs (진행 중)

**다음 iteration 시작점**: `git log --oneline` + 본 PROGRESS 의 진행도 확인 후 다음 묶음 picker.

- [ ] Anthropic SDK 통합 — `interpret_signal` 의 메타 LLM interpreter 구현 (haiku, cycle 당 비용 측정 — proposal R8)
- [ ] ambiguous prose 카탈로그 — `MissingSignal(ambiguous)` raise 시 `.metrics/ambiguous-prose.jsonl` 누적 (proposal R1 acceptance)
- [ ] 다른 agent docs 를 prose writing guide 로 변환:
  - [x] **iter 1 완료** (DCN-CHG-20260429-15): `agents/pr-reviewer.md`, `agents/plan-reviewer.md`, `agents/qa.md`, `agents/security-reviewer.md`
  - [x] **iter 2 완료** (DCN-CHG-20260429-16): `agents/architect.md` + 7 mode sub-doc
  - [x] **iter 3 완료** (DCN-CHG-20260429-17): `agents/engineer.md` + `agents/test-engineer.md`
  - [x] **iter 4 완료** (DCN-CHG-20260429-18): `agents/designer.md` (4 모드 inline) + `agents/design-critic.md`
  - [ ] **iter 5**: `agents/ux-architect.md` + `agents/product-planner.md`

### Phase 3 — Plugin 배포 dry-run (선택)
- [ ] RWHarness 와 공존 시나리오 검증 (proposal §12.3.2)
- [ ] 1 프로젝트 1 cycle 도그푸딩
- [ ] 휴리스틱 interpreter hit rate 측정 (단어경계 매칭 vs ambiguous 빈도)

### 인프라 / CI 보강
- [ ] branch protection 룰 추가 (사용자 수동, GitHub Settings)
- [ ] CLAUDE.md §6 환경변수 — 도입 시 갱신

## Blockers
- 없음
