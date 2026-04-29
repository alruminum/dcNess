# Change Rationale History (WHY log)

> 본 파일은 dcNess 프로젝트 모든 변경 작업의 **WHY** (왜 바꿨나) 로그.
> 규칙 정의: [`governance.md`](governance.md) §2.3 / §2.6 (재기술 금지).

## 형식

```
### {Task-ID}
- **Date**: YYYY-MM-DD
- **Rationale**: 변경 동기 / 해결할 문제
- **Alternatives**: 검토한 대안과 기각 이유 (최소 1개 이상)
- **Decision**: 채택안 + 채택 이유
- **Follow-Up**: 후속 작업 / 측정 항목 / 회귀 위험
```

---

## Records

### DCN-CHG-20260429-01
- **Date**: 2026-04-29
- **Rationale**: 신규 프로젝트 dcNess 는 RWHarness fork-and-refactor 의 메인 Claude 직접 작업 모드(`status-json-mutate-pattern.md` §10/§11). 코드/정책/빌드 변경이 관련 문서를 동반하지 않아 발생하는 drift 를 commit 단위에서 차단할 거버넌스가 부재.
- **Alternatives**:
  1. *PR 리뷰어 수동 검사* — 인적 오류, 일관성 없음. 기각.
  2. *GitHub Action 만 (push 후 fail)* — 피드백 지연, `status-json-mutate-pattern.md` R9 trade-off 와 동일. local 차단 부재. 기각.
  3. *(채택)* **3중 pre-commit + SSOT** — git hook + Claude Code hook + 에이전트 지침 + diff 기반 게이트. local 차단 + 기계 강제 + 에이전트 강제 동시.
- **Decision**: 옵션 3. `governance.md` SSOT + `scripts/check_document_sync.mjs` diff 게이트 + 3중 pre-commit. `status-json-mutate-pattern.md` §2.5 원칙 1(룰 순감소) 정합 — *기존 룰 중복 회피* 위해 SSOT 단일화, 다른 파일은 참조만.
- **Follow-Up**:
  - bootstrap PR 머지 후 1주 사용 데이터 수집 (Document-Exception 빈도, false positive 횟수)
  - GitHub Actions workflow (`.github/workflows/document-sync.yml`) 추가는 별도 Task-ID
  - 30일 후 carry-over: 게이트가 차단한 위반 카탈로그 → `governance.md` §2.6 룰 정정 input
  - git 저장소 초기화 + 첫 commit (별도 작업)

### DCN-CHG-20260429-02
- **Date**: 2026-04-29
- **Rationale**:
  - dcNess 는 글로벌 `~/.claude/CLAUDE.md` 의 RWHarness 위임 룰(에이전트 분기 / 인프라 분기)이 미적용되는 신규 프로젝트(`status-json-mutate-pattern.md` §10/§11.4). 메인 Claude 가 본 저장소 작업 시 *어떤 절차·문서·금지사항*을 따라야 하는지 단일 진입점이 부재.
  - 부수 문제: `CLAUDE.md` / `AGENTS.md` 같은 루트 정책 파일이 게이트의 Change-Type 분류에서 어떤 패턴에도 매칭되지 않아 *분류 비대상* → 정책 변경이 record/rationale 동반 없이 통과되는 구멍.
- **Alternatives**:
  1. *글로벌 `~/.claude/CLAUDE.md` 만 의존* — RWHarness 위임 룰이 dcNess 모드와 충돌 (architect/engineer 강제 vs §11.4 메인 직접 작업). 기각.
  2. *루트 정책 파일을 `docs-only` 로 분류* — 정책 변경에 WHY 로그 동반 강제가 안 됨. 기각.
  3. *(채택)* **루트 CLAUDE.md 신규 + 게이트 `agent` 카테고리에 `^CLAUDE\.md$` / `^AGENTS\.md$` 추가** — 프로젝트 모드 명시 + 정책 변경에 record + rationale 동반 강제.
- **Decision**: 옵션 3. CLAUDE.md 는 SSOT 재기술 금지 — 절차·링크·문서지도만 박는다. 게이트 룰은 governance.md §2.2 와 `check_document_sync.mjs` 양쪽 동시 갱신 (코드 = 명세 구현).
- **Follow-Up**:
  - 후속 정책 파일(예: `SECURITY.md`, `CONTRIBUTING.md`) 도입 시 동일 카테고리 검토.
  - 빌드/테스트 도입 시 CLAUDE.md §4 개발 명령어 / §6 환경변수 갱신 (별도 Task-ID).
  - `.github/workflows/document-sync.yml` 추가 (CI 게이트, 별도 Task-ID).

