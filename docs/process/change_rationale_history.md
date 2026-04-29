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

### DCN-CHG-20260429-18
- **Date**: 2026-04-29
- **Rationale**:
  - Phase 2 iter 4 = designer + design-critic 짝. designer 는 Pencil MCP 도구 다수 (batch_design, set_variables, replace_all_matching_properties 등 write-side) 보유 → variant 생성·HANDOFF 패키지 출력. design-critic 은 read-only (model: opus, 정량 평가).
  - PROGRESS 의 picker 에 "designer + 4 mode sub-doc + design-critic" 으로 적었으나 RWHarness 원본 확인 결과 designer 는 4 모드를 inline 으로 가짐 (별도 디렉토리 X). architect 와 다른 패턴. 그대로 따름.
- **Alternatives**:
  1. *designer 4 모드를 sub-doc 로 분리* — RWHarness 패턴과 다름. 일관성 깨짐. 기각.
  2. *designer 단독, design-critic 은 다음 iter* — design-critic 은 designer THREE_WAY 의 짝 호출 — 분리 시 라이프사이클 불완전. 기각.
  3. *(채택)* **designer + design-critic 짝 묶음, designer 4 모드 inline**: 라이프사이클 완전 + RWHarness 원본 패턴 정합.
- **Decision**:
  - 옵션 3. 2 docs 동시 작성. inline 4 모드.
  - **proposal §2.5 원칙 1 (룰 순감소)**: designer 의 Phase 4 outline 자기규율은 architect SYSTEM_DESIGN/TASK_DECOMPOSE 와 동일 — *thinking 폭증 방지* 의 작업 순서 강제 (대 원칙 적용 가능).
  - **View 전용 원칙 보존**: model 레이어 변경 금지 (store/hooks/biz logic). 작업 영역 강제(접근 영역) — proposal §2.5 대 원칙 적용 가능. 권장이 아닌 catastrophic 시퀀스 보호.
  - **차별화 의무 보존**: 4 축 중 2 축 이상. 색상만 다른 variant 는 1개 — 작업 결과물 품질 게이트지만 형식 강제 X (prose writing guide 의 *권장*).
  - **금지/허용 목록 보존**: AI 클리셰, Generic 폰트, Tailwind 등 — *자율성* 영역이지만 dcNess 메인 작업 모드 환경 외부 정책. plugin 배포 시 사용자 프로젝트 정합.
  - **design-critic model: opus**: 정량 평가의 정확성 위해 RWHarness 가 sonnet → opus 로 승격한 정책 보존.
- **Follow-Up**:
  - **(다음 iteration iter 5 — 마지막)**: ux-architect + product-planner. 두 에이전트는 PRD 단계의 시작점 (planner = PRD 생성, ux-architect = PRD → UX Flow Doc).
  - **(별도 Task-ID)** designer/design-critic 의 prose hash 안정성 측정 — Pencil MCP 출력은 결정론 X (스크린샷 path 변동) 이라 prose 본문 hash 만으로 checkpoint 가능한지 검증.