### DCN-CHG-20260429-03
- **Date**: 2026-04-29
- **Rationale**:
  - `docs/status-json-mutate-pattern.md` Phase 1 의 acceptance criteria 첫 항목: "`harness/state_io.py` 모듈 + R8 normalize (MissingStatus exception) + 테스트 100%".
  - RWHarness 의 `parse_marker` (regex + alias 사다리, ~110 LOC + `MARKER_ALIASES` 54 LOC) 가 LLM 변형 emit 마다 사다리 확장(jajang 도그푸딩 12 PR cycle, CHG-09→CHG-14.1 PR #17 12 변형 추가) → 룰이 룰을 부르는 reactive cycle (proposal §2.5 원칙 1 위반).
  - 발상 전환: agent 의 자유 텍스트 신뢰 폐기 → agent 가 **외부 상태 파일 mutate**, harness 는 그 파일만 read. 텍스트 파싱 0, 결정론 100%.
  - 본 작업은 Phase 1 의 *단일 신규 모듈* — RWHarness 코드 복사 없이 `state_io.py` 만 net-new 작성. 다른 Phase 1 항목(disallowedTools / ALLOW_MATRIX / 7 호출지 / handoff / preamble / checkpoint) 진입 전 foundation 확보.
- **Alternatives**:
  1. *RWHarness `harness/core.py` 전체 복사 후 in-place 수정* — Phase 1 sub-phase 분리(1.1 mechanism / 1.2 handoff / 1.3 preamble / 1.4 checkpoint) 가치 손실. 회귀 발생 시 어느 sub 가 원인인지 분리 불가능. proposal §5 Phase 1 sub-분할 정신 위반. 기각.
  2. *바로 7 parse_marker 호출지부터 변환* — `state_io.py` 부재 상태로 호출지만 변환 불가능. 순서 역전. 기각.
  3. *(채택)* **단일 신규 모듈 + 32 테스트 + 거버넌스 동반** — Phase 1 sub 1.1 mechanism 의 *맨 처음 단계*. R8 5 failure modes (not_found/empty/race/malformed_json/schema_violation) 단일 normalize + atomic write (POSIX rename) + path traversal self-check (R1 layer 1) 한 번에 covered.
- **Decision**:
  - 옵션 3. `harness/state_io.py` 신규 ~290 LOC, `tests/test_state_io.py` 32 케이스.
  - **proposal §2.5 원칙 3 (자율성 최대화) 정합**: schema 의 required 키는 `status` 하나만. `fail_items`, `non_obvious_patterns`, `next_actions` 등 freeform. agent 가 자유롭게 채울 수 있는 영역 보존.
  - **R1 layer 1 (3-layer defense 첫 layer)**: state_path 가 화이트리스트 패턴(`_AGENT_NAME_RE` / `_MODE_NAME_RE` / `_RUN_ID_RE`) + path.relative_to(base) self-check 으로 path traversal 차단. agent-boundary.py PreToolUse + PostToolUse 추가 layer 는 이후 Task 에서.
  - **atomic write (POSIX `os.replace`)**: tmp 에 쓰고 rename → Write 도중 read 시 race / malformed 차단.
  - **race vs empty 분리**: 빈 파일 + mtime < 100ms 면 `race` (재read 권장), 그 외엔 `empty`. caller retry 정책 분기 명확.
  - **base_dir 기본값 lazy**: `Path.cwd()` 가 import 시점이 아니라 호출 시점 평가 — `_DefaultBaseProxy` 로 우회. 테스트 격리 + 다른 cwd 에서 import 안전.
- **Follow-Up**:
  - **(다음 Task-ID)** validator @OUTPUT 형식 변환 — `agents/validator*.md` 의 `@OUTPUT_FILE` / `@OUTPUT_SCHEMA` / `@OUTPUT_RULE` 컨벤션 도입. RWHarness 의 `agents/validator/*.md` (5 모드 sub-doc) 복사 후 각 변환.
  - **(다음 Task-ID)** RWHarness `harness/core.py` 의 plan_validation / design_validation / ux_validation 함수 (총 7 호출지) 복사 + `parse_marker` → `read_status` 치환. ENV 게이트 `HARNESS_STATUS_JSON_VALIDATOR=1` 도입.
  - **(다음 Task-ID)** RWHarness `hooks/agent-boundary.py` 복사 + validator ALLOW_MATRIX 에 status path regex 추가, `_AGENT_DISALLOWED["validator"]` 에서 Write 제거.
  - **(다음 Task-ID)** `docs/migration-decisions.md` — proposal §11.2 framework (catastrophic-prevention / 자연 폐기 / 단순화) 모듈 분류표.
  - **측정 항목**: 5 failure modes 모두 `MissingStatus` 단일 catch 보장 (다른 exception 누수 0). 테스트로 명문화 — `TestMissingStatusContract`. 실제 운영 시 다른 exception 누수 발견되면 회귀 PR.