### DCN-CHG-20260429-17
- **Date**: 2026-04-29
- **Rationale**:
  - Phase 2 iter 3 = engineer + test-engineer (구현/테스트 짝). engineer 는 *Write 권한 보유* + agent-boundary ALLOW 영역(src/**) 강제 대상. test-engineer 는 *src/ 읽기 금지* (TDD 의 핵심) — 두 에이전트는 catastrophic-prevention 정책상 동시 검토.
  - PR #16 머지로 architect 8 docs 통과 → 다음은 engineer-side. proposal §11.4 정합으로 dcNess 메인 작업 모드는 위임 사이클 강제 없음, 단 plugin 배포 시점에 사용자 프로젝트에서 agent-boundary 가드 하 동작.
- **Alternatives**:
  1. *engineer + test-engineer + designer 3 묶음* — designer 는 4 mode sub-doc 보유 → 컨텍스트 폭증. 기각.
  2. *engineer 만 단독* — test-engineer 는 engineer 의 짝(TDD attempt 0) 이라 분리 시 일관성 흐림. 기각.
  3. *(채택)* **engineer + test-engineer 짝 묶음**: 둘이 같은 attempt 0 라이프사이클 공유 → 일관 변환.
- **Decision**:
  - 옵션 3. 2 docs 동시 작성. 한 commit 한 PR.
  - **catastrophic-prevention 보존**: test-engineer 의 "src/ 읽기 금지" + "impl 경로 외 추측 금지" + "RevivalButton.test.tsx 사고 박제" 보존. proposal §2.5 원칙 4 (catastrophic 시퀀스 보존) 정합 — 작업 순서·접근 영역 강제는 catastrophic 만.
  - **재시도 한도 정책 (attempt 3 + spec_gap 2 = 5회)** 보존: 작업 순서 영역 (proposal §2.5 대 원칙 적용 가능). 무한 루프 차단.
  - **attempt 1+ 토큰 최소화 룰**: 비용 폭증 패턴(out_tok 20K~37K 폭주가 ESCALATE 비용 80%) 보존. 권고 + 경고 영역 (proposal 원칙 2 정합).
  - **듀얼 모드 가드레일**: architect iter 2 와 동일 정책 — `src/theme/` 강제. 일관.
  - **engineer.md `tools` 라인**: RWHarness 원본 그대로 (Read, Write, Edit, Bash, Glob, Grep, Pencil MCP 5개). dcNess plugin 배포 시 같은 권한 매트릭스.
- **Follow-Up**:
  - **(다음 iteration iter 4)**: designer 마스터 + 4 mode sub-doc + design-critic. designer 는 Pencil MCP write 도구 다수 보유.
  - **(별도 Task-ID)** validator 의 code-validation 모드와 engineer 의 IMPL_DONE 사이 핸드오프 prose 디렉토리 path 가이드 — proposal §3 (Handoff) 정합으로 별도 형식 없이 prose 디렉토리만 명시.

### DCN-CHG-20260429-16
- **Date**: 2026-04-29
- **Rationale**:
  - Phase 2 iter 2 = architect 8 docs 변환 (마스터 + 7 sub-doc). RWHarness 의 architect 는 가장 큰 mode set (7 modes: SYSTEM_DESIGN, MODULE_PLAN, SPEC_GAP, TASK_DECOMPOSE, TECH_EPIC, LIGHT_PLAN, DOCS_SYNC) 이라 한 묶음으로 처리하는 게 일관성 측면 효율적.
  - architect 는 *Write* 도구 보유 + GitHub MCP / Pencil MCP 도구 → tools 라인 보존이 중요. RWHarness 원본의 도구 목록 그대로 복사.
  - 자기규율 (Outline-First) / Schema-First / NFR / impl frontmatter (depth, design) / TRD 현행화 / 듀얼 모드 가드레일 등 *정책* 부분은 모두 보존. 형식 강제(`---MARKER:X---` 텍스트 + `@OUTPUT` JSON schema) 만 폐기.
- **Alternatives**:
  1. *마스터만 작성하고 7 sub-doc 은 다음 iteration* — sub-doc 없이 마스터의 모드 인덱스만 있으면 incomplete. 기각.
  2. *7 sub-doc 을 단일 architect.md 에 통합* — 670 LOC 단일 파일은 가독성 저하 + 모드별 독립 변경 어려움. RWHarness 의 분리 패턴 정합성 깨짐. 기각.
  3. *(채택)* **마스터 + 7 sub-doc 일괄 작성**: RWHarness 디렉토리 구조 유지. 모드별 독립 evolutionary path 보존.
- **Decision**:
  - 옵션 3. 8 파일 동시 작성 + 한 commit + 한 PR.
  - **proposal §2.5 원칙 1 (룰 순감소) 정합**: RWHarness 원본의 마커 자기점검 섹션 ("🔴 출력 마커 절대 규칙" 등) + `@OUTPUT` JSON schema + preamble 자동주입 안내 + agent-config 별 layer 안내 모두 폐기. 각 docs 자기완결.
  - **원칙 3 (자율성 최대화)**: prose 결론 예시는 *권장* 으로만. 형식 자유, 마지막 단락 enum 단어만 명시 가이드.
  - **Outline-First 자기규율 보존**: 본문 생성량 큰 모드(SYSTEM_DESIGN / TASK_DECOMPOSE) 에서 thinking 폭증 방지. agent 자율성 영역(=*어떻게* 출력) 이지만 **구조 강제** 는 작업 순서 영역 (proposal §2.5 대 원칙). 권장.
  - **TRD 현행화 매핑 + impl frontmatter 정책 보존**: agent 자율 형식이 아니라 *프로젝트 정합성* 정책. proposal §2.5 적용 가능 영역 — 작업 순서.
  - **듀얼 모드 가드레일**: 디자인 시안 도착 후 컴포넌트 갈아엎기 0 정책. impl 의 `## 의존성` / `## 수용 기준` 추가 룰 보존.
- **Follow-Up**:
  - **(다음 iteration iter 3)**: engineer + test-engineer (구현·테스트 짝). engineer 는 src/ Write 권한 + agent-boundary ALLOW 매트릭스 영역. test-engineer 는 TDD attempt 0 전용.
  - **(별도 Task-ID)** 각 mode 의 prose 산출물 hash 안정성 측정 (proposal R7) — checkpoint 도입 시.

### DCN-CHG-20260429-15
- **Date**: 2026-04-29
- **Rationale**:
  - proposal §5 Phase 2 acceptance: "33 @OUTPUT 정의 → 작성 지침 변경, agent-config/*.md → agents/*.md 통합". dcNess Phase 1 에서 validator 6 docs 는 변환 완료. 나머지 12 agent docs 변환이 Phase 2 의 핵심.
  - 한 iteration 에 13 agent 전부 변환은 컨텍스트 압박 + 검토 부담. 5 iterations 분산 (proposal §11.4 안전망 "sub-phase 마다 smoke test" 정합).
  - iter 1 우선순위 = read-only validator 류 4 개 (pr-reviewer, plan-reviewer, qa, security-reviewer): 모두 도구 단순(Read/Glob/Grep) + 출력 enum 단순 + 검증된 패턴(validator.md). 가장 위험 낮은 묶음.
- **Alternatives**:
  1. *13 agent 일괄 변환* — 컨텍스트 폭증, 일관성 흐트러질 위험. 기각.
  2. *역할 카테고리별 (validator-류 / planning-류 / engineering-류 / design-류)* — 카테고리 경계 모호 (test-engineer 가 engineering 인지 validation 인지). 기각.
  3. *(채택)* **5 iterations × 묶음**: iter 1 read-only 4, iter 2 architect 8, iter 3 engineer+test-engineer, iter 4 designer 5, iter 5 ux+product. 각 묶음 = squash merge 단위.
- **Decision**:
  - 옵션 3. iter 1 = pr-reviewer + plan-reviewer + qa + security-reviewer.
  - **proposal §2.5 원칙 1 (룰 순감소) 정합**: RWHarness 원본의 `---MARKER:X---` 자기점검 섹션 + `@OUTPUT` JSON schema + preamble 자동주입 안내 + agent-config 별 layer 안내 모두 폐기. 각 docs 자기완결.
  - **원칙 3 (자율성 최대화)**: prose 작성 골격은 *권장* 으로만. 형식 자유, enum 단어만 마지막 단락에 명시.
  - **plan-reviewer 의 "검토 범위 경계" 섹션 보존**: scope drift 차단은 *접근 영역* 강제 (proposal §2.5 대원칙 적용 가능 영역). agent 의 도구 호출 지침은 정상 가이드.
  - **qa 의 GitHub MCP / tracker CLI 폴백**: 외부 시스템 mutation 도구 보존 (Bash 추적 ID 발급 한정). 작업 순서 강제 영역 — proposal §2.5 대 원칙 적용 가능.
- **Follow-Up**:
  - **(다음 iteration)** iter 2: architect 8 docs (System Design / Module Plan / SPEC_GAP / Task Decompose / Technical Epic / Light Plan / Docs Sync). architect 는 mode sub-doc 패턴 (validator 와 동일).
  - **(측정)** iter 1 후 4 docs 평균 LOC vs 원본 LOC 비교. 순감소 추세 모니터링 (proposal §2.5 원칙 1).

### DCN-CHG-20260429-14
- **Date**: 2026-04-29
- **Rationale**:
  - DCN-CHG-20260429-13 가 prose-only 로 패턴 전환했으나 forward-looking 문서/메타 (CLAUDE.md test 명령어 / python-tests.yml 헤더 / marketplace.json description / .gitignore 코멘트 / migration-decisions framework 질문) 에 stale `status JSON` / `state_io` 표현이 잔존.
  - Plugin manifest 의 `tags: ["status-json-mutate"]` 는 marketplace 검색 인덱스에 노출되는 *공개 메타* 라 정정 우선 순위 높음. CLAUDE.md §4 의 stale 단일 모듈 테스트 명령은 실행 시 `ModuleNotFoundError` (이미 삭제된 모듈) — 신규 기여자 onboarding 함정.
- **Alternatives**:
  1. *과거 record/rationale 항목까지 일괄 정정* — governance §2.4 "현재 diff 추가 라인만 유효" 정합 위반. 과거 사실 (당시 status JSON 도입했음) 을 사후에 prose-only 로 위장하면 history 신뢰성 손상. 기각.
  2. *Phase 2 시점에 일괄* — Phase 2 는 메타 LLM 통합 + 12 agent docs 변환이라 *별도 책임*. stale 표현은 onboarding 비용을 매일 발생시키므로 즉시 cleanup 이 옳음. 기각.
  3. *(채택)* **forward-looking 문서만 sweep + history 항목 보존 + Document-Exception 명시**.
- **Decision**:
  - 옵션 3. 5 파일 cleanup. history record 본문은 governance §2.4 정합으로 *명시적 미수정*. record 의 "본 변경" 자체는 새 Task-ID 의 추가 라인이라 게이트 통과.
  - tags 변경: `status-json-mutate` → `prose-only`. marketplace 사용자가 본 plugin 의 결정론 메커니즘을 정확히 식별 가능.
- **Follow-Up**:
  - **(별도 Task-ID)** RWHarness 와 plugin name 충돌 시나리오 dry-run — plugin 메타 변경이 install/disable 동작에 영향 주는지 확인.
  - **측정**: marketplace 검색 키워드 분석 시 `prose-only` 매칭 횟수 추적 (해당 메트릭 도입 시).

### DCN-CHG-20260429-13
- **Date**: 2026-04-29
- **Rationale**:
  - `docs/status-json-mutate-pattern.md` 가 Prose-Only Pattern 으로 전면 개정됨 — *형식 강제 자체가 사다리를 부른다* 는 자각. 이전 dcNess Phase 1 산출물(`state_io.py` 의 JSON schema + validator docs 의 `@OUTPUT_SCHEMA` + 32+9 schema round-trip 테스트)은 *status JSON 으로 형식만 바꾼 같은 함정* 이라는 진단. 폐기 대상.
  - 갱신된 proposal §1 의 사다리 다이어그램: parse_marker → MARKER_ALIASES → status JSON schema → 더 정교한 schema → 같은 함정 부활. JSON 으로 형식만 바꿔도 같은 cycle.
  - 갱신된 proposal §2.5 대 원칙: harness 가 강제하는 것은 *작업 순서 + 접근 영역만*. 출력 형식 / handoff 형식 / preamble 구조 / marker / status JSON / Flag 모두 agent 자율.
  - dcNess 메인 작업 모드(§10/§11.4)는 RWHarness 가드 미적용이라 작업 순서·접근 영역 강제 자체가 환경 경계 밖. 본 저장소가 Phase 1 에서 산출할 수 있는 것은 *prose I/O foundation* (signal_io.py) + *prose writing guide* (validator docs) + 회귀 테스트.
- **Alternatives**:
  1. *기존 state_io.py 보존 + 신규 signal_io.py 병행* — JSON schema 강제 자체를 *deprecated* 로 박고 이전 패턴 회귀 가능성 유지. proposal §2.5 원칙 1(룰 순감소) 위반. 코드/문서 양쪽에 두 패턴이 공존하면 *형식 사다리 부활 입구* 가 됨. 기각.
  2. *Phase 2 까지 status JSON 잔존 + Phase 3 에서 일괄 폐기* — proposal 갱신본의 acceptance("형식 강제 0, flag 0, schema 0") 와 직접 충돌. 본 저장소 잔존 코드가 plugin 배포 시 사용자 프로젝트의 reactive 룰 추가 진입점이 될 수 있음. 기각.
  3. *(채택)* **state_io / schema 테스트 / validator @OUTPUT_SCHEMA 모두 동일 commit 에 폐기 + signal_io 로 교체** — proposal §5 Phase 1 단순화 정합. 형식 강제 0 일관성 유지. 폐기 LOC ~390 vs 신규 ~290(signal_io ~290 + 29 테스트 + 5 mode docs 변경) → 순감소.
- **Decision**:
  - 옵션 3. 단일 Task-ID(`DCN-CHG-20260429-13`) 로 폐기 + 신규 + 문서 갱신 일괄.
  - **proposal §2.5 원칙 1 정합**: 룰 순감소 — JSON schema required 키 / allowed_status set / 5 failure modes (`schema_violation` 포함) → prose 자유 + ambiguous 단일 reason 으로 압축.
  - **proposal §2.5 원칙 3 (자율성 최대화)**: agent 가 prose 자유 emit. 마지막 단락에 enum 단어 1개만 가이드 (형식 X, *의미* O).
  - **interpret_signal 휴리스틱 + DI swap point**: 본 저장소는 메타 LLM 호출 환경 외부 (claude CLI 의존 없음, Anthropic SDK 미설치) → 휴리스틱(`prose 의 마지막 2000자 영역에서 allowed enum 1개 word-boundary 매칭`) 을 기본 interpreter 로 제공. 프로덕션은 `interpret_signal(..., interpreter=anthropic_haiku_call)` 로 swap. 휴리스틱 자체도 도그푸딩 baseline 제공.
  - **path traversal 자기검증 + 화이트리스트 보존**: signal_io 도 `_AGENT_NAME_RE` / `_MODE_NAME_RE` / `_RUN_ID_RE` + `Path.relative_to(base)` 로 catastrophic-prevention 유지 (proposal §2.5 원칙 2 — 강제 vs 권고 분리: 보안은 catastrophic 강제).
  - **atomic write (POSIX `os.replace`) 보존**: race 회피는 catastrophic-prevention.
  - **MissingSignal reasons 압축**: not_found / empty / ambiguous 3종으로 충분. race / malformed_json / schema_violation 모두 폐기 (race 는 휴리스틱 인터프리터의 retry 정책 영역, malformed/schema 는 prose 에 의미 없음).
- **Follow-Up**:
  - **(다음 Task-ID)** Anthropic SDK 통합 — `interpret_signal` 의 메타 LLM interpreter 구현. cycle 당 비용 측정 (proposal R8 정합).
  - **(다음 Task-ID)** ambiguous 카탈로그 — `interpret_signal` 이 `MissingSignal(ambiguous)` raise 시 prose 를 `.metrics/ambiguous-prose.jsonl` 에 누적. proposal R1 acceptance.
  - **(다음 Task-ID)** prose hash checkpoint — `plan_loop.py` 류 도입 시 prose 파일 hash 안정성 측정 (proposal R7).
  - **(별도 Task-ID)** plugin 배포 dry-run — RWHarness 와 공존 시나리오 검증 (proposal §12.3.2). Phase 1 prose-only foundation 위에서.
  - **측정 항목**: 휴리스틱 interpreter 의 hit rate (단어 경계 매칭 성공률 vs ambiguous 빈도). 30일 사용 후 enum 매칭 누락 빈도 분석 → writing guide 정정 input (proposal R1 정합).

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

### DCN-CHG-20260429-04
- **Date**: 2026-04-29
- **Rationale**:
  - dcNess 의 정체성: `status-json-mutate-pattern.md` §11.1 — "RWHarness 코어 보존 + 본 proposal 정합 최소 레이어" + §12 — "신규 plugin 1차 완성 후 RWHarness 대체 테스트". 즉 dcNess 는 **Claude Code plugin** 으로 배포돼 RWHarness 와 공존 가능해야 한다.
  - `.claude-plugin/plugin.json` + `marketplace.json` 부재 시: plugin 매니저(`claude plugin install`) 가 dcNess 를 인식 못 함 → 도그푸딩 / 단계적 전환 / 롤백 시나리오(§12.3.2 ~ §12.3.5) 진입 불가.
  - 부수 문제: 본 manifest 변경이 governance §2.2 의 어떤 카테고리에도 매칭 안 됨 → record/rationale 동반 없이 통과되는 구멍. plugin 메타는 정책급 (잘못 배포 시 사용자 환경 파괴 catastrophic) → heavy 카테고리 매칭 강제 필요.
- **Alternatives**:
  1. *plugin manifest 만 추가, 게이트 룰 변경 없음* — 정책 변경에 record/rationale 동반 강제가 안 됨. CHG-02 와 동일 함정. 기각.
  2. *`hooks` 카테고리에 추가* — plugin manifest 는 hook 정의가 아니라 plugin 정체성. 의미 mismatch. 기각.
  3. *`ci` 카테고리에 추가* — build/deploy 메타로 보면 후보. 단 plugin manifest = "패키지 정체성 + agent/hook/skill 묶음" 로 정책 성격 강함. 기각.
  4. *(채택)* **`agent` 카테고리에 `^\.claude-plugin/` 추가** — agent prompt / 정책 / plugin 메타가 모두 정책급 정합. CLAUDE.md / AGENTS.md / agents/ 와 같은 line-up. heavy 카테고리(rationale 동반 강제) 자동 적용.
- **Decision**:
  - 옵션 4 채택. `governance.md` §2.2 agent 패턴 + `check_document_sync.mjs` CATEGORY_RULES 동시 갱신 (코드 = 명세 구현, CHG-02 룰 정합).
  - plugin 이름 = `dcness`, 마켓플레이스 이름 = `dcness` (소문자 통일). proposal §11.1 후보(`lightharness`, `microharness`, `rwh-lite`, `harness-v2`) 대신 저장소 이름 그대로 채택 — 사용자 결정 + 저장소-plugin 1:1 매핑 명시성.
  - **RWHarness 와 공존 가능 설계**: plugin 이름이 `realworld-harness` 와 다름 → `claude plugin install` 시 충돌 0. proposal §12.3.2 의 "공존 가능 검증" 시나리오 실현 가능.
  - **버전**: `0.1.0-alpha` — RWHarness 와 동일 alpha 대역. 첫 plugin 도입.
  - **hook/agent prefix**: 본 Task 에선 미정. 후속 Task (RWHarness `hooks/` / `agents/` 복사 시) 에서 `dcness-` prefix 또는 별도 디렉토리 결정. 현재는 manifest 만.
- **Follow-Up**:
  - **(다음 Task-ID)** `docs/migration-decisions.md` — proposal §11.2 framework 적용 (RWHarness 모듈 분류). plugin layout 결정 (hook/agent 어디 위치할지) 동시 박기.
  - **(다음 Task-ID)** `agents/validator*.md` 복사 + `@OUTPUT_FILE/SCHEMA/RULE` 변환. plugin manifest 의 hook/agent 매핑 추가.
  - **(별도 Task)** `claude plugin validate .claude-plugin/` 자동 실행 CI workflow — plugin manifest 형식 검증.
  - **측정**: plugin 설치/제거 1회 dry-run 후 RWHarness 와 충돌 0 검증 (proposal §12.3.2). 단 plugin 매니저 실측은 후속 — 현 Task 는 manifest 정의 단독.

### DCN-CHG-20260429-06
- **Date**: 2026-04-29
- **Rationale**:
  - `status-json-mutate-pattern.md` Phase 1 acceptance 의 핵심 항목: "agent/validator*.md 의 @OUTPUT_FILE / @OUTPUT_SCHEMA / @OUTPUT_RULE 형식 변환". 단 1번 모듈(state_io.py) 만 있어선 *agent 가 status JSON 을 어떤 schema 로 박을지* 명세 없음 — agent docs 형식 정의가 다음 단계.
  - RWHarness 의 `agents/validator*.md` 6개(마스터 + 5 모드)는 `---MARKER:X---` 텍스트 컨벤션 + `preamble.md` 자동 주입 + `agent-config/validator.md` 별 layer 의존 — proposal §2.5 원칙 1(룰 순감소) 위반 누적 구조.
  - 변환 *대상*: validator 단일 agent (Phase 1 sub 1.1 mechanism). 다른 12 agent 는 Phase 2.
- **Alternatives**:
  1. *RWHarness 파일 그대로 복사 + 마지막 줄만 status JSON 으로 교체* — preamble/agent-config 의존 잔존. 다음 변환 부담 누적. 기각.
  2. *마스터 1개만 변환하고 sub-doc 5개는 후속 Task* — 마스터의 @OUTPUT_FILE/SCHEMA 가 sub-doc 의 schema 와 정합 필요. 분리 시 일관성 위험. 기각.
  3. *(채택)* **마스터 + 5 sub-doc 동시 변환, preamble/agent-config 의존 제거**: validator agent 단위가 *원자 단위* — 마스터의 @OUTPUT 매트릭스 + sub-doc 의 모드별 schema 가 한 번에 정합. RWHarness 의 체크리스트 내용은 보존(검증 가치는 그대로), 출력 부분만 status JSON Write 로 교체.
- **Decision**:
  - 옵션 3 채택. 6개 파일 신규.
  - **schema 설계**: `status` (mode-specific enum) + `fail_items` (FAIL 시 필수) + `next_actions` (handoff, optional) + `non_obvious_patterns` (자율 영역, optional) + 모드별 추가 필드(spec_missing / save_path / metrics).
  - **proposal §2.5 원칙 3 (자율성 최대화) 정합**: required 키는 `status` + (FAIL 시) `fail_items` 만. 나머지 freeform — agent 가 자유롭게 채우거나 비우기 가능.
  - **mode-specific status enum**: `state_io.read_status` 의 `allowed_status` 매개변수와 정합. caller 측이 enum 강제. 기존 `MARKER_ALIASES` (PLAN_LGTM / OK / APPROVE 변형 흡수) 폴백은 *agent docs 가 정확한 enum 만 emit 강제* 로 대체.
  - **`tools` 변경**: `Read, Glob, Grep` → `Read, Glob, Grep, Write`. status JSON Write 만 허용 — 다른 path Write 는 향후 hook (agent-boundary ALLOW_MATRIX) 에서 차단 (proposal §4.2 R1 layer 2). 본 Task 에선 *agent docs 형식만* 정의, hook 강제는 후속.
  - **preamble.md 의존 제거**: 공통 규칙 (읽기 전용 / Bash 금지 / 단일 책임 / 증거 기반 / 추측 금지) 을 본 마스터 문서 안에 직접 박음. proposal §5 Phase 1.3 (점진 공개) 정합.
  - **agent-config 의존 제거**: 프로젝트별 컨텍스트는 호출 측 prompt 가 명시. 별 layer 폐기 (proposal §11.4 — agent-config DISCARD).
- **Follow-Up**:
  - **(다음 Task-ID)** `tests/test_validator_schemas.py` — 5 모드의 status JSON 예시가 `state_io.read_status(allowed_status={...})` 와 round-trip 통과하는지 검증. agent docs 의 schema 정합성 자동 검증.
  - **(별도 Task)** Phase 2 — 다른 12 agent docs (architect 7 모드, engineer, designer 4 모드, design-critic, qa, ux-architect, product-planner, plan-reviewer, pr-reviewer, security-reviewer, test-engineer) 변환. 본 Task 의 형식이 template.
  - **(별도 Task)** plugin 배포 시 hook 도입 — agent-boundary ALLOW_MATRIX 에 validator status path regex 추가. 현재 dcNess 자체엔 hook 미도입 (proposal §11.4).
  - **측정**: validator 호출 시 alias hit (옛 LGTM/OK/APPROVE) 0건. 실제 호출 데이터 누적 (`.claude/harness-state/.metrics/`) 후 측정.
- **Document-Exception**: agent 카테고리(heavy)지만 코드/CI 변경 없음 → PROGRESS 미해당. 거버넌스 §2.6 룰상 PROGRESS 는 harness/hooks/ci 만 강제이므로 본 변경엔 미적용. 단 후속 갱신 시 본 Task ID 도 명시.

### DCN-CHG-20260429-08
- **Date**: 2026-04-29
- **Rationale**:
  - 거버넌스 부트스트랩(`DCN-CHG-20260429-01`) 시 명시한 follow-up: "GitHub Actions workflow (`.github/workflows/document-sync.yml`) 추가는 별도 Task-ID". 본 Task 가 그 항목.
  - **Local 우회 가능성**: 현재 3중 강제(git pre-commit + Claude Code PreToolUse + AGENTS.md) 는 `git commit --no-verify` 또는 hook 미설치(`cp scripts/hooks/pre-commit .git/hooks/pre-commit` 미실행) 시 우회 가능. 사용자 실수 또는 외부 에이전트가 `--no-verify` 추가하면 거버넌스 자체가 무력.
  - **proposal §2.5 원칙 2 (강제 vs 권고 분리)** 정합: Document Sync 게이트는 *catastrophic* 가 아닌 *측정 가능 신호* — 단 거버넌스 시스템 자체의 무결성을 위해 *최후 차단* 만 강제.
  - **proposal R9 (GitHub 외부화 trade-off)** 인지: PR 후 CI 실패 = 분 단위 피드백 지연. 단 *local hook 이 정상 작동 시* 90%+ catch → CI 는 잔여 10% 만 차단.
- **Alternatives**:
  1. *현 상태 유지 (3중 local 강제만)* — `--no-verify` 우회 가능. 외부 에이전트(Codex 등) 로컬 hook 미설치 시 무방비. 기각.
  2. *모든 변경에 PR 리뷰어 수동 검사 강제* — 인적 오류, CHG-01 에서 이미 기각.
  3. *(채택)* **CI workflow 추가** — base..head diff 검사. local 통과한 PR 도 CI 가 재검 → 우회 차단.
- **Decision**:
  - 옵션 3 채택. `.github/workflows/document-sync.yml` 신규.
  - **trigger**: `pull_request` (base 검증) + `push: branches: [main]` (직접 push 또는 squash merge 후 main 재검).
  - **base..head diff**: PR 의 경우 `pull_request.base.sha` ↔ `pull_request.head.sha`. push to main 의 경우 `event.before` ↔ `sha`. 첫 push 등 base 부재 시 *비대상* 처리(no-op) — false fail 방지.
  - **fetch-depth: 0**: shallow clone 으론 base..head diff 불가. 본 게이트는 history 전체 필요.
  - **Node 20**: `scripts/check_document_sync.mjs` 의 ESM import 동작 검증된 메이저 버전.
  - **permissions: contents: read, pull-requests: read**: 최소 권한. 게이트는 *읽기만*, 차단은 exit code 로 표현.
  - **로컬 게이트와의 인터페이스 (R9 완화)**: 본 CI 는 *최후 차단* 이지 *유일 차단* 아님. local 게이트가 90% catch, CI 가 10% catch 이상적. 사용자 git pre-commit hook 정상 설치 가이드 (`CLAUDE.md` §4) 보존.
- **Follow-Up**:
  - **(별도 Task)** `.github/workflows/plugin-validate.yml` — `claude plugin validate .claude-plugin/` 자동 실행. plugin manifest 형식 회귀 차단.
  - **(별도 Task)** `.github/workflows/python-tests.yml` — `python3 -m unittest discover -s tests` 자동 실행. agent docs schema round-trip 회귀 차단.
  - **측정 (proposal §2.5 원칙 5 — 30일 데이터 후 결정)**:
    - 본 CI 가 차단한 위반 카탈로그 → governance §2.6 룰 정정 input
    - false positive 발생 시 게이트 룰 완화 / Document-Exception 사용 빈도
  - **branch protection 권장 (사용자 수동)**: GitHub Settings → Branches → main → "Require status checks to pass" → `document-sync` 추가. 본 PR 머지 후 사용자 액션. 본 Task 에선 워크플로우 자체만.

### DCN-CHG-20260429-09
- **Date**: 2026-04-29
- **Rationale**:
  - 현재 41 단위 테스트 (`tests/test_state_io.py` 32 + `tests/test_validator_schemas.py` 9) 가 로컬 실행만 가능 — PR 에서 회귀가 들어와도 CI 가 자동 실행 안 함.
  - **schema round-trip 회귀 위험**: `agents/validator/*.md` 의 status enum / required 필드가 변경되면 `state_io.read_status` 와 어긋날 수 있는데, 본 docs 변경 PR 에서 *테스트 자동 실행* 안 되면 머지 후 발견.
  - proposal §11.4 안전망: "매 sub-phase squash merge 후 smoke test 강제" — 본 워크플로우가 그 *자동화 버전*.
  - DCN-CHG-20260429-08 (document-sync workflow) 와 보완 관계: 그쪽은 *거버넌스 구조*, 본 Task 는 *코드/스키마 정합* 강제.
- **Alternatives**:
  1. *전 PR 에 unittest 무조건 실행* — docs-only PR 도 발동 → 불필요 CI 시간 + 큐 점유. 기각.
  2. *local pre-push hook 만 추가* — `--no-verify` 우회 가능. CHG-08 와 동일 함정. 기각.
  3. *(채택)* **paths 필터 + GitHub Actions** — `harness/` / `tests/` / `agents/` / 본 workflow 자체 변경 시만 발동. docs-only PR 면제. CI 우회 차단.
- **Decision**:
  - 옵션 3 채택. trigger paths 필터 명시.
  - **Python 3.11**: `unittest`, `pathlib`, `tempfile` 등 표준 라이브러리만 사용 — 의존성 install 단계 없음. 런타임 ~5초 예상.
  - **dev dependency 부재**: 현재 외부 패키지 미사용 (json/re/time/os/pathlib 모두 표준). `requirements.txt` 미도입. 도입 시점에 본 workflow 도 갱신.
  - **agents/ 도 trigger paths**: validator agent docs 변경 시 schema round-trip 테스트가 자동 실행 → docs 변경의 *acceptance 검증* 자동.
  - **permissions: contents: read** 단독: 테스트는 코드 *읽고 실행* 만 — 쓰기·외부 호출 없음.
- **Follow-Up**:
  - **(별도 Task)** `.github/workflows/plugin-validate.yml` — `claude plugin validate` 자동.
  - **(별도 Task)** branch protection 룰에 `python-tests / unittest discover` required 등록 (사용자 수동).
  - **측정**: 본 workflow 가 차단한 회귀 카탈로그 → 30일 후 운영 데이터로 false positive / 평균 실행 시간 / 회귀 발견율 분석.

### DCN-CHG-20260429-10
- **Date**: 2026-04-29
- **Rationale**:
  - DCN-CHG-20260429-04 에서 명시한 follow-up: "`claude plugin validate .claude-plugin/` 자동 실행 CI workflow — plugin manifest 형식 검증". 본 Task 가 그 항목.
  - **`claude plugin validate` 도입 위험**: claude CLI 자체가 GitHub Actions runner 에 설치/인증 필요. 토큰 secret 도입 + maintenance burden + CI 의존성 폭증. proposal §2.5 원칙 1 (룰 순감소) 위반.
  - **하지만 manifest 형식 자체 검증은 가치**: `plugin.json` 의 `name` 이 regex 위반 (예: 대문자 포함) 또는 `marketplace.json.plugins[0].name` 이 `plugin.json.name` 과 다른 경우 — plugin install 시점에 발견되면 사용자 환경 파괴. 형식 무결성은 *catastrophic-prevention* 성격 (proposal §2.5 원칙 2).
- **Alternatives**:
  1. *`claude plugin validate` 도입* — CLI 의존 폭증. 기각.
  2. *JSON Schema (ajv) 기반 엄밀 검증* — schema 정의 + ajv 의존 추가. 의존성 install 단계 발생. 첫 모듈 단위로 과함. 기각.
  3. *(채택)* **Node-only minimum guard** — 표준 라이브러리 (fs / path) 만. required 필드 + name regex + cross-reference 만 검증. ~70 LOC.
- **Decision**:
  - 옵션 3 채택. `scripts/check_plugin_manifest.mjs` (~70 LOC) + `.github/workflows/plugin-manifest.yml`.
  - **검증 항목**:
    - `plugin.json`: name (regex `^[a-z][a-z0-9-]*$`), version (string), description (string)
    - `marketplace.json`: plugins[] non-empty, plugins[0].name + source 존재
    - cross-reference: `plugin.json.name === marketplace.json.plugins[0].name`
  - **검증 외 (의도적 제외)**:
    - hook/agent 매핑 실재 — plugin install 시점에 매니저가 검증
    - 의미적 정합 (예: keywords 적합성) — manual review
  - **paths 필터**: `.claude-plugin/**` + `scripts/check_plugin_manifest.mjs` + 본 workflow. 다른 변경 시엔 발동 안 함.
- **Follow-Up**:
  - **(별도 Task — 위험 수용 시)** `claude plugin validate` 도입 검토 — 30일 데이터 + 결정 PR. 본 Task 가 *not yet* 결정.
  - **(별도 Task)** dcNess plugin 실 설치 dry-run — `claude plugin install /Users/dc.kim/project/dcNess/.claude-plugin` 후 hook/agent 매핑 정합 실측. proposal §12.3.2 검증.
  - **branch protection 권장**: `plugin-manifest / validate manifest` required 등록 (사용자 수동).

### DCN-CHG-20260429-12
- **Date**: 2026-04-29
- **Rationale**:
  - DCN-06 (validator agent docs 변환) + DCN-11 (README 보강) 으로 status JSON 패턴이 *내부 컨벤션* 으로 박혔음. 단 외부 에이전트(Codex 등) 가 본 저장소에 PR 작성 시 *기존 RWHarness 컨벤션* (`---MARKER:X---`, `MARKER_ALIASES` 변형) 으로 작성할 우려 — AGENTS.md 가 그 진입점인데 status JSON 패턴 언급 부재.
  - proposal §2.5 원칙 1 (룰 순감소) 정합으로 *재기술 금지* 지키며, AGENTS.md 는 짧은 *지침 + SSOT 링크* 만 박는다.
- **Alternatives**:
  1. *AGENTS.md 변경 없음* — 외부 에이전트가 폐기된 컨벤션 사용 위험. 기각.
  2. *AGENTS.md 에 schema 전체 박기* — `governance.md` SSOT 룰 위반(재기술). 기각.
  3. *(채택)* **5줄 짜리 안내 + SSOT 링크**: 결과 파일 경로 / schema 필수 / Write 도구 / 폐기된 컨벤션 명시 / 자세한 건 `agents/validator.md` + `docs/status-json-mutate-pattern.md` 참조.
- **Decision**:
  - 옵션 3 채택. AGENTS.md 에 "Status JSON Mutate 패턴" 섹션 한 단락 + 참조 5 링크.
  - **재기술 금지 정합**: 본 추가는 *어디 가서 보면 되는지* 만. 룰 자체는 SSOT(`agents/validator.md` + proposal) 가 정의.
- **Follow-Up**:
  - **(별도 Task)** Phase 2 다른 12 agent docs 변환 시 본 섹션의 "validator 등" 표현이 자연스럽게 일반화 (각 검증 에이전트마다 동일 패턴).
  - **(측정)** 외부 에이전트가 본 저장소에 보낸 PR 의 status JSON 사용 빈도. 30일 후 운영 데이터로 본 안내가 효과적인지 평가.
