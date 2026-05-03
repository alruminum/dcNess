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

### DCN-CHG-20260503-04
- **Date**: 2026-05-03
- **Rationale**: git-naming-spec 규칙이 문서로만 존재해 로컬에서 우회 가능. 브랜치명·PR 제목·커밋 제목 위반이 사람 눈에만 걸리면 늦게 발견됨. CI+hook으로 자동 차단해야 규칙이 실제로 작동.
- **Alternatives**:
  - PR 리뷰에서 수동 검수 — 리뷰어 부담, 일관성 보장 불가.
  - task-id-validation.yml 확장 — 관심사 혼합. 별도 파일로 분리가 명확.
- **Decision**: `scripts/check_git_naming.mjs` 신규 + CI workflow + commit-msg hook 3단 강제. 로컬(commit-msg)→CI(PR open) 두 단계로 조기 차단.
- **Follow-Up**: CLAUDE.md §4 hook 설치 명령어에 commit-msg 추가.

### DCN-CHG-20260503-03
- **Date**: 2026-05-03
- **Rationale**: (1) CLAUDE.md 문서 지도가 즉시읽기/lazy 구분 없이 나열되어 세션 시작 시 무엇을 읽어야 하는지 불명확. (2) §5 커밋 절차에 squash merge가 남아 있어 git-naming-spec(regular merge 강제)과 직접 충돌. (3) 브랜치 타입에 chore·feat 잔존으로 새 네이밍 규칙과 불일치.
- **Alternatives**:
  - 문서 지도에 주석만 추가 — 즉시읽기/lazy 의도가 모호하게 남음. 실제 행동 변화 없음.
- **Decision**: 문서 지도 테이블을 즉시읽기/lazy 두 섹션으로 분리. §5를 git-naming-spec 위임 + regular merge로 일원화.
- **Follow-Up**: PR 제목·브랜치명 포맷 CI/hook 강제 (DCN-CHG-20260503-04).

### DCN-CHG-20260503-02
- **Date**: 2026-05-03
- **Rationale**: dcNess 자체 작업이 epic 분류 없이 Task-ID만으로 관리되어 이슈 추적 구조 부재. git-naming-spec 도입으로 epic/story 기반 브랜치·이슈 규칙이 생겼으므로 dcNess 자신도 동일 구조 적용.
- **Alternatives**:
  - Task-ID 체계만 유지 — 브랜치/이슈 네이밍 규칙과 정합 안 됨. epic 없이는 Story 레이블도 붙일 수 없음.
- **Decision**: epic 3개(하네스/에이전트/인프라) + 마일스톤 v0.1.0 정의. 배포 시마다 마일스톤 버전 증가.
- **Follow-Up**: 앞으로 작업 생성 시 3 epic 중 하나에 귀속된 story 이슈 발행.

### DCN-CHG-20260502-05
- **Date**: 2026-05-02
- **Rationale**: jajang PR #179처럼 architect TECH_EPIC → DESIGN_VALIDATION → TASK_DECOMPOSE 전체가 commit 1개 + PR 1개에 묶이는 문제. 이슈/PR 간 관계 미정립, squash merge로 브랜치 히스토리 소실. (1) docs/tests/src 단계별 히스토리 보존 필요. (2) epic/story/bug 이슈 자동 연결 필요. (3) PR body에 Closes/Part of 자동화 필요.
- **Alternatives**:
  - (1) 단일 commit 유지 — 히스토리 소실 문제 미해결. impl 흔적 추적 불가.
  - (2) 수동 3-commit — 메인 Claude 가 잊으면 무의미. catastrophic gate 없이는 강제 불가.
  - (3) 이슈 레이블 수동 — agent마다 제각각. setup_labels.sh + agent 명문화로 통일.
- **Decision**: 3-commit(docs→tests→src) + record-stage-commit + catastrophic gate 3개(§2.3.6~§2.3.8) 채택. impl loop 계열(entry_point=impl)에만 적용 — quick/qa 등은 해당 없음. 이슈 레이블 체계: 정적(BugFix/UI/Docs) + 동적(V0N/EPIC0N/Story0N). epic-index.md로 EPIC↔이슈 번호 매핑 관리. squash merge → regular merge(3 commit 히스토리 보존).
- **Follow-Up**: (1) ISSUE_SYNC 모드 통합 검토 (product-planner ISSUE_SYNC와 epic-index.md 연동). (2) record-stage-commit 서브커맨드 단위 테스트 추가 (별도 Task-ID). (3) PR title/body 자동 생성 helper 구현 (별도 Task-ID).

### DCN-CHG-20260502-04
- **Date**: 2026-05-02
- **Rationale**: impl 구현 단위를 "batch"로 불렀으나 직관성이 낮음. 사용자가 보편적으로 쓰는 Jira-style Epic→Story→Task 계층과 불일치 — "batch 다 돌려", "per-batch" 등이 신규 기여자에게 낯설었음.
- **Alternatives**: (1) "unit" — 너무 추상적, 계층 관계 불명확. (2) "item" — 동일 문제. (3) "task" — `architect TASK_DECOMPOSE`가 이미 task라는 단어를 사용 + Epic→Story→**Task** 계층과 완벽 정합.
- **Decision**: "task" 채택. 루프명 `impl-batch-loop` → `impl-task-loop`. 행동 변경 없음 — 순수 용어 통일.
- **Follow-Up**: 과거 change_rationale_history.md / document_update_record.md / PROGRESS.md 의 히스토리 기록은 정확성 보존을 위해 변경하지 않음.

### DCN-CHG-20260502-03
- **Date**: 2026-05-02
- **Rationale**: DCN-01에서 BLOCKING 게이트를 넣었으나 inject 내 Read 경로가 상대 경로("docs/process/dcness-guidelines.md")였음. Read 도구는 절대 경로만 허용하므로 Claude가 Read를 시도해도 즉시 실패 → "파일이 없어 로드는 스킵됐습니다" 오류.
- **Alternatives**: (1) 파일 내용을 inject에 직접 포함 — 13KB, 10K cap 초과 위험. (2) 절대 경로 하드코딩 — 이식성 없음. (3) CLAUDE_PROJECT_DIR 환경변수로 동적 절대 경로 구성 — 실행 시점에 정확한 경로 확보.
- **Decision**: (3) 채택. `PROJ="${CLAUDE_PROJECT_DIR:-$(pwd)}"` → `GUIDELINES_PATH="${PROJ}/docs/process/dcness-guidelines.md"` → Python에 sys.argv[1]로 전달.
- **Follow-Up**: 다음 세션에서 Read 성공 + 토큰 출력 확인.

### DCN-CHG-20260502-02
- **Date**: 2026-05-02
- **Rationale**: 루프가 끝날 때 redo-log + WASTE/GOOD findings를 agent별로 누적하고 다음 루프에서 begin-step stdout으로 주입. sentinel/gate 없이 AI 신뢰 원칙 적용.
- **Alternatives considered**:
  - sentinel 게이트 (catastrophic-gate 확장) — "자연어끼리 비교라 의미 없음" 기각. 형식 검증은 메인이 문자열만 박고 내용은 생략 가능.
  - 단일 파일 누적 — agent별 파일 분리로 begin-step 에서 해당 agent 것만 추출 가능.
- **Decision**: 누적(finalize-run --accumulate) + begin-step stdout 주입 2군데만. 게이트 없음.
- **Follow-Up**: Layer 2 — agent definition 파일이 스스로 insights 읽는 방향 (별도 Task).

### DCN-CHG-20260502-01
- **Date**: 2026-05-02
- **Rationale**: 기존 inject("지금 즉시 read")가 단순 인사("안녕") 에 대해 무시됨. LLM이 "인사 → 짧은 응답" 패턴으로 즉시 분류, system-reminder를 "나중에 작업할 때 적용" 대상으로 후순위 처리. inject가 읽혔는지 검증할 방법도 없음.
- **Alternatives**: (1) 파일 전체 내용 inject — 13KB, 10K cap 초과. (2) "필수 read" 텍스트 강조 추가 — 현재 상태와 동일, 효과 없음 확인됨. (3) BLOCKING 3원칙 적용 — 출력 금지 조건 + 검증 토큰 + 예외 없음 명시.
- **Decision**: (3) 채택. "텍스트 출력 금지" 조건이 패턴 매칭을 차단. 검증 토큰("[dcness-guidelines 로드 완료 — §13 감시자 Hat 장착]")이 유저 감사 가능하게 함. "인사도 예외 없음" 명시가 "안녕" 케이스를 명시적으로 차단.
- **Follow-Up**: 다음 세션 첫 응답에서 토큰 출력 여부 확인. 미출력 시 추가 강화 (파일 일부 내용 직접 inject 검토).

### DCN-CHG-20260501-18
- **Date**: 2026-05-01
- **Rationale**: DCN-17에서 [lazy] 레이블 아래 파일 경로를 나열했더니 Claude가 레이블을 무시하고 경로를 보는 즉시 read. 경로 존재 자체가 read 트리거. dcness-guidelines.md §0의 마크다운 링크도 동일하게 트리거됨.
- **Alternatives**: (1) "지금 읽지 말 것" 강조 텍스트 추가 — 텍스트 지시로 행동을 막는 것은 불안정. (2) 파일 경로/링크 자체를 inject와 §0에서 제거 — 경로가 없으면 read 트리거 없음.
- **Decision**: (2) 채택. inject lazy 섹션에서 파일경로 완전 제거, §0 마크다운 링크를 비활성 텍스트로 교체. 경로는 skill 파일 `## 사전 read` 섹션에만 존재.
- **Follow-Up**: 다음 세션에서 session-start 시 loop-procedure 등 4개 doc read 여부 재확인.

### DCN-CHG-20260501-17
- **Date**: 2026-05-01
- **Rationale**: dcness 활성 프로젝트 세션 시작 시 5개 SSOT 문서(61KB, ~15K 토큰)가 즉시 read 강제됨. session-start inject 가 "5개 전부 즉시 read 의무"를 선언하고, dcness-guidelines.md §0이 loop-procedure + loop-catalog 추가 즉시 read 강제. 결과: skill 미호출 세션에서도 61KB 전부 컨텍스트 적재 → Messages 32.5k tokens의 주요 원인.
- **Alternatives**: (1) inject 제거 — 강제력 소실, 메인이 규칙 미인지 상태로 작업 시작. (2) 5개 doc 내용을 inject에 직접 포함 — additionalContext 10K cap 초과, 더 악화. (3) 문서 내용 압축 — doc 품질 하락, 실제 필요 정보 소실. (4) 현재 채택안: 1개(dcness-guidelines.md)만 즉시, 나머지 4개는 skill 파일의 `## 사전 read` 섹션으로 lazy.
- **Decision**: (4) 채택. dcness-guidelines.md는 항상 필요(행동 규칙 SSOT). loop-procedure/loop-catalog/orchestration/handoff-matrix는 루프 실행 시에만 필요 — skill 파일에 명시적 사전 read 지시 추가. 감시자 Hat(inject 15줄)은 dcness-guidelines.md §13으로 이전, inject에 1줄 포인터만.
- **Follow-Up**: skill 미호출 세션 ~13K 토큰 절감, skill 호출 세션 ~5-8K 토큰 절감. doc-sync gate 통과 확인. 실제 운영에서 "사전 read 누락" 패턴 발생 시 skill 파일 강화 검토.

### DCN-CHG-20260501-15
- **Date**: 2026-05-01
- **Rationale**: 메인 Claude 가 sub-agent 완료 후 prose 를 `Write/Bash heredoc` 으로 staging 하는 작업은 kabuki — PostToolUse hook stdin 에 `tool_response.text` 로 이미 prose 전체가 있는데 같은 바이트를 메인이 다시 disk 에 옮기는 구조. 매 step 마다 Write/Bash 1~2 회 + Write hook block 회피용 heredoc 사용이 반복.
- **Alternatives**: (1) `--prose-stdin` pipe — argparse 1줄 추가, 메인은 `echo "$PROSE" | end-step` 호출. 메인에서 prose string 처리 부담이 여전히 남음. (2) `--prose "$PROSE"` inline arg — arg escape 부담 있음. (3) PostToolUse hook 자동 staging + `--prose-file` optional — 메인 Write/Bash 0회, end-step 만 호출.
- **Decision**: (3) 채택. `handle_posttooluse_agent` 가 `tool_response.text` 추출 → `write_prose` → `live.json.current_step.prose_file` 기록. `_cli_end_step` 이 `args.prose_file=None` 시 `current_step.prose_file` 자동 읽기. `_count_step_occurrences` 에 `base_dir` 추가 (hook test 정합). legacy `--prose-file` 경로 보존.
- **Follow-Up**: 운영 skill 에서 `Write/Bash heredoc` 제거 가능 (별도 Task-ID). hook 실패 시 (disk 오류 등) end-step 이 `--prose-file 미제공 + hook staging 없음` 으로 rc=1 명시 → 메인에게 가시.

### DCN-CHG-20260501-14
- **Date**: 2026-05-01
- **Rationale**: `.prose-staging/` 파일명 컨벤션 불일치로 `_resolve_prose_path()` 패턴 매칭이 실제 파일명과 안 맞음 → 같은 (agent, mode) 반복 시 두번째 end-step이 outer prose를 덮어씌워 `run-review`가 첫번째 결과를 영구 분실.
- **Alternatives**: (1) `_resolve_prose_path()` 파일명 패턴 수정 — 컨벤션이 skill마다 달라서 유지보수 지속 필요, 근본 해결 아님. (2) `.steps.jsonl`에 `prose_file` 절대 경로 저장 — `end-step`이 쓴 경로를 그대로 기록하므로 패턴 매칭 불필요.
- **Decision**: (2) 채택. `signal_io.write_prose(occurrence=N)` — 같은 (agent, mode) N번째 호출 시 `<agent>[-mode]-N.md`로 충돌 방지. `_append_step_status()`가 `prose_file` 필드 추가. `parse_steps()`는 `prose_file` 직접 read, legacy fallback 보존. `_resolve_prose_path()` 삭제.
- **Follow-Up**: `.prose-staging/` 디렉토리는 skill 임시 수집용으로만 남음 (parse_steps가 직접 읽지 않음). 향후 `.prose-staging/` 생성 자체 제거 가능하나 현재 skill 변경 없이 방치해도 무해.

### DCN-CHG-20260501-13
- **Date**: 2026-05-01
- **Rationale**:
  - PR-2 (`-12`) 머지 후 jajang 운영 데이터 1 cycle: trace 178 호출 정상 캡처 ✅, 메인이 trace read + 정확한 sub 평가 ✅, 단 **redo-log 0 entry** ❌. 권고 어휘로는 메인 능동 retrieval 행동 강제 불가 (메인 자기 진단 — "능동 retrieval 의무 응답률 ~20%").
  - jajang 메인 자기 진단 (사용자가 인용) ROI 표:
    | 변경 | ROI | 메인 인지 비용 |
    |---|---|---|
    | `<usage>` 옆 tool-histogram | 🔥🔥🔥 | 0 (수동 인지) |
    | finalize-run 자동 redo_log | 🔥🔥 | 0 |
    | anomaly 조건부 reminder | 🔥🔥 | 낮음 |
    | blanket 룰 의무화 | 🟡 | 높음 (theater) |
  - 핵심 진단 — "**룰 추가 < surface 개선**". 메인이 *자연스럽게 보는 surface* 를 신호 풍부하게 만드는 게 룰 박는 것보다 압도적 효과. retrieval 의무는 *룰 강화로 안 풀림, push 로 바꿔야 풀림*.
  - PostToolUse hook 의 `hookSpecificOutput.additionalContext` 가 *tool result 옆에* system reminder 로 inject 됨 — 공식 docs 확정 ([code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks)). 즉 SessionStart 가 세션 시작 1회 inject 라면 PostToolUse Agent 는 매 sub 완료마다 inject — *정확히 우리가 원하는 push 채널*.
- **Alternatives**:
  1. **권고 어휘 강화 (의무 / 필수 escalation)** — 대원칙 §0 self-check 위반 가능 + theater 위험 (메인이 rote PASS 박기). *기각*.
  2. **블랭킷 매 sub reminder** — 정상 cycle 에서도 의미 없는 reminder 누적 → 신호 가치 dilution. *기각*.
  3. **`<usage>` 자체 수정 (tool histogram 박힘)** — Claude Code 플랫폼이 박는 메타라 우리가 직접 못 함. *기각*.
  4. **(채택)** **PostToolUse Agent hook 가 `additionalContext` 로 histogram + anomaly inject + redo_log 자동 append**.
- **Decision**:
  - `harness/sub_eval.py` 신규 — anomaly 룰 (tool_uses<2 / 같은 tool 5회+ / Write 약속+0건 prose-only). 보수적 임계 (`MIN_TOOL_USES=2`, `REPEAT_TOOL_THRESHOLD=5`). 운영 데이터 보고 조정.
  - `agent_trace.histogram(sid, rid, agent_id)` + `last_agent_id` helper — pre phase 만 카운트 (post 짝 중복 회피).
  - `handle_posttooluse_agent` 확장:
    - sub agent_id 식별 — payload `agent_id` 우선, fallback `last_agent_id(trace)`
    - histogram 계산 + anomaly 검출
    - **stdout JSON** — `{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "..."}}`
    - 정상: `[감시자 hook] sub=engineer tool histogram: Bash:2 Read:4 Write:1 (PASS)` (한 줄)
    - anomaly: `⚠️ anomaly 감지: ... + REDO 권고` (강조 다중 줄)
    - redo_log 자동 append (`auto:true` 마커)
  - 모든 실패 silent (`try/except Exception`) — hook 본 흐름 (active_agent clear) 방해 0.
  - **트레이드오프 §0 self-check**: histogram + anomaly 메시지 = *정보 inject* 으로 작업 순서 / 접근 영역 강제 X. 메인 자율 침해 0. 메인은 inject 메시지 보고 *자기 판단* 으로 REDO 결정 (강제 X). agent 자율 정합.
- **Follow-Up**:
  - **(P5 운영 1-2 주)** redo_log 자동 entry 100+ 누적 → anomaly false positive / negative 비율 측정 → 임계값 조정 PR.
  - **(측정)** 메인이 anomaly 메시지 받고 *실제 redo 결정 비율* — surface push 효과 정량.
  - **(P6 환류)** anomaly 패턴 검증된 것 → `agents/*.md` system prompt 에 사전 경고 박기.
  - **(P7 미래)** sub_prompt_hint 확장 — 한국어 키워드 ("작성", "생성") 외 더 정확한 약속 검출.
  - **(별도 PR)** `/audit-redo` skill 이 `auto:true` entry 와 메인 manual entry 구분 분석 — auto 만으로 패턴 추출 가능한지.

### DCN-CHG-20260501-12
- **Date**: 2026-05-01
- **Rationale**:
  - DCN-CHG-20260501-11 (PR-1) 가 인프라만 — `redo_log.py` + `agent_trace.py` + Pre/PostToolUse hook 확장. 단 메인이 *언제 어떻게* 활용할지 가이드 부재 → 인프라가 잠자게 됨.
  - 본 PR-2 가 비전 4축 중 (1) 결과 평가 + (4) 학습 진화 운영 layer.
  - **SessionStart 메시지 — 권고 어휘 사용**: 대원칙 §0 "harness 가 강제하는 건 작업 순서 + 접근 영역만, 그 외 agent 자율" 정합. "의무" / "필수" 같은 강제 어휘 자제, "권고" / "권장" / "X = 가장 비싼 실수" 같은 *명시 + 자율 판단* 어휘. 메인 자율 침해 0.
  - **`/audit-redo` skill 분리**: `/run-review` 와 직교. /run-review = waste/good findings (RWHarness 변환), /audit-redo = redo 패턴 학습. 같은 데이터 (.steps.jsonl + redo-log + trace) 다른 분석축. 단일 skill 통합 X (Karpathy 2 — 단일 책임 분리).
- **Alternatives**:
  1. **SessionStart 메시지 의무 어휘** — 대원칙 §0 위반. *기각*.
  2. **`/audit-redo` 를 `/run-review` 안에 통합** — 분석축 충돌, 사용자 발화 (사후 분석 vs 학습 환류) 다름. *기각*.
  3. **메인 매 sub spawn 시 자동 prompt 첨가 — 기능 박힘** — 메인이 *판단 없이 기계 첨가* 하면 자율 침해. 첨가 자체는 메인이 `/audit-redo` 결과 보고 결정. *기각*.
  4. **(채택)** **권고 메시지 + skill 분리 + Layer 1/2 명시** — 메인 자율 + cheap 실험 + 점진 환류.
- **Decision**:
  - SessionStart 메시지에 "감시자 Hat (DCN-CHG-20260501-12, 권고)" 섹션 추가. 권고 어휘만 사용. 본문 ~700 byte (CC additionalContext 10K cap 충분 여유).
  - `commands/audit-redo.md` 신규 skill — Step 0~5 절차. `/run-review` 와 동일한 "stdout 리포트 그대로 복사" 룰 (압축 본능 차단).
  - **Layer 1 / Layer 2 명시 분리**: 즉시 적용 (Layer 1) vs 인프라 환류 (Layer 2). 후자는 `agents/*.md` patch + governance §2.2 `agent` Change-Type 새 PR.
- **Follow-Up**:
  - **(P5 운영 — 1-2 주)** redo-log + trace 누적 → `/audit-redo` 첫 패턴 발견 → Layer 1 첨가 → 효과 측정.
  - **(P6 환류 — 주기)** Layer 1 적용 N 회 검증된 패턴 → Layer 2 patch PR (별도 Task-ID).
  - **(측정)** 메인이 SessionStart 권고를 실제 *따르는지* — redo-log entry 수 / cycle 수 비율. 0 이면 권고 효과 0 → 강제 어휘로 escalation 검토 (단 §0 정합 다시 self-check).
  - **(P7 미래)** `.output` 가공 helper — 본 skill 이 trace 만으로 분석한 redo 패턴이 부족하면 thinking 까지 cover.
  - **(P8 미래)** Auto-wakeup polling — 본 PR 운영 데이터에서 "결과 후 redo 만으론 헛수고 토큰 큰 손실" 측정 시.

### DCN-CHG-20260501-11
- **Date**: 2026-05-01
- **Rationale**:
  - 사용자 비전 (장 토론 산출물): "정적 룰 (path matrix / 도구 화이트리스트) 추가 게임은 끝 없다. 프로젝트 변형마다 화이트리스트 폭발". 룰 5개 cap + 추론 기반 judgment 로 패러다임 전환.
  - 비전 핵심 4축 (`/Users/dc.kim/.claude/plans/vast-singing-donut.md`): (1) 메인이 sub completion 결과 *깐깐히* 평가 + redo 권한 적극 행사, (2) sub 행동 hook 로 사후 추적, (3) audit log 누적, (4) 학습 진화 (Layer 1 즉시 prompt 첨가, Layer 2 dcness 인프라 환류).
  - **본 PR (PR-1)** 은 (2) 와 (3) 의 *코드 인프라* 만 — `redo_log.py` + `agent_trace.py` + hook 확장. (1) 과 (4) 는 PR-2 (DCN-CHG-20260501-12) 에서 SessionStart 메시지 + audit-redo skill.
  - **실시간 polling 폐기** — auto-wakeup 인프라 1일+ + 토큰 비용 30k/sub. 사용자 결정 — "결과 후 평가 + 학습" 으로 충분. 폴링은 P8 미래.
  - **`.output` 직접 read 폐기** — 시스템 명시 금지 (context 폭발). hook trace + completion notification `<result>` + `<usage>` 만으로 redo 결정 80%+ cover. thinking / 중간 message 추적은 P7 미래.
- **Alternatives**:
  1. **외부 supervisor sub-agent** — fresh context 매 호출 → 시계열 누적 판단 X. *기각*.
  2. **메인 self-review** — 같은 머리 + 같은 맥락 → cognitive lock-in 심화 위험. *기각*.
  3. **Hook 차단 → sensor 강등** — 현 catastrophic-gate / file-guard 매일 작동 중. 강등 = 안전 후퇴. *기각*.
  4. **agent-trace + redo-log 분리 vs 단일 파일** — 두 용도 schema 다름 (행동 stream vs 평가 결정). 분리 유지. *채택*.
  5. **(채택)** **PreToolUse 끝 + PostToolUse 신규** — boundary 통과 행동만 trace, 차단된 행동은 file-guard stderr 로 별도 기록. 단순함 우선 (Karpathy 2). 향후 *모든 시도* 기록 보강 가능.
- **Decision**:
  - `harness/redo_log.py` + `harness/agent_trace.py` 분리. 동일 패턴 (append/read_all/tail) 단일 함수 추출 보류 — 단일 사용처 추상화 회피 (Karpathy 2).
  - 기존 `handle_pretooluse_file_op` 끝 (return 0 직전) 에 trace pre append. 차단 시 (return 1 직전) 미기록.
  - 신규 `handle_posttooluse_file_op` + `hooks/post-file-op-trace.sh` wrapper + `hooks.json` PostToolUse `Edit|Write|Read|Bash` matcher 등록.
  - **트레이드오프 명시 (대원칙 §0 self-check)**: 본 변경은 *관측 인프라* — 작업 순서 / 접근 영역 강제 X. agent 자율 침해 0.
  - tool_input 핵심을 200 bytes 로 truncate (`_summarize_input`) — POSIX append atomic 4096 bytes 이내 보장.
  - trace append 모든 실패 silent (`_append_trace_safe`) — hook 본 흐름 (boundary 검사) 방해 X.
- **Follow-Up**:
  - **(PR-2 / DCN-CHG-20260501-12)** SessionStart 감시자 hat 메시지 + `commands/audit-redo.md` skill (Layer 1 즉시 첨가 + Layer 2 환류 patch 제안).
  - **(P5 운영)** 1-2 주 redo-log + trace 수집 → 패턴 추출 정확도 측정.
  - **(P6 환류 / 주기)** N 프로젝트 검증된 패턴 → `agents/*.md` system prompt 영구 patch → plugin release.
  - **(P7 미래)** `.output` JSONL 가공 helper — sub thinking + 중간 message 추적이 redo 결정에 *현저히 가치* 있다고 측정 시.
  - **(P8 미래)** Auto-wakeup polling skill — sub 헛수고 토큰 손실이 결정적이라 측정 시.
  - **(측정)** 1-2 주 후: sub spawn 평균 `tool_uses` / completion 평균 `duration_ms` / redo-log 카테고리 분포.

### DCN-CHG-20260501-10
- **Date**: 2026-05-01
- **Rationale**:
  - DCN-CHG-20260501-09 forward-only 한계 — `_append_step_status` 신규 negation-aware regex 가 *기록 시점* 만 적용. 이전 run 의 `.steps.jsonl` 은 stale must_fix 보유 → retro `/run-review` 시 MUST_FIX_GHOST 동일 false positive 잔재. 사용자 지적 — "회고 정확도".
  - 본질 — `.steps.jsonl` 의 must_fix 는 helper 시점 산출물 (snapshot). parser 는 prose 직접 보유 (이미 prose_full read). prose 가 진짜 source of truth → parser 측에서 재계산 가능.
- **Alternatives**:
  1. *옵션 A — parser parse_steps 재계산* (prose_full 있을 때 `_has_positive_must_fix`, 없으면 jsonl fallback). 5줄 + 테스트 2. **(채택)**.
  2. *옵션 B — 일회성 migration script* (모든 `.steps.jsonl` walk + 재계산 + atomic rewrite). 큰 blast radius. version data. 단발 효용 < 옵션 A.
  3. *옵션 C — 현 상태 유지 (forward-only)*. 신규 run 은 깨끗하지만 retro 폴루션. 사용자 명시 거부.
- **Decision**:
  - 옵션 A 채택. `harness/run_review.py` 에 `_has_positive_must_fix` import (session_state) + `parse_steps()` 안 prose_full 보유 시 재계산.
  - **Source 분리 자각** — `finalize-run` (session_state) 은 여전히 jsonl `must_fix` 사용. 단 finalize-run 은 *run 중* 호출 (실시간 fresh, DCN-CHG-20260501-09 신규 regex 적용) → 신규 run 은 정확. retro 분석은 parser 만 → 두 측 의도적 분리.
  - **자장 run-ef6c2c00 retro 검증** — `parse_steps` + `detect_wastes` → MUST_FIX_GHOST 6 → 0 직접 확인.
  - **신규 2 테스트** — recompute (legacy stale → False 정정) + fallback (prose 부재 → jsonl 신뢰).
- **Follow-Up**:
  - 옵션 B (jsonl migration) 도입 검토 — 사용자 다른 retro analysis 도구가 jsonl 직접 읽으면 source 분리 혼란. 본 task 범위 외, 후속 측정.

### DCN-CHG-20260501-09
- **Date**: 2026-05-01
- **Rationale**:
  - 자장 run-ef6c2c00 사용자 보고 — 40 step run / 28 waste finding 중 다수 false positive 의심. 사용자 직접 분류 ("MUST FIX 0 negation 미파악 / staging anchor 누락" 등) 후 메인 직접 검증 요청.
  - 직접 실측 (`/Users/dc.kim/project/jajang/.../run-ef6c2c00/.prose-staging/*` + `_MUST_FIX_RE` 코드) 결과 4 이슈 동시 확인:
    - **MISSING_SELF_VERIFY 9건 = 100% false positive (결정적 parser bug)**. skill 은 DCN-30-21 부터 `.prose-staging/<bN>.<agent>-<mode>.md` 에 prose 작성, 그러나 `run_review.py:223` 는 legacy `<run_dir>/<agent>-<mode>.md` 만 읽음. 9 engineer step 모두 같은 1 파일 매칭 → 마지막 batch 의 anchor 부재 시 9건 발화. 실측 — staging `b1/b2/b3.engineer-IMPL.md` 모두 `## 자가 검증` 박혀있음.
    - **MUST_FIX_GHOST 6건 = 100% false positive (regex bug)**. pr-reviewer 6건 모두 prose 안 "MUST FIX 0, NICE TO HAVE 6" 부정문. `_MUST_FIX_RE = r"\bMUST[\s_-]?FIX\b"` 단순 단어경계 → 부정문 매칭.
    - **THINKING_LOOP 4건 = 진짜 (engineer banner 부재)**. agents/engineer.md grep — `extended thinking` / `드래프트 금지` / `CRITICAL` 0 hit. DCN-CHG-20260430-39 가 architect sub-mode 7 + product-planner 에만 banner 박음. engineer 누락.
    - **prose_excerpt cap mismatch = MEDIUM 룰 정합**. `_append_step_status(max_lines=4)` vs ECHO_VIOLATION 메시지 "5~12 룰 의무". cap 4 일 때 사실상 ECHO `< 3` 임계 의미 불명확.
- **Alternatives**:
  1. *옵션 A — #1 (path) 만 fix*. 가장 큰 노이즈 (9건) 즉시 제거. 6건 + 4건 잔여. 기각 — 사용자 "한방에" PICK.
  2. *옵션 B — parser 측 substance 검사 강화 (anchor 자율, 실측 명령 패턴 검사)*. anchor 불필요. 단 substance regex 정의 어려움 (jest/pytest/grep/wc 등 도구 자율) + DCN-CHG-20260430-38 정신 (anchor 자율) 이미 정합. path bug 가 진짜 원인이라 fix 만으로 충분.
  3. **(채택) 옵션 C — 4 이슈 동시 fix (#1+#2+#3+#4)**. 사용자 PICK. 단일 PR 묶음.
- **Decision**:
  - **#1 prose_path bug fix** (`harness/run_review.py:_resolve_prose_path`):
    - `<run_dir>/.prose-staging/` lexical 정렬 → 같은 (agent, mode) Nth occurrence 매칭 (`b1.* < b2.* < ... < bare suffix`).
    - `parse_steps` 가 occurrence_counter dict 로 step idx 별 N번째 picking.
    - fallback = legacy `<run_dir>/<agent>-<mode>.md` (DCN-30-21 이전 데이터 호환).
  - **#2 MUST_FIX_GHOST regex** (`harness/session_state.py`):
    - `_MUST_FIX_NEGATION_RE` 신규 — `MUST FIX` + `0` (단일 자릿수) / `없[음다]` / `no MUST FIX` 검출.
    - `_has_positive_must_fix()` 신규 — 라인 단위 매칭. 매칭 라인 중 *부정 컨텍스트 아닌* 라인 1+ → True. 모두 부정 → False. mixed (positive 라인 + 부정 라인) → True (positive 우선).
    - `_append_step_status` 의 `bool(_MUST_FIX_RE.search(prose))` → `_has_positive_must_fix(prose)`.
  - **#3 engineer banner** (`agents/engineer.md`):
    - H1 직후 architect sub-mode 패턴 동일 1 블록 — 자장 4 stall 실측 (614/1102/429/670s) 명시.
  - **#4 cap mismatch** (`harness/session_state.py`):
    - `_append_step_status` 의 `_extract_prose_summary(prose, max_lines=4)` → `max_lines=12` (5~12 룰 정합). ECHO 임계 `< 3` 유지 (실 2-liner 케이스 검출).
  - **신규 7 테스트** — `ResolveProsePathTests` (5) + `test_must_fix_negation_no_false_positive` + `test_must_fix_positive_still_detected`. 281 → 288 ran / all PASS.
  - **자장 run-ef6c2c00 회귀 직접 검증** — `parse_steps` 후 9 engineer step 중 b1~b3 (= idx 2/7/12) anchor=True 회복 확인. b4~b8 (idx 17/22/27/29/34/37) 은 staging 자체 anchor 부재 → 진짜 위반 6건 (메인 행동 룰).
- **Follow-Up**:
  - 진짜 6 MISSING_SELF_VERIFY (b4-b8 staging anchor 부재) 는 메인 행동. dcness-guidelines.md §자가 검증 룰 강도 ↑ 또는 staging template 도입 후속 별 task.
  - TOOL_USE_OVERFLOW 1건 (batch 06 112 tools) — agent self-discipline. hint 강도 ↑ 또는 IMPL_PARTIAL 임계 자동 trigger 후속.
  - ECHO_VIOLATION 8 케이스 (실 2-liner) — 메인 가시성 룰 행동 변화. cap 12 정합 후 룰 인식 재교육 후속.
  - 다른 patterns (PLACEHOLDER_LEAK / INFRA_READ / READONLY_BASH / EXTERNAL_VERIFIED_*) — 본 path fix 로 정확도 자동 회복. 별 검증 후속.

### DCN-CHG-20260501-08
- **Date**: 2026-05-01
- **Rationale**:
  - 사용자 — SessionStart 훅이 plugin cache 안 SSOT 문서 (`docs/process/dcness-guidelines.md` 등) 를 inject 해도 메인 Claude 가 `Read(~/.claude/plugins/cache/dcness/**)` 권한 부재로 read 못함. inject 한 system-reminder 안 cross-ref 따라가기 0.
  - 권한 시스템 본질 — `acceptEdits` defaultMode 라도 plugin cache 디렉토리는 user-managed 영역 (CC 가 자동 관리) 으로 read deny 디폴트. 사용자가 명시 allow 등록해야 read 가능.
  - `/init-dcness` 가 활성화 부트스트랩의 진입점 → 권한 grant 도 같은 절차 안에 묶는 게 자연스러움. 사용자 직접 요청.
- **Alternatives**:
  1. *옵션 A — Step 2.5 inline jq*. 단순. 의존 = jq. CC 환경 표준. **(채택)**.
  2. *옵션 B — `dcness-helper grant-perm` 신규 subcommand*. python 으로 settings.json merge. 멱등 안전. 재사용 가능. 단 본 use case 만 → over-engineering.
  3. *옵션 C — settings 직접 편집 안내만*. 사용자 매뉴얼 step. 활성화 자동화 의도 위반. 기각.
- **Decision**:
  - 옵션 A 채택. jq merge 3 케이스 (이미 존재 / 빈 allow / permissions key 자체 부재) 직접 검증 PASS.
  - settings 부재 시 신규 생성 (`mkdir -p` + 빈 JSON). jq 미설치 fallback = WARN + 수동 안내.
  - 재설치 시 settings 보존 (`~/.claude/plugins/data/dcness-dcness/` 만 정리됨) — 멱등 재실행 안내 추가.
- **Follow-Up**:
  - 본 권한이 필요한 다른 plugin path 발견 시 같은 step 에 추가 (예: data/ read 가 필요해지면).
  - `/disable-dcness` skill 도입 시 권한 제거 step 동반 검토 — 단 다른 dcness 활성 프로젝트 영향 받지 않게 careful (전역 권한이라 사용자 수동 관리 권장).

### DCN-CHG-20260501-07
- **Date**: 2026-05-01
- **Rationale**:
  - 직전 task (`-06`) 로 branch protection 폐기 → CI 4 checks 중 `unittest discover` 표시 레벨로 떨어짐. 사용자 — 회귀 잦았던 만큼 (DCN-30-37 ~ -40) doc-sync 동급 mechanical 차단 원함.
  - 사용자 직접 선택 — "pytest 도 강제 못해?" → 옵션 B (paths 분기) PICK.
  - 도입 비용 측정 — 현재 unittest 약 3초. 매 commit 강제 시 비용 누적이지만 paths 분기로 비매칭 commit 0초.
- **Alternatives**:
  1. *옵션 A — 무조건 실행*. 단순. docs-only commit 도 3초. 비매칭 비용 누적. 기각 (사용자 PICK X).
  2. **(채택) 옵션 B — paths 분기 (`harness/` / `tests/` / `agents/` / `python-tests.yml`)**. 사용자 PICK. CI workflow paths 필터와 동일 의도 — 변경 영역만 실행.
  3. *옵션 C — branch protection 재활성*. doc-sync 정도 의도 위반. 직전 task 정합 깨짐. 기각.
- **Decision**:
  - **`scripts/check_python_tests.sh`** 신규 — paths 분기 + `GITHUB_ACTIONS` skip (workflow 가 별도 실행) + 실패 시 exit 1 + 우회 안내 (`--no-verify`, 룰 위반 명시).
  - **`scripts/hooks/pre-commit`** — chain 화 (`set -e` + node doc-sync + sh pytest). 기존 단일 exec 패턴 유지.
  - **`scripts/hooks/cc-pre-commit.sh`** — `git commit` case 안 doc-sync 통과 후 pytest 게이트 추가. 실패 시 exit 2 (PreToolUse 차단).
  - **`docs/process/governance.md` §2.7** — 강제 메커니즘 표 신설 (게이트 / 스크립트 / 적용 범위 / 우회). 참조 파일 표에 신규 스크립트 추가.
  - **`CLAUDE.md`** — §1 commit 직전 단계 + 문서 지도 표 갱신 (2 게이트 명시).
- **Follow-Up**:
  - 신규 hook 효력 측정 — 첫 회귀 시 `--no-verify` 사용 여부 자기 모니터링 (1인 운영 자기 룰 위반 패턴 추적).
  - tests 수 ↑ 또는 elapsed > 10초 도달 시 paths 추가 분기 / parallel 도입 검토.
  - AGENTS.md (외부 에이전트 지침) 에 pytest 게이트 룰 명시 후속.

### DCN-CHG-20260501-06
- **Date**: 2026-05-01
- **Rationale**:
  - DCN-CHG-20260501-04 (branch protection 도입) 가 사용자 의도 과해석. 사용자 원본 명령은 "pytest CI 적용" — doc-sync 정도의 제어 의도였음. 이전 세션 메인이 "CI 강제해서 실패 못하게" 로 확장 + branch protection ON + paths 필터 폐기 동반 결정.
  - 사용자 직접 지적 — "거버넌스 ci 는 document-sync gate 잘 강제하는거 같은데?". doc-sync 는 §2.7 3중 hook (git pre-commit + Claude Code PreToolUse + AGENTS.md) 으로 commit 시점 차단 → CI 의 역할은 표시. 나머지 게이트도 동일 패턴이면 충분.
  - paths 필터 폐기 부작용 — docs-only PR 도 python-tests / plugin-manifest 매번 실행 (불필요 비용). protection 폐기 시 자연 해소.
- **Alternatives**:
  1. *옵션 A — 현 상태 유지 (protection ON + paths 필터 OFF)*. 사용자 의도 이탈 + paths 비용. 기각.
  2. *옵션 B — protection OFF + paths 필터 복구 + 로컬 hook 으로 python-tests / Task-ID 도 doc-sync 처럼 commit 차단*. 1인 운영 + `--no-verify` 우회 가능 → mechanical 효력 약함. 사용자 의도 ("doc-sync 정도") 초과. 기각.
  3. **(채택) 옵션 C — protection OFF + paths 필터 복구. 추가 hook 없음**. 사용자 의도 정합 (doc-sync 만 강제). CI 표시 레벨 유지 — fail 시 PR 페이지 빨갛게 보임 + 사용자 자율 판단.
- **Decision**:
  - 옵션 C 채택.
  - **branch protection live 폐기** — `gh api -X DELETE repos/alruminum/dcNess/branches/main/protection` 200. `gh api ... branches/main/protection` 재호출 → 404 "Branch not protected" 확인.
  - **workflow paths 필터 복구** — `python-tests.yml` (`harness/**` / `tests/**` / `agents/**` / 본 yml), `plugin-manifest.yml` (`.claude-plugin/**` / `scripts/check_plugin_manifest.mjs` / 본 yml).
  - **governance.md §2.8** — "Branch Protection (CI 게이트 강제)" → "Branch Protection (현재 비활성)" 으로 재작성. 비활성 사유 / 도입 옵션 / 머지 룰 / 근거 명시. `gh pr merge --squash --auto` 의무 룰 폐기 (protection 없으면 작동 X).
  - **branch-protection-setup.md / setup_branch_protection.mjs** — header 에 ⚠️ OFF 상태 명시. 스크립트 자체는 보존 (재활성용).
- **Follow-Up**:
  - python-tests / plugin-manifest CI fail 시 사용자 시각 의존 — 회귀 잦으면 로컬 hook 도입 재검토.
  - DCN-30-37 ~ DCN-30-40 회귀 패턴 (CI 결과 안 보고 즉시 머지) 은 메인 행동 룰로 흡수 — `/run-review` `CI_NOT_VERIFIED` 패턴 도입 후속 별 task.
  - main-claude-rules.md / CLAUDE.md 의 `--auto` flag 의무 룰 (있다면) 함께 폐기 검토 — 본 task 범위 외, 후속.

### DCN-CHG-20260501-05
- **Date**: 2026-05-01
- **Rationale**:
  - 사용자 관찰 — impl 단독 open / grep 시 어느 Story / 이슈인지 H1 만으로 파악 안 됨. frontmatter 메타는 ToC 안 보임. 8 batch ↑ epic 시 검색 비용 ↑.
  - 별개 관찰 — impl batch PR 에서 src/* 만 commit + impl/NN-*.md 누락 케이스 발생 → spec ↔ 코드 단절. revert 시 sync 깨짐.
  - 두 룰 모두 "agent self-discipline" 영역 — 메인이 매번 룰 인용 부담. agent prompt SSOT 박음으로 자율 적용.
- **Alternatives**:
  1. *옵션 A — `docs/process/dcness-guidelines.md` 에 박음*. 단 agent 가 매번 guidelines 통해 강제 인지하지 못함 (해당 prompt 안 직접 룰이 더 효과).
  2. *옵션 B — agent prompt 에 사용자 원본 텍스트 그대로 복붙*. 기존 "각 impl 파일 형식 의무" / "커밋 단위 규칙" 과 부분 중복 → 토큰 낭비 + 룰 충돌 위험.
  3. **(채택) 옵션 C — agent prompt 에 미커버 영역만 추가**. task-decompose 의 기존 섹션 = 내용 (생성/수정 파일 / 인터페이스 / 의사코드 등) 만 다룸 → 제목 룰 추가. engineer 의 기존 "커밋 단위 규칙" = 1 커밋 = 1 논리 변경 / branch 룰만 다룸 → "1 batch = 1 PR 셋트" 하위 섹션 추가.
- **Decision**:
  - **task-decompose.md** — `## impl 파일 명명 + H1 제목` 섹션 신규. 파일명 + H1 정규식 + 자가 검증. 기존 `## 각 impl 파일 형식 의무 (DCN-30-13)` *직전* 배치 — 명명 → 형식 자연 순서.
  - **engineer.md** — 기존 `## 커밋 단위 규칙` 안 `### 1 batch = 1 PR` 하위 섹션. 필수 stage 3 항목 + batch 01 한정 추가 + `git diff --cached --name-only` 자가 검증 + 안티패턴 3.
  - 사용자 원안 보존 (의도 유지) + 표 → bullet 슬림화 + Why 1줄 압축.
- **Follow-Up**:
  - 자장 plugin reinstall 후 첫 epic TASK_DECOMPOSE 시 H1 위반 검출 여부 측정. 미발화 시 prompt 가시성 ↑ 강화.
  - engineer commit 시 stories.md 누락 검출 → run-review 패턴화 (후속).

### DCN-CHG-20260501-04
- **Date**: 2026-05-01
- **Rationale**:
  - DCN-30-37 ~ DCN-30-40 7+ PR 동안 GitHub Python tests CI fail 누적 — 매번 `gh pr merge --squash` 즉시 머지 (CI 결과 wait X). 사용자가 알아챈 후에야 발견.
  - 실측 — PR #84 머지 시각 15:28:21 / CI 완료 15:28:32~39 → **11~18초 일찍 머지**. 단순 우연으로 나중 success.
  - `branch protection` 미설정 (404 "Branch not protected") + `gh pr merge` 가 wait 안 함 = CI fail 코드도 머지 가능 = 거버넌스 부재.
  - 사용자 명령 ("CI 로 강제해서 앞으로는 실패 못하게") — branch protection 적용 + `--auto` flag 의무.
- **Alternatives**:
  1. *옵션 A — 그대로 유지 (review 1 approve)*. 1인 운영 self-approve 불가 (GitHub 정책) → 매 PR 머지 자체 불가. 기각.
  2. *옵션 B — review 0 + CI 4 강제 (채택)*. 사용자 명령 정확 정합. CI 가 실질 게이트.
  3. *옵션 C — review 1 + admin enforce_admins=false 우회*. 매 PR 우회 = 거버넌스 약화. 기각.
- **Decision**:
  - 옵션 B 채택.
  - **`scripts/setup_branch_protection.mjs`** 수정 — `required_pull_request_reviews: null`. governance §2.8 표 갱신.
  - **branch protection live 적용** — gh API PUT repos/alruminum/dcNess/branches/main/protection. 4 status checks 강제 (Document Sync gate / unittest discover / validate manifest / Task-ID format gate) + strict + linear history.
  - **`gh pr merge --squash --auto` 의무 룰 추가** (governance §2.8) — CI 통과 후 자동 머지. 11~18초 일찍 머지 회귀 차단.
  - **workflow paths 필터 폐기** (`python-tests.yml` / `plugin-manifest.yml`) — branch protection required check 가 paths 미스매치로 발화 안 하면 PR BLOCKED 영원 (본 PR 자체에서 발견 — scripts/+docs/ 만 변경 시 python-tests 발화 X). CI 비용 < 안전성. 본 repo small.
  - Document-Exception: amend 로 commit message Task-ID 형식 정정 (`DCN-30-04` → `DCN-CHG-20260501-04`). 파일 변경 0, message 정정만.
- **Follow-Up**:
  - **본 PR 부터 적용 검증** — `--auto` flag 사용 + CI 4 checks 통과 후 자동 머지 실측.
  - **CLAUDE.md 커밋 절차 / main-claude-rules.md §2.3** 갱신 후속 — `gh pr merge --squash --auto` flag 의무 명시.
  - **회귀 안전망** — `/run-review` 에 `CI_NOT_VERIFIED` 패턴 추가 후속 (PR merge 시각 vs CI 완료 시각 비교 휴리스틱).

### DCN-CHG-20260501-02
- **Date**: 2026-05-01
- **Rationale**:
  - DCN-30-40 발견 — SessionStart inject 처음부터 작동 0회. 후속 PR 5+개 모두 inject 작동 가정 위에 진행 → 가정 거짓 입증. 자기 룰 위반 회귀 패턴 (글로벌 제1룰 + dcness §12 우리가 박은 룰).
  - 원인: inject 깨져도 룰 인지 보장하는 *backup 메커니즘 부재*. CLAUDE.md = 거버넌스 절차 문서, 행동 룰 (대원칙 / 가정 금지 / Karpathy / 인프라 메타) 은 SSOT 분산 (orchestration §0 / dcness-guidelines / agents/*).
  - 사용자 요청 — CLAUDE.md 와 동일 레벨 강제 read 단일 문서. 3 항목 + 대원칙: (0) 강제 = 작업 순서 + 접근 영역, (1) 실존 검증 강제, (2) dcness-guide 인프라 메타, (3) Karpathy 4 원칙 전문.
- **Alternatives**:
  1. *옵션 A — SessionStart inject 만 의존*. DCN-30-40 회귀 입증. 기각.
  2. *옵션 B — CLAUDE.md 본체에 룰 직접 추가*. 거버넌스 절차 ↔ 행동 룰 책임 혼재 + 300줄 cap 위반 위험. 기각.
  3. **(채택) 옵션 C — `docs/process/main-claude-rules.md` 신설 + CLAUDE.md reference**. CC 가 CLAUDE.md 자동 로드 → 본 문서 read 자연 유도. 책임 분리 + cap 충족 (226줄).
- **Decision**:
  - 옵션 C 채택. 4 섹션:
    - **§0 대원칙** — `orchestration.md` §0 / `status-json-mutate-pattern.md` §2.5 직접 인용. 새 룰 도입 시 self-check + 룰 위반 사례 (DCN-30-34 형식 강제) 명시.
    - **§1 실존 검증 강제** — 글로벌 제1룰 + dcness §12 통합. 안티패턴 7건 실측 사례.
    - **§2 dcness 인프라** — 300줄 cap / 5 SSOT 표 / 거버넌스 / 핵심 강제 룰 4 / sub-agent path 보호.
    - **§3 Karpathy 4 원칙 전문** — `forrestchang/andrej-karpathy-skills` (MIT) 인용. agent 별 적용 매핑.
  - **CLAUDE.md 상단 🔴 reference 박스** — "본 프로젝트 작업 *직전* read 의무". 문서 지도 표 첫 행 추가.
- **Follow-Up**:
  - **DCN-CHG-20260501-03 후속** — `tests/test_session_state.py:CleanupStaleRunsTests` time-bomb fix. fixture hardcoded ts 가 시간 흐름 + 24h TTL 으로 stale 판정. CI 7+ 회 fail 누적 (DCN-30-40 작업 중 사용자 GitHub CI 보고로 발견).
  - **dcness-guidelines.md §12 안티패턴 1줄 추가** — "자기 박은 mechanical 메커니즘도 *실 작동 검증 후* 후속 PR 진행" (DCN-30-40 회고 룰화).
  - **자장 plugin reinstall + 새 epic 검증** — inject + 본 문서 reference 양측 동시 작동 확인.

### DCN-CHG-20260501-01
- **Date**: 2026-05-01
- **Rationale**:
  - DCN-30-39 5번 follow-up — `DCNESS_INFRA_PATTERNS` 가 `handoff-matrix.md §4.4` spec 으로만 박힘, 코드 enforcement 0. `hooks/catastrophic-gate.sh` 가 차단하는 건 PreToolUse Agent 만 — sub-agent 내부 Edit/Write/Bash 는 자유.
  - 사용자 진단 (자장 plugin 활성 환경): "엔지니어가 아무 문서나 수정할수 있다는거지? 어쩐지 시발 경고 한번 안뜨더라" — 실측 갭 확인.
  - 첫 원칙 정합 — "강제 = (1) 작업 순서 + (2) 접근 영역". 접근 영역은 dcness 가 코드로 미강제 → 첫 원칙 일부 미이행 (자율 침해 X — 자율 영역 = 출력 형식 / handoff 페이로드 등과 직교).
  - 검증 (claude-code-guide + RWHarness 실 구현 확인): PreToolUse 훅이 sub-agent 내부 tool 호출에도 fire. 부모 CC session_id 가 PreToolUse stdin 에 그대로 — 메인 vs sub-agent 식별 가능 (live.json 공유 상태 lookup).
- **Alternatives**:
  1. *옵션 A — payload `agent_id` 직접 필드*. 사용자 초안. 단 RWHarness 실 구현은 live.json 공유 상태 — `agent-gate.py` 가 `live.json.agent` 기록, `agent-boundary.py` 가 PreToolUse Edit 에서 stdin session_id → live.json 조회로 활성 agent 판정. 더 견고 (Claude Code agent_id payload 호환성 의존 X).
  2. *옵션 B — Bash 정밀 path 추출 (shlex 등)*. 복잡. v1 = 보수적 heuristic (write indicator + path 토큰 휴리스틱). false positive 회피 우선.
  3. *옵션 C — agent prompt 안 룰 강화만 (agent-side 자율)*. 자장 5 incident 중 일부는 agent self-monitor 부재 — 자율 의존 시 회귀 (DCN-30-20 jajang 6분 stall 정합).
  4. **(채택) 옵션 D — RWHarness 패턴 그대로 차용**. live.json.active_agent 기록/해제 + agent_boundary.py 분리 + Edit/Write/Read/Bash matcher 4개. 검증된 구현 (RWHarness `~/.claude/plugins/cache/realworld-harness/0.1.0-alpha/hooks/agent-boundary.py`).
- **Decision**:
  - **(1) `harness/agent_boundary.py` 신규** — 9 INFRA pattern + 12 agent ALLOW_MATRIX + 4 agent READ_DENY + `is_infra_project()` 4 OR 신호 + `.no-dcness-guard` opt-out + Bash heuristic.
  - **(2) `harness/hooks.py` 핸들러 3개**:
    - `handle_pretooluse_agent` 끝에 `update_live(active_agent=subagent, active_mode=mode)` — sub-agent 식별 등록.
    - `handle_pretooluse_file_op()` — Edit/Write/NotebookEdit/Read/Bash 검사. Bash 는 write indicator (sed -i / cp / mv / rm / >) 있을 때만 path 추출.
    - `handle_posttooluse_agent()` — `update_live(active_agent=None, active_mode=None)` 으로 clear.
  - **(3) `hooks/file-guard.sh` + `hooks/post-agent-clear.sh`** — bash wrapper. is-active 게이트로 미활성 프로젝트 즉시 통과.
  - **(4) `hooks/hooks.json` matcher 확장** — `Edit|Write|NotebookEdit|Read|Bash` (PreToolUse) + `Agent` (PostToolUse).
  - **(5) opt-out 다중**: ① `.no-dcness-guard` 마커 (RWHarness `.no-harness` 정합) ② `DCNESS_INFRA=1` env (개발자 모드) ③ `CLAUDE_PLUGIN_ROOT` env ④ cwd 화이트리스트 (현 저장소).
  - **(6) Bash 휴리스틱 v1 보수적** — write indicator 부재 시 빈 list. quoted pattern 도 path 후보 포함 (false negative 회피). 정밀 추출은 후속.
- **Follow-Up**:
  - **자장 plugin 재install + 새 epic 검증** — sub-agent 가 인프라 path Edit/Write 시도 → block 메시지 (`[agent-boundary] ...`) 실 발화 확인. 첫 incident 후 임계값 / 패턴 조정.
  - **(2) Bash 정밀 path 추출 강화** (후속) — `shlex.split` + 알려진 cmd 별 인자 위치 (예: `cp src dst` → dst index). v1 false positive 발생 시 즉시 진행.
  - **(2) READ_DENY_MATRIX 정밀화** (후속) — test-engineer impl 외 src 차단 등. v1 = 일부 비어있음.
  - **(2) NotebookEdit 검증** — 환경 외 동작 미실측. CC 환경에서 발화 시 동작 확인.
  - **DCN-30-39 (2) 30일 누적 임계값 tuning** — 보류 (5월 30일 이후).

### DCN-CHG-20260430-40
- **Date**: 2026-04-30
- **Rationale**:
  - 자장 jajang 사용자 보고 — `/product-plan` 진입 시 메인이 dcness 룰 (loop-procedure / Step 기록 / TaskCreate / begin-step) 미인지. SessionStart system-reminder 에 "OK" 만 보일 뿐 dcness 본문 부재.
  - 본 dcness 세션 jsonl `grep -c "dcness Guidelines (자동 로드"` = 0 직접 검증 — DCN-30-26 inject 처음부터 작동 0회.
  - 진짜 위반 — DCN-30-26 머지 후 *실제 작동 검증 없이* 후속 PR 5+개 진행. 글로벌 제1룰 ("실존 검증 강제") + dcness §12 self-verify 원칙 (우리 박은 룰) 위반. I5 회귀 패턴 동일.
- **2 Bug**:
  - **B1: JSON schema 잘못** — claude-code-guide 검증 결과 `{"continue", "additionalContext"}` top-level 은 CC honor X. 정확 schema = `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}`. nested wrapper 필수.
  - **B2: content 10K cap 초과** — guidelines.md 12,077 char inject 시도. CC additionalContext cap 10,000 초과 → truncate 또는 silent drop.
- **Alternatives**:
  1. *옵션 A — guidelines.md 자체 < 10K 압축*. SSOT 정보 손실.
  2. *옵션 B — 핵심 룰 5K inject + 자세 read*. 강제력 약함.
  3. **(채택) 옵션 C — directive only inject (~1K) + SSOT path + 핵심 강제 룰 4**. CLAUDE.md 와 동일 레벨 강제. cap 회피.
- **Decision**:
  - 옵션 C 채택.
  - Schema fix — `hookSpecificOutput` wrapper.
  - Content compression — directive 1.2K. 5 SSOT path + 핵심 강제 룰 4 (가시성 echo / Step 기록 / self-verify / finalize-run --auto-review).
  - 글로벌 강제 표현 — "글로벌 `~/.claude/CLAUDE.md` 와 동일 레벨 강제. 미인지 진행 = 룰 위반".
- **Follow-Up (의무)**:
  - **본 PR 머지 후 새 dcness 세션 시작** — system-reminder 에 "DCN-30-40 자동 로드" 출현 확인. 검증 *전* 다른 작업 금지.
  - **자장 plugin reinstall** — 사용자 환경. 새 자장 세션 → inject 검증 → 새 epic 진입 시 메인이 SSOT read + Step 절차 자율 적용 확인.
  - **DCN-30-27 ~ -39 의존성 재검증** — inject 작동 후 5 slim skill 메인이 SSOT 만 보고 task 동적 구성 가능 self-test.
  - **회귀 안전망** — `/run-review` 에 `INJECT_NOT_RECEIVED` 패턴 추가 후속.
  - **본 incident 회고 룰화** — dcness §12 안티패턴 1줄 추가 ("자기 박은 mechanical 메커니즘도 실 작동 검증 후 후속 PR 진행. 가정 진행 금지").

### DCN-CHG-20260430-39
- **Date**: 2026-04-30
- **Rationale**:
  - DCN-30-38 follow-up 3건 묶음 처리 (사용자 우선순위 결정 — 4-3-1 한 PR, 5번 별도).
  - **(4) cross-ref sweep**: DCN-30-32 split 시 `orchestration.md §4~§7` → `handoff-matrix.md §1~§4` 이전. agent prompt 안 잔재 전수 grep 결과 = 1줄 (`agents/pr-reviewer.md:86 "orchestration.md §7 정합"`). `orchestration.md` 현재 구조 (§0~§6, §216 자체에서 §7 이전 명시) — 진짜 stale.
  - **(3) tool_uses 컬럼**: DCN-30-37 `StepRecord.tool_use_count` + TOOL_USE_OVERFLOW 패턴 추가 후 단계별 상세 표 미노출 — 회귀 측정 시 한눈에 안 들어옴.
  - **(1) sub-mode banner**: DCN-30-20 jajang 6분 stall (extended thinking 안 prose 무한 회전, prose emit X) — `agents/architect.md:98-103` master 룰 강함. 단 architect 의 실제 실행은 `agents/architect/<mode>.md` sub-prompt — sub-mode 7개 banner 부재 → 회귀 회피율 ↓.
- **Alternatives**:
  1. *옵션 A — master 파일에만 banner 추가*. 사용자 초안. 단 architect 의 mode-별 sub-prompt 가 실제 실행 → master 단순 중복은 효과 ↓.
  2. *옵션 B — sub-mode 7개 모두 banner*. 가시성 ↑, 단 7 곳 중복 (LLM 토큰 ↑).
  3. *옵션 C — sub-mode + import 패턴 (`@agents/architect.md` 참조)*. .md 안 import 미지원 — 기각.
  4. **(채택) 옵션 B**. 토큰 비용 (각 banner 4줄 × 7 = 28줄) 대비 회귀 회피 가치 ↑. master 중복 X (master 에는 이미 §자기규율 lines 98-103 강한 룰 존재).
  5. *render_report 컬럼 — 표 너비 ↑ 우려*. tool_uses 12 컬럼 → 13 컬럼. 트레이드오프 수용 — TOOL_USE_OVERFLOW 가시성 ↑ 가치 우선.
  6. *bold 임계 — 100 / 50 / 200 후보*. **100 채택** — `run_review.py:465` `TOOL_USE_OVERFLOW` 검출 임계와 동일. 두 신호 정합.
- **Decision**:
  - **(4)** `pr-reviewer.md:86` 1줄 `orchestration.md §7 정합` → `handoff-matrix.md §4 정합`.
  - **(3)** `render_report` 단계별 상세 표 컬럼 13개로 확장 (`tool_uses` 추가). `≥ 100` 시 `**bold**` 강조. 미매칭 invocation 은 `-`. 헤더 코멘트에 DCN-CHG-20260430-39 cross-ref. 테스트 3개 신규 (`ToolUsesColumnTests`).
  - **(1)** `agents/architect/{system-design,task-decompose,module-plan,tech-epic,light-plan,docs-sync,spec-gap}.md` 7 파일 H1 직후 1 블록 banner. 텍스트 80~95자, sub-mode 별 prose 본문 키워드 (Domain Model 표 / impl 본문 / plan 본문 / patch 본문) 차등 표기. 모두 master 룰 (`agents/architect.md` §자기규율) cross-ref. 7 파일 모두 300줄 cap 미충돌 (최대 254줄).
- **Follow-Up**:
  - **자장 plugin 재install + 다음 epic 측정** — `tool_uses` 컬럼 가시성 + sub-mode banner 효과 실측 (THINKING_LOOP 회귀율 ↓ 여부).
  - **(5) catastrophic-gate DCNESS_INFRA_PATTERNS path 보호** — 별도 PR (사용자 결정). 실 scope = `tool=Edit/Write` PreToolUse 신규 hook 추가 + `harness/hooks.py` path-pattern 핸들러 + `hooks.json` 등록. 1~2일.
  - **(2) 임계값 30일 누적 tuning** — 보류 (5월 30일 이후).

### DCN-CHG-20260430-38
- **Date**: 2026-04-30
- **Rationale**:
  - DCN-30-34 self-verify echo `## 자가 검증` 섹션 단일 형식 강제 — first-principle ("출력 형식 자유") 회색 영역. dcness-guidelines §1 가시성 룰 (다중 anchor `## 결론 / ## Summary / ## 변경 요약`) 와 비교 strict.
  - 사용자 명령 ("자율성을 심하게 저하하는 부분이 있는지 형식에 얽매게하는 부분이 있는지 자율 판단으로 어려운건지 1원칙에 입각해서 고민") — strict anchor 형식 약화 권고.
  - DCN-30-37 follow-up 으로 `MISSING_SELF_VERIFY` 패턴 추가 약속 — anchor 자율화 후 다중 anchor 검출 로직 필요.
  - DCN-30-37 follow-up 으로 §12 안티패턴 강화 약속 — Bash sed/awk 후 검증 의무 1줄 (#39 흡수, B안 — SSOT 강화).
- **Alternatives**:
  1. *옵션 A — `## 자가 검증` 단일 anchor 유지*. 형식 strict, agent 자율 약함. first-principle 회색.
  2. *옵션 B — anchor 완전 자율 (특정 섹션 명 X)*. 메인 추출 로직 구현 어려움 (regex 매칭 불가).
  3. **(채택) 옵션 C — 다중 anchor 옵션 + substance 의무**. dcness §1 가시성 룰 패턴 정합. 자율 + 검출 가능성 양립.
- **Decision**:
  - 옵션 C 채택. 4 anchor 옵션:
    - `## 자가 검증` (기존 DCN-30-34)
    - `## Verification` (영어)
    - `## 검증` (한국어 짧은 형)
    - `## Self-Verify` / `## Self Verify` (영어 dash 변형)
  - `agents/engineer.md` 양 섹션 (자가 검증 + IMPL_PARTIAL 남은 작업) anchor 자율화 명시.
  - `harness/run_review.py:SELF_VERIFY_ANCHORS` regex 4개 + `_has_self_verify_anchor(prose)` helper.
  - `MISSING_SELF_VERIFY` MEDIUM (HIGH 아님) — 누락 시 메인 결과 신뢰 어려운 정도지 critical 아님. engineer agent + IMPL_DONE/IMPL_PARTIAL/POLISH_DONE enum 한정 (escalate enum 비대상).
  - `dcness-guidelines.md` §12 안티패턴 1줄 추가 — Bash sed/awk 후 *전·후* 실측 의무 (방법 자율: git diff --stat / 결과 grep / Read 등). DCN-30-37 `MAIN_SED_MISDIAGNOSIS` 자동 검출 cross-ref.
- **Follow-Up**:
  - **자장 plugin 재install + 새 epic 검증** — DCN-30-33~38 효과 실 측정. 다음 epic 진행 시 prior count hint stderr / `MISSING_SELF_VERIFY` 검출 / `MAIN_SED_MISDIAGNOSIS` 검출 모두 자동 발화 확인.
  - **agent prompt §4/§5/§6/§7 → handoff-matrix sweep** (DCN-30-32 follow-up) — 별도 PR 후보.
  - **THINKING_LOOP CRITICAL banner** (smart-compact #5) — agents/{architect,ux-architect,product-planner}.md.
  - **render_report `tool_uses` 컬럼** — 단계별 표 보강.
  - **catastrophic-gate.sh handoff-matrix.md 보호 sync 검증**.
  - **임계값 30일 누적 tuning** — TOOL_USE_OVERFLOW 100 / PARTIAL_LOOP 3 / END_STEP_SKIP margin 1.

### DCN-CHG-20260430-37
- **Date**: 2026-04-30
- **Rationale**:
  - DCN-30-36 prior count hint 도입했으나 *효과 측정 인프라* 부재 — 다음 epic 진행 후 회귀 자동 발화 X. /run-review 수동 분석 의존.
  - 자장 실 데이터 (5.5MB JSONL, 5 epic-08/09 incidents) 분석 결과 — 4 패턴 모두 textually 식별 가능했으나 자동화 부재.
  - first-principle: 사후 측정은 자율 무관 — 결과 측정만, 실시간 강제 X. **dcness-guidelines.md §0.1 행동지침 md 의 measurement** 인프라가 없으면 회귀 검출이 매번 수동 → 비용 ↑.
- **Alternatives**:
  1. *옵션 A — 매 incident 시 사용자가 수동 회고*. 비용 ↑, drift.
  2. *옵션 B — agent prompt 안에 self-check 룰 inject*. 자율 침해 + 형식 강제 + 토큰 누적.
  3. **(채택) 옵션 C — `/run-review` 회귀 패턴 4종 자동 검출**. 사후 측정만 — 자율 무관. fix 효과 측정 가능.
- **Decision**:
  - 옵션 C 채택. 4 패턴 + StepRecord `tool_use_count` 필드.
  - `TOOL_USE_OVERFLOW` 임계 `≥ 100` — 자장 실측 5건 (102/119/153/170/223) 모두 PR PARTIAL 회귀. 마법수 아님 — 실측 기반.
  - `PARTIAL_LOOP` 임계 `≥ 3` — DCN-30-34 권고 cycle ≤ 3 정합.
  - `END_STEP_SKIP` margin `1` — sub-agent self-recurse / POLISH 같은 정상 변동 흡수.
  - `MAIN_SED_MISDIAGNOSIS` — 텍스트 패턴 검출 (한국어 + 영어). 휴리스틱 — false positive 가능, 단 sed 후 검증 누락은 큰 incident 라 보수적 검출 가치 ↑.
  - `MISSING_SELF_VERIFY` 패턴 **제외** (DCN-34 anchor 자율화 후 PR3 에서 추가 — 다중 anchor 옵션 검출 로직 필요).
  - signature 확장 — kwargs default None 으로 backward compat 보존. 기존 9 test caller 영향 0.
- **Follow-Up**:
  - **PR3 (DCN-30-38)**: DCN-34 self-verify echo `## 자가 검증` 섹션 anchor 자율화 (`## 자가 검증` / `## Verification` / `## 검증` 등 다중) + dcness-guidelines.md §12 안티패턴 1줄 강화 (sed 후 실측 의무) + `/run-review` `MISSING_SELF_VERIFY` 패턴 추가.
  - **자장 실 검증** — 자장 plugin 재install 후 다음 epic 시 4 패턴 모두 자동 검출 확인. 임계값 (100/3/1) tuning 후속.
  - **`MAIN_SED_MISDIAGNOSIS` false positive 모니터링** — 정상 자기 정정 텍스트도 패턴 매칭 가능. 30일 누적 측정 후 임계 강화 검토.
  - **render_report 컬럼 확장** — 단계별 표에 `tool_uses` 컬럼 추가 후속 (현재 duration / out_tok / total_tok / cost / matched 만).

### DCN-CHG-20260430-36
- **Date**: 2026-04-30
- **Rationale**:
  - DCN-30-34 IMPL_PARTIAL enum 도입 후 자장 추가 데이터 분석 (오후 5.5MB JSONL) — engineer overflow 5회 발생 (102/119/153/170/223 tool uses). 정상 invocation = 36~64. enum 만으론 self-monitor 불가능 (LLM 이 자기 tool_use_count 모름 — CC API 미노출 본질 한계).
  - first-principle 재검토 — "측정 정보 부재로 자율 판단 *원천 불가능* 했던 영역에 정보 보충 = 자율 *조건* 보강 (자율 침해 X)".
  - 측정 source 발견: CC session JSONL `toolUseResult.totalToolUseCount` 필드. 자장 실측에서 119 / 170 등 실제 값 일치 확인.
- **Alternatives**:
  1. *옵션 A — agent prompt 안에 숫자 cap (≤ 60 tool uses)*. 자율 침해 ↑. 마법수 기각.
  2. *옵션 B — IMPL_PARTIAL enum 만 (DCN-30-34 그대로 유지)*. self-monitor 불가능 → 실효 부족 (자장 실측 입증).
  3. **(채택) 옵션 C — helper 단 prior count 측정 → stderr hint**. 정보 보강만. 메인이 다음 begin-step 호출 시점에 인지 → agent prompt 에 명시 (예: "이전 87, 이번 분할 고려") 가능. 자율 침해 0.
  4. *옵션 D — agent 호출 시 prompt 에 자동 inject*. 인프라 복잡도 ↑ (agent invocation context 변형). v1 = stderr hint 단순.
- **Decision**:
  - 옵션 C 채택.
  - **`harness/run_review.py:extract_agent_invocations`** 에 `tool_use_count` 필드 추가 (기존 사용처 영향 0).
  - **`harness/session_state.py:_prior_engineer_tool_use_count(sid)`** 신규. CC session JSONL 단일 파일 (`<sid>.jsonl`) 만 스캔 — 효율 (전체 project dir scan X).
  - **`_cli_begin_step`** 가 `agent="engineer"` 시 hint 출력. 다른 agent 는 silent (engineer 가 자장 overflow 95% 점유 — 우선순위).
  - 측정 실패 silent (jsonl 없음 / 파싱 오류 — 노이즈 회피).
- **Follow-Up**:
  - **PR2 (DCN-30-37)**: `/run-review` 회귀 4 패턴 추가 (TOOL_USE_OVERFLOW / END_STEP_SKIP / PARTIAL_LOOP / MAIN_SED_MISDIAGNOSIS). hint 효과 *측정* 인프라.
  - **PR3 (DCN-30-38)**: DCN-30-34 self-verify echo `## 자가 검증` 섹션 → anchor 자유 약화 (substance 의무, 형식 자율). + dcness-guidelines §12 안티패턴 강화 (sed 후 검증 의무 inline).
  - **임계값 권고 (≥ 60 등) prompt 명시 X** — 메인 자율 판단. hint 가 정보 보강만.
  - **다른 agent 확장 후속** — architect/validator 도 overflow 발견 시 (자장 architect 64/58 케이스) 같은 hint 확장 검토. 현재 v1 = engineer.

### DCN-CHG-20260430-35
- **Date**: 2026-04-30
- **Rationale**: jajang impl-loop epic-08 회고 I5 — 메인이 "130개 즉시 fix" 진단 사용자에 전달 → 실측 시 0개 → 15분 추가 cycle. 메인 추측 진단 패턴. 글로벌 `~/.claude/CLAUDE.md` "제1 룰 — 실존 검증 강제" 가 *이미 박혀있음* — but dcness skill 진행 중 메인이 해당 룰을 잊는 경향 발견. SessionStart 훅이 dcness-guidelines.md 자동 inject — 본 룰을 §12 로 박아두면 skill 진행 컨텍스트에서 항시 가시.
- **Alternatives**:
  1. **commands/quick.md SSOT 1곳 + 4 skill 1줄 참조** (이전 plan) — 기각: SessionStart 훅 자동 inject (DCN-30-26 이후) 가 이미 dcness-guidelines.md 광역 inject. 4 skill 참조 redundant. 검토자 피드백 정합.
  2. **글로벌 `~/.claude/CLAUDE.md` 제1룰 강화** — 기각: 글로벌 룰 변경은 dcness 범위 밖 (사용자 결정). 본 PR 은 dcness 컨텍스트 보강만.
  3. **별도 룰 신설 (글로벌과 충돌 없는 새 룰)** — 기각: 룰 순감소 (§2.5) 위반 가능성. 글로벌 룰 재인용 + dcness 컨텍스트 추가가 적합.
  4. **채택**: dcness-guidelines.md §12 신설 — 글로벌 제1룰 재인용 + dcness skill 진행 컨텍스트에 맞춘 안티패턴 예시 (DCN-30-34 실측 사례). 검증 방법은 자율 (grep / ls / Read / Bash / WebFetch 자기 판단), 형식 X.
- **Decision**: 옵션 4. dcness-guidelines.md §12 — 룰 (MUST) + 자율 보존 + 안티패턴 (실측 사례) + 효과 (I5 회귀 방지 + agent self-verify echo 와 짝).
- **Follow-Up**:
  - 다음 dcness skill 진행 시 메인 추측 진단 발생률 측정 (목표: I5 같은 실측 0건 대비 추측 0).
  - I5 잔여 — 글로벌 `~/.claude/CLAUDE.md` 제1룰 강화는 사용자 결정 (별도 검토).
  - dcness-guidelines.md 가 ~256줄 — 300 cap 근접. 다음 룰 추가 시 분리 axis 결정 (`행동 룰` vs `참조 룰` 등).

### DCN-CHG-20260430-34
- **Date**: 2026-04-30
- **Rationale**: jajang impl-loop epic-08 회고 — 5 incident 중 I1 (mobile pivot batch 4 engineer overflow 119 tool uses) / I2 (e08 batch 2 overflow 119) / I3 (e08 batch 3 overflow 170 + sed 보다 Edit 선호) / I5 (메인 sed misdiagnosis "130개 fix" → 실제 0개) 회귀 방지. 부수 발견: architect/validator 가 `setupFilesAfterFramework` (jest 에 없는 키) 출력 — LLM 학습 데이터 노이즈.
- **Alternatives**:
  1. **숫자 cap 강제 (file edits ≤ 20 / tool uses ≤ 60 / bash output ≤ 2000 lines)** — 기각: 자율 정신 (`status-json-mutate-pattern.md` §2.5) 위반. agent 가 자기 capacity 자율 판단 못 하게 봉쇄.
  2. **mass mechanical transform 강제 (Edit 금지, sed/codemod 의무)** — 기각: 도구 자율 선택 침해. 권고로 완화.
  3. **catalog 를 architect 3 prompt 에 직접 박기** — 기각: 매 호출마다 read = 토큰 누적. SSOT 분리 + cross-ref 1줄로 충분.
  4. **WebFetch 의무 광역 적용 (모든 architect agent + 모든 외부 도구)** — 기각: 광역 강제는 자율 침해. *의심 시 권고* 로 완화.
  5. **채택**: ① IMPL_PARTIAL enum 도입 (순서 정의, 분할 시점 자율 판단) + 새 context window 로 follow-up. ② mass transform 권고 (도구 자율 선택). ③ self-verify echo 의무 (형식만 강제, 명령 자율 — I5 회귀 방지). ④ known-hallucinations.md SSOT + 4 agent cross-ref 1줄 (정보 제공, 활용 자율). ⑤ validator 자율 schema 검증 권고.
- **Decision**: 옵션 5. SSOT 위치는 검토자 피드백 정합 — handoff-matrix.md §1.5 + §2 (engineer enum + retry), loop-catalog.md §3 + §5 (allowed_enums), dcness-guidelines.md §5 (yolo 매트릭스). agent prompt 의 IMPL_PARTIAL / mass transform 권고 / self-verify echo 는 engineer.md 내부 (행동 정의 자체이므로). known-hallucinations.md 는 신설 SSOT, 4 agent cross-ref 1줄.
- **Follow-Up**:
  - 다음 impl-loop 운용 시 engineer caveat 비율 측정 (목표: jajang epic-08 의 13회 → 5회 미만).
  - prose 종이 `## 자가 검증` 섹션 박힘 비율 측정.
  - known-hallucinations.md 카탈로그 누적 — `change_rationale_history` alternatives / 발견 사례 자동 추출 follow-up (governance active loop 정합, 별도 Task).
  - jajang Epic 09 (mobile test triage 156 fails) 진행 시 효과 검증.
  - I4 (`.steps.jsonl` engineer 누락) 는 DCN-30-33 으로 cover. I5 부분 cover — 나머지는 글로벌 `~/.claude/CLAUDE.md` 제1룰 영역 (사용자 결정).

### DCN-CHG-20260430-33
- **Date**: 2026-04-30
- **Rationale**: jajang impl-loop epic-08 회고에서 발견된 I4 — e08 batch 2 의 `.steps.jsonl` 에 engineer step 통째 누락. 메인 Claude 가 git 작업으로 distract → engineer end-step 호출 skip → 다음 step 의 begin-step 이 current_step 덮어쓰면서 직전 step 기록 휘발. DCN-30-25 의 end-step drift detector / `--expected-steps` 검증은 *end-step 호출 자체가 발생한 케이스* 만 cover. *end-step 누락 + 다음 begin-step* 패턴은 미커버.
- **Alternatives**:
  1. **end-step 자동 보정 (begin-step 시 이전 step 자동 end-step 박음)** — 기각: DCN-30-25 가 명시적 reject ("자동 보정 X — 안전. WARN 으로 메인 사후 인지"). 자동 보정은 잘못된 enum/prose 박을 위험 있음.
  2. **현 detector (end-step drift) 만 의지 + WARN 출력 강화** — 기각: I4 패턴은 end-step 자체가 미호출 → drift detector 미발동. 새 trigger 필요.
  3. **채택: begin-step 시 *기존* current_step 의 last_confirmed_at 이 30분 초과 시 stderr WARN** — DCN-30-25 의 정책 (자동 보정 X) 정합. WARN 만 출력, 동작 정상 진행. trigger = next begin-step 호출 시점.
  4. **timeout-based daemon 으로 polling** — 기각: helper 는 daemon 아님. 추가 인프라 비용 ↑.
- **Decision**: 옵션 3. `STALE_STEP_TTL_SEC = 30 * 60` (30분) 상수 + `update_current_step` 안에 stale 검사. WARN 메시지 — `[session_state] STALE STEP WARN — previous current_step={agent:mode} stale {N}s. end-step 누락 의심 — .steps.jsonl 에 직전 step 기록 안 됨.`
- **Follow-Up**:
  - 효과 측정 — 다음 impl-loop 운용 시 STALE STEP WARN 발생률 측정. 0이면 운영자 행동 변화로 해결됨, 빈발이면 추가 가드 검토.
  - 30분 cap 자체는 hard-coded — 큰 batch (mobile dense) 작업에서 정상 30분+ 가능. 오탐 잦으면 환경변수로 cap 조정 옵션 검토 (별도 Task).
  - jajang Epic 09 진행 시 .steps.jsonl 누락 0 검증 — 본 detector 가 미연 차단.

### DCN-CHG-20260430-32
- **Date**: 2026-04-30
- **Rationale**:
  - PR4 (DCN-30-30) 에서 행동지침 md 300줄 cap 룰 SSOT 화 + 알려진 위반으로 `orchestration.md` (540줄) 명시. 본 PR 으로 해소.
  - 사용자 명령 ("줄이고 검증하고 split하자 죽 해") — PR5 skill bulk slim 직후 orchestration.md split 진행 의무.
- **Alternatives**:
  1. *옵션 1 — orchestration.md 그대로 두고 cap 룰 완화*. 사용자 의도 위반. 기각.
  2. **(채택) 옵션 2 — agent 결정 영역 (§4 결정표 + §5 retry + §6 escalate + §7 권한) 을 별도 파일로**. 책임 축 = 시퀀스 ↔ agent 결정/권한. RWHarness `harness-architecture.md` §3 어휘 정합 (handoff matrix).
  3. *옵션 3 — §4 결정표만 별도 (decision-table.md)*. 결정표 121줄 + 나머지 (§5/6/7 = 113줄) = 두 sub-axis 인데 같이 두는게 자연 (전부 agent 외부 강제). 분리하면 fragmentation. 기각.
  4. *옵션 4 — §3 mini-graph 별도*. mini-graph 는 시퀀스 visualisation — orchestration 본질과 직결. 분리 X.
- **Decision**:
  - 옵션 2 채택.
  - **`docs/handoff-matrix.md` 신규** (256줄):
    - §1 결론 enum → 다음 agent trigger 결정표 (12 agent / 13 mode 펼침)
    - §2 Retry 한도
    - §3 Escalate 조건 카탈로그
    - §4 접근 권한 매트릭스 (호출 / Write / Read / 인프라 패턴 / 인프라 프로젝트 판정)
    - §5 참조
  - **orchestration.md 슬림** (540 → 298줄): 시퀀스 SSOT 만. §4 = cross-ref 1 단락. §5/6/7 → handoff-matrix 로 이전. §8/9/10/11 → §5/6/7/8 renumber + sub-section §X.Y 참조 갱신 (구 §6/§7.X → handoff-matrix §1/§2/§3/§4).
  - **§7 proposal 인용 압축** (21줄 → 1 단락 cross-ref) — 원전이 status-json-mutate-pattern.md §2.5 / §11.4 에 이미 있음.
  - **`dcness-guidelines.md` §0.1** — "현재 알려진 위반" 갱신 (없음).
- **Follow-Up**:
  - **agent prompt 안 §4/§5/§6/§7 참조 sweep** — `agents/*.md` 가 orchestration.md §4 결정표 인용 시 handoff-matrix §1 로 갱신 필요. 각 agent doc 별 적용 검토 (별도 Task-ID 후보).
  - **catastrophic-gate.sh 등 hook 코드 안 ORCHESTRATION_REF 어휘** — 현재는 path 만 보호 (`docs/orchestration.md`). handoff-matrix.md 도 같은 보호 필요 (DCNESS_INFRA_PATTERNS 갱신 — 본 PR `handoff-matrix §4.4` 에 박힘).
  - **5 dcness 행동지침 SSOT 연쇄**: orchestration → loop-procedure → loop-catalog → handoff-matrix → dcness-guidelines. 모두 < 300줄. 다음 cap 위반 발견 시 같은 책임 축 split 패턴 적용.

### DCN-CHG-20260430-31
- **Date**: 2026-04-30
- **Rationale**:
  - PR1~PR4 (DCN-30-27/28/29/30) 로 SSOT 인프라 (loop-procedure.md mechanics + loop-catalog.md loop spec + 300줄 cap 룰 + helper --auto-review) 완성.
  - PR3 에서 `commands/qa.md` slim pilot (127 → 28줄) 으로 새 SSOT cross-ref 만으로 동작 가능 입증.
  - 사용자 명령 ("줄이고 검증하고 split하자 죽 해") — 나머지 4 skill bulk slim 즉시 진행. migration 본 목표 = skill 통째로 트리거화.
- **Alternatives**:
  1. **(채택) 옵션 A — 4 skill 일괄 bulk slim**. PR3 qa.md pilot 패턴 동일 적용. 5 skill 합계 80%+ 절감.
  2. *옵션 B — 1 skill 씩 4 PR 분할*. 안전 ↑ 단 review 부담 ↑ + drift (간 PR 사이 SSOT 변경) 위험. pilot 이미 완료 → bulk 안전.
- **Decision**:
  - 옵션 A.
  - **slim 형식 (5 절 표준)** — frontmatter (description trigger keyword 보존) / Loop / Inputs / 비대상 + 후속 라우팅 / 절차 cross-ref.
  - **per-skill 핵심**:
    - `quick.md` — Inputs (이슈 / 영향 파일 / 재현 / 방향) + qa enum 별 라우팅 (FUNCTIONAL_BUG/CLEANUP advance, DESIGN_ISSUE → /ux 추천).
    - `impl.md` — batch 경로 필수 Input + UI 감지 시 `impl-ui-design-loop` 자동 전환 + state-aware skip (DCN-30-13).
    - `impl-loop.md` — outer/inner 컨벤션 명시 (DCN-30-12 의무) + chain 정책 (clean 자동 / caveat 멈춤).
    - `product-plan.md` — 5 Input 항목 (요구사항 / 시나리오 / 제약 / 우선순위 / 변경 vs 신규) — `CLARITY_INSUFFICIENT` 사전 회피.
  - 모든 mechanics (helper begin-run / TaskCreate / begin-step / Agent / end-step / prose-staging / finalize-run / 7a 7b / commit-PR) 제거. catalog + procedure 단일 source.
- **Follow-Up**:
  - **orchestration.md split** (별도 Task-ID, 540줄 cap 위반) — 책임 축 후보: §2~§4 시퀀스+결정표 ↔ §5~§7 retry+escalate+handoff.
  - **jajang plugin 재설치 후 검증** — 새 세션에서 SessionStart 훅이 dcness-guidelines.md (§0 + §0.1) inject 확인 + 5 slim skill 모두 catalog/procedure cross-ref 만으로 정상 동작 확인.
  - **drift 모니터링** — skill 안에 mechanics 재유입 (다음 fix 시 누가 helper 호출 inline 박는지) 감시. /run-review 에서 SKILL_BLOAT 패턴 추가 검토.
  - **THINKING_LOOP fix** (smart-compact 미해결 #5) — agents/{architect,ux-architect,product-planner}.md "thinking 본문 드래프트 금지" CRITICAL banner 격상 후속.

### DCN-CHG-20260430-30
- **Date**: 2026-04-30
- **Rationale**:
  - 사용자 지시 (PR3 작업 중 발화) — "loop-procedure.md 이거 좀 쪼개자 가급적 300라인 넘기지 말랬잖아 행동지침 md는 이것도 룰로 적어놔줘". loop-procedure.md 436줄 = cap 초과. 룰 자체도 dcness-guidelines.md 에 SSOT 화해야 미래 회귀 방지.
  - 사용자 의도: 행동지침 md (메인/sub-agent 가 결정 시 직접 read 하는 md) 는 토큰 + thinking 시간 부담 ↑ → 300줄 임계 강제. 초과 시 *책임 축* 분리 (단순 복붙 X).
- **Alternatives**:
  1. *옵션 1 — loop-procedure.md 전체를 단일 파일 유지 + 사용자에게 "300줄 위반 OK" 요청*. 사용자 지시 거부 = 비대상.
  2. **(채택) 옵션 2 — procedure (Step 0~8 mechanics) ↔ catalog (8 loop 행별 풀스펙) 책임 축 split**. 자연스러운 분리 (mechanics vs spec). 둘 다 < 300줄.
  3. *옵션 3 — Step 별 sub-file 8개 (loop-procedure-step-0.md, step-1.md, ...)*. 과도 fragmentation. 메인이 한 루프 reconstruct 위해 8 파일 read = 부담 ↑. 기각.
  4. *옵션 4 — 행별 sub-file 8개 (loops/feature-build.md, impl-batch.md, ...)*. PR1 plan 단계에서 검토했던 안. 8 파일 = 너무 잘게. 단일 catalog 파일 (옵션 2) 가 보기 좋음.
- **Decision**:
  - **옵션 2 채택**.
  - **`docs/loop-catalog.md` 신규** (239줄) — 8 loop 행별 풀스펙 SSOT. 책임: loop spec.
  - **`docs/loop-procedure.md` 슬림** (436 → 242줄) — Step 0~8 mechanics 보존. 책임: 절차.
  - **300줄 cap 룰** = `dcness-guidelines.md` §0.1 신설 — 대상 (skill / agent / loop SSOT / guidelines 자체) / 대상 외 (역사 로그 / spec / proposals / 코드) / Why (토큰 + thinking) / How to apply (모니터링 + split PR + 양방향 cross-ref) / **현재 알려진 위반** (`orchestration.md` 540줄, split 후속 Task-ID 예정 명시).
  - cross-ref drift 가드: 양 파일 (procedure + catalog) 양방향 link + governance §2.2 doc-sync gate. orchestration.md §3 헤더도 catalog cross-ref 추가.
- **Follow-Up**:
  - **PR4 (DCN-CHG-20260430-31 예정)** — 4 skill bulk slim (quick / impl / impl-loop / product-plan). loop-procedure + catalog 2 SSOT cross-ref 만 박는 형태로.
  - **orchestration.md split (별도 Task-ID 예정)** — 540줄 cap 위반. 책임 축 후보: 시퀀스+결정표 (§2~§4) ↔ retry+escalate+handoff (§5~§7).
  - **다른 cap 위반 모니터링** — `git ls-files | xargs wc -l` 등 sanity script 검토 (후속).
  - **사용자 검증** — 다음 세션 SessionStart inject 시 §0 (procedure + catalog 의무 read) + §0.1 (300줄 cap) 모두 반영 확인.

### DCN-CHG-20260430-29
- **Date**: 2026-04-30
- **Rationale**:
  - PR1/PR2 (DCN-30-27/28) 로 loop-procedure.md SSOT + §7 풀스펙 매트릭스 확보. 이제 skill 슬림화 + helper 단 자동 트리거 도입 차례.
  - **`/run-review` 자동 호출 mechanical 강제 필요** — DCN-30-26 에서 dcness-guidelines.md §3 에 "루프 종료 시 의무" 박았으나 directive 일 뿐. 메인 Claude 가 finalize-run 끝나고 commit/PR 하느라 review 호출 잊는 회귀 (DCN-30-26 직전 사례) 우려.
  - **skill 슬림화 pilot 필요** — PR4 에서 4 skill bulk slim 전, 가장 단순한 1 skill 로 새 SSOT (loop-procedure.md §7) cross-ref 만으로 동작 가능 입증. /qa = qa-triage 1 step → 가장 단순.
- **Alternatives**:
  1. *옵션 A — skill prompt 에 `/run-review` 호출 inline*. PR1 분석에서 사용자 reject ("스킬에 왜 범용적인걸 넣어"). 4 skill 동시 변경 = 중복 누적. 기각.
  2. *옵션 B — SessionEnd 훅 자동 fire*. cross-session run false positive 우려 + 훅 stdout transcript 미진입. 기각 (PR1 plan 단계 동일 결정).
  3. **(채택) 옵션 C — helper `finalize-run --auto-review` flag (in-process)**. STATUS JSON + review 리포트 한 stdout 에 chained. 메인이 finalize-run 부르면 자동 piggy-back. 의도적 skip 불가 + Bash collapsed 보호 (메인이 가시성 §4 룰대로 character-for-character echo).
  4. *옵션 D — `dcness-helper` wrapper 가 finalize-run 호출 후 `dcness-review` subprocess 실행*. process 분리 → import 의존 0. 단 stdout 합치기 시 buffering 이슈 우려 + 추가 wrapper 복잡도. 기각.
- **Decision**:
  - **옵션 C 채택**.
  - `_cli_finalize_run` 안에서 `from harness import run_review as _rv; _rv.main(...)` lazy import. argparse `SystemExit` 안전 처리 (정상 흐름 미지장).
  - 실패 안전망: 모든 `Exception` (SystemExit 제외) → stderr `AUTO_REVIEW_FAIL` WARN, STATUS JSON 보존, exit 0. review 실패가 finalize 자체를 깨트리지 않음.
  - **qa.md slim pilot**: 127줄 → 28줄. frontmatter / Loop / Inputs / 후속 라우팅 추천 / 절차 cross-ref 의 5 절. helper 호출 / TaskCreate / begin-step / end-step / prose-staging / finalize-run / 7a / 7b 모든 mechanics 제거 — 절차는 loop-procedure.md §7.5 단일 source.
- **Follow-Up**:
  - **PR4 (DCN-CHG-20260430-30 예정)** — 4 skill bulk slim (quick / impl / impl-loop / product-plan).
  - **--auto-review 가시성 검증** — qa pilot E2E 시 stdout 양 확인. review 리포트 폭증 (수백줄) 시 후속 Task 로 `--brief` mode 옵션.
  - **finalize-run 호출 자체 mechanical 강제는 별도** — 메인이 finalize-run 부르는 step 7 자체를 skip 하는 회귀는 본 PR 으로 해결 X. SessionEnd 훅 또는 Stop 훅 안전망은 후속 검토 (현재는 메인 신뢰).
  - **drift 모니터링** — qa pilot 진입 시 메인이 loop-procedure.md §7.5 만 보고 mechanics 모두 reconstruct 가능한지 jajang 재install 후 실측.

### DCN-CHG-20260430-28
- **Date**: 2026-04-30
- **Rationale**:
  - PR1 (DCN-30-27 — loop-procedure.md SSOT 신설) 머지 후 self-test 진행. 메인 Claude 가 §7 매트릭스만 보고 8 loop reconstruct 가능한지 확인.
  - **Gap 발견** (4 loop + 공통 4):
    - `feature-build-loop` 분기 (PRODUCT_PLAN_UPDATED skip / UX_REFINE_READY / CLARITY_INSUFFICIENT) 매트릭스에 없음
    - `impl-ui-design-loop` task 모호 — designer + design-critic 가 1 step 인지 2 step 인지 불명, DESIGN_LOOP_ESCALATE 분기 없음
    - `ux-design-stage` designer mode (ONE/THREE_WAY) / 사용자 PICK 단계 미명시
    - `ux-refine-stage` 사용자 승인 단계 (§3.3 mini-graph 에 있음) 매트릭스에 없음
    - 공통: `allowed_enums` full set / `branch_prefix` decision rule (impl-batch-loop feat vs chore 분기 기준) / sub_cycle agent (SPEC_GAP / POLISH / IMPL-RETRY / SCREEN-ROUND) / Step 4.5 적용 여부 컬럼 부재
  - 사용자 의도: skill 슬림화 후 메인 Claude 가 §7 만 보고 task 동적 구성. baseline reconstruct 가능해도 분기 / sub_cycle 부족하면 실전 운영에서 매번 commands/<skill>.md 또는 orchestration.md §3 / §4 cross-ref 필요 → 슬림화 효과 ↓.
- **Alternatives**:
  1. **(채택) Option A — §7 매트릭스 보강 후 PR3 진입**. 매트릭스를 §7.0 인덱스 (간소) + §7.1~§7.8 행별 풀스펙 sub-section 으로 재구조화. 가독성 ↑ + reconstruct 100%.
  2. *Option B — 매트릭스 그대로 두고 cross-ref 강화*. §7 행마다 "분기 details = §3.3 / §4.X" link 박음. 가벼움. 단 메인 Claude 가 cross-ref 따라가는 부담 ↑ → 슬림화 의도 약화.
  3. *Option C — 현 상태로 PR2 (qa.md pilot) 진행*. PR2 자체는 가장 단순한 loop (qa-triage 1 step) — 즉시 가능. 단 PR3 진입 *전* 보강 필요 = 결국 미루기. 기각.
- **Decision**:
  - Option A 채택 (사용자 명시 컨펌).
  - **§7 재구조화**:
    - §7.0 인덱스: 8 loop × 6 컬럼 (loop / entry_point / task_list / advance / clean_enum / expected_steps). 한눈 인지용.
    - §7.1~§7.8 행별 풀스펙: 각 loop 별 sub-section. 컬럼 = `branch_prefix` / `Step 4.5 적용` / Step 별 `allowed_enums` 표 / 분기 표 / sub_cycles 표.
    - §7.9 = `impl-loop` multi-batch chain
    - §7.10 = catastrophic 룰 정합
  - **Migration Plan 갱신**: PR2 (현재) = §7 보강. PR3 (-29) = `--auto-review` flag + qa.md slim. PR4 (-30) = 4 skill bulk slim. 총 4 PR.
- **Follow-Up**:
  - **PR3 (DCN-CHG-20260430-29 예정)**: `harness/session_state.py:_cli_finalize_run --auto-review` flag + tests + `commands/qa.md` slim pilot.
  - **PR4 (DCN-CHG-20260430-30 예정)**: 4 skill bulk slim.
  - **drift 가드**: §7.0 인덱스 ↔ §7.1~§7.8 sub-section 행 수 1:1 강제. 행 추가 시 sub-section 추가 의무. cross-ref drift = doc-sync gate 자동 검출 X (수동) — 후속 PR 에서 sanity check script 검토.
  - **잠재 미흡 부분 모니터링**: ONE_WAY 키워드 트리거 룰 (사용자 발화 어떤 keyword 포함 시?), Step 2.5 사용자 승인 helper 처리 (begin/end-step 비대상 명시 — driver 도입 시 review).

### DCN-CHG-20260430-27
- **Date**: 2026-04-30
- **Rationale**:
  - 사용자 아키텍처 지적 (DCN-30-26 직후) — skill 5종 (`commands/{qa,quick,product-plan,impl,impl-loop}.md`) 이 Step 0~7 실행 절차 (begin-run / TaskCreate / begin-step/Agent/end-step/echo / finalize-run / 7a 7b commit-PR / run-review) 를 통째로 중복 보유 (100~215줄). /run-review 자동 호출 같은 새 룰 추가 시 5 skill 모두 손대야 함 = 중복 누적.
  - 사용자 의도: **skill = 그 루프를 돌기 위해 필요한 정보를 수집하는 정도** (info-collection trigger). 메인 Claude = orchestration SSOT 읽고 동적 Task 구성. 기술 에픽 도입 사례 evidence — 메인이 룰 보고 task 짠 게 잘 동작.
  - skill 두께가 메인 thinking 시간 + 토큰 부담 + drift 위험 모두 누적 (DCN-30-21/22 슬림 시도 후에도 100+줄).
- **Alternatives**:
  1. *옵션 A — skill 마다 `/run-review` 호출 inline*. 5 skill 동시 수정 = 사용자 아키텍처 정신 위반 ("스킬에 왜 범용적인걸 넣어"). 기각.
  2. *옵션 B — helper `finalize-run` 자체에 review 통합*. 진짜 mechanical. 단 trigger 책임 = 메인이 finalize-run 부르는 시점 의존. skill 절차에 박혀있는 finalize-run 호출이 곧 review trigger 가 되는 구조 — 옵션 A 와 동일 의존.
  3. *옵션 C — SessionEnd 훅 자동 fire*. cross-session run false positive 우려 + 훅 stdout transcript 미진입 → review 결과 가시성 ↓. 기각.
  4. **(채택) 옵션 D — 절차 SSOT (`loop-procedure.md`) 신설 + skill 슬림화 + helper `--auto-review` flag**. skill = 트리거, 절차 = SSOT, review = helper in-process piggy-back. 3 PR 분할 마이그레이션.
- **Decision**:
  - **옵션 D 채택** + **3 PR 분할** (SSOT → /qa pilot → 4 skill bulk).
  - 본 PR (PR1) = SSOT 신설 + cross-ref 박음. skill 변경 / harness 변경 X.
  - **`docs/loop-procedure.md` 신규** — Step 0~8 골격 + §7 매트릭스 (8 loop × 7 컬럼: entry_point / task_list / agent_sequence / advance / clean_enum / branch_prefix / expected_steps).
  - **`docs/process/dcness-guidelines.md` §0 신설** — SessionStart inject 시 loop-procedure.md 의무 read 명시. drift mitigation: governance §2.2 doc-sync gate + cross-ref 박힘.
  - **`docs/orchestration.md` §3 헤더 cross-ref** — §3 mini-graph (시퀀스 카탈로그) 와 loop-procedure.md §7 (실행 매트릭스) 1:1 강제. 8 loop name 매핑 명시.
  - **SSOT 위치 결정** (사용자 컨펌): orchestration.md §11 신설 ❌ — orchestration = WHAT (시퀀스), procedure = HOW (mechanics) 다른 axis. 별도 파일이 책임 분리 명확. guidelines.md (option C) 도 reject — guidelines = cross-cutting 룰 (echo/yolo/worktree), procedure = 시퀀스 mechanics 다른 축. inject 187줄 → 400+줄 비대화 우려.
- **Follow-Up**:
  - **PR2 (DCN-CHG-20260430-28 예정)** — `harness/session_state.py:_cli_finalize_run --auto-review` flag 신설 + `tests/test_session_state.py` wiring 케이스 + `commands/qa.md` slim pilot (~25 줄). qa flow E2E 검증 (jajang reinstall 후 1회).
  - **PR3 (DCN-CHG-20260430-29 예정)** — `commands/{quick,impl,impl-loop,product-plan}.md` bulk slim. 4 skill 1회씩 dry-run 검증.
  - **drift 위험 모니터링** — §3 mini-graph ↔ §7 매트릭스 sync 가 doc-sync gate 자동 강제. 매 변경 시 양쪽 동시 update 의무.
  - **PR1 self-test** — 메인 Claude 가 §7 매트릭스 만 보고 8 loop 모두 task 리스트 + advance enum reconstruct 가능한지 (skill 안 보고). 실패 시 §7 보강 후 PR2 진입.
  - **review 자동 트리거 v2** — `--auto-review` stdout 폭증 시 후속 Task 로 `--brief` mode 옵션 검토.

### DCN-CHG-20260430-26
- **Date**: 2026-04-30
- **Rationale**:
  - 사용자 지적 — quick.md (light path 전용 skill) 에 범용 룰들 (가시성 / yolo / AMBIGUOUS / worktree / Step 기록) 이 다 박혀 책임 혼재. 사용자 발화 ("범용적인걸 왜 넣어, 사탄들렀어?") — 아키텍처 잘못.
  - 미래 추가될 dcness 지침 명시:
    - Epic/Story/Milestone 분할 기준 (CLAUDE.md 와 ~/.claude/CLAUDE.md 어디에도 부재)
    - Skill 외 커스텀 루프 가이드 (orchestration.md 참조해 메인 자율 구성)
    - 등 — 단발 룰 1개가 아닌 *지침 본체* 필요.
  - 추가로 사용자 명시 룰 2개:
    - 루프 종료 시 `/run-review` 의무 호출 ("모니터 스킬 빼먹지 말고")
    - 결과 출력 룰 — Bash stdout 을 텍스트 응답으로 character-for-character 복사 ("백그라운드가 아닌 제대로 출력")
- **Alternatives**:
  1. *옵션 A — `init-dcness` 가 `<project>/CLAUDE.md` inject*. CLAUDE.md 자동 로드 ✓. 단 plugin uninstall 시 orphan content. 차순위.
  2. *옵션 B — SessionStart 훅 reminder 출력 ("guidelines.md 참조해라")*. dynamic. 단 LLM 무시 가능 ("참조" → 실제 read X).
  3. **(채택) 옵션 C — SessionStart 훅이 guidelines.md 내용 *자체* 를 system-reminder 로 inject**. CC 자동 로드 보장 + plugin 비활성 시 발화 X (orphan 0) + 무시 위험 ↓.
  4. *옵션 D — quick.md 안 룰 압축만*. 책임 혼재 미해결.
- **Decision**:
  - 옵션 C 채택. RWHarness `harness-review-inject.py` 패턴 정합 (이미 검증된 메커니즘).
  - **`docs/process/dcness-guidelines.md` 신규** (11 섹션):
    1. 가시성 룰 (DCN-30-15)
    2. Step 기록 룰 (DCN-30-25)
    3. **루프 종료 시 `/run-review` 의무 (신규)**
    4. **결과 출력 룰 (신규)** — Bash collapsed 회피
    5. yolo 모드
    6. AMBIGUOUS cascade
    7. worktree 격리
    8. (TBD) Epic / Story / Milestone 분할 기준
    9. (TBD) Skill 외 커스텀 루프 가이드
    10. 권한/툴 부족 시 사용자 요청 (DCN-30-18)
    11. (참조) Karpathy 4 원칙 (DCN-30-17)
  - **`hooks/session-start.sh`** — `is-active` 게이트 통과 후 inline python 으로 guidelines.md 내용 read + JSON `{continue, additionalContext}` stdout. CC 매 세션 자동 인지.
  - **`commands/quick.md` 슬림화** — 380줄 → 215줄. 범용 룰 본문 제거, cross-ref 만.
  - **다른 skill (impl / impl-loop / product-plan / qa) cross-ref 통일** — 이미 quick.md SSOT 인용 중이라 자동 정합.
- **Follow-Up**:
  - **TBD §8 (분할 기준)** — 다음 PR 후보. 마일스톤 bump 임계 / 에픽 / 스토리 분할 단위 명시.
  - **TBD §9 (커스텀 루프 가이드)** — 다음 PR 후보. orchestration 시퀀스 카탈로그 참조 패턴.
  - **테스트** — 현재는 unit test 없음 (hook bash 스크립트 testability 한계). 통합 검증은 jajang plugin 재설치 후 새 세션 시 system-reminder 로 가이드라인 자동 발화 확인.
  - **다른 skill 의 finalize-run 후 `/run-review` 호출 자동 박음** — `commands/quick.md` Step 7 / `commands/impl.md` Step 7 등에 inline `dcness-review --run-id $RUN_ID` 추가 (별도 PR).
  - **PR 권한 룰** (engineer commit/push/PR 매트릭스) — 사용자 보류. 별도 follow-up.

### DCN-CHG-20260430-25
- **Date**: 2026-04-30
- **Rationale**:
  - jajang DCN-30-23 사후 분석 (jajang 메인 self-introspection):
    - batch 2 engineer 끝난 직후 메인 시퀀스: git status check → 별도 commit/push → validator Agent 호출 (end-step engineer skip) → end-step validator + begin-step pr-reviewer
    - POLISH 사이클 동일 — engineer POLISH Agent 호출 시 begin/end-step 안 둘러쌈
    - 결과: .steps.jsonl 에 engineer / pr-reviewer 첫 호출 / POLISH 누락 → /run-review 검출 X → 가시성 손실
  - 본질: 메인 Claude 행동 결함 (skill prompt SSOT 가 명시 안 한 영역 = engineer 자체 PR / POLISH naming / 재호출 시 step 등록).
  - Karpathy MUST 패턴 정합 — 자율에 맡기면 토큰 절약 본능으로 skip. mechanical 강제 필요.
- **Alternatives**:
  1. *옵션 1 — skill prompt 강화만*. 자율 의존. 메인이 또 까먹을 가능성. 차순위.
  2. *옵션 2 — helper 자동 보정 (drift 시 이전 step 자동 end-step)*. 위험 — 옛 prose + 새 enum 매칭. 기각.
  3. **(채택) 옵션 3 — helper 측 안전망 (WARN only) + skill prompt SSOT 강화 동시**. WARN 으로 메인 즉시 인지 + 룰 명시로 prompt 신뢰성 격상. 자동 보정 X = 안전.
- **Decision**:
  - 옵션 3. 4 fix:
    1. **drift detector** — `_cli_end_step` 가 호출 시 live.json 의 current_step 과 args.agent 비교. 불일치 또는 부재 시 stderr WARN. 동작은 정상 (자동 cancel X).
    2. **step count 검증** — `_cli_finalize_run --expected-steps N` 옵션. row count 미달 시 stderr WARN.
    3. **commands/quick.md SSOT 강화** — `## Step 기록 룰` 신규:
       - Agent 호출 1회 = begin/end-step 1쌍 의무
       - POLISH 네이밍 컨벤션 (`engineer:POLISH-1`, `engineer:POLISH-2`)
       - 재호출 컨벤션 (`engineer:IMPL-RETRY-1`)
       - 안티패턴 4건 명시 (jajang 실측 기반):
         - engineer 자체 commit/PR 후 end-step skip
         - POLISH Agent 호출 시 begin/end-step 안 둘러쌈
         - 사용자 입력 받느라 end-step 보류 후 망각
         - multi-batch 보고 작성 후 begin-step 다시 안 부름
       - helper 안전망 cross-ref (drift WARN / step count WARN)
    4. **commands/impl.md Step 7** — `--expected-steps 5` 박음.
  - **PR 권한 룰** (engineer 자체 PR 생성) 은 사용자 "디테일하게 볼게 있어" 발화로 본 PR 에서 보류. 별도 follow-up.
- **Follow-Up**:
  - **PR 권한 룰화** — engineer 의 commit/push/PR 권한 매트릭스 명시 (별도 Task-ID)
  - **POLISH agent prompt** — engineer.md 측 POLISH 네이밍 reminder
  - **/impl-loop --expected-steps** — multi-batch 환경 step count 검증 룰화
  - **30일 회귀 측정** — drift WARN 발생 빈도 모니터. 0 이면 룰 안정. >0 이면 추가 강화.

### DCN-CHG-20260430-24
- **Date**: 2026-04-30
- **Rationale**: 사용자 jajang 분석 디버그 도중 ts 가 `04:xx` 로 보여 헷갈림. `.steps.jsonl` UTC 저장 + 사용자 KST 환경 + Mac mtime local 표시의 timezone mix.
- **Decision**: render 측 `astimezone()` 변환 (system local). 저장 형식 (UTC ISO) 변경 X — 시스템 간 전송 표준 보존.
- **Follow-Up**: 후속 debug 도구 작성 시 동일 패턴 적용.

### DCN-CHG-20260430-23
- **Date**: 2026-04-30
- **Rationale**:
  - 사용자 jajang 실측 분석 후 2 결함 보고:
    1. `/run-review` Phase 2 (DCN-30-20) 매칭 알고리즘 cascade 결함 — 9 step 중 2 만 매칭. step 0 invocation 부재 (다른 세션 이력) → 후속 step 매칭 모두 한 칸씩 어긋남.
    2. skill prompt 의 `/tmp/dcness-*.md` 고정 path 가 세션 격리 X — 멀티세션 race / stale prose 잔여로 helper 가 옛 prose 의 enum 추출.
  - 두 결함 모두 jajang 실측 데이터로 확인 — 추측 X.
- **Alternatives**:
  1. *옵션 1 — 2 PR 분리* (매칭 fix + /tmp fix). 깔끔. 사용자 "한번에 하자" 발화 X.
  2. **(채택) 옵션 2 — 단일 PR 동시 fix**. 사용자 "한번에 하자" 정합 + 두 결함이 같은 jajang 실측에서 발견.
- **Decision**:
  - 옵션 2. 단일 PR 동시 fix.
  - **매칭 알고리즘**: 단순 순서 + agent name → timestamp-proximity:
    - inv.ts < step.ts (sub-agent 가 end-step 전에 끝남)
    - step.ts - inv.ts ≤ 600s (10분 — sub-agent budget 한도)
    - inv.agent == step.agent
    - 같은 agent 후보 여럿이면 가장 최근 (closest before step.ts)
    - 1 invocation = 1 step (used set)
  - **prose-file path 격리**:
    - helper 신규 subcommand `run-dir` — 현재 active run 의 run_dir 절대 경로 stdout
    - skill prompt 4개 (`quick` / `product-plan` / `impl` / `qa`) 가 `RUN_DIR=$("$HELPER" run-dir)` + `mkdir -p "$RUN_DIR/.prose-staging"` + `--prose-file "$RUN_DIR/.prose-staging/<step>.md"` 패턴 사용
    - 멀티세션 자동 격리. 명시 cleanup 의존도 0 (run-dir 자체가 run 별).
  - **검증**: jajang run-657d86fc 재실행 → 8 매칭 (이전 2). step 0 만 정당 미매칭 (다른 세션 이력).
- **Follow-Up**:
  - **매칭 결과 보고 보강** — 미매칭 step 에 대해 "왜 매칭 X" 진단 prose 출력 (Phase 3 후보)
  - **자동 트리거** — finalize-run post-hook (Phase 3 미해결)
  - **30일 누적 ranking** — Phase 3 미해결
  - **STREAM_STALL** — stream_event gap 분석 (Phase 3 미해결)

### DCN-CHG-20260430-22
- **Date**: 2026-04-30
- **Rationale**: DCN-CHG-20260430-21 슬림 작업 시 Antigravity language server 의 file revert 우회를 위해 `commands/slim/` 에 staging 사본을 두고 atomic cp + git add 로 race 회피했음. follow-up 으로 staging 디렉토리 정리 약속 (rationale §Follow-Up).
- **Alternatives**:
  1. **유지** — 추후 슬림 작업 reference 로 활용. 기각: 본 위치 (`commands/*.md`) 가 SSOT, staging 은 일회성 우회.
  2. **`docs/` 로 이전** — 기각: skill 본문 변경 이력은 git log 가 SSOT, 별도 doc 불필요.
  3. **채택: 삭제** — 본 작업 완료 + 본 위치에 commit 됐으므로 불필요. clean state 유지.
- **Decision**: 옵션 3. `commands/slim/` 디렉토리 통째 삭제.
- **Follow-Up**: Antigravity revert 우회 패턴은 본 사례로 충분 — 글로벌 CLAUDE.md 등에 노트 추가는 별도 Task (사용자 결정).

### DCN-CHG-20260430-21
- **Date**: 2026-04-30
- **Rationale**: jajang 도그푸딩 중 `/product-plan` 진입 시 메인 Claude skill prompt (14,660자) 처리에 **3분 46초 thinking** 소요 (캐시 히트·output 1352 토큰임에도). 본 skill 외에도 4개 dcness skill (`/quick` 19,463자 / `/impl` 15,973자 / `/impl-loop` 8,730자 / `/qa` 8,094자) 모두 동일 비대 패턴. 원인 — 매 skill 이 *공통 룰* (가시성 / AMBIGUOUS / yolo / worktree / catastrophic / 의무 echo 템플릿 + 자가 점검 + 안티패턴) 본문을 풀어 재기술. 거버넌스 §2.5 "함정 회피 5원칙" 룰 순감소 위반.
- **Alternatives**:
  1. **공통 룰 외부 doc 추출 + skill prompt 한 줄 reference만** — 기각: 메인이 reference doc 안 읽으면 룰 미적용. 의무 템플릿·자가 점검·안티패턴은 skill prompt 안에 직접 박혀야 강제력 보존.
  2. **5 skill 균등 슬림 + 룰 본문 5번 동일 박기** — 기각: 룰 변경 시 5곳 동기화 비용. SSOT 위배.
  3. **채택**: `commands/quick.md` 를 공통 룰 SSOT 로 격상 + 다른 4 skill 은 SSOT 참조 + 시퀀스/분기 표만 명세.
  4. **메인 모델 다운그레이드** — 기각: 모델 선택 권한이 dcness 범위 밖. 비대 자체가 문제.
- **Decision**: 옵션 3. 5 skill 합계 68,488 → 32,721자 (52% 절감, ~9k 토큰). quick.md 만 본문 보존, 4개 skill (product-plan 68% / impl 52% / impl-loop 45% / qa 46% 절감). 동작 spec 100% 보존 — 모든 enum / 분기 / cycle 한도 / catastrophic §2.3 정합 / Step 4.5 / Step 2.0 SKIP / yolo auto-resolve 그대로. 가시성 룰 (DCN-CHG-30-15) 의무 템플릿·자가 점검 4항·안티패턴·5~12줄 cap 모두 quick.md 보존.
- **Follow-Up**:
  - jajang/dcTest 다음 `/product-plan` 진입 시 메인 thinking 시간 측정 — 목표 3분 46초 → 1분대.
  - `commands/slim/` staging 디렉토리 정리 (별도 follow-up Task).
  - Antigravity language server file revert 환경 이슈 노트 추가 검토 (별도 Task).
  - 추후 skill 추가 시 본 패턴 (SSOT = quick.md, 다른 skill 은 표 + 참조) 정착.

### DCN-CHG-20260430-20
- **Date**: 2026-04-30
- **Rationale**:
  - 사용자 jajang 실측 보고 — `/product-plan PRODUCT_PLAN_CHANGE` 진행 중 product-planner sub-agent 가 6분 동안 ↓624 tokens 만 흘리고 stall. user 입력 후 다시 살아남.
  - 토큰량과 elapsed 의 비율로 *thinking 무한 loop / stream stall* 검출 가능.
  - 사용자 요청 — `/run-review` Phase 2 진입해서 본 패턴 자동 검출 가능 여부 확인.
- **Alternatives**:
  1. *옵션 1 — Phase 2 통째 (per-Agent cost + automatic trigger + 누적 분석)*. 큰 변경. 차순위.
  2. **(채택) 옵션 2 — Phase 2 부분 (per-Agent metrics + THINKING_LOOP only)** — 사용자 시급한 케이스 먼저. 자동 트리거 / 누적 분석은 별도 후속.
- **Decision**:
  - 옵션 2 채택. THINKING_LOOP detection 우선 박음.
  - 데이터 소스 — CC session JSONL `toolUseResult.usage` 안 `output_tokens` + `totalDurationMs`. `agentType` 으로 sub-agent 식별.
  - 매칭 알고리즘 — 순서 (timestamp 오름차순) + agent name 정합 (`dcness:architect:system-design` → `architect`).
  - `EXPECTED_AGENT_BUDGETS` 12 agent 표 (elapsed_s / min_output_tokens):
    - product-planner / architect / engineer / test-engineer / validator / pr-reviewer / security-reviewer / qa / plan-reviewer / design-critic / designer / ux-architect
  - THINKING_LOOP threshold:
    - duration > budget × 1.5 AND output < min × 0.3 (정상 budget 기준)
    - OR duration > 300s AND output < 1000 (절대 한도)
  - 사용자 사례 (product-planner 6분 + 624 tokens) 정확히 caught — 1 케이스로 reproduction 테스트.
- **Follow-Up**:
  - **STREAM_STALL** — stream_event 별 timestamp gap 분석으로 단일 invocation 내 정체 검출 (Phase 3 후보)
  - **자동 트리거** — finalize-run 직후 자동 review (RWHarness HARNESS_DONE post-hook)
  - **누적 ranking** — 30일 N runs 의 agent 별 THINKING_LOOP 빈도 → prompt 강화 자동 권고
  - **DCN-CHG-20260430-21 후속** — skill prompt 의 `--prose-file /tmp/dcness-*.md` 고정 path 결함 fix (세션 격리 X, 멀티세션 race 가능). run-dir 안 격리 path 또는 mktemp 로 전환.

### DCN-CHG-20260430-19
- **Date**: 2026-04-30
- **Rationale**:
  - 사용자 메타-하네스 self-improvement 루프 요청 — RWHarness 의 `/harness-review` 패턴을 dcness 에 도입.
  - RWHarness review skill 분석 결과:
    - JSONL log 파싱 → agent 별 cost/elapsed/tools/files_read 추출
    - 8 waste 패턴 (INFRA_READ / SUB_AGENT / TIMEOUT / NO_OUTPUT / RETRY / CONTEXT_BLOAT / SLOW / DUPLICATE_READ)
    - 마크다운 리포트 + 수정 제안
    - HARNESS_DONE / ESCALATE 후 자동 트리거
  - dcness 데이터 소스 확인 (실측):
    - `.steps.jsonl` (DCN-30-2 부터 존재) → step 별 (agent, mode, enum, must_fix, prose_excerpt, ts)
    - per-agent prose files → 전체 결론 + 본문
    - CC session JSONL → assistant turn 별 cost/usage (이미 `harness/efficiency/` 가 파싱)
    - Agent tool `toolUseResult` → `totalCost` / `totalDurationMs` / `totalTokens` (Phase 2 후속용)
  - 가능성 확인: ✅ 잘한 점/잘못한 점 추출 + ⚠️ 단계별 금액 부분 가능 (Phase 1 = run-level, Phase 2 = per-Agent).
- **Alternatives**:
  1. *옵션 1 — RW review.py 통째 fork*. 최소 변경. 단 RW JSONL event format 과 dcness `.steps.jsonl` 형식이 다름 → 무의미. 기각.
  2. *옵션 2 — Phase 1 + Phase 2 동시 구현*. 한 번에 완성. per-Agent cost 매칭은 timestamp + subagent_type 매핑 복잡 — 본 PR 비대 위험. 차순위.
  3. **(채택) 옵션 3 — Phase 1 (run-level coarse) 우선 + Phase 2 후속** — 빠른 가치 제공 + 추후 정밀화. 사용자 "확인" (feasibility 우선) 발화 정합.
- **Decision**:
  - 옵션 3 채택. Phase 1 = `harness/run_review.py` 신규 (~370 LOC).
  - 잘한 점 (GOOD findings) 5 패턴:
    - `ENUM_CLEAN` — step enum 이 expected 매트릭스 정합 + must_fix=False
    - `PROSE_ECHO_OK` — prose_excerpt 5~12줄 (DCN-30-15 룰 회귀 검출)
    - `DDD_PHASE_A` — architect SD prose 안 Domain Model / Phase A 섹션 (DCN-30-16)
    - `DEPENDENCY_CAUSAL` — 의존성 화살표에 인과관계 1줄 (DCN-30-16)
    - `EXTERNAL_VERIFIED_PRESENT` — plan-reviewer EXTERNAL_VERIFIED 섹션 (DCN-30-18)
  - 잘못한 점 (WASTE findings) 8 패턴:
    - `RETRY_SAME_FAIL` (MEDIUM) — 연속 동일 FAIL enum
    - `ECHO_VIOLATION` (MEDIUM) — prose_excerpt < 3줄 (DCN-30-15 회귀)
    - `PLACEHOLDER_LEAK` (HIGH/MEDIUM) — `[미기록]` / `M0 이후` / `NotImplementedError` 발견 (DCN-30-18 회귀)
    - `MUST_FIX_GHOST` (HIGH) — must_fix=true 이후 다음 step 진행
    - `SPEC_GAP_LOOP` (MEDIUM) — architect SPEC_GAP > 2회
    - `INFRA_READ` (HIGH) — prose 안 인프라 경로 흔적
    - `READONLY_BASH` (HIGH) — read-only agent 가 Bash 호출 흔적
    - `EXTERNAL_VERIFIED_MISSING` (HIGH) — plan-reviewer EXTERNAL_VERIFIED 섹션 부재 (DCN-30-18 회귀)
  - 출력 룰 — Bash stdout 의 마크다운 리포트를 character-for-character 그대로 (RWHarness review 패턴 정합 + DCN-30-15 echo 룰 정합).
  - dcness skill 9 개 (efficiency 와 보완 관계: efficiency=세션 단위 / run-review=run 단위).
- **Follow-Up**:
  - **Phase 2** — per-Agent cost 매칭 (`toolUseResult.totalCost` 추출, Agent tool 호출 timestamp + subagent_type 으로 step 에 매핑)
  - **자동 트리거** — finalize-run 직후 자동 review trigger 옵션 (RWHarness 의 HARNESS_DONE post-hook 정합)
  - **누적 분석** — 30일 N runs 비교 + 에이전트 별 위반 빈도 ranking (별도 skill)
  - **테스트 flaky fix** — `tests/test_session_state.CleanupStaleRunsTests` 2건 pre-existing 별도 Task-ID 로 fix
  - **prose 텍스트 분석 강화** — 현재 regex 기반. semantic 분석 (key 단어 다양성) 도입 검토.

### DCN-CHG-20260430-18
- **Date**: 2026-04-30
- **Rationale**:
  - 사용자 jajang 실전 푸딩 사단 사후 분석 보고 (이전 세션 사용자 직접 리서치 결과):
    - PRD: "30초 녹음 → 부모 음색 자장가 (90초 이내, 60% 부모 인식)"
    - 후보 4개 모델 (OpenVoice V2 / F5-TTS / RVC / CosyVoice) 비교 검증을 "M0 마일스톤" 으로 미룸
    - M0 한 번도 실행 안 됨 — `docs/reference.md` §1, §2, §9 전부 `[미기록]`
    - architect 가 추상 인터페이스 (`VoiceInferenceClient ABC`) + `MockInferenceClient` 만으로 SYSTEM_DESIGN_READY 통과
    - engineer 가 F1~F14 전체 구현 (PR #143/#144/#145 까지)
    - 모바일 → API → Mock 추출 → 로컬 저장 → 재생 데이터 플로우 동작
    - 그러나 *실제 voice cloning 호출 0회* — 어떤 입력이든 5프레임 무음 mp3 base64 하드코딩
    - 사용자 직접 WebFetch 리서치 결과: 후보 4개 모두 *허밍 합성 불가* (speech TTS only). PRD 시나리오 자체가 2026 기준 불가능.
  - 진단:
    - plan-reviewer 가 PRD 단계에서 잡았어야 함 (차원 8 = 기술 실현성). 그런데 도구가 Read/Glob/Grep 만 — *외부 사실 검증 수단 부재* → "M0 에서 검증한다" 조건부 약속을 그대로 통과시킴.
    - architect SYSTEM_DESIGN 가 "M0 이후 결정" placeholder + 추상 ABC 만으로 통과 → 핵심 가치 0% 검증 상태에서 구현 진입.
    - validator(Design) 도 placeholder 가 PRD Must 직결인지 검사 안 함 → 추상 인터페이스 통과.
  - "미래의 약속은 검증이 아니다" — Spike 1개 실측이 PRD/SD 통과 *전* 게이트.
- **Alternatives**:
  1. *옵션 1 — plan-reviewer 에 WebFetch 추가만*. 도구는 생기지만 *조건부 약속 탐지 룰* 없으면 같은 함정. 차순위.
  2. *옵션 2 — architect Spike Gate 만 추가*. PRD 단계 validation 누락 → plan-reviewer 단계에서 같은 사단. 차순위.
  3. **(채택) 옵션 3 — 3 단 동시 처방** — plan-reviewer (WebFetch + 외부 검증 + 조건부 약속 탐지) + architect (Spike Gate) + validator(Design) (Placeholder Leak). 사용자 직접 권고 정합.
- **Decision**:
  - 옵션 3 채택. 3 agent 강화 + 공통 지침 13 agent 동시 박음.
  - **plan-reviewer**:
    - tools 에 WebFetch / WebSearch 추가
    - 차원 8 §8.1 외부 검증 의무 (PRD 명시 외부 의존 1개당 공식 문서 1회 fetch)
    - 차원 8 §8.2 조건부 약속 자동 탐지 ("M0 에서 검증" / "후보 N개 비교 후 선정" / "X 안 되면 Y fallback" → Must 직결 시 FAIL)
    - 산출물에 `EXTERNAL_VERIFIED` 섹션 의무
  - **architect/system-design**:
    - Spike Gate 신설 — 추상 ABC + Mock 만으로 SYSTEM_DESIGN_READY 통과 금지
    - PRD Must 직결 외부 의존 spike 1개 실측 의무 (5~10 라인 minimal example + 공식 문서 검증)
    - Spike PASS 시 concrete 구현 + sdk.md 갱신 / FAIL 시 TECH_CONSTRAINT_CONFLICT
  - **validator/design-validation**:
    - Placeholder Leak 룰 (계층 A) — `[미기록]` / `[미결]` / `M0 이후` / `NotImplementedError` placeholder 가 PRD Must 핵심 가치 직결 시 → DESIGN_REVIEW_FAIL
    - Spike Gate 정합 검증
  - **공통 지침** — 13 agent 권한 경계 절에 동일 1줄 박음:
    - "목표 달성에 가용 도구·권한·정보 부족 시 *추측 진행 X*. 메인 Claude 에게 (a) 무엇이 부족 (b) 왜 필요 (c) 어떻게 얻는지 명시 요청 후 진행"
    - Karpathy 원칙 1 (Think Before — surface assumptions) 의 *권한/툴 측면* 확장
- **Follow-Up**:
  - **jajang 후속** — 본 변경 적용 후 jajang PRD 재호출 시 plan-reviewer 가 voice cloning 외부 검증 발화 + "M0 검증" 패턴 잡는지 측정.
  - **미래 함정 기록** — `docs/process/governance.md` 에 jajang 사례 case study 추가 검토 (별도 Task-ID).
  - **회귀 측정** — 30일간 다른 프로젝트에서 동일 사단 (placeholder + Mock 통과) 발생 여부 모니터.

### DCN-CHG-20260430-17
- **Date**: 2026-04-30
- **Rationale**:
  - 사용자 forrestchang/andrej-karpathy-skills 분석 + dcness agent 에 분배 삽입 요청.
  - Andrej Karpathy 의 LLM coding pitfalls 관찰 정합 — "wrong assumptions / hidden confusion / overcomplicate / orthogonal edits / weak success criteria".
  - dcness 의 기존 agent 룰들이 이 원칙들과 *부분* 정합 ("추측 금지", "수정 범위 엄수" 등) 이지만 *구체 운영 방식* 부재. LLM 의 압축/추측/over-engineer 본능을 prompt 텍스트만으로 막기 어려운 문제는 DCN-CHG-20260430-15 에서 이미 인지됨 (echo 룰 강화).
- **Alternatives**:
  1. *옵션 1 — 글로벌 CLAUDE.md 에 4 원칙 박기*. 단순. 단 dcness 는 plugin 으로 다른 프로젝트에 배포되므로 글로벌 CLAUDE.md 외 agent 별 inject 가 정확. 차순위.
  2. *옵션 2 — agent 1개에 통합*. 모든 agent 가 1 file 참조. 분리 책임 위반 + 각 agent 의 *적합한* 원칙만 박는 fine-grained 안 됨. 기각.
  3. **(채택) 옵션 3 — agent 별 적합한 원칙 분배 (중복 허용)** — 사용자 매핑 (1→planner, 2→architect, 3→engineer) 우선 + 4 (test-engineer 주요) 추가 + 나머지 agent 에 적합한 원칙 보조 삽입.
- **Decision**:
  - 옵션 3 채택. 10 agent 동시 강화.
  - 분배 매트릭스:
    | Agent | 주요 원칙 | 보조 원칙 |
    |---|---|---|
    | product-planner | 1 Think Before | 4 Goal-Driven Spec |
    | architect | 2 Simplicity First | 1, 4 |
    | engineer | 3 Surgical Changes | 2, 4 |
    | test-engineer | 4 Goal-Driven Execution | 1 |
    | validator | — (정합 강화) | 1, 4 |
    | pr-reviewer | — | 3, 1 |
    | security-reviewer | — | 1, 4 |
    | designer | — | 2, 1 |
    | ux-architect | — | 1, 2 |
    | qa | 1 Think Before Triaging | 4 |
  - 각 agent 의 기존 룰 (예: planner 의 "추측 금지", engineer 의 "수정 범위 엄수") 을 Karpathy 원칙의 *구체 운영 방식* 으로 강화. 별도 신설 X — 기존 룰 정합 강화.
  - 출처 링크 1회 인용 (각 agent 첫 Karpathy 절에).
  - DCN-CHG-30-15 (echo 룰 should → MUST) 와 동일 정신 — prompt 텍스트의 신뢰성 격상.
- **Follow-Up**:
  - **jajang 실전 푸딩 측정** — 첫 1~2 사이클에서 Karpathy 원칙 발화 확인. 특히:
    - product-planner 가 가정 명시 / 다중 해석 제시하는가
    - architect 가 단순화 push back / "200줄 → 50줄 가능?" self-check 하는가
    - engineer 가 인접 코드 안 건드리는가 (실측 위반 사례 수집)
    - test-engineer 가 모호한 spec 에 SPEC_GAP_FOUND emit 하는가
  - **회귀 시 강화 추가 검토** — 위반 사례 수집되면 mechanical enforcement (helper-side 등) fallback.

### DCN-CHG-20260430-16
- **Date**: 2026-04-30
- **Rationale**:
  - 사용자 dcness 실전 푸딩 (jajang 진입) 직전 architect / engineer / test-engineer / reviewer agent 강화 요청.
  - 핵심 요구 5건:
    1. **DDD 기반 데이터 도메인 모델 *선정의*** — 시스템 설계 *전*에 도메인 모델 확정. 추후 갈아엎기 비용 회피.
    2. **Clean Arch (Robert Martin) + SOLID 5** — 가급적 준수. 특히 DIP 는 조심스럽게 사용하되 *필요한 곳엔 반드시*.
    3. **시스템 디자인 문서 300줄 cap + 상세 도면 링크 분리 + 항상 현행화** — 컨텍스트 부담 / 변경 충돌 / 집중력 회피.
    4. **모듈 분할 = 테스트 단위** — test-engineer 가 명확한 테스트 짤 수 있는 범위.
    5. **Domain Model 문서 SSOT + 수정 권한 격리** — 구현 관련 엔지니어 (engineer / test-engineer / validator / pr-reviewer / security-reviewer) 가 read 가능, 수정 시 architect escalate.
  - 사용자 추가 통찰 — 전화앱 도메인 예시:
    - 녹음 (독립) ← 요약 (재생 시 녹음 의존) ← 기록 (요약·녹음 알아야 UI 분기)
    - 역방향 cascade (녹음 삭제 시 Pending 요약 같이 삭제) → DIP listener interface 로 의존 방향 보존
    - "누가 봐도 납득 가능한 논리로 의존성 설정 + 깨지지 않도록".
- **Alternatives**:
  1. *옵션 1 — 단일 agent (architect) 만 강화*. 영향 작음. 단 engineer/test-engineer 가 도메인 모델 모르고 구현 → invariant 위반 위험. 기각.
  2. *옵션 2 — domain-model.md 를 architect 외 agent 도 수정 가능*. 빠른 변경. 단 도메인 SSOT 가 분산되어 invariant 깨짐. 사용자 명시 거부 ("수정이 필요한 경우 반드시 아키텍쳐에게 에스컬레이션해서 바꿀수 있도록"). 기각.
  3. *옵션 3 — 의무 read 를 engineer 만*. test-engineer 는 의존성 그래프 모르고 단순 입출력 테스트만 짜게 됨. 차순위.
  4. **(채택) 옵션 4 — 9 agent 강화 + 권한 매트릭스** — architect 단독 수정 / engineer + test-engineer 의무 read / validator + pr-reviewer + security-reviewer + 그 외 권한 read. 사용자 매트릭스 그대로 승인.
- **Decision**:
  - 옵션 4 채택. 9 agent 동시 강화.
  - 핵심 산출물:
    - **`docs/domain-model.md` 신규** — DDD 4 요소 (Entity / VO / Aggregate / Domain Service) + invariant + bounded context. architect 단독 수정.
    - **`docs/architecture.md`** + 분리 detail 파일 — 모듈 의존성 인과관계 1줄 의무 + 독립성 자가 검증 표 + DIP interface 모음.
  - 의존성 설계 4 원칙:
    1. 모든 의존성 화살표에 인과관계 1줄
    2. 독립성 자가 검증 표 (단독 lifecycle 가능? / 의존 부재 시 동작? / DIP 필요?)
    3. 역방향 cascade 필요 시 DIP 의무 (직접 import 금지, listener interface)
    4. 누가 봐도 납득 (추측 0)
  - 모듈 = 테스트 단위 = 의존성 1 묶음 3 정합 (충돌 시 testable 우선 — 사용자 룰).
  - 300줄 cap + 현행화 룰 (architect SYSTEM_DESIGN / SPEC_GAP 호출마다 정합 검사).
  - 권한 매트릭스:
    | Agent | 읽기 | 수정 |
    |---|---|---|
    | architect (SD/SPEC_GAP) | 의무 | 권한 (SSOT) |
    | engineer (IMPL) | 의무 (Phase 1) | 금지 → SPEC_GAP escalate |
    | test-engineer | 의무 | 금지 → SPEC_GAP escalate |
    | validator (CODE_VAL) | 권한 | 금지 |
    | pr-reviewer | 권한 | 금지 |
    | security-reviewer | 권한 | 금지 |
- **Follow-Up**:
  - **jajang 실전 푸딩 회귀 측정** — 도메인 모델 + Clean Arch + SOLID 룰이 실제 PR 에서 발화하는지 첫 1~2 사이클 모니터.
  - **domain-model.md 템플릿** — jajang 첫 진입 시 architect SYSTEM_DESIGN 가 빈 prd → domain-model 생성 흐름 측정. 템플릿화 후속 검토.
  - **DIP 남용 vs 미사용 측정** — "필요한 곳엔 반드시" 가 실제 LLM 판단으로 잘 작동하는지 사례 수집. 미작동 시 trigger keyword 추가 검토.
  - **300줄 cap enforcement** — 현재 룰만 박힘. 자동 체크 (linter / gate) 도입 여부 후속 결정.

### DCN-CHG-20260430-15
- **Date**: 2026-04-30
- **Rationale**:
  - dcTest manual smoke 도중 발견 — 메인 Claude 가 `commands/quick.md` "가시성 룰" (DCN-CHG-30-11) 을 *알면서도* prose echo 를 1~2줄로 압축하거나 생략. 사용자 명시 지적 ("이거 원래 그렇게 룰로 설정되 있는데 왜 빠먹음?") 후 메인 자기 진단 — "토큰 절약 습관이 룰을 덮어쓴 케이스".
  - prompt 텍스트 자체는 "필수" 라고 박혀있으나 톤이 *should* 수준 (안티패턴 / 자가 점검 부재). LLM 의 일반 압축 본능 > prompt 텍스트.
  - 위반 누적 효과: /impl-loop multi-batch 환경에서 batch N × 5 step = 5N 회 가시성 누락 → 사용자 ctrl+o 의존 회귀 → conveyor 핵심 가치 (자동 가시성) 붕괴.
- **Alternatives**:
  1. *옵션 B — helper end-step `--echo-summary N` 추가* (stdout 으로 prose 12줄 강제). mechanical 강제. 단 토큰 ~3~5% 추가 (input 측). **사용자 거부** ("저거 출력하면 토큰을 더 많이써?" → 추가 부담 인지 후 prompt 강화 선택).
  2. *옵션 C — 결론 섹션만 stdout (2~4줄)*. 가벼움. 단 본문 발췌 손실 → 가시성 trade-off. 차순위.
  3. **(채택) 옵션 A 강화 — should → MUST + 의무 템플릿 + 자가 점검 + 안티패턴**. prompt 신뢰성 격상. 토큰 추가 0 (현재 룰 준수 비용 그대로). 사용자 발화 ("강제로좀 잘 말하게 해줘") 정합.
- **Decision**:
  - 옵션 A 강화 채택. SSOT = `commands/quick.md` "가시성 룰" 절.
  - 강화 4축:
    1. **MUST 톤** — 🚨 CRITICAL banner + "skip = bug" 명시
    2. **의무 템플릿** — `[<task-id>.<agent>] echo` + `▎` prefix + 결론 enum 줄 (구조 변경 금지)
    3. **자가 점검 4항** — TaskUpdate(completed) 전 확인 체크리스트 (Agent prose read / 결론 섹션 우선 / 5~12줄 / enum 포함)
    4. **안티패턴 4종 명시** — 압축 paraphrase / table 생략 / 결론만 echo / 늦은 echo
  - 5 skill 동일 톤 정합 (quick / impl / impl-loop / qa / product-plan).
  - 토큰 비용 인지 박음 — 3~5% 부담 사용자 룰 1번 (검증) 으로 수용 명시.
  - helper-side 강제 (옵션 B/C) 는 미적용 — 사용자 거부 + prompt 강화 우선 시도.
- **Follow-Up**:
  - **회귀 측정** — 다음 dcTest /impl-loop 실행 시 5 step 모두 의무 템플릿 echo 발화 여부 확인. 회귀 발견 시 옵션 B (helper stdout) fallback 검토.
  - **batch 회 측정** — 본 강화 *후* 30일간 echo 룰 위반 사례 모니터. >0 이면 옵션 B 강제 진입 검토.
  - **prose echo 실측 분량** — dcTest 결과 5~12줄 cap 안에 들어오는지 (cap 위반 = 다른 방향 위반) 측정.

### DCN-CHG-20260430-14
- **Date**: 2026-04-30
- **Rationale**:
  - 글로벌 `~/.claude/CLAUDE.md` 룰 = "태스크 완료 → stories.md 체크. 에픽 완료 → backlog.md 체크". 룰 자체는 존재하나 `/impl` 시퀀스에 *step 으로* 박혀있지 않음.
  - 실제 dcTest epic-01 manual smoke 에서 발견 — src/ 반영 (commit 4b185b9 `feat: greet lang 인자 실 적용`) 됐는데 stories.md Story 1 체크박스 8개 `[ ]` 상태 그대로. backlog.md epic-01 라인도 미체크.
  - 메인 Claude 가 매 batch 마다 stories.md/backlog.md 체크 누락 → 사용자가 별도 명령으로 정리해야 함. 사용자 "하나의 구현루프가 끝나면 이런거 작업하게 해줘" 직접 지시.
- **Alternatives**:
  1. *옵션 1 — engineer agent 가 직접 처리*. engineer 룰 (`src/**` 만) 위반 위험 + agent prompt 비대해짐. 기각.
  2. *옵션 2 — Step 6.5 (pr-reviewer LGTM 후, commit 전)*. 1 PR 에 코드+doc 같이 들어가는 건 동일하나, pr-reviewer 가 doc 변경 검토 못 함 (LGTM 후 추가). 사용자 지정한 잘못 체크 catch 기회 상실. 차순위.
  3. *옵션 3 — Step 7 후 별도 commit/PR*. doc-only PR 추가 — 노이즈 + governance 오버헤드. 기각.
  4. **(채택) 옵션 A — Step 4.5 (engineer IMPL 직후, validator 전)** — 메인이 mechanical edit. validator 는 src/ 만 검증 (doc 무시). pr-reviewer 가 코드 + doc 같이 검토 (체크 누락/오류 catch). 1 PR = 1 batch 완성.
- **Decision**:
  - 옵션 A. engineer 룰 위반 X (메인 직접 edit), pr-reviewer 검토 범위 포함, 1 PR 단위 보존.
  - 위치 = `commands/impl.md` Step 4.5 (Step 4 engineer IMPL ↔ Step 5 validator CODE_VALIDATION 사이).
  - 동작:
    1. batch 파일 경로에서 epic dir + stories.md 위치 추출
    2. batch 가 다룬 Story 의 `[ ]` → `[x]` (batch 메타 또는 파일명 매칭)
    3. 모든 Story `[x]` 면 backlog.md epic 라인도 `[x]`
    4. 부분 진행이면 backlog.md 손대지 않음
  - `/impl-loop` 는 inner /impl 이 알아서 처리 — 추가 변경 불필요.
- **Follow-Up**:
  - **dcTest epic-01 retro 갱신** — 본 변경 적용 *후* 누적된 미체크 stories.md 를 한번에 sync (별도 Task-ID, 본 변경 범위 외).
  - **batch 메타 컨벤션** — batch 파일 안 `## 관련 Story: Story 1.3` 명시 컨벤션은 architect TASK_DECOMPOSE 산출 시 박힐지 후속 검토. 현재는 메인이 batch 파일명/제목으로 매칭.
  - **회귀 검증** — 다음 dcTest /impl-loop 실행 시 매 batch 마다 stories.md 체크 동기화 자동 발화 확인.

### DCN-CHG-20260430-13
- **Date**: 2026-04-30
- **Rationale**:
  - 사용자 통찰 (manual smoke 도중) — "근데 이미 아키텍트가 모듈 나누고 왔는데 왜 B1에서 아키텍트부터 다시 시작해? 원래 루프에 있던 의미는 없으면 다시하고 오라는거였고 패스되는거였을텐데."
  - RWHarness plan_loop 원래 의도 = state-aware skip:
    ```
    impl_loop 진입:
      if 산출물 (MODULE_PLAN.md) 있음 → 통과 + test-engineer 직진
      else → architect MODULE_PLAN 호출 ("다시 하고 와")
    ```
  - dcness 가 사다리 #2 (state hole — checkpoint 보존 의무 자리) 회피하느라 분기 자체를 없앤 결과 *효율성도 함께 잃음*. 매 batch 마다 무조건 MODULE_PLAN 호출 = LLM 비용 / 시간 N×.
  - architect TASK_DECOMPOSE 가 이미 batch 산출 시 ## 생성/수정 파일 / ## 인터페이스 / ## 의사코드 / ## 결정 근거 박는 컨벤션 일부 — MODULE_PLAN 수준 detail 충족이면 *재설계* 의미 없음.
- **Alternatives** (사용자 의문 정합 4 옵션):
  1. *옵션 A — 현재 유지* (매 batch 마다 MODULE_PLAN 호출). 보수적 / 비효율. 기각.
  2. *옵션 B — batch 충분 상세 시 skip* (자동 판정). detail 판정 룰이 새 hole 후보 자리. 기각.
  3. *옵션 C — helper 단 격리* (`dcness-helper batch-status`). 자동화 + skill prompt 의 분기 추가 0. 단 helper 안 분기 추가. 차순위.
  4. **(채택) 옵션 D — 컨벤션 + 메인 자율** — TASK_DECOMPOSE 가 batch 산출 시 `MODULE_PLAN_READY` 마커 박음. /impl Step 2.0 에서 grep 1줄 — 마커 충족 시 skip / 부재 시 정상 호출. 분기 추가 = 1 (skip vs 호출 / grep 단순 검사). branch-surface-tracking 임계 미달.
- **Decision**:
  - 옵션 D. 사용자 발화 ("D 가 맞지 이게 우리 철학이잖아") 정합.
  - **컨벤션 박는 자리** = `agents/architect/task-decompose.md` 의 "각 impl 파일 형식 의무" 절. architect TASK_DECOMPOSE 가 prose 산출 시 batch 파일 마지막에 `MODULE_PLAN_READY` 마커 박음.
  - **검사 자리** = `commands/impl.md` Step 2.0. `grep -q "MODULE_PLAN_READY" "<batch>"` 1줄. SKIP_MODULE_PLAN=true 시 batch 파일을 MODULE_PLAN prose 로 cp + Step 3 (test-engineer) 직진.
  - **catastrophic 훅 §2.3.3 정합**: engineer 직전 architect-MODULE_PLAN.md (or LIGHT_PLAN.md) 안 READY_FOR_IMPL grep 검사. SKIP 케이스도 batch path 를 cp 했으므로 자연 정합 (batch 파일이 architect-MODULE_PLAN.md 위치에 박힘).
  - **권장 vs 의무**: 본 컨벤션은 *권장*. 마커 안 박힌 batch 도 정상 호출 (옵션 A 동작). dcness 정신 정합 — agent 자율 + 메인 자율.
- **Follow-Up**:
  - **(별도 Task)** /impl-loop 의 resume 메커니즘 — 본 마커 + 코드 검사 결합으로 이미 구현된 batch 검출 (사용자 이전 질문 정합).
  - **(측정)** 30 batch 산출 후 `MODULE_PLAN_READY` 마커 박힘 비율. 80%+ 면 컨벤션 정합. 그 미만이면 task-decompose prompt 강도 추가 보강.
  - **(branch-surface-tracking 자가 점검)**: 본 PR 이 추가하는 분기 = 1 (impl Step 2.0 의 grep 분기). hole 후보 자리 = batch 파일에 마커 박는 의무 자리 1곳 (TASK_DECOMPOSE prompt 강화). warning 임계 (3 회/30일) 미달.

### DCN-CHG-20260430-12
- **Date**: 2026-04-30
- **Rationale**:
  - 사용자 manual smoke (`/dcness:impl-loop yolo`, 5 batch v0.3) 도중 발견 — 메인이 batch-1 진입 시 INNER_RUN 시작 + begin-step architect MODULE_PLAN + Agent 호출까지 진행했지만 *inner 5 sub-task TaskCreate* 가 누락. 외부 task list 에 "impl-1: ..." 1개만 보이고 inner 진행 (MODULE_PLAN / test-engineer / engineer / validator / pr-reviewer) 무가시.
  - 사용자가 명시 instruction ("각 batch 진입 시 /impl 의 5 sub-task TaskCreate 의무, inline skip 금지") 으로 워크어라운드 → 메인이 `b1.architect: MODULE_PLAN` 등 prefix 컨벤션으로 등록 → 사용자가 "오 잘되네 이런식으로 표시해주면 좋겠다" 피드백.
  - 결함 = `/impl-loop.md` Step 2 의 명시 강도 부족. "→ /impl 의 Step 1~7 시퀀스 호출" 만 박혀 있어 메인이 inline skip 가능. 사용자가 매번 명시 발화 안 해도 되도록 default 컨벤션화 필요.
- **Alternatives**:
  1. *현 prompt 유지 + 매번 사용자 명시* — 매번 부담. 기각.
  2. *helper 단에서 sub-task 강제* — Task tool 은 메인이 호출 (helper subprocess 가 호출 못 함). 기각.
  3. **(채택) skill prompt 의무 강도 ↑** — Step 2 에 ⚠️ 경고 ("inline skip 금지") + `b<i>.<agent>` prefix 컨벤션 + 사용자가 본 가시성 형식 그대로 박음. /impl.md Step 1 도 같은 강도.
- **Decision**:
  - 옵션 3.
  - **prefix 컨벤션 = `b<i>.<agent>: <mode_or_state>`** (예: `b1.architect: MODULE_PLAN` / `b3.engineer: IMPL`). 사용자가 본 형식 그대로 default. /impl-loop 안에서만 prefix, /impl standalone 시 prefix 없음.
  - **outer task = `impl-{i}: <짧은 제목>`** (DCN-30-6 의 컨벤션 유지).
  - **batch 종료 시 inner sub-task 정리 vs 보존**: 메인 자유. b1 끝났을 때 `b1.*` 들 ✓ 표시 후 b2 시작 시 새 sub-task 등록. UX 단순.
- **Follow-Up**:
  - **(별도 Task — v2)** `/impl-loop` resume 메커니즘 — batch 의 ## 생성/수정 파일 자동 검사로 이미 구현된 batch skip. 사용자 질문 정합 ("이미 구현된 batch 인지 어떻게 판단?").
  - **(별도 Task — measurement)** /impl-loop run 후 inner sub-task 등록률 측정. 100% 면 본 fix 정합. 그 미만이면 prompt 강도 추가 보강.

### DCN-CHG-20260430-11
- **Date**: 2026-04-30
- **Rationale**:
  - 사용자 manual smoke (`/product-plan v0.3`) 도중 — DCN-CHG-30-2 의 "stderr 자동 prose 요약" 이 helper 단에선 적용됐지만 사용자가 본 transcript 의 핵심 정보 (Agent 의 prose response — v0.2→v0.3 diff 12 항목) 는 여전히 `(ctrl+o to expand)` collapsed.
  - 원인 = CC 의 Task tool / Bash tool 출력이 표준 collapsed 동작. helper stderr 요약은 Bash output 안에 들어가서 같이 collapsed. 사용자가 ctrl+o 안 누르면 메인이 받은 prose 본문 안 보임.
  - **두 채널 동시 보강 필요**:
    1. helper stderr 의 추출 정밀도 ↑ (결론 섹션 우선) + cap 확장
    2. skill prompt 단에서 메인 *text reply* (Bash X) 로 echo 의무 — text 는 collapsed 안 됨.
- **Alternatives**:
  1. *현 stderr 요약만 유지* — 사용자 ctrl+o 의존 ↑. smoke 피드백 정합 X. 기각.
  2. *full prose 자동 cat (Bash output)* — transcript 폭발 + 여전히 collapsed. 기각.
  3. **(채택) 두 채널 동시** — helper extractor 개선 (결론 섹션 우선 + cap 확장) + skill prompt 단 메인 text echo (5~12줄). text reply 는 CC 가 collapsed 안 함 — 자동 가시.
- **Decision**:
  - 옵션 3.
  - **`_CONCLUSION_HEADER_RE` 정규식**: `결론` / `결과` / `요약` / `변경 요약` / `변경 사항` / `변경 내용` / `Conclusion` / `Summary` / `Result` / `Key Changes?` / `Outcome` / `Verdict` 매칭. `\b` 미사용 (한국어 word boundary 무효). generic `변경` 단독 매칭은 차단 (`## 변경 분석` 같은 헤더 회피).
  - **cap 확장**: 8줄 / 600char → 12줄 / 1200char. 결론 섹션이 보통 5~10줄이라 12줄 cap 으로 흡수 가능. 단 char cap 1200 으로 hard limit.
  - **skill prompt 가시성 룰 절 신규**: 매 Agent 호출 후 메인이 *text reply* (markdown 정합 보존) 로 prose 의 결론/요약 섹션 본문 echo. helper stderr 요약과 동시 = 사용자 가시성 최대. verbose 회피 위해 5~12줄 cap.
  - **5 skill 일괄 적용**: qa / quick / product-plan / impl / impl-loop. /smart-compact / /init-dcness / /efficiency 는 read-only 라 비대상.
- **Follow-Up**:
  - **(별도 Task — 측정)** smoke 후 사용자 ctrl+o 누름 빈도 정성 측정. 본 변경 후 0~1 회/skill run 이면 정합. 그 이상이면 cap 추가 확장 또는 다른 채널 검토.
  - **(별도 Task — 후속)** "## 결론" 섹션 위치가 prose 마지막에 안 박힌 케이스 — agent prose writing guide 정정 (각 agent.md 의 system prompt 에서 "결론은 prose 마지막에 명시" 강조).

### DCN-CHG-20260430-10
- **Date**: 2026-04-30
- **Rationale**: 8 skill 흡수 + 5 PR 누적 후 사용자 요청 — "재인스톨 가이드 + 스킬별 도그푸딩 재료 + 발화 prompt". 매 smoke 마다 사용자가 발화 만들고 기대 동작 추론하는 비용 ↑. 가이드 1 문서로 표준화 가치.
- **Decision**:
  - `docs/process/manual-smoke-guide.md` 단일 파일 — 사전 준비 (plugin 재설치 + RWHarness 충돌 회피) + 8 skill 발화 + 검증 체크리스트 + 트러블슈팅 + 보고 양식.
  - dcTest 자체 변경 X — 현 상태 (greet 가드 + calc subtract + prd + architecture + ux-flow + milestones) 가 8 skill smoke 에 충분.
  - **/efficiency dcTest 외 추천**: dcTest 가 CC 사용 history 부재 → "분석할 세션 없음". dcness repo 에서 시도 권장 명시.
- **Follow-Up**:
  - **(별도 Task — 측정)** 사용자 smoke 결과 누적 후 가이드 정합 갱신 (실 동작과 다른 항목 발견 시).
  - **(별도 Task — automation)** 사용자 보고 양식 → 자동 회귀 테스트 변환 (현재는 manual + `tests/test_multisession_smoke.py` 일부만).

### DCN-CHG-20260430-09
- **Date**: 2026-04-30
- **Rationale**: README skill 표가 7개 시점 stale. /efficiency 흡수로 8개. 또 yolo/worktree keyword 가 행동형 skill 만 적용되는데 README 가 "모든 skill 공통" 으로 표기 → 읽기형 (`/qa` `/smart-compact` `/efficiency`) 에서 혼동 가능.
- **Decision**: 표 1 row 추가 + 행동형/읽기형 분류 명시. docs-only.
- **Follow-Up**: 없음 (정합성 갱신).

### DCN-CHG-20260430-08
- **Date**: 2026-04-30
- **Rationale**:
  - 사용자 요청 — `https://github.com/jha0313/skills_repo` 검토 + 흡수 가치 평가.
  - 3 skills 평가:
    1. `improve-token-efficiency` ⭐⭐⭐ — proposal §5 Phase 4 fitness (도그푸딩 비용 측정) 와 자연 정합. dcness 의 `.metrics/heuristic-calls.jsonl` (heuristic enum 추출 telemetry) 와 별개로 *CC 세션 단위 비용 분석* 보강. 가치 ↑.
    2. `ai-readiness-cartography` ⭐⭐ — governance 자가 점검 도구. 단 score.py 룰이 dcness 자체 룰 (branch-surface-tracking / Document Sync) 과 일부 중첩 + dcness 정체성 (RWHarness fork) 과 layer 다름. 외부 plugin 추천이 적합.
    3. `presentation_slides` ⭐ — YouTube 발표용 HTML. dcness 무관.
  - `improve-token-efficiency` 1개만 흡수. as-is fork + dcness 패턴 wrapper.
- **Alternatives**:
  1. *모두 무시* — 기존 dcness 8 skill 로 충분. 단 비용 측정은 proposal §5 핵심 fitness 항목, 누락이 흠. 기각.
  2. *전체 3 skill 흡수* — presentation_slides 가 정체성 무관, ai-readiness 도 정합 검토 비용 ↑. 기각.
  3. **(채택) 1개 (improve-token-efficiency) 만 흡수**. 4 script as-is fork (검증된 stdlib only) + dcness 패턴 (wrapper script + skill prompt + helper 진입 옵션). 출처 attribution 명시.
- **Decision**:
  - 옵션 3.
  - **as-is fork (rewrite X)**: 4 script (analyze_sessions / build_dashboard / detect_patterns / build_patterns_dashboard) 그대로 `harness/efficiency/` 패키지에 복사. 출처 = `harness/efficiency/__init__.py` docstring + `commands/efficiency.md` 첫 줄 명시.
  - **dcness fix 2건**:
    1. `encode_repo_path` 의 `.` → `-` 추가 — CC 실 인코딩 룰 (예: `/Users/dc.kim/project/dcNess` → `-Users-dc-kim-project-dcNess`) 정합. 원본은 `/` 만 변환 → 사용자 `dc.kim` 같은 dotted username 환경에서 `[error] sessions dir not found` 발생. 사용자 환경 검증으로 발견.
    2. `price_for` prefix 매칭 — `claude-haiku-4-5-20251001` (dated suffix), `claude-opus-4-7[1m]` (variant tag) 같은 신모델 ID 자동 흡수. 원본은 exact 매칭 후 Opus default fallback → haiku 사용량이 Opus 가격으로 과추정.
  - **read-only 분석 도구라 catastrophic 룰 비대상**: agent 호출 X, prose 종이 X, PreToolUse 훅 §2.3 검사 비대상. helper protocol (begin-run / end-run) 은 *선택* (.steps.jsonl 추적 원할 때).
  - **wrapper subcommand 5개**: analyze / dashboard / patterns / patterns-dashboard / full. `full` = analyze → dashboard chain 편의.
- **Follow-Up**:
  - **(별도 Task — 측정)** 30일 dcness 도그푸딩 후 `/efficiency` 자가 사용 빈도. 최소 5회/주 사용 안 되면 skill prompt description 정정.
  - **(별도 Task — 가격 갱신)** Anthropic 신모델 출시 시 `PRICING` dict 한 줄 추가.
  - **(별도 Task — 후속 흡수 검토)** 30일 후 `ai-readiness-cartography` 재평가 — dcness governance 와 정합 가능한지 정량 검토.
  - **(별도 Task — upstream 기여)** dcness fix 2건 (encode_repo_path + price_for) 을 jha0313 upstream 에 PR 제안 (선택).

### DCN-CHG-20260430-07
- **Date**: 2026-04-30
- **Rationale**:
  - 작업 누적 7 PR 후 skill 7개 보유. README 가 1~3 skill 시점 표현 (개별 항목 나열) 으로 stale. 사용자 / 외부 reader 의 skill discoverability ↓.
- **Decision**:
  - README 에 skill 표 1개 추가 (7개 entry + 역할 1줄). 공통 keyword (yolo / worktree) 도 별도 명시.
  - 후속 항목 갱신: DESIGN_VALIDATION 완료 표시, /impl/impl-loop 완료 표시, /ux 만 후속으로 남김.
- **Follow-Up**: 없음 (docs 정합성 갱신).

### DCN-CHG-20260430-06
- **Date**: 2026-04-30
- **Rationale**:
  - 사용자 manual smoke (/product-plan v0.2 → "하나씩 순차로 구현해") 도중 발견 — /product-plan 종료 시 architect TASK_DECOMPOSE 산출 = 5 impl batch list. 그러나 후속 정식 impl 루프 (orchestration §2.1) 호출 진입점 부재 → 메인이 즉흥 처리. 외부 task 5 개만 등록 (batch 별), 각 batch 안 5 sub-task (plan/test/impl/validate/review) 누락 → 진행 가시성 ↓.
  - 사용자 지적: "근데 이게 맞냐 impl마다 단계를 task로 잡아야지". 정확.
  - 갭 = orchestration §3.1 의 "→ 구현 루프 §2.1 (별도)" 가 *concrete entry skill* 부재.
- **Alternatives**:
  1. */product-plan 자체에 impl 루프 chain 박기* — /product-plan 의 spec/design 책임이 폭증. 단발 impl batch 만 처리하고 싶을 때 과한 작업. 기각.
  2. */quick 으로 batch 처리* — /quick 은 light path (test-engineer 생략, BUGFIX_VALIDATION 사용). batch 처리엔 부족 (test 없음 + 회귀 위험). 기각.
  3. **(채택) 신규 skill 2 개**: /impl (per-batch 정식 루프) + /impl-loop (multi-batch wrapper). /impl 은 orchestration §2.1 그대로 5 단계. /impl-loop 은 batch list 받아 각 batch 마다 /impl chain + clean 자동 진행.
- **Decision**:
  - 옵션 3. 두 skill 신규.
  - **/impl 시퀀스** = orchestration §2.1 정합. PreToolUse 훅 §2.3.1 / §2.3.3 자연 정합.
  - **5 sub-task per batch** — 각 batch 안 architect MODULE_PLAN / test-engineer / engineer / validator / pr-reviewer 가 task list 로 보임. 사용자 지적 정합.
  - **clean 자동 commit/PR**: /quick Step 7a 패턴 정합 — finalize-run JSON 집계 + clean 판정 + graceful degrade.
  - **yolo 모드**: /quick / /product-plan 동일 keyword + auto-resolve 매핑.
  - **/impl-loop wrapper**: 각 batch 마다 /impl 의 inner run 별도 (begin-run impl-batch-N). outer run 은 batch list 진행 메타만 추적.
  - **caveat 멈춤**: clean 아니면 멈춤 + 사용자 위임. yolo 도 has_must_fix true 시 멈춤 (hard safety).
- **Follow-Up**:
  - **(별도 Task)** /impl-loop 의 multi-batch resume — caveat 멈춤 후 재실행 시 처음부터 다시 도는 거 정정 (이미 commit 된 batch skip).
  - **(별도 Task)** batch 간 의존성 처리 (병렬 가능 / 직렬 강제 자동 판단). 현재 v1 = 무조건 직렬.
  - **(별도 Task)** /product-plan 종료 시 "/impl-loop 진입" 옵션 자동 제안 (현재는 사용자 명시 발화 필요).
  - **(측정)** /impl-loop 의 N batch 자동 진행률 + 멈춤 횟수. 30 회 후 yolo 매트릭스 보강.

### DCN-CHG-20260430-05
- **Date**: 2026-04-30
- **Rationale**:
  - 사용자 manual smoke 도중 (`/product-plan` 실행) 발견 — 설계 루프가 SYSTEM_DESIGN_READY 후 곧바로 TASK_DECOMPOSE 진입. 사용자 지적: "아키텍트 루프의 최종은 벨리데이터가 검증하고 필요하면 다시 아키텍트가 재설계해서 최종 설계 리뷰 완료까지" — 검증 step 누락.
  - 검증 결과: `agents/validator/design-validation.md` 가 *이미 존재* (enum: DESIGN_REVIEW_PASS / FAIL / ESCALATE) — agent 정의는 있는데 *orchestration §3.1 + /product-plan skill 시퀀스에 호출 자리 없음*. 갭.
  - 결과: SYSTEM_DESIGN 후 검증 없이 TASK_DECOMPOSE → 구현 가능성 / 스펙 완결성 / 리스크 검증 안 된 채 impl batch 분해. 잘못된 설계가 batch 단계로 흐르면 후속 impl loop 에서야 발견 → 비싼 rollback.
- **Alternatives**:
  1. *DESIGN_VALIDATION step 도입 안 함* — 사용자 지적 무시. 기각.
  2. *DESIGN_VALIDATION 을 architect 자체에 inline* (architect SD 가 자가 검증). 동일 LLM 의 자가 검증은 검증 가치 ↓. 기각.
  3. **(채택) validator DESIGN_VALIDATION step 신규** — orchestration §3.1 mermaid 에 노드 + FAIL 루프 추가, /product-plan skill Step 6.5 신규, catastrophic §2.3.5 (TD 직전 DESIGN_REVIEW_PASS 필수) hooks.py 강제. cycle 한도 2 (FAIL → SD 재진입).
- **Decision**:
  - 옵션 3. 시퀀스 위치 = SD 와 TD 사이.
  - **catastrophic §2.3.5 강제 조건**: `architect-SYSTEM_DESIGN.md` 가 존재할 때만 발동 — 단순 `MODULE_PLAN` 후 TASK_DECOMPOSE 직접 호출 등 다른 진입 경로엔 미적용 (그 케이스는 §3.4 직접 호출 시퀀스).
  - **cycle 한도 2 일관성**: PLAN_REVIEW_CHANGES_REQUESTED (2) / UX_VALIDATION FAIL (2) 와 동일. 초과 시 사용자 위임.
  - **enum 매트릭스**: DESIGN_REVIEW_PASS / DESIGN_REVIEW_FAIL / DESIGN_REVIEW_ESCALATE — 기존 agent 정의 그대로.
  - **task 등록 6 → 7**: /product-plan Step 1 갱신.
- **Follow-Up**:
  - **(별도 Task — PR 후속)** `/impl` skill 신규 — TASK_DECOMPOSE 의 impl batch 1개 받아 정식 impl 루프 (architect MODULE_PLAN → test-engineer → engineer → validator CODE_VALIDATION → pr-reviewer).
  - **(별도 Task — PR 후속)** `/impl-loop` skill — impl batch list sequential /impl chain.
  - **(별도 Task — 측정)** 30 회 /product-plan run 후 DESIGN_REVIEW_FAIL 비율. 30%+ 면 architect SYSTEM_DESIGN 의 prompt 또는 input 형식 정정 (FAIL 잦으면 SD 자가 검증 강화 후보 — cycle 비용 vs 검증 정확도 트레이드오프).

### DCN-CHG-20260430-04
- **Date**: 2026-04-30
- **Rationale**:
  - 2026-04-30 RWH 에이전트의 트렌드 분석 (DCN-CHG-20260430-03 동반 토론) 에서 사실 오류 발견 — "DC 의 signal_io.interpret_signal = agent prose → haiku" 단정. 검증 결과: dcness 의 실 호출 경로는 `interpret_with_fallback(prose, allowed)` 에서 `llm_interpreter=None` 디폴트라 LLM 호출 0 (heuristic-only). `harness/llm_interpreter.py` 는 dead code (테스트만 import).
  - 사실 오류는 `harness/llm_interpreter.py` 파일 존재 + signal_io docstring "프로덕션 = haiku 주입" 표현이 미래 reader 에 같은 오해 유발. 이미 RWH 에이전트가 같은 오해.
  - dcness 가 사실은 RWH 가 본 [2025 메타 LLM] 단계가 아닌 [2025+ heuristic-only + 메인 cascade] 위치 — 한 발 더 가벼움. 단 codebase 가 그 정착을 명시 못 함.
  - 또 사용자 명시 권한 — "필요없는거 지우고 남은거 해줘" — dead code 제거 mandate.
- **Alternatives**:
  1. *llm_interpreter.py 보존 (future-proof)* — dead code 유지. CLAUDE.md 룰 위반 ("don't add features for hypothetical future requirements"). proposal §2.5 원칙 1 (룰 순감소) 위반. 기각.
  2. *deprecate 만 + 코드 보존* — dead path 그대로, docstring deprecation. 같은 오해 재발 위험. 기각.
  3. **(채택) 완전 폐기** — `llm_interpreter.py` + `test_llm_interpreter.py` 삭제. `interpret_with_fallback` 의 `llm_interpreter=` 인자 제거. docstring 정정. 미래 reintroduce 시 git history 에서 복원 가능.
- **Decision**:
  - 옵션 3. dead code 완전 삭제.
  - **함수명 `interpret_with_fallback` 보존** — 외부 호출자 (`harness/session_state.py` `_cli_end_step`) 변경 비용 ↓. docstring 에 "함수명에 _with_fallback 잔존, 실제론 heuristic-only" 명시.
  - **proposal §0 정착 박스** — `docs/status-json-mutate-pattern.md` 의 *원안 (메타 LLM 비전)* 은 historical 가치로 보존, 단 §0 박스에 정착 결정 + 4 이유 + 트렌드 위치 명시. 미래 reader 가 같은 오해 회피.
  - **trend 위치 재정의**: RWH ([2024] regex parser) → 본 proposal 원안 ([2025] 메타 LLM judge) → **dcness 정착 ([2025+] heuristic-only + 메인 cascade)** → structured tool output ([2026] 미래). 한 정거장 더 가벼움 = RWH 에이전트가 본 그래프상 dcness 의 실제 위치.
  - **DI swap option 보존** — `interpret_signal(..., interpreter=)` 의 `interpreter` 인자는 보존 (테스트용). 단 docstring 명시 "프로덕션 미사용".
- **Follow-Up**:
  - **(별도 Task — 측정)** 30일 도그푸딩 후 휴리스틱 hit rate 측정. 80%+ = 정당. 그 미만 = agent prose writing guide 정정 (LLM fallback 재도입 X — agent 가 enum 명시하도록 가이드).
  - **(별도 Task — 6개월)** Anthropic structured tool output 안정화 + Opus 5 출시 시점 재검토. 그때 schema 강제로 갈아탈 가치 있는지 평가. 단 본 결정 (heuristic-only) 은 그 시점까지 유효.
  - **(별도 Task — 미래 reintroduce 시)** git history 에서 `llm_interpreter.py` 복원 가능. 단 도입 동기 = 휴리스틱 fail rate 30%+ 측정 데이터 + 정량 비교.

### DCN-CHG-20260430-03
- **Date**: 2026-04-30
- **Rationale**:
  - 2026-04-30 RWH 에이전트가 dcness 의 git log (3일 / 82 commit) 분석 + 진단 제출. 핵심 4 메시지:
    1. dcness 의 prose-only 가 사다리 #1 (alias) 정조준 끊음 = 확정.
    2. 사다리 #2 (state hole) 와 #3 (sweep) 는 dcness 가 *분기 자체 폐기* 로 회피 (해결 아님).
    3. DCN-CHG-41/42 가 사다리 시그널 (PYTHONPATH wrapper → cache glob fallback patch).
    4. RWH 가 더 이상 진화 못 하는 임계 / [200.1] 도달 단정.
  - dcness 응답 검토 — 4개 정확 / 1개 over-claim / 1개 부분 정정 결과:
    - 수용: prose-only 의 정조준 평가, 사다리 #2 회피 = 운영적 절제, DCN-41/42 시그널, RWH = baseline 카탈로그.
    - 반박: "[200.1] / 더 이상 진화 못 함" 단정 = inverse fallacy. commit 빈도 → 가치 곡선 추론은 outside view 부재 (양쪽 동일).
    - 부분 정정: DCN-41/42 vs RWH alias 사다리 layer 구분 — 형식 같지만 #2.5 (외부 환경) 신규 분류로 분리. 사다리 #2 (내부 state hole) 는 dcness 안 아직 시작 안 함.
  - RWH 에이전트가 정정 두 건 (inverse fallacy 철회 + layer 혼동 정정 → #2.5 분류 수용) 응답.
  - 외부 진단을 dcness governance 안 영구 자리로 흡수해야 — 분석이 외부 코멘트로 흐르지 않고 self-discipline 문서로 작동.
- **Alternatives**:
  1. *RWH 진단 무시* (dcness 가 우월 가정). over-claim. 기각.
  2. *dcness 코드 안에 자동 사다리 차단 메커니즘* — 어떤 분기를 자동 차단할지 spec 부재 + 자동 차단이 새 사다리. 기각.
  3. **(채택) governance 문서에 진단 흡수 + self-check 회로** — 신규 분기 PR self-check (`branch-surface-tracking.md`) + 사다리 카탈로그 sticky 명시 (`migration-decisions.md` §7). 자동 차단 X, 자가 점검 ⚪. 사람의 판단 (사용자 / 메인 Claude) 이 신호 보고 결정.
- **Decision**:
  - 옵션 3. 두 문서 신규/보강 docs-only PR.
  - **사다리 #2.5 (외부 환경) 신규 분류** — RWH 진단 layer 혼동 정정 결과. 사다리 #2 와 #2.5 layer 차이 (내부 코드 vs 외부 시스템 인터페이스) 박음. 양쪽 회피 전략 다름.
  - **임계 수치 (30일/3 warning, 30일/5 critical)** — RWH 데이터 1-time snapshot 기반 추정. 30 회 dcness 자가 데이터 후 보정 (별도 Task).
  - **layer 회색지대 보수적**: 사다리 #2 vs #2.5 모호 시 #2 분류 (더 엄격).
  - **inverse fallacy 양쪽 동일**: "RWH 임계 도달 / dcness 사다리 자유" 둘 다 단정 못 함. 측정 데이터 누적이 1차.
- **Follow-Up**:
  - **(별도 Task — 측정)** branch-surface-tracking.md 의 임계 수치 30일 누적 데이터 수집 후 보정.
  - **(별도 Task — 측정)** 매 `harness` / `hooks` / `spec` PR 의 self-check 첨부 강제 — 현재는 권장 (governance §2.6 카테고리 PR 한정). 30일 후 강제 vs 권장 결정.
  - **(별도 Task — 가능성)** dcness 가 critical 임계 도달 시 자동 alert 메커니즘 (`scripts/check_branch_surface.mjs` 같은 형식). 단 자동 차단 X — 사람 판단 우선.

### DCN-CHG-20260430-02
- **Date**: 2026-04-30
- **Rationale**:
  - Manual smoke 종합 피드백 (3가지) 동반 처리:
    1. "중간 출력 가시성" — CC 가 Bash/Agent 출력 collapsed 표시. step 간 무엇이 일어나는지 기본으로 안 보임.
    2. "별일 없으면 자동 commit/PR" — clean run 에 매번 사용자 컨펌 round-trip 비싸다.
    3. "yolo / autopilot 모드" — CLARITY_INSUFFICIENT / *_ESCALATE / AMBIGUOUS 시 사용자 답 대기로 자주 멈춤.
  - 동시에 사용자 지적: "skill 마다 같은 boilerplate 박으면 중복 ↑". helper-side 로 해결해야.
- **Alternatives**:
  1. *각 skill prompt 안 메인이 요약 print + 분기 처리* — 중복 폭증. 기각.
  2. *full prose dump (cat)* — transcript 폭발. 기각.
  3. **(채택) helper-side automation** — `dcness-helper end-step` 자동 stderr 요약 + `finalize-run` JSON 집계 + `auto-resolve` yolo 폴백. skill prompt 손 안 대고 모든 skill 자동 수혜.
- **Decision**:
  - 옵션 3. helper 3개 변경 (`_cli_end_step` stderr 출력 추가, `_cli_finalize_run` 신규, `_cli_auto_resolve` 신규) + skill 2개 (quick/product-plan) yolo + Step 7 분기.
  - **`.steps.jsonl` append-only 로그** — end-step 마다 한 줄 append. finalize-run 이 read + JSON 집계. atomic write 불필요 (append-only).
  - **MUST_FIX detection** — 정규식 (`\bMUST[\s_-]?FIX\b` /i) 검사 → boolean 저장.
  - **clean 자동 commit guard**: `.env` / `secrets.*` / `credentials.*` 있거나 10+ unstaged 또는 submodule 변경 시 7b fallback.
  - **worktree squash 흡수 검사**: ExitWorktree(remove) 전 `git diff main..worktree-branch -- :^.claude` 빈 줄이면 변경 흡수 확인 → discard_changes=true 자동.
  - **yolo 매핑 매트릭스**: `_YOLO_FALLBACKS` dict — `ux-architect:UX_FLOW_ESCALATE`, `product-planner:CLARITY_INSUFFICIENT`, `architect:SPEC_GAP_FOUND`, `validator:FAIL`, `*:AMBIGUOUS`. 매핑 없으면 user-delegate (안전 default).
  - **catastrophic 보존**: PreToolUse 훅 §2.3 4룰 = hard safety. yolo 무관 통과 못 하면 차단.
- **Follow-Up**:
  - **(별도 Task — PR2)** orchestration §3.1 + §2.3.4 에 validator DESIGN_VALIDATION 추가 + /product-plan 6.5 step + hooks.py 검사.
  - **(별도 Task — PR2)** `/impl` skill — per-batch 정식 impl 루프 (architect MODULE_PLAN → test-engineer → engineer → validator CODE_VALIDATION → pr-reviewer).
  - **(별도 Task — PR2)** `/impl-loop` skill — sequential /impl chain.
  - **(별도 Task)** /qa / /init-dcness 도 finalize-run 패턴 적용 검토.
  - **(측정)** 다음 manual smoke 에서 clean run 자동 진행율 + yolo 사용 빈도. 30 회 데이터 후 default 동작 재검토.

### DCN-CHG-20260429-42
- **Date**: 2026-04-29
- **Rationale**:
  - DCN-CHG-41 의 wrapper invocation 패턴 `${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/dcness}/scripts/dcness-helper` 가 사용자 manual smoke 에서 ENOENT.
  - 원인 1: CC slash command bash 환경엔 `CLAUDE_PLUGIN_ROOT` 미설정 → fallback 발동.
  - 원인 2: local marketplace add 시나리오 (`claude plugin marketplace add /path/to/dcNess`) 에선 `~/.claude/plugins/marketplaces/dcness` 디렉토리 미생성 — 이 경로는 GitHub source 마켓플레이스 clone 위치라 local source 엔 미적용.
  - 실제 install 위치 = `~/.claude/plugins/cache/{plugin}/{plugin}/{version}/` (versioned, CC 표준).
- **Alternatives**:
  1. *fallback 을 cache 의 specific 버전 path 로 hardcode* (`cache/dcness/dcness/0.1.0-alpha`). 버전 업그레이드마다 깨짐. 기각.
  2. *wrapper 자체를 user PATH 에 install* (symlink to `~/.local/bin/`). install step 추가 + PATH 의존. 기각.
  3. **(채택) fallback 을 cache glob 으로** — `$(ls -d ${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/cache/dcness/dcness/*} 2>/dev/null | head -1)`. CLAUDE_PLUGIN_ROOT set 됐으면 그대로 / 미설정이면 glob 으로 versioned dir 자동 픽 / 다중 버전 시 첫 결과 (alphabetical first — 일반적으로 lowest version, 단일 버전 환경에선 무관).
- **Decision**:
  - 옵션 3. 4 skill 일괄 변경.
  - **부수 발견 — uninstall 시 whitelist 소실**: `claude plugin uninstall` 이 `~/.claude/plugins/data/dcness-dcness/` 를 정리 → whitelist 소실. 매 재설치마다 `/init-dcness` 재실행 필요. init-dcness 문서에 경고 명시.
  - **per-project 마커 미채택 (재확인)**: DCN-CHG-40 의 plugin-scoped 결정 유지. 재설치 빈도 ↓ + plugin 제거 시 자동 cleanup 가치 ↑ 트레이드오프 정합.
- **Follow-Up**:
  - **(별도 Task — v2)** plugin postinstall hook 으로 whitelist 보존 (Backup → Restore) 가능성 검토.
  - **(측정)** Manual smoke 재실행 — wrapper fallback 경로 정상 동작 + /init-dcness 후 SessionStart 훅 발화 + /qa 첫 helper 호출 성공.

### DCN-CHG-20260429-41
- **Date**: 2026-04-29
- **Rationale**:
  - Manual smoke (`/qa src/greet.py 빈 문자열 처리 이상`) 도중 사용자 첫 helper 호출 (`begin-run qa`) 에서 ModuleNotFoundError 발견. 원인 = skill bash 환경에 PYTHONPATH 미설정. dcNess plugin install 위치 (`~/.claude/plugins/marketplaces/dcness/`) 가 PYTHONPATH 에 없으니 `python3 -m harness.session_state` 가 `harness` 패키지 못 찾음.
  - DCN-CHG-40 에서 hook 스크립트는 `${CLAUDE_PLUGIN_ROOT}` 를 PYTHONPATH 에 prepend 하도록 수정했지만, slash command bash 환경엔 같은 처리가 빠짐. hook 과 skill 은 별개 진입점이라 양쪽 모두 PYTHONPATH 손봐야.
- **Alternatives**:
  1. *모든 helper 호출에 `PYTHONPATH=...` 인라인 prefix* (verbose, 매번 반복). 기각.
  2. *`harness/` 를 user site-packages 에 install* (`pip install -e`). plugin 설치 외 추가 setup step + 다른 dcness 인스턴스와 충돌. 기각.
  3. **(채택) wrapper script** (`scripts/dcness-helper`). RWH 패턴 정합 (`scripts/setup-rwh.sh` 등). script 가 자기 위치 (`BASH_SOURCE`) 로부터 plugin root 추출 → PYTHONPATH 자동 설정 후 `exec python3 -m harness.session_state "$@"`. CLAUDE_PLUGIN_ROOT 의존 0 (set 안 돼도 동작).
- **Decision**:
  - 옵션 3. wrapper script + 4 skill 의 helper 호출 일괄 변경.
  - skill 호출 형식: `"${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/plugins/marketplaces/dcness}/scripts/dcness-helper" <subcommand>` (RWH 패턴 정합 — CLAUDE_PLUGIN_ROOT 폴백 path 명시).
  - wrapper 자체는 BASH_SOURCE 기반 자기위치 추출 → CLAUDE_PLUGIN_ROOT 가 set 됐든 안 됐든 동일 동작 (방어 코드).
- **Follow-Up**:
  - **(별도 Task)** `scripts/dcness-helper` 만의 단위 테스트 — wrapper bash 동작 검증.
  - **(측정)** Manual smoke 재실행 — `/qa` 첫 helper 호출 성공 + run state 정상 생성 확인.

### DCN-CHG-20260429-40
- **Date**: 2026-04-29
- **Rationale**:
  - Manual smoke 도중 사용자 발견: dcNess plugin 설치만 했는데도 RWHarness 처럼 자동 활성 안 되면서 hook 미발화. 그 외 cross-project 시나리오 (dcNess repo 밖 cwd 에서 claude 실행) 에선 helper 가 `harness/` import 실패로 ModuleNotFoundError → silent exit. 두 문제 동반 해결 필요.
  - 더 큰 문제: dcNess plugin 이 모든 프로젝트에 자동 활성되면 부작용 폭증 — RWHarness 와 hook race + 사용자가 의도하지 않은 카테고리 자동 검사 + cross-project 사용자 경험 surprise.
  - RWHarness 는 `~/.claude/harness-projects.json` 글로벌 whitelist 로 해결. 단 글로벌 파일 = 다른 plugin 도 보일 수 있음 + plugin 제거해도 잔재. 사용자는 plugin-scoped 저장 명시 요구.
- **Alternatives** (활성화 메커니즘):
  1. *항상 활성* (현재 디폴트). 부작용 폭증. 기각.
  2. *RWHarness 와 동일 글로벌 whitelist* (`~/.claude/harness-projects.json`). 명시 거부 (사용자 발화).
  3. *프로젝트 별 마커 파일* (`<project>/.claude/harness-state/.dcness-enabled`). 자기선언 명확 + 글로벌 0. 단점: plugin 단에서 활성 프로젝트 목록 한눈에 못 봄 + 마커 파일 별도 관리 부담. 차순위.
  4. **(채택) plugin-scoped whitelist** (`~/.claude/plugins/data/dcness-dcness/projects.json`). CC 공식 plugin-data 컨벤션 정합 — plugin namespace + reinstall 보존 + plugin 제거 시 자동 cleanup. 사용자 발화 정합.
- **Alternatives** (PYTHONPATH 해법):
  1. *plugin install 시 PYTHONPATH 환경변수 자동 추가* — 사용자 shell init 변경 부담. 기각.
  2. **(채택) hook 스크립트가 `${CLAUDE_PLUGIN_ROOT}` 를 PYTHONPATH 에 prepend** — 1줄 추가, plugin install 위치 자동 추적, 사용자 환경 영향 0.
- **Decision**:
  - 활성화 = 옵션 4 (plugin-scoped whitelist). PYTHONPATH = 옵션 2 (hook 스크립트 prepend). 같은 PR 에 묶음 — 둘 다 cross-project 인프라.
  - **게이트 위치**: hook 스크립트 첫 줄 (`is-active` exit 1 시 즉시 `exit 0`). Python 진입 전이라 inactive 프로젝트는 import 비용도 0.
  - **`/init-dcness` skill**: `python3 -m harness.session_state enable` 호출 + 사용자 안내 (다음 세션 재시작 권장).
  - **`/disable-dcness`**: v1 미구현 — 명시 비활성화는 CLI 직접 호출 (`python3 -m harness.session_state disable`). v2 follow-up.
  - **테스트 환경 우회**: `DCNESS_FORCE_ENABLE=1` env 로 whitelist 무시 + 무조건 active. multisession smoke 11 테스트가 의존.
  - **γ resolution 정합**: `is_project_active` 가 `_resolve_project_root` (worktree → main repo) 사용 → worktree cwd 도 main repo whitelist 상속.
- **Follow-Up**:
  - **(별도 Task — v1.1)** `/disable-dcness` skill 신규 (cousin to /init-dcness).
  - **(별도 Task — v2)** plugin uninstall hook — `data/dcness-dcness/` 자동 cleanup 검증.
  - **(별도 Task — v2)** `/init-dcness` 가 첫 호출 시 plugin uninstall reminder + 추천 후속 skill 안내.
  - **측정**: 첫 manual smoke 결과 — hook 게이트가 inactive 프로젝트에서 100% no-op 인지.

### DCN-CHG-20260429-39
- **Date**: 2026-04-29
- **Rationale**:
  - 멀티세션 = dcNess 컨베이어의 기본 가정 (`docs/conveyor-design.md` §4.1). 단 §4 의 by-pid 레지스트리 + `.sessions/{sid}/runs/{rid}/` 격리는 *상태/prose* 차원만 분리하고 src/ 파일 차원에선 main repo cwd 를 공유. 동시 다중 작업 시 working tree 충돌 + commit/staging 침범 위험.
  - `EnterWorktree` 가 제공하는 git worktree 격리를 결합하면 src/ 차원 분리까지 달성. 단 worktree 진입 시 cwd 가 `.claude/worktrees/{name}/` 으로 변경 → 기존 `_default_base()` (cwd 기준) 가 worktree 안 빈 `.claude/harness-state/` 를 봄 → SessionStart 훅이 main repo 에서 박은 by-pid / live.json 미발견 → catastrophic 미동작.
- **Alternatives** (트리거 정책):
  1. *옵션 A — 매번 자동* (skill Step 0 무조건 EnterWorktree). EnterWorktree 룰 ("explicit user instruction") 회색지대. 기각.
  2. *옵션 B — 사용자 1회 확인* ("worktree 격리?" 묻기). round-trip 1회 추가. 기각.
  3. *옵션 D — 디폴트 + opt-out* (`--no-worktree` 시만 main). 단발 작업 90% 에 과한 격리 + cwd 변경 surprise + worktree 누적 cleanup 룰 위험 + 세션 종료 시 매번 keep/remove 모달. 4 함정. 기각.
  4. **(채택) 옵션 C — 명시 keyword** ("worktree" / "wt" / "격리" / "isolate" 발화 시만). 점진 도입 + EnterWorktree 룰 정합 + 단발 작업 friction 0 + 누적 부담 ↓.
- **Alternatives** (sid 단일 source 해법):
  1. *옵션 α — 런타임 read 폴백* (helper 의 `read_pid_session` 등에 worktree → main repo cross-search). 함수 다수 수정 + race window. 기각.
  2. *옵션 β — 진입 직후 inheritance step* (EnterWorktree → `inherit-session` helper 가 main 의 by-pid 를 worktree 로 복사). 별도 step + 동기화 룰 부담. 기각.
  3. **(채택) 옵션 γ — `_default_base()` 단일 변경** (`git rev-parse --git-common-dir` 으로 main repo `.git` 추출 → main repo `.claude/harness-state/` 단일 source). 1 함수 수정으로 모든 R/W 호출 사이트 일관 정합. cwd 별 캐시로 subprocess 비용 1회/cwd. main repo 안 호출 시 동작 변화 0 (`.git` 상대경로 → cwd 그대로). 비-git 환경 폴백 보존.
- **Decision**:
  - 트리거 = 옵션 C, sid 해법 = 옵션 γ.
  - `commands/quick.md` `commands/product-plan.md` 에 Step 0a (keyword 트리거) + 종료 step 에 ExitWorktree 옵션 (keep/remove 사용자 결정).
  - `commands/qa.md` 는 src/ 미수정 → 미적용.
  - `_default_base()` 의 캐시는 cwd 별 dict (`_DEFAULT_BASE_CACHE`). `_clear_default_base_cache()` 는 테스트 보조 (production 미사용).
  - 테스트 5개 (`DefaultBaseWorktreeTests`) — plain repo / worktree / 비-git / 캐시 멱등 / by-pid cross-cwd 일관성.
- **Follow-Up**:
  - **(별도 Task — v2)** 자동 cleanup 룰 — 24h 보관 후 ExitWorktree(remove) 자동 후보.
  - **(별도 Task — v2)** PR merge 감지 자동화 (`gh pr merge` 후 ExitWorktree(remove)).
  - **(별도 Task — v2)** 사용 데이터 측정 후 옵션 D 디폴트 마이그레이션 검토.
  - **측정**: keyword 트리거 사용 빈도 vs 일반 호출 빈도. 30일 후 v2 디폴트 검토 자료.

### DCN-CHG-20260429-38
- **Date**: 2026-04-29
- **Rationale**:
  - 사용자 직접 요청 — 현재 세션 컨텍스트 60%+ 도달 → 다음 세션 이어가기용 smart-compact 필요.
  - CC 내장 `/compact` 는 *기계적 요약* — 의도/결정/진행상태 추출 안 함. 사용자가 다음 세션에서 어떤 단계인지 즉시 못 잡음.
  - smart-compact = 메인이 자체 LLM 으로 *능동 추출* (rationale + decision + open question 위주) + resume prompt 자동 생성 + clipboard.
- **Decision**:
  - skill prompt 5 step:
    1. 추출 (git + governance docs + PROGRESS + TaskList + transcript 미해결 의논)
    2. 단일-메시지 prompt 작성 (정해진 템플릿)
    3. clipboard 복사 (pbcopy / xclip / clip)
    4. transcript 출력 (사용자 직접 복사 가능)
    5. 파일 백업 (`.claude/resume-prompts/{ts}.md`) — clipboard 깨짐 대비
  - 추출 우선순위:
    - **포함**: 미해결 결정 + 핵심 reasoning + uncommitted state + 다음 step 후보
    - **제외**: 도구 호출 결과 raw / 폐기된 검토안 (rationale 박힘) / 자체 reasoning 중간 단계
- **Follow-Up**:
  - 사용자가 본 skill 직접 실행 (다음 세션 시작 시 효과 측정)
  - 추출 quality 측정 — 다음 세션이 resume prompt 만으로 매끄럽게 이어지는지 회고

### DCN-CHG-20260429-37
- **Date**: 2026-04-29
- **Rationale**:
  - `/qa` (DCN-CHG-20260429-36) 다음으로 핵심 진입점 2개 추가:
    - `/quick` = `/qa` 분류 결과가 FUNCTIONAL_BUG/CLEANUP 시 *자동 진행* — light path. 사용자가 일일이 다음 step 결정 안 해도 됨.
    - `/product-plan` = 큰 기획 / 새 기능 / PRD 변경 진입점 — spec/design 단계까지 자동 진행, 구현은 별도.
  - 둘 다 `/qa` skill 의 8-step protocol 패턴 확장. 시퀀스 길이만 다름 (qa 1 task / quick 5 task / product-plan 6 task).
  - 재진입 cycle 한도 명시 — PRD 심사 / UX 검증 fail 시 무한 루프 방지.
- **Alternatives**:
  1. *quick + product-plan 분리 PR* — 작은 PR 단위 OK 하지만 둘 다 prompt-only + 동일 패턴이라 같이 묶는 게 review 효율 ↑. 기각.
  2. *quick 안에 product-plan 자동 라우팅* — quick 이 분류 결과 SCOPE 가 크면 product-plan 호출. 복잡도 ↑. 기각 (사용자가 진입점 선택).
  3. *product-plan 에 구현 자동 진입 (architect MODULE_PLAN 부터 impl 루프 N회)* — spec 단계 + 구현 단계 분리가 사용자 결정에 자연스러움. 자동 진입은 큰 작업 통제 어려움. 기각.
  4. *(채택)* **`/quick` + `/product-plan` 동일 PR + 구현 자동 진입 X** — 사용자 결정 layer 보존.
- **Decision**:
  - **`/quick` 시퀀스** (orchestration.md §3.5 light path):
    - qa (분류) → architect LIGHT_PLAN → engineer IMPL → validator BUGFIX_VALIDATION → pr-reviewer
    - 5 task 자동 진행. depth=simple 고정. test-engineer 단계 생략.
    - qa 분류 결과 FUNCTIONAL_BUG / CLEANUP 만 자동 진행. 그 외 (DESIGN_ISSUE / KNOWN_ISSUE / SCOPE_ESCALATE) → 종료 + 사용자 결정.
  - **`/product-plan` 시퀀스** (orchestration.md §3.1):
    - product-planner → plan-reviewer → ux-architect → validator UX_VALIDATION → architect SYSTEM_DESIGN → architect TASK_DECOMPOSE
    - 6 task. spec 단계까지만. 구현 진입은 별도 (사용자 결정).
    - PLAN_REVIEW_CHANGES_REQUESTED → product-planner 재진입 (2 cycle 한도)
    - UX_VALIDATION FAIL → ux-architect 재진입 (2 cycle 한도)
  - **공통 — AMBIGUOUS cascade**: `/qa` 정합. 재호출 (1회) → 사용자 위임.
  - **공통 — catastrophic 자동 정합**: skill 시퀀스가 §2.3 4룰 충족하도록 짜여서 PreToolUse 훅이 자연 통과.
    - `/quick` Step 3 (architect LIGHT_PLAN_READY) → Step 4 engineer (§2.3.3 충족)
    - `/quick` Step 5 (validator BUGFIX_VALIDATION PASS) → Step 6 pr-reviewer (§2.3.1 충족)
    - `/product-plan` Step 3 (plan-reviewer PASS) + Step 4-5 (ux-architect READY) → Step 6 architect SYSTEM_DESIGN (§2.3.4 충족)
- **Follow-Up**:
  - **Task -38**: `/init-dcness` skill (enable/disable 부트스트랩)
  - **Task -39**: `/ux` skill (designer + design-critic THREE_WAY)
  - **manual smoke**: 실 `claude` 에서 `/quick`, `/product-plan` 발화 → 전체 흐름 검증
  - **architect TASK_DECOMPOSE 의 impl batch 자동 처리** — v2 follow-up
  - **회귀 위험**: skill prompt 가 helper CLI 시그니처에 묶임. `harness/session_state.py` CLI 변경 시 3개 skill 모두 동기화 필요. governance §2.6 docs-only sync 가 catch.

### DCN-CHG-20260429-36
- **Date**: 2026-04-29
- **Rationale**:
  - dcNess plugin 의 첫 skill 도입. 사용자 진입점 = "버그 있다" 류 자연어 발화 → 분류 + 라우팅 추천.
  - 사용자 결정 — heuristic only (haiku 안 켬). 이유:
    1. **메인 단독 판단 vs catastrophic 훅 일관성** 트레이드오프 검토 결과 heuristic 유지가 안전 (메인이 prose 본문 본 의미 vs 훅 grep 결과 어긋날 위험)
    2. **API 키 의존 회피** — dcNess 자체 도그푸딩 환경 (subscription only) 호환
    3. **비용 0** — heuristic 은 Python regex (cycle 당 LLM 호출 0)
    4. **dcNess 정신 정합** — heuristic 은 가벼운 enum 추출 (단어경계 매칭 1개), 형식 강제 사다리 아님
  - AMBIGUOUS 처리 = cascade 패턴 — agent 재호출 (1회) → 사용자 위임. 메인 단독 판단으로 진행 시 다음 step 의 catastrophic 훅 grep 과 어긋날 risk 회피.
- **Alternatives**:
  1. *heuristic + haiku fallback 동시 켬* — robustness ↑, but API 키 의존 + dcNess 도그푸딩 호환성 ↓. 기각.
  2. *heuristic + haiku 둘 다 폐기, 메인이 prose 본문 보고 직접 판단* — 메인 vs 훅 일관성 깨짐 risk. 기각.
  3. *(채택)* **heuristic only + AMBIGUOUS cascade (재호출 → 사용자)** — 결정론 + plugin 환경 호환 + dcNess 정신 정합.
- **Decision**:
  - `commands/qa.md` 신규. CC 가 `commands/*.md` 자동 디스커버 (RWHarness 패턴 정합).
  - **8 step protocol**:
    - Step 0 — `begin-run qa` 로 run_id 발급
    - Step 1 — `TaskCreate("qa: 이슈 분류")` (단일 task)
    - Step 2 — 사용자 입력 명확화 (재현·범위·예상 동작 등 모호 시 역질문)
    - Step 3 — `TaskUpdate(in_progress)` + `begin-step qa` + `Agent(qa, ...)`
    - Step 4 — prose 임시 파일 저장 + `end-step qa --allowed-enums "..." --prose-file ...` → enum 또는 AMBIGUOUS
    - Step 5 — AMBIGUOUS 시 cascade (5-1 재호출 / 5-2 사용자 위임)
    - Step 6 — `TaskUpdate(completed)` + 분류 결과 보고 + 후속 skill 추천 (자동 진입 X)
    - Step 7 — 종료 시 `end-run`
  - **agents/qa.md 정합**: 5 결론 enum (FUNCTIONAL_BUG / CLEANUP / DESIGN_ISSUE / KNOWN_ISSUE / SCOPE_ESCALATE) 그대로 사용.
  - **catastrophic 룰 무관**: qa agent 는 HARNESS_ONLY_AGENTS 미해당, §2.3 4룰 모두 비대상.
  - **후속 skill 미구현 명시**: `/quick`, `/ux` 가 없으므로 분류 결과만 보여주고 자동 라우팅 X. 사용자 결정 받고 architect 직접 호출 또는 종료.
- **Follow-Up**:
  - **Task -37**: `/quick` skill (FUNCTIONAL_BUG / CLEANUP 분류 후 light path 자동 진입)
  - **Task -38**: `/init-dcness` (enable / disable 헬퍼)
  - **Task -39**: `/harness-monitor` `/harness-list` `/harness-kill` (디버깅/운영)
  - **manual smoke**: 실 `claude` 세션에서 `/qa <bug 보고>` 발화 → SessionStart 훅 → run_dir + prose 종이 + end-run 검증
  - **measurement**: `.metrics/heuristic-calls.jsonl` 누적 → AMBIGUOUS 빈도 측정. 30%+ 면 haiku fallback 검토.
  - **회귀 위험**: skill prompt 가 helper CLI 시그니처에 묶임. `harness/session_state.py` 변경 시 skill prompt 도 동기화 필요. governance §2.6 의 doc-sync 가 자동 catch (commands/ 는 docs-only category, 매 변경 시 doc-sync 발화).

### DCN-CHG-20260429-35
- **Date**: 2026-04-29
- **Rationale**:
  - PR #33 (DCN-CHG-20260429-34) 머지 후 사용자 지적 — "멀티세션 코드는 들어갔는데 e2e 검증 안 함" 부분 보강 필요.
  - 기존 단위 테스트는 모두 mock 기반 (`base_dir` 격리, `cc_pid` 인자 명시). 실 bash → python 파이프라인은 검증 안 됨.
  - smoke 단계 = 실 subprocess 호출 + 실 stdin payload + 실 파일 시스템 부수효과 검증.
- **Alternatives**:
  1. *manual smoke (사용자가 두 `claude` 띄워 검증)* — 가장 정확하나 자동화 0, 회귀 검증 어려움. follow-up 으로 보존.
  2. *fixture 기반 mock subprocess* — 빠르지만 실 파이프라인 검증 X. 기각.
  3. *(채택)* **subprocess.run + Popen 으로 실 bash 호출 + 동시 spawn 으로 race 검증**. 한계 (PPID 가 pytest pid 라 bash 자체 PPID 검증 불가) 는 `--cc-pid` 명시로 우회.
- **Decision**:
  - **3 테스트 그룹**:
    - `BashPipelineSmokeTests` (4) — bash 훅 동작 + invalid sid silent + 빈 payload silent
    - `MultiSessionIsolationTests` (3) — 두 cc_pid 격리 + live.json 자기참조 + 동시 Popen 격리
    - `CatastrophicRuleE2eTests` (4) — engineer §2.3.3 / pr-reviewer §2.3.1 / HARNESS_ONLY 차단 + plan 있을 때 통과
  - **subprocess 환경**:
    - cwd 격리 (TemporaryDirectory)
    - PYTHONPATH 명시 (REPO_ROOT)
    - timeout 10s
    - stdin = JSON payload, capture_output=True
  - **명시 한계** (docstring):
    - bash 의 자기 PPID 가 pytest pid 라 두 호출이 같은 cc_pid → 격리 검증은 python CLI 직접 호출 (`--cc-pid` 명시) 로 우회
    - 실 Claude Code 환경의 PPID 신뢰성 / stdin payload 형식은 별도 manual smoke 필요
- **Follow-Up**:
  - **manual smoke**: 사용자가 동시 두 `claude` 띄움 → 같은 working dir 에서 작업 → `.claude/harness-state/` 검사로 격리 확인. README 또는 dcNess 자체 도그푸딩 가이드에 추가.
  - **CC 환경 검증**:
    - SessionStart payload 의 `sessionId` 필드 실측
    - PreToolUse Agent payload 의 `tool_input.subagent_type` / `tool_input.mode` 필드 실측
    - PPID 가 CC main 인지 shell 인지 실측 (TBD)
  - **회귀 위험**: 본 smoke 는 subprocess 가 macOS / Linux 동작 가정. Windows 미지원. tmux/screen 같은 환경에서 PPID 비표준일 수 있음.

### DCN-CHG-20260429-34
- **Date**: 2026-04-29
- **Rationale**:
  - `docs/conveyor-design.md` v2 (DCN-CHG-20260429-32) §7/§8 의 훅 인프라 코드 구현. catastrophic 보호의 *물리 강제선* — 메인이 protocol 따르든 안 따르든 Agent 호출 시 자동 발화.
  - 훅 스크립트는 bash 래퍼 + Python 핸들러 분리. 이유:
    1. bash 가 PPID 캡처 + python 인자로 전달 — Python 의 `os.getppid()` 가 shell 인지 CC 인지 모호한 케이스 회피
    2. 모든 로직은 Python (테스트 가능) — bash 는 1줄 wrapper
    3. RWHarness 패턴 정합 (`hooks/hooks.json` 으로 plugin 활성 시 자동 등록)
- **Alternatives**:
  1. *Python 직접 invoke (bash wrapper 없이)* — `python3 -m harness.hooks ...` 로 hooks.json 박음. 단점: PPID 가 shell 인지 CC 인지 모호. 기각 (bash 래퍼가 PPID 명시 캡처).
  2. *훅 안에 catastrophic 검사 직접 구현 (Python 모듈 없이)* — 테스트 어려움 + 코드 분산. 기각.
  3. *Settings.json 의 hooks 직접 박기 (plugin 자동 등록 안 함)* — plugin 사용자가 수동 설정 필요. 기각.
  4. *(채택)* **bash 래퍼 + Python 핸들러 + hooks.json plugin 자동 등록** (RWHarness 패턴).
- **Decision**:
  - **`harness/hooks.py` 모듈** (~280 LOC):
    - `HARNESS_ONLY_AGENTS` 상수 — orchestration.md §7.1 정합
    - `handle_session_start(stdin_data, cc_pid)` — sid 추출 + write_pid_session + update_live 초기화
    - `handle_pretooluse_agent(stdin_data, cc_pid)` — HARNESS_ONLY_AGENTS + §2.3.1/3/4 검사
    - `_resolve_rid(sid, cc_pid)` — by-pid-current-run 우선, live.json 가장 최근 미완료 슬롯 폴백
    - 헬퍼 4개 (`_has_plan_ready`, `_has_engineer_write`, `_has_validator_pass`, `_has_plan_review_pass`, `_has_ux_flow_ready`)
    - CLI `python3 -m harness.hooks {session-start, pretooluse-agent}`
  - **bash 래퍼**:
    - `hooks/session-start.sh` — `CC_PID=$PPID; python3 -m harness.hooks session-start --cc-pid $CC_PID; exit 0` (silent skip on error)
    - `hooks/catastrophic-gate.sh` — `CC_PID=$PPID; python3 -m harness.hooks pretooluse-agent --cc-pid $CC_PID; exit $?` (block 시 exit 1)
  - **`hooks/hooks.json`** — plugin 자동 등록:
    - `SessionStart` → session-start.sh (timeout 5s)
    - `PreToolUse` matcher=Agent → catastrophic-gate.sh (timeout 10s)
  - **silent skip 정책**:
    - 모든 비-catastrophic 실패 (sid 없음 / cc_pid 없음 / parse 실패 / OS 에러) → exit 0 + skip
    - 진짜 위반만 exit 1 + stderr 메시지
    - 이유: CC 동작 방해 안 함 + plugin 환경 차이 (jq 없음 등) 견딤
  - **테스트**:
    - 28 케이스. mock stdin payload + base_dir 격리.
    - HARNESS_ONLY_AGENTS 차단 / 통과 매트릭스
    - §2.3.1/3/4 4룰 모두 happy/blocked path
    - rid 폴백 (by-pid 없을 때 live.json 미완료 슬롯 픽업)
- **Follow-Up**:
  - **e2e 테스트** — 실 plugin 환경에서 `claude` 띄워 hook 발화 검증 (수동, 별도 PR)
  - **multi-session 한계 명시** — Phase 1 은 단일 working directory 단일 세션 가정. 멀티세션 도그푸딩은 plugin Phase follow-up.
  - **PostToolUse(Agent) heartbeat 갱신 훅** (선택) — last_confirmed_at 자동화
  - **skill prompt 템플릿 갱신** — `/quick`, `/product-plan` 등이 helper protocol (begin-run/begin-step/end-step) 박음
  - **`signal_io.write_prose` atomic write 강화** — 현재 `os.replace` → `session_state.atomic_write`
  - **plugin smoke test** — `.claude-plugin/plugin.json` 의 hooks 등록 자동화 검증

### DCN-CHG-20260429-33
- **Date**: 2026-04-29
- **Rationale**:
  - `docs/conveyor-design.md` v2 (DCN-CHG-20260429-32) 의 §4/§5 멀티세션 인프라 코드 구현. helper protocol 의 진입점 (`begin-run/begin-step/end-step/end-run`) 도 동시 도입.
  - 멀티세션 정합 = 환경변수 `DCNESS_RUN_ID` 전파가 Bash subprocess 휘발성으로 작동 안 함을 발견. 대체 = **PID-keyed 레지스트리** (RWH issue #19 패턴 부분 차용 + 글로벌 폴백 제외).
  - PPID chain walker — python helper 가 자기 grandparent (CC main) PID 추출. `os.getppid()` 는 bash pid (직접 부모), `ps -o ppid=` 명령으로 한 단계 더 위 = CC main pid 획득. macOS / Linux 모두 동작.
- **Alternatives**:
  1. *환경변수 `DCNESS_RUN_ID` 메인이 export* — Bash subprocess 가 메인 process env 변경 못 함. 동작 안 함. 기각.
  2. *메인이 helper 호출 시 sid/rid 직접 인자로 전달* — 사용자가 매번 `--sid abc --rid run-xxx` 박아야 → skill prompt 복잡 + 실수 위험. 기각.
  3. *Skill prompt template 안에서 ps 로 CC pid 추출 후 인자로 전달* — 가능하나 매 helper 호출마다 boilerplate. 기각.
  4. *(채택)* **CLI 안에서 PPID chain walker 가 자동 추출** + auto_detect_session_id / auto_detect_run_id helper. 메인이 인자 안 박아도 됨.
- **Decision**:
  - **by-pid 레지스트리 함수 8개**:
    - `pid_session_path` / `pid_run_path` — 경로 helper
    - `write_pid_session` / `read_pid_session` — sid 매핑
    - `write_pid_current_run` / `read_pid_current_run` / `clear_pid_current_run` — rid 매핑
    - `cleanup_stale_pid_files` — TTL (24h) 기반 정리 (PID 재사용 보호)
  - **PPID chain walker** — `get_cc_pid_via_ppid_chain()`:
    - `os.getppid()` = bash pid
    - `subprocess.run(["ps", "-o", "ppid=", "-p", str(bash_pid)])` = CC main pid
    - 실패 시 None 반환 (fallback to env/pointer in auto_detect)
  - **auto-detect 함수**:
    - `auto_detect_session_id` — by-pid 우선, current_session_id() 폴백
    - `auto_detect_run_id` — by-pid-current-run lookup
  - **CLI subcommand 5개**:
    - `init-session <sid> <cc_pid>` — SessionStart 훅 보조 (write_pid_session + update_live 초기화)
    - `begin-run <entry_point>` — sid auto-detect → generate rid → start_run + write_pid_current_run → stdout: rid
    - `end-run` — sid+rid auto-detect → complete_run + clear_pid_current_run
    - `begin-step <agent> [<mode>]` — sid+rid auto-detect → update_current_step
    - `end-step <agent> [<mode>] --allowed-enums <csv> --prose-file <path>` — sid+rid auto-detect → write_prose + interpret_with_fallback → stdout: enum 1단어 (또는 "AMBIGUOUS")
  - **end-step 의 ambiguous 처리** — interpret_with_fallback 실패 시 stdout="AMBIGUOUS" + stderr 에 detail. exit 0 (정상 결과 — 메인이 이 신호 보고 자율 처리).
  - **PID 재사용 보호** — `cleanup_stale_pid_files(ttl_sec=24h)` 가 mtime 기준 stale by-pid 파일 정리. (start_ts hash 박는 옵션은 보류 — 24h TTL 충분).
- **Follow-Up**:
  - **Task -34**: `hooks/session-start.sh` (CLI 의 init-session 호출) + `hooks/catastrophic-gate.sh` (PreToolUse Agent 검사) 신규.
  - **Task 후속**: `signal_io.write_prose` 의 `os.replace` → `session_state.atomic_write` 로 강화.
  - **plugin Phase**: skill prompt 템플릿 (`/quick`, `/product-plan` 등) 가 helper protocol 박음.
  - **회귀 위험**: PPID chain walker 가 macOS / Linux 동작 가정. Windows 미지원. tmux/screen 같은 환경에서 ppid 가 비표준일 수 있음 — auto_detect 가 폴백 (current_session_id) 으로 우회.
  - **측정 (proposal §2.5 원칙 5)**: end-step 의 stdout 이 "AMBIGUOUS" 빈도 telemetry 누적 → agent prose writing guide 정확도 측정 데이터.

### DCN-CHG-20260429-32
- **Date**: 2026-04-29
- **Rationale**:
  - PR #29 (`docs/conveyor-design.md` 초안) 의 Python `run_conveyor` 모델이 실 구현 단계 (Task -31) 검토 중 본질적 결함 발견:
    1. **Subagent 호출 격리 문제** — Python 안에서 Agent 호출 시 subprocess `claude --agent` 또는 SDK 직접 호출 필요. 메인 세션의 PreToolUse 훅 미발화 또는 다른 settings 적용. catastrophic 보호 깨짐.
    2. **사용자 가시성 0** — Python batch 종료까지 진행 안 보임.
    3. **메인 자율도 0** — 매 step 사이 메인 개입 불가.
  - 대안 검토:
    - α) 단일 라벨 결정 하이쿠 — 라벨 늘면 driver hardcode 부담
    - β) 정적 dict 라우팅 (옵션 b 부활) — 분기 룰 코드 박힘 (§2.5 원칙 1 약화)
    - 글로벌 ~/.claude 폴백 — 도그푸딩 가치 < 4-가드 복잡도
    - 관문 하이쿠 별도 LLM — 해석 하이쿠 + advance_when 로 충분
    - **Task tool + Agent + helper + 훅** ← 채택
  - 추가 발견 — 멀티세션 정합:
    - `.session-id` / `.current-run-id` 단일 pointer = 동시 두 세션 띄우면 덮어쓰기 충돌
    - env `DCNESS_RUN_ID` 전파 = Bash subprocess 휘발성 (메인 다음 호출 시 사라짐)
    - 해결 = sid 별 디렉토리 격리 + by-pid 레지스트리 (`{cc_pid}` → sid/rid 매핑)
- **Alternatives**:
  1. *PR #29 그대로 머지하고 v1 design 으로 구현* — PreToolUse 훅 우회, 멀티세션 충돌 등 본질적 결함 그대로. 기각.
  2. *PR #29 force-push 갈아엎기* — 리뷰 어려움. 기각.
  3. *(채택)* **별도 PR (DCN-CHG-20260429-32) 로 conveyor-design.md rewrite + governance retraction notice** — 머지 이력 보존 + 전환 사유 명시.
- **Decision**:
  - 옵션 3. 동일 파일 (`docs/conveyor-design.md`) 의 12 절 내용 대폭 갱신:
    - §0.4 신규 — Task tool 패턴 채택 이유
    - §1 등장인물 — Python 컨베이어 폐기, helper module + 훅 명시
    - §2 흐름 — Task lifecycle mermaid (TaskCreate → Update → Agent → end-step → Update)
    - §3 데이터 모델 — Step (참고용), helper 호출 인터페이스 (Bash subcommand)
    - §4 멀티세션 — by-pid 레지스트리, env 폐기 사유, PID 재사용 보호
    - §5 디렉토리 — `.by-pid/` `.by-pid-current-run/` 추가
    - §6 live.json — 그대로 (이미 OMC active_runs 패턴)
    - §7 훅 — SessionStart + PreToolUse Agent 명시
    - §8 catastrophic — pseudo-bash 풀 코드 박음
    - §11 폐기 — PR #28 + v1 (Python 컨베이어) + 토론 검토 옵션 모두 명시
  - **멀티세션 정합 핵심**:
    - 모든 자원 sid 별 격리 (`.sessions/{sid}/`)
    - by-pid 레지스트리 (`.by-pid/{cc_pid}` → sid, `.by-pid-current-run/{cc_pid}` → rid)
    - 훅은 stdin payload sid 사용, helper 는 PPID 로 by-pid lookup
    - PID 재사용 보호 = TTL + (선택) 시작 timestamp hash
  - **HARNESS_ONLY_AGENTS 강제 mechanism**:
    - PreToolUse Agent 훅이 by-pid-current-run 검사
    - 없으면 engineer / validator-PLAN/CODE/BUGFIX_VALIDATION 차단
    - "메인이 컨베이어 protocol 안 따르고 Agent 직접 호출" 시나리오 자동 차단
- **Follow-Up**:
  - **Task -33**: `harness/session_state.py` 확장 — by-pid 함수 (`write_pid_session/read_session_by_pid/...`) + CLI argparse subcommand (`init-session/begin-run/end-run/begin-step/end-step`). 기존 49 테스트 + 추가 ~20.
  - **Task -34**: `hooks/session-start.sh` + `hooks/catastrophic-gate.sh` 신규. `.claude/settings.json` 템플릿 갱신 (plugin 활성 시 hook 자동 등록 패턴). shell test 또는 python pytest 로 회귀.
  - **Task 후속**: `signal_io.write_prose` 의 atomic write 강화 (현재 `os.replace` → `session_state.atomic_write`).
  - **plugin Phase follow-up**: skill prompt 템플릿 갱신 (`/quick` 등이 helper protocol 박음), `agents/orchestrator.md` PM 도입 검토.
  - **회귀 위험**: 본 spec 박힌 후 Task -33/-34 가 spec 어긋나면 재PR. PR review 시 conveyor-design.md 정합 확인 필수.

### DCN-CHG-20260429-30
- **Date**: 2026-04-29
- **Rationale**:
  - `docs/conveyor-design.md` (DCN-CHG-20260429-29 PR #29 머지) spec 의 첫 코드 구현 단계. 컨베이어 / 훅 / impl_driver 모두 본 모듈의 session_id / run_id / live.json API 에 의존 → **인프라 우선 박음**.
  - 멀티세션 기본 가정 (사용자가 동시 다중 세션 띄움) → 격리 메커니즘 필수. OMC `SkillActiveStateV2` (active_runs map 다중 슬롯 + soft tombstone + heartbeat) + RWH `_meta` envelope (자기참조 sessionId 검증) + 3-tier resolution (env > pointer, 글로벌 폴백 제외) 차용.
  - atomic write 는 `signal_io.write_prose` 의 단순 `os.replace` 대비 강화 — POSIX O_EXCL+fsync+rename+dir fsync 4 단계로 race 0 + 디스크 fault tolerance + 0o600 권한 (다중 사용자 머신 보호).
- **Alternatives**:
  1. *RWH 단일 active_state + 자기참조* — 동시 다중 run 미지원. 한 세션에 백그라운드 ralph + foreground quick 띄우는 시나리오 막힘. 기각.
  2. *OMC active_skills map 만 + RWH 차용 0* — `_meta` envelope + atomic write 누락 → leftover 방어 약화. 기각.
  3. *글로벌 ~/.claude pointer 폴백 도입 (RWH issue #19)* — dcNess 자체 도그푸딩 시 SessionStart 훅 미적용 환경 대응. 4-가드 복잡도 vs 도그푸딩 가치 trade-off 검토 후 미채택. dcNess 자체 SessionStart 훅 작성으로 우회 가능. 기각.
  4. *(채택)* **OMC active_runs + RWH `_meta` envelope + atomic write + 2-tier resolution (글로벌 폴백 제외)**. conveyor-design.md §6 차용 표 정합.
- **Decision**:
  - 모듈 export 14 함수 + 4 상수.
  - **session_id**: OMC regex `^[a-zA-Z0-9][a-zA-Z0-9_-]{0,255}$`, OMC 3 변형 stdin (sessionId/session_id/sessionid), 2-tier resolution (env > pointer).
  - **run_id**: `run-{token_hex(4)}` 8 hex chars 정형 (RUN_ID_RE 검증). 16M 조합 → sid 안 충돌 사실상 0. 1000회 충돌 테스트 PASS.
  - **atomic_write**: O_EXCL (충돌 시 raise) + tmp 파일명 `{name}.tmp.{pid}.{uuid8}` (race-safe) + fsync + rename + dir fsync. 0o600 기본. 일부 파일시스템 (tmpfs) 의 dir fsync 미지원은 silent ignore.
  - **live.json envelope**: `_meta.sessionId/writtenAt/version` + top-level `session_id` 자기참조. read 시 sessionId 불일치면 leftover 로 거부 (빈 dict). update 시 `_meta` 항상 갱신 (옛 envelope 신뢰 0).
  - **active_runs slot 필드**: run_id, entry_point, started_at, last_confirmed_at, completed_at, run_dir, current_step, issue_num.
  - **cleanup**: completed+24h 또는 heartbeat dead+24h 슬롯 삭제. ttl_sec 인자로 조정 가능.
- **Follow-Up**:
  - **Task -31**: `harness/orchestration_agent.py` 폐기 + `harness/impl_driver.py` 새로 작성 (~50 줄). 본 모듈의 start_run / update_current_step / complete_run 사용.
  - **Task -32**: `hooks/session-start.sh` (stdin → sid 추출 → write_session_pointer + update_live 초기화) 신규. 본 모듈 함수 호출.
  - **Task -33**: `hooks/catastrophic-gate.sh` PreToolUse Agent 훅 신규. current_session_id + run_dir 으로 prose 종이 검사.
  - **Task -34** (선택): `signal_io.write_prose` 의 atomic write 를 본 모듈의 atomic_write 로 교체.
  - **회귀 위험**: 본 API 가 후속 모듈/훅의 인터페이스 spec 이 됨. signature 변경 시 cascade 영향 — major version 변경 또는 backward-compat alias 필수.

### DCN-CHG-20260429-29
- **Date**: 2026-04-29
- **Rationale**:
  - 직전 PR #28 (`DCN-CHG-20260429-28`, 옵션 c JSON 결정자 모델) 이 dcNess proposal §2.5 (prose-only) 와 충돌. 사용자 직접 검증 — 결정 LLM 의 JSON 출력 강제 = 형식 강제 사다리 부활. 도그푸딩 결과 (Claude Code CLI 어댑터 라이브 호출) 에서 LLM 이 ```json fence + Rationale prose 추가로 형식 미준수, 휴리스틱 파싱 추가는 정신 위반. → PR #28 close 결정.
  - 사용자와의 1시간+ 토론으로 새 모델 합의: **메인 클로드 = 시퀀스 결정자**, 컨베이어 = 멍청한 순회기, catastrophic = PreToolUse 훅. proposal §2.5 직접 정합.
  - 멀티세션이 사용자 환경 기본값. 격리 메커니즘 = OMC `SkillActiveStateV2` (active_runs map) + RWH `_meta` envelope/3-tier session_id resolution 차용. 글로벌 `~/.claude` 폴백 (RWH issue #19) 은 도그푸딩 가치 < 4-가드 복잡도라 미채택.
  - 코드 작업 시작 전 **spec 문서 먼저 박음** — 이전 토론 흐름이 디자인 표류 (옵션 c 채택 → 도그푸딩 → JSON 충돌 → 재토론) 였던 회귀 방지.
- **Alternatives**:
  1. *PR #28 그대로 머지 + 후속 PR 로 깎기* — 코드 ~95% 재사용 불가, 머지 이력 누적, governance docs 의 misleading entries 부담. 기각.
  2. *PR #28 force-push 갈아엎기* — 리뷰 어려움, 작업 이력 소실. 기각.
  3. *옵션 (α) 단일 라벨 결정 하이쿠 (`ADVANCE/RETRY/INSERT_SPEC_GAP/ESCALATE`)* — 라벨 늘면 driver hardcode 부담, 메인 결정 + 훅이 더 단순. 기각.
  4. *옵션 (β) 정적 dict 라우팅 (= 옵션 b 부활)* — 분기 룰 hardcode = §2.5 원칙 1 (룰 순감소) 약화. 기각.
  5. *PM 오케스트레이터 서브에이전트 즉시 도입* — stateless 단점 + 메인 직접 결정 round trip 추가. plugin Phase follow-up 으로 미룸.
  6. *(채택)* **PR #28 close + spec 문서 (`docs/conveyor-design.md`) 먼저 + 코드는 spec 후 별도 Task** — 디자인 표류 방지 + 코드 작업의 단일 spec 확보.
- **Decision**:
  - 옵션 6. PR #28 close (이미 GitHub 처리됨), `docs/conveyor-design.md` 12 절 신규 작성, `docs/orchestration.md` §9 정정.
  - **컨베이어 모델 핵심**:
    1. 메인 클로드가 `orchestration.md` §4 결정표 prose 직접 읽고 `list[Step]` 구성 → JSON 파싱 0
    2. 컨베이어 (`harness/impl_driver.py` 별도 Task ~50 줄) = 시퀀스 순회 + Agent 호출 + `signal_io.interpret_signal` + `Step.advance_when` 비교 + `ConveyorPause` 반환
    3. `Step.allowed_enums` (interpret_signal 후보 집합) ⊇ `advance_when` (성공 enum 부분집합) — 두 필드로 분리
    4. catastrophic backbone (§2.3 4룰) + HARNESS_ONLY_AGENTS (§7.1) = `hooks/catastrophic-gate.sh` (별도 Task) 가 PreToolUse Agent 에서 강제. 컨베이어 코드 conditional 0.
    5. `_meta` envelope + atomic write (O_EXCL+fsync+rename+dir fsync, 0o600) = RWH 차용
    6. `live.json.active_runs` map = OMC 차용 (다중 동시 run 지원, soft tombstone, heartbeat)
  - **세션 정책**:
    - session_id = OMC stdin 3 변형 fallback + RWH 3-tier resolution (env → project pointer). 글로벌 폴백 미채택.
    - run_id = `run-{token_hex(4)}` (16M 조합, sid 안 격리)
    - 디렉토리 = `.claude/harness-state/.sessions/{sid}/runs/{run_id}/<agent>[-mode].md`
    - env 전파: 컨베이어가 `DCNESS_SESSION_ID` / `DCNESS_RUN_ID` set/unset
- **Follow-Up**:
  - **별도 Task** — `harness/impl_driver.py` 새로 작성 (~50 줄), `harness/orchestration_agent.py` 폐기, `harness/session_state.py` 신규 (OMC+RWH 차용)
  - **별도 Task** — `hooks/session-start.sh` (sid 추출 + pointer + live.json 초기화), `hooks/catastrophic-gate.sh` (PreToolUse Agent §2.3 검사) 신규
  - **별도 Task** — `signal_io.write_prose` 의 atomic write 강화 (현재 `os.replace` → O_EXCL+fsync+rename+dir fsync, 0o600)
  - **plugin Phase follow-up** — `agents/orchestrator.md` (PM 도입 검토), 도입 시점 사용자 결정
  - **회귀 위험**: 본 spec 박힌 이후 후속 코드 Task 들이 spec 어긋나는지 — 매 코드 Task PR review 시 conveyor-design.md 정합 확인 필수
  - **측정 (proposal §2.5 원칙 5)**: 30일 후 `live.json` 의 active_runs 슬롯 평균 수, last_confirmed_at heartbeat 신선도, ConveyorPause 빈도 측정 → 메인 직접 결정 vs PM 도입 의사결정 데이터화

### DCN-CHG-20260429-27
- **Date**: 2026-04-29
- **Rationale**:
  - 사용자 요청 — "에이전트들 싹 다 점검 좀 하자. 너무 길고 복잡하고 제약 많아. 우리 프로젝트 성격에 맞춰서 자율성을 늘리고 판단 기준을 스스로 할 수 있도록."
  - 진단: 24 파일 4350 줄. 6 가지 과잉 강제 패턴 — (1) 자기인식 강박 ("🔴 정체성" + "절대 출력 금지 패턴" 16~20 줄, RWHarness 위임 사고 방지 정합이지만 dcNess 메인 직접 작업 모드엔 과잉) (2) 거대 메타 룰 (Anti-AI-Smell 100+ 줄, 일부 권고를 강제로 박음) (3) Phase/Step 단계 강박 (Step 1~7 자율 판단 여지 0) (4) 산출물 마크다운 템플릿 박힘 (와이어프레임 ASCII / 표 / Doc 섹션 형식 강제) (5) 결론 enum 예시 반복 (모드마다 4~5 회) (6) 다중 체크리스트.
  - 모두 proposal §2.5 원칙 1 (룰 순감소) + 원칙 2 (강제 vs 권고) + 원칙 3 (agent 자율성) 위반.
  - 형식 어휘 sweep (`-26`) 직후. 형식 강제는 폐기됐으나 *내용 강제* (제약 다발) 가 잔존 — 본 Task 가 그 잔존 정리.
- **Alternatives**:
  1. *부분 정리 (가장 긴 3 파일만)* — 일관성 깨짐. 다른 21 파일이 여전히 비대칭. 기각.
  2. *agent 별 분리 PR (13 PR)* — review 부담 ↓ but 일관성 보장 어려움 + 변환 패턴 표류. 기각.
  3. *(채택)* **단일 PR 24 파일 일괄 변환 + 6 원칙 변환 가이드 정착**. 전체 일관성 + 한 PR review.
  4. *Anti-AI-Smell 별도 docs/ 분리* — 새 파일 생성 부담 + cross-link 깨짐 risk. 가치 있지만 압축으로 충분. 기각.
- **Decision**:
  - 옵션 3. 6 변환 원칙 (A~F) 정합 일괄 변환. 사용자 자율 판단 위임 부분 (Anti-AI-Smell 처리, 페르소나 보존, 옵션) 은 보수적 자율 판단 — Anti-AI-Smell 1 단락 압축, 페르소나 1~2 줄 압축, 옵션 1 단일 PR.
  - **6 변환 원칙**:
    - **(A) frontmatter = 자기인식**: "🔴 정체성" 강박 + "절대 출력 금지 패턴" list 폐기 → frontmatter `name`/`description` + 1 줄 메타 ("> 본 문서는 X 에이전트의 시스템 프롬프트. 호출자가 지정한 모드 즉시 수행 + prose 마지막 단락에 결론 enum 명시 후 종료."). RWHarness 위임 사고 방지 정합은 dcNess 메인 직접 작업 모드엔 과잉.
    - **(B) 원칙 1 줄 + 자율 판단 1 줄**: 다중 체크리스트 → "X 원칙. 위반 발견 시 prose 본문에 명시 후 escalate."
    - **(C) Phase/Step 단계 강박 → 1 단락 권고**: "수행 흐름 (자율 조정 가능)" 단락 1 개로 압축.
    - **(D) 산출물 형식 자율**: "산출물 정보 의무 (형식 자유)" 명시. 마크다운 템플릿 박힘 폐기.
    - **(E) 결론 enum 예시 1 회**: 헤더 자연어 3 라인 (sweep `-26`) 으로 충분. 모드마다 예시 반복 폐기.
    - **(F) catastrophic 분리**: "절대 금지" 다중 → "권한 경계 (catastrophic)" 1~2 항목 + 권고는 prose.
  - **자기인식 강박 폐기 정당화**: dcNess 정체성 = 메인 Claude 직접 작업 모드 (CLAUDE.md §0). RWHarness 의 "위임 사고 방지" 가 부재. plugin 배포 후 사용자 프로젝트에서도 frontmatter `description` 만으로 자기인식 충분 — Claude SDK 의 agent 호출 시 description 이 시스템 프롬프트 컨텍스트로 들어감.
  - **Anti-AI-Smell 1 단락 압축 정당화**: 가치는 보존 (디자인 가이드 작성 시 자기 점검 권고). 단 "5 가지 중 3 개 만족 시 자동 reject" 같은 hard rule 은 *권고* 영역 — proposal §2.5 원칙 2 (catastrophic 만 강제) 정합. 별도 docs/ 분리는 cross-link 부담 + 새 파일 = 룰 부채 → 기각.
  - **폐기된 컨벤션 섹션 제거**: 24 파일 모두 끝에 박혀 있던 "폐기된 컨벤션" 섹션 제거. 의미는 `docs/orchestration.md` §0.1 (RWHarness vs dcNess 차이 표) + `docs/status-json-mutate-pattern.md` §1·§3·§11.4 가 SSOT — 24 파일 반복 불필요.
  - **Cross-link 통일**: 모든 파일 끝에 `## 참조` 섹션 — `docs/orchestration.md` (시퀀스/핸드오프/권한) + `docs/status-json-mutate-pattern.md` (prose-only 발상). 신규 컨트리뷰터 navigation.
  - **proposal §2.5 원칙 정합**:
    - 원칙 1 (룰 순감소): 4350 → 1683 줄 (61% 감소). 신규 룰 0.
    - 원칙 2 (강제 vs 권고): catastrophic 분리 (각 파일 "권한 경계 (catastrophic)" 1~2 항목 명시). 그 외 다중 체크리스트는 권고/prose.
    - 원칙 3 (agent 자율성): "수행 흐름 (자율 조정 가능)" 명문. 산출물 "정보 의무 (형식 자유)". 단계 강박 X.
    - 원칙 4 (catastrophic 시퀀스 보존): src/ 외 mutation 차단·write 경로 제한 등 catastrophic 은 보존.
    - 원칙 5 (30일 측정 후 강제): 기존 룰 정리만, 신규 강제 0.
- **Follow-Up**:
  - **(검증)** plugin 배포 dry-run 시 압축 후 agent 가 실제 호출 흐름에서 정상 동작 확인 (자기인식 frontmatter 만으로 충분한지). 부족 시 1 줄 메타 보강.
  - **(별도 Task)** 옵션 (a)/(b)/(c) 코드 driver 채택 결정 + 구현 (orchestration.md §9). 본 압축 후 agents/* 가 driver 의 입력으로 더 깔끔.
  - **(별도 Task)** Anti-AI-Smell 운영 데이터 누적 (designer / ux-architect 산출물의 클리셰 빈도) → 패턴 발견 시 권고 강화 또는 별도 docs 추출.
  - **(측정)** 본 압축 전후 agent 호출 비용·완료 시간 비교 (token 효율 분석 스킬). agent prompt 60% 감소 → 호출당 입력 토큰 감소 예상.

### DCN-CHG-20260429-26
- **Date**: 2026-04-29
- **Rationale**:
  - 외부 review 지적 — "`agents/validator/code-validation.md` 등의 헤더에 `@MODE:VALIDATOR:CODE_VALIDATION → prose emit` + 코드 블록 안 `@PARAMS: { ... }` + `@CONCLUSION_ENUM: PASS | FAIL | SPEC_MISSING` 가 박혀 있음. 이건 우리가 폐기한 status JSON schema 의 약화 변형. 한 번 형식이 doc 안에 박히면 → 'agent 가 @PARAMS 빠뜨림' → '강제 룰 추가' → MARKER_ALIASES 사다리 재현. caller prompt 가 동적 주입할 메타 정보면 OK 지만, agent doc 자체에 박힌 건 형식 강제 — proposal §2.5 원칙 3 위반."
  - 자체 점검 — 24 파일 모두 영향 (177 hit). Phase 2 iter 1~5 동안 RWHarness 원본 패턴 (`@MODE:X:Y` 헤더) 을 *그대로* 옮긴 게 원인. dcNess 변환 의도 (prose-only) 와 잔재 어휘가 모순.
  - 시점 — Phase 3 (signal_io / interpret_strategy / orchestration.md) 모두 완료 후. agents/* 만 형식 사다리 잔재. 지금 정리 안 하면 plugin 배포 시 사용자 프로젝트로 *형식 강제 어휘* 가 그대로 전파.
- **Alternatives**:
  1. *접두사 `@` 만 제거 (예: `MODE:X:Y` 로 바꾸기)* — 시각적 형식 강제 신호는 유지. 본질 동일 (agent doc 안 형식 강제). 기각.
  2. *코드 블록 안 메타만 남기고 표는 유지* — 표 안 `@MODE:` 접두사 = 형식 신호. 부분 정리는 사다리 재현 risk. 기각.
  3. *(채택)* **24 파일 일괄 sweep — 헤더 메타 블록 자연어화 + 표 접두사 제거 + 본문 참조 자연어 변환**. 한 PR 로 전체 처리.
  4. *agents/* 분할 (sub-agent 별 PR)* — 5~10 PR. review 부담 ↓ but 일관성 보장 어려움 + dangling 참조 위험. 기각.
- **Decision**:
  - 옵션 3. 단일 PR 24 파일 일괄.
  - **변환 패턴 정착** (validator/code-validation.md 가 reference):
    - Before: `\`@MODE:X:Y\` → prose emit (마지막 단락에 결론 enum)` + `\`\`\` @PARAMS: { ... } @CONCLUSION_ENUM: A | B \`\`\``
    - After: 자연어 3 라인 — `**모드**: 설명. **결론**: prose 마지막 단락에 \`A\` / \`B\` 중 하나 명시. **호출자가 prompt 로 전달하는 정보**: 인자 목록.`
  - **표 안 `@MODE:` 접두사 제거** — `| @MODE:ARCHITECT:SYSTEM_DESIGN | ... |` → `| System Design | ... |`. 모드명만 남김.
  - **본문 참조 자연어** — `@PARAMS.issue 에서 추출` → `호출자가 prompt 로 전달한 이슈 본문에서 추출`. ux-architect / product-planner 의 "절대 출력 금지 패턴" 안 `@MODE:X:Y` 예시도 자연어 모드명으로.
  - **"폐기된 컨벤션 (참고)" 본문은 *원리 보존*** — 마커/스키마 *사용 금지* 명시는 보존. 단 형식 어휘 (예: `---MARKER:LGTM---`, `@OUTPUT JSON schema`) 자체는 *원리* 로만 표현 ("정형 텍스트 마커 토큰", "구조 강제 메타 헤더"). 신규 컨트리뷰터가 어휘를 *되살리지 않도록* 근거만 남김.
  - **proposal §2.5 원칙 정합 명시** — 모든 "폐기된 컨벤션" 섹션 앞에 "dcNess 는 다음 형식 강제 어휘를 사용하지 않는다 (proposal §2.5 정합)" 한 줄 추가.
  - **proposal §2.5 원칙 정합**:
    - 원칙 1 (룰 순감소): 형식 강제 어휘 폐기 → 룰 부채 감소.
    - 원칙 2 (강제 vs 권고): 본 sweep 자체가 원칙 2 정합 — agent 안 형식 강제(deny risk) → 자연어 권고/안내(warn).
    - 원칙 3 (agent 자율성): 가장 강한 정합 — 본 sweep 의 핵심 의도. agent prose 자유 emit + 형식 0.
    - 원칙 4 (catastrophic 시퀀스 보존): 본 sweep 은 시퀀스 변경 없음. agents/*.md 만 변환.
    - 원칙 5 (30일 측정 후 강제): 본 sweep 은 *기존 잔재 정정*. 신규 강제 0.
  - **review 의 stale 부분 정정**: review 가 "메타 LLM 미통합" 이라고 지적했으나 사실은 통합됨 (`harness/llm_interpreter.py` `-22`, `interpret_strategy.py` `-23`, `analyze_metrics.mjs` `-23` 모두 머지). orchestrator (impl_driver) 부재는 정확 (옵션 a/b/c 결정 보류 상태, `docs/orchestration.md` §9). 본 Task 의 scope 외.
- **Follow-Up**:
  - **(별도 Task `-27`)** 300+ 라인 파일 분리 — `ux-architect.md` (550) / `product-planner.md` (418) / `designer.md` (407). 출력 예시 등을 sub-doc 으로 분리 (architect 패턴 정합).
  - **(별도 Task)** 코드 driver (옵션 a/b/c) 채택 결정 + 구현. orchestration.md §9 의 옵션 (c) Orchestration Agent 가 가장 dcNess 정신 정합.
  - **(별도 Task)** RWHarness 와의 drift 모니터링 — RWHarness 가 agent docs 패턴 변경 시 dcNess sweep 반복 위험. 본 sweep 의 변환 패턴을 cherry-pick 가이드에 박아야.
  - **(검증)** plugin-dryrun-guide §5 smoke test 시 agent prose emit 이 자연어 변환 후에도 정상 동작하는지 확인.

### DCN-CHG-20260429-25
- **Date**: 2026-04-29
- **Rationale**:
  - Phase 3 종결(`-24`) 직후 사용자 지적 — proposal §2.5 원칙 4 가 "impl_loop 시퀀스 보존" 명시했고 §11.4 "작업 순서 강제" 도입 의무 명문이지만, *그 시퀀스의 정의 SSOT* 자체가 dcNess 안에 부재. agents/*.md 13 docs 는 *개별 agent* 의 결론 enum 박음, signal_io 등 인프라는 *결론 추출기*, 거버넌스는 *commit/PR 룰* — 어디에도 시퀀스 정의 (어떤 enum → 어떤 다음 agent / retry / escalate / 권한 매트릭스) SSOT 없음.
  - 사용자 정정 — RWHarness 도 시퀀스 SSOT 가 따로 있음 (`harness-spec.md` §4.2/§4.3 + `harness-architecture.md` §3). impl_loop.py 는 그 SSOT 의 *코드 driver* 일 뿐. dcNess 도 같은 패턴 가야 한다.
  - migration-decisions §2.1 의 RWHarness `impl_loop.py` "DISCARD (dcNess 한정)" 처리는 *코드 driver* 폐기 의도였으나 *룰 자체* 까지 같이 폐기한 결과가 됨. 룰 부활 필요.
  - dcNess 정체성 = "RWHarness 의 오케스트레이션 동일 보존 + 형식 강제만 LLM 으로 대체" (사용자 정리). 따라서 본 SSOT = RWHarness 의 시퀀스/핸드오프/권한 매트릭스 *그대로* + 형식 어휘만 변환.
- **Alternatives**:
  1. *분산 정의* — 각 agents/*.md 끝에 "다음 trigger" 권고 추가 (per-agent SSOT). 13 곳 일관성 보장 어려움. 또한 RWHarness 의 단일 spec 패턴과 어긋남. 기각.
  2. *메인 Claude 자율* — CLAUDE.md 가이드만, 시퀀스 명문 X. 결정 일관성 ↓. proposal §2.5 원칙 4 보존 의무 충족 X. 기각.
  3. *(채택)* **단일 SSOT `docs/orchestration.md`** — RWHarness §4.2 + §4.3 + §3 통째 가져와 형식 어휘만 변환. 11 섹션 단일 파일.
  4. *별도 권한 매트릭스 분리* (`docs/access-matrix.md`) — 시퀀스와 매트릭스 두 파일. RWHarness 의 §3 안에 묶인 패턴과 어긋남, cross-link 깨짐 위험. 기각.
  5. *proposal §부록 으로 박기* — proposal SSOT 와 운영 SSOT 분리 흐려짐. proposal 은 *발상*, 본 SSOT 는 *적용 표현*. 분리 유지. 기각.
- **Decision**:
  - 옵션 3. 단일 파일 `docs/orchestration.md` 11 섹션 + proposal `status-json-mutate-pattern.md` §11.4 cross-link 만 추가.
  - **Mermaid 분할**: 큰 흐름 1 (game gate sequence) + 진입 경로별 mini graph 6 (신규 기능 / UI / 리디자인 / 일반 구현 / 작은 버그 / 버그 보고). RWHarness §4.3 표 정합 — 단일 거대 그래프는 가독성 ↓.
  - **결정표 13 agent 펼침**: validator 5 mode + architect 7 mode 별 행 분리. agent 단일 행 + sub-row 패턴은 markdown 표에서 읽기 어려움.
  - **catastrophic 백본 4 항목 명시** (§2.3): src/ 변경 후 validator 우회 금지 / pr-reviewer LGTM 없이 merge 금지 / engineer 가 module-plan 통과 없이 src/ 작성 금지 / PRD 변경 후 plan-reviewer + ux-architect 검토 없이 architect 진입 금지. 코드 driver 도입 시 hook 강제 대상.
  - **DCNESS_INFRA_PATTERNS** (§7.4): RWHarness `HARNESS_INFRA_PATTERNS` 안 `r'orchestration-rules\.md'` 옛 어휘 잔재를 본 SSOT 가 정정 — dcNess 의 SSOT 파일명은 `docs/orchestration.md` (단일).
  - **옵션 (c) Orchestration Agent + 동적 시퀀스** (§9): 사용자 회의 발상. driver 가 sequence list 만 받아 순회, 각 step 후 메타 LLM agent 가 prose 보고 sequence 동적 갱신. catastrophic backbone (§2.3 + §7) 은 코드 hook 으로 강제. 채택 결정은 별도 Task — 본 SSOT 안엔 옵션 카탈로그로만.
  - **proposal §2.5 원칙 정합**:
    - 원칙 1 (룰 순감소): 신규 docs ~450 줄. 그러나 *기존 분산된 의도* (proposal §2.5 / §11.4 / 13 agents/*.md) 의 *집계 + 명시화* — 새 진실 없음.
    - 원칙 2 (강제 vs 권고): §8 에서 명시 분리 — catastrophic 만 코드 강제, 그 외 권고/측정.
    - 원칙 3 (agent 자율성): §8.2 agent 자율 영역 명시 — prose 형식 / handoff 본문 / preamble / 도구 호출 순서 자유.
    - 원칙 4 (catastrophic 시퀀스 보존): §10 직접 인용 + §2.3 catastrophic 4 항목 명문화.
    - 원칙 5 (30일 측정 후 강제): 옵션 (c) 동적 시퀀스 도입 결정은 도그푸딩 후 — 본 SSOT 는 옵션 카탈로그만.
  - **메인 dcNess 자체 작업 모드 처리**: §1.2 에 명시 — 본 SSOT 는 *권고* (CLAUDE.md §0 정합). hook 차단 X.
- **Follow-Up**:
  - **(별도 Task)** 옵션 (a)/(b)/(c) 채택 결정 + 코드 driver 구현. 옵션 (c) 가 가장 dcNess 정신 정합이지만 결정론 risk → smoke test 후 결정.
  - **(별도 Task)** Orchestration Agent (옵션 c 채택 시) 의 prompt 설계 — 입력 = 직전 prose + 현재 sequence + 컨텍스트, 출력 = 갱신된 sequence list. 메타 LLM 호출 비용 측정.
  - **(별도 Task)** dcNess 의 `agent-boundary.py` (또는 등가) 도입 — 본 SSOT §7 권한 매트릭스의 *코드 강제*. 현재 dcNess 자체엔 hook 없음 (인프라 미도입).
  - **(별도 Task)** 본 SSOT 와 RWHarness 의 drift 모니터링 — RWHarness 가 §4.2 시퀀스 변경 시 본 SSOT 도 갱신 의무. proposal §11.5 정합.
  - **(검증)** plugin-dryrun-guide §6 의 1 cycle 도그푸딩 시 본 SSOT 가 실제 가이드 역할 하는지 확인.

### DCN-CHG-20260429-24
- **Date**: 2026-04-29
- **Rationale**:
  - Phase 3 iter 1~4 (Task-ID 검증 / branch protection / haiku interpreter / heuristic-fallback + analyzer) 누적 후 *종결 시그널* 필요. proposal §6 acceptance 항목별 PASS 매핑 안 하면 Phase 4 진입 정합 모호.
  - proposal §12 (plugin 배포 절차) 는 SSOT 안 *intent* 만 제시 — 실 운영 단계 절차 (manifest 검증 명령어, smoke test python 코드, fitness 측정 명령) 는 문서화 안 됨. 운영자 (사용자) 가 매번 proposal 안 read + 자기 추정으로 명령어 작성 → 부담.
  - PROGRESS.md 의 "Phase 3 (확장) — Plugin 배포 dry-run (선택)" TODO 항목이 *별도 섹션* 으로 분리돼 있어 Phase 3 본 항목과 관계 모호. iter 5 가 둘 통합.
- **Alternatives**:
  1. *PROGRESS.md 만 갱신* — proposal SSOT acceptance 표시 누락 → 향후 검색 시 Phase 3 PASS 여부 추적 어려움. 기각.
  2. *plugin-dryrun-guide 만 작성, status-doc 미수정* — Phase 3 종결 시그널 부재. Phase 4 진입 정합성 모호. 기각.
  3. *(채택)* **plugin-dryrun-guide + status-doc §6 acceptance 표시 + PROGRESS 매핑 표 + Phase 4 TODO 진입** 4종 동시 — Phase 3 닫기 + Phase 4 시작 준비를 한 PR 에서.
  4. *Phase 4 까지 한 PR 에 묶기* — Phase 4 는 *측정* 작업이라 dry-run 가이드 절차 실행 후 데이터 누적 필요. 분리.
- **Decision**:
  - 옵션 3. 4종 동시 + Phase 4 TODO 만 박고 측정 작업은 별도 Task.
  - **plugin-dryrun-guide 의 11 섹션 구조**: 사전검증 → manifest → marketplace → 충돌회피 → smoke test (실 LLM 1 호출) → 1 cycle 도그푸딩 → 완전 제거 → 즉시 롤백 → acceptance → 본 가이드 관계 → Phase 4 후속. 운영자가 *순서대로* 따라가면 dry-run 완료.
  - **status-doc §6 의 acceptance 표시 정책**:
    - "자연 만족" — RWHarness 와 다른 정체성으로 처음부터 미도입 → ✅ 가짜 표시 X, *기록*. (commit-gate.py / ENV gate)
    - "신규 워크플로" — 실제로 한 일. (`-08`/`-09`/`-10`/`-20`/`-21`)
    - "비대상" — RWHarness 영역으로 dcNess 적용 외 (CHG-14.1 폐기 정정).
    - "dcNess 한정 추가" — proposal 에 명시 안 됐지만 본 fork 가 추가한 가치 (Task-ID 검증 / interpreter / analyzer / 가이드).
  - **PROGRESS 매핑 표 신설**: proposal §6 항목 ↔ dcNess Task-ID 매핑 1:1. Phase 3 검색 시 단일 표로 추적.
  - **proposal §2.5 원칙 정합**:
    - 원칙 1 (룰 순감소): 신규 LOC 0 (코드). 신규 docs ~250 줄. 룰 자체는 추가/삭제 0.
    - 원칙 2 (강제 vs 권고): plugin-dryrun-guide 는 *권장 절차*. 강제 hook 0.
    - 원칙 3 (agent 자율성): agent prompts 변경 0.
    - 원칙 4 (catastrophic 시퀀스): plugin uninstall 단계 (§7) 에 "🔴 destructive" 명시 + 사용자 동의 강제.
  - **Document-Exception 없음**: status-doc 갱신은 spec 의도지만 docs/ 직속이라 docs-only 분류. 게이트 비요구이므로 자연 통과. 분류 매트릭스 제약 자체는 별도 Task 검토 가능.
- **Follow-Up**:
  - **Phase 4 진입** (별도 Task-ID 시리즈):
    - 컨텍스트 layer 측정 (CLAUDE.md + agents/*.md + AGENTS.md + ...)
    - LOC 순감소 측정 (RWHarness baseline 비교)
    - poor_cache_util 비용 측정 (improve-token-efficiency 스킬 실행)
    - plugin 배포 dry-run 실행 (운영자, 본 가이드 §1~§9)
    - cache hit rate 측정 (R5 control)
  - **(검증)** plugin-dryrun-guide §5 의 smoke test 를 운영자가 1회 실행 → 실 ANTHROPIC_API_KEY 환경에서 휴리스틱 hit + LLM fallback 양 케이스 확인.
  - **(별도 Task)** PROGRESS 매핑 표 패턴을 향후 Phase 4 종결 시에도 동일하게 사용.

### DCN-CHG-20260429-23
- **Date**: 2026-04-29
- **Rationale**:
  - iter 3 의 haiku interpreter 는 *모든* 호출을 LLM 으로 보냄 (호출자가 직접 주입 시). proposal §3 의 의도 = "휴리스틱이 ambiguous 일 때만 LLM" — iter 3 은 swap point 만, 합성 정책 부재.
  - 운영 안전성 = 휴리스틱 hit 비율 측정 + ambiguous 패턴 카탈로그. proposal R1 / R8 acceptance 의 *측정 인프라* 가 비어있음.
  - PR #22 머지 후 시점, signal_io / llm_interpreter 가 둘 다 안정 → 합성 모듈 + 분석기 추가가 자연스러운 다음 단계.
- **Alternatives**:
  1. *interpret_signal 자체 수정* — heuristic-first + LLM-fallback 을 inline. 기존 함수 시그니처 변경 → 회귀 위험 + signal_io 책임 분리(파일 I/O + 결론 추출 + 합성 정책) 위반. 기각.
  2. *signal_io 안에 새 함수만 추가* — 책임 혼재. interpret_signal vs interpret_with_fallback 두 함수 같은 모듈 → 호출자 혼동. 기각.
  3. *(채택)* **별도 `harness/interpret_strategy.py`** + signal_io 미수정 + interpret_with_fallback 단일 export. 책임 깔끔.
  4. *분석 스크립트만, 합성은 호출자 책임* — 매 호출자가 try/except heuristic + LLM 작성 → 중복. 기각.
- **Decision**:
  - 옵션 3. 신규 모듈 + 합성 함수 + 분석기 + 7 테스트.
  - **outcome 5종**:
    - `heuristic_hit` — 휴리스틱 단어경계 단일 매칭 (LLM 미호출, 비용 0)
    - `llm_fallback_hit` — heuristic ambiguous → LLM 호출 → 결론
    - `llm_fallback_unknown` — LLM 도 UNKNOWN/allowed 외 (proposal R1 카탈로그 핵심)
    - `heuristic_ambiguous_no_fallback` — LLM 미주입 + heuristic ambiguous (개발/테스트 모드)
    - `heuristic_not_found` / `heuristic_empty` — prose 자체 부재 (LLM fallback 무의미)
  - **Python 3 except as 변수 unbind 처리**: `heuristic_exc` 를 외부 변수 (`heuristic_detail`/`saved_exc`) 로 보존. PEP 3134 정합 (except 블록 종료 시 변수 명시 unbind 로 GC 사이클 회피).
  - **defensive ValueError on LLM contract 위반**: llm_interpreter 가 allowed 외 값 반환 시 즉시 ValueError (silent corruption 차단).
  - **분석기 fitness 자동 판정**: proposal §5 Phase 4 의 두 목표 (cycle 당 메타 LLM < $0.10, ambiguous < 5건/cycle) 를 PASS/WATCH 출력 — 운영자가 매 cycle 후 수동 실행.
  - **proposal §2.5 원칙 정합**:
    - 원칙 1 (룰 순감소): 신규 LOC ~120 (strategy + tests + analyzer). signal_io / llm_interpreter 변경 0.
    - 원칙 2 (강제 vs 권고): outcome telemetry 는 *측정* 만. fitness 판정도 PASS/WATCH (deny X).
    - 원칙 3 (agent 자율성): agent 측은 변경 0. 합성은 harness 측 책임.
    - 원칙 5 (30일 측정 후 hook): 본 합성 + analyzer = 30일 데이터 누적 인프라. 향후 (1) ambiguous 빈도 ↑ 시 agent writing guide 정정 (2) 비용 ↑ 시 retry/cache 정책 정당화.
  - **테스트 cwd `.metrics/` 오염 fix**: `make_haiku_interpreter` 의 telemetry_dir 누락 3 케이스 (`ApiFailureTests`, `ValidationTests`, `PromptConstructionTests`) → setUp/tearDown 추가. 향후 회귀 방지.
- **Follow-Up**:
  - **iter 5 (Phase 3 종결)**: Phase 3 종결 + plugin 배포 dry-run 가이드 정리.
  - **(별도 Task)** 휴리스틱 hit rate 90%+ 가 1 cycle 데이터로 확인되면 dcNess 의 self-application (메인 작업 모드) 에 interpret_with_fallback 채택.
  - **(별도 Task)** ambiguous 누적 시 패턴 분석 → agent writing guide 정정 (proposal R1 사이클).
  - **(검증)** ANTHROPIC_API_KEY 보유 운영자가 1 cycle 실 호출 후 analyzer 실행 → fitness 판정.

### DCN-CHG-20260429-22
- **Date**: 2026-04-29
- **Rationale**:
  - Phase 3 iter 3. `harness/signal_io.py` (DCN-CHG-20260429-13) 의 `interpret_signal(..., interpreter=)` 는 휴리스틱 fallback 만 가능했음. 프로덕션 swap 함수가 부재 → proposal §3 의 "메타 LLM (haiku) 1 호출" 메커니즘이 비어있는 상태.
  - migration-decisions §3 의 "메타 LLM (haiku) interpreter 통합" TODO 와 PROGRESS.md Phase 2 미완 항목 정합. Phase 3 의 외부화 + sweep 의 일환.
  - 휴리스틱이 ambiguous (단어경계 0 hit / 다중 hit) 일 때만 LLM 호출 = 비용 minimization (proposal §3 cycle 당 $0.001 미만 목표).
- **Alternatives**:
  1. *signal_io.py 안에 직접 SDK import* — anthropic 패키지 미설치 환경 (CI / 외부 컨트리뷰터) 에서 import error. 분리 모듈 + 지연 import 가 안전.
  2. *별도 모듈 + 즉시 import* — anthropic 미설치 시 모듈 import 자체 실패. 지연 import (factory 안에서 import) 가 적절.
  3. *(채택)* **별도 `harness/llm_interpreter.py` + factory 안 지연 import + DI client**. 테스트는 mock client 주입으로 실 API 호출 0.
  4. *prompt caching 도입* — system prompt ~50 토큰. haiku 의 cache minimum (~1024 토큰) 미달. 매 호출 prose 다름 → cache hit 0. 손익 negative. 기각 (claude-api skill 의 trigger 정합 검토했지만 본 use case 엔 N/A).
  5. *다중 retry / exponential backoff* — proposal §3 / R1 의 "ambiguous → 사용자 prompt" fallback. 본 Task 에선 기본 단일 호출 + ambiguous propagate 만 구현. 재시도 정책은 호출 측 결정.
- **Decision**:
  - 옵션 3. 분리 모듈 + factory + DI + ambiguous fallback.
  - **모델**: `claude-haiku-4-5-20251001` (시스템 cutoff 정합, 가장 저렴 + classifier 용도 충분).
  - **prompt 설계**:
    - system: allowed enum + "한 단어, 대문자, UNKNOWN if 모호" 룰. 50~100 토큰.
    - user: prose 마지막 4000 chars (~1000 tokens, proposal R2 정합).
    - max_tokens=10 (한 단어 충분).
  - **응답 파싱**: 첫 단어 → uppercase → 구두점 strip → allowed 매칭. 매칭 실패 = `MissingSignal('ambiguous')`. raw response 200 chars 까지 telemetry 기록 (디버깅용).
  - **Telemetry SSOT**: `.metrics/meta-llm-calls.jsonl` (proposal R8 정합). 항목: ts/model/allowed/raw_response[:200]/parsed/input_tokens/output_tokens/cost_usd/elapsed_ms.
  - **비용 모델**: haiku 4.5 input $1/1M, output $5/1M. 평균 호출 = 80 in + 5 out ≈ $0.000105. cycle 당 65 호출 = ~$0.007 (proposal §3 의 $0.065 추정보다 9× 저렴 — haiku 가격 인하 반영).
  - **proposal §2.5 원칙 정합**:
    - 원칙 1 (룰 순감소): 신규 LOC ~180 (interpreter + tests). signal_io 의 swap point 활용 — 추가 함수형 강제 0.
    - 원칙 2 (강제 vs 권고): LLM 응답 형식은 prompt *권고* (system 안에 ALL CAPS 단일 단어 출력 룰). 형식 강제 X — 모호 시 ambiguous propagate.
    - 원칙 3 (agent 자율성): agent prose emit 형식은 그대로 자유. interpreter 가 결론을 추출.
- **Follow-Up**:
  - **(검증)** ANTHROPIC_API_KEY 환경에서 실 호출 1회 — 본 Task 에선 미실시 (auto mode + secrets 정책). 운영자 수동.
  - **iter 4 (Phase 3)**: ambiguous prose 카탈로그 + 휴리스틱 hit rate 측정 — telemetry JSONL 분석 스크립트.
  - **iter 5 (Phase 3)**: Phase 3 종결 + plugin 배포 dry-run 가이드.
  - **(별도 Task)** ambiguous 누적 패턴 발견 시 agent prose writing guide 정정 (proposal R1 카탈로그 → 작성 가이드 강화 사이클).
  - **(별도 Task)** prompt caching 재검토 — agent prose 가 표준화돼 system prompt 가 ≥1024 토큰 되면 도입 가능.
  - **(별도 Task)** 비용 폭증 시 retry/backoff/cache 정책 — 주간 cost 리포트 첫 1주 데이터 후 결정.

### DCN-CHG-20260429-21
- **Date**: 2026-04-29
- **Rationale**:
  - Phase 3 iter 1(Task-ID 검증) 직후 iter 2. proposal §5 Phase 3 의 4 항목 중 "Gate 5 (LGTM flag) → branch protection required reviewers" 이행.
  - dcNess 는 RWHarness `class Flag` (in-process LGTM flag) 를 자연 폐기 (migration-decisions §2.2 — `class Flag` DISCARD). LGTM 의 의미적 강제 메커니즘이 *비어 있음* — PR 머지가 사실상 자유.
  - 외부화 대안 = GitHub branch protection. RWHarness 이 자체적으로 못 한 GitHub 직접 강제를 dcNess 는 처음부터 채택 → proposal §11 4-pillar #2 정합 + RWHarness 부채 제거.
  - 자동 적용 스크립트 vs UI 가이드 *둘 다* 도입 — admin 권한 의존성(스크립트 403 시 수동 fallback) + 미래 재적용/CI 추가 시 멱등 PUT 활용.
- **Alternatives**:
  1. *문서만 작성, 스크립트 X* — 운영자가 매번 UI 클릭. 멱등 검증 없음. CI 게이트 추가 시 누락 위험. 기각.
  2. *스크립트만 작성, 문서 X* — admin 권한 부재 시 fallback 가이드 부재. 비-admin 컨트리뷰터가 응급 적용 못 함. 기각.
  3. *(채택)* **스크립트 + 가이드 + governance §2.8 룰 정의 3종 동시**. 스크립트 = 자동, 가이드 = 수동/검증, §2.8 = 정의(SSOT).
  4. *governance §2.8 추가 없이 스크립트만* — SSOT 누락. 신규 컨트리뷰터가 "왜 이 스크립트가 필요한지" 추적 불가. 기각.
  5. *enforce_admins=true* — admin 도 강제. 운영자(자기) hot-fix 불가. 기각 (운영 유연성 우선).
- **Decision**:
  - 옵션 3. 3종 동시 + `enforce_admins=false`.
  - **status check 이름 hardcoding**: 워크플로우 `jobs.<id>.name` 과 protection rule status check 이름은 *문자열 일치* 가 GitHub API 강제 — 둘 다 같은 SSOT(`setup_branch_protection.mjs:REQUIRED_CHECKS` + `governance.md` §2.8 표) 에서 관리. mismatch 시 영구 머지 블록.
  - **dismiss_stale_reviews=true**: PR 에 새 commit push 시 기존 approval 자동 무효화 — proposal §2.5 원칙 4(흐름 강제 catastrophic 만) 정합. approve 후 임의 변경 후 머지하는 사고 차단 = catastrophic.
  - **required_linear_history=true**: 본 저장소는 squash merge 전제 — merge commit 차단으로 history 단순화 (Task-ID anchor 검색 용이).
  - **proposal §2.5 원칙 정합**:
    - 원칙 1 (룰 순감소): RWHarness in-process LGTM flag 메커니즘 폐기 → 외부 강제로 *대체*. 신규 코드 LOC 추가는 ~80(스크립트) 이지만 RWHarness 폐기 부분(class Flag + flag_touch + flag_exists 등 70+ LOC) 절감.
    - 원칙 2 (강제 vs 권고): catastrophic(LGTM 우회 머지 / force-push) 만 deny. 형식적 요건은 status check 통과로 자연 해결.
    - 원칙 4 (흐름 강제 catastrophic 만): main push / 머지 시퀀스만 강제. PR 안 행동(commit message format 등) 은 별도 gate(task-id-validation) 가 카테고리별 처리.
- **Follow-Up**:
  - **(즉시)** 본 PR 머지 후 운영자(사용자) 가 `node scripts/setup_branch_protection.mjs` 실행 — admin 권한 필요. 본 Task 에선 *적용 안 함* (auto mode 의 "shared/production systems 변경 사용자 승인 필요" 정합).
  - **(검증)** 적용 후 §4 회귀 시나리오 4 항목 dry-run.
  - **iter 3**: Anthropic SDK haiku interpreter 통합 — `harness/signal_io.py` swap point 채움 (proposal §3 비용 측정 시작).
  - **iter 4**: ambiguous prose 카탈로그 + 휴리스틱 hit rate 측정.
  - **iter 5**: Phase 3 종결 + plugin dry-run 가이드.
  - **(별도 Task)** 첫 게이트 추가 시 "branch up-to-date" 강제로 PR 머지 시 base sync 필요 → squash 시 Task-ID 보존 검증.

### DCN-CHG-20260429-20
- **Date**: 2026-04-29
- **Rationale**:
  - Phase 2 종결(13 agent docs prose-only) 직후 Phase 3 진입. proposal §5 Phase 3 = "GitHub 외부화 + Sweep". RWHarness 의 commit-gate Gate 1/4/5 → GitHub Actions.
  - dcNess 는 commit-gate.py 자체를 도입하지 않음 (migration-decisions §2.2 DISCARD) → 자연 외부화 상태. Gate 4(doc-sync) 는 이미 `.github/workflows/document-sync.yml` 로 외부화 완료 (`DCN-CHG-20260429-08`).
  - 남은 즉시 가능 항목 = **Task-ID 형식 검증**. governance §2.1 의 `DCN-CHG-YYYYMMDD-NN` 룰은 PR template + AGENTS.md 에 *문서화* 만 돼 있고 *기계적 강제* 가 없었다. PR #1~#19 19개 모두 수동 준수했지만, 외부 에이전트(Codex 등) 또는 미래 자동 PR 시 누락 위험.
  - 분류 우선순위: Task-ID 누락은 다른 모든 거버넌스 룰(record/rationale/PROGRESS 동반)의 *anchor* — 누락 시 두 로그가 묶일 anchor 자체가 없음. 따라서 Phase 3 first-class 항목.
- **Alternatives**:
  1. *PR template 강조 + 수동 검증* — 현재 상태. 외부 에이전트/자동 PR 누락 위험. 기각.
  2. *commit-msg git hook 으로 로컬 차단* — 로컬 우회(`--no-verify`) 가능. proposal §11 4-pillar #2 정합 안 함. CI 게이트가 본질. 단 *추가* 옵션으로 도입 가능 — 본 Task 에선 CI 만 도입, 로컬 hook 은 후속.
  3. *(채택)* **CI 워크플로우 + 로컬 스크립트 듀얼 모드**. 로컬은 수동 호출(`node scripts/check_task_id.mjs`), CI 는 PR/push 자동. PR title 검증도 부가.
  4. *PR template-only 검증* — title 만 검사. body 안 Task-ID 누락 가능. commit 별 검사가 정확. 기각.
- **Decision**:
  - 옵션 3. CI(필수) + 로컬 스크립트(선택). PR title 추가 검증.
  - **머지 커밋 면제**: 2개+ parent 커밋은 squash merge 합본 등 자동 생성 메시지 케이스. 이미 squash 된 commit subject 안에 Task-ID 가 있으므로 머지 합본 검사 면제는 안전.
  - **다중 Task-ID 차단**: governance §2.1 "단 하나의 Task-ID" 명문 — `unique.length > 1` 도 FAIL. PR 한번에 두 Task 를 합치는 패턴 차단.
  - **Document-Exception-Task 자연 인정**: 같은 정규식이라 별도 처리 불필요.
  - **proposal §2.5 원칙 정합**: (원칙 1) 기존 룰(governance §2.1) 강제 *정밀화* — 신규 룰 추가 X. (원칙 2) catastrophic 차단(Task-ID 0 = anchor 부재 = governance 시스템 무효화). 강제(deny) 정당화.
- **Follow-Up**:
  - **iter 2 (Phase 3)**: 브랜치 보호 룰 + LGTM 게이트 — `gh api` CLI 또는 README 운영 가이드 추가 (proposal §5 Phase 3 "Gate 5 → branch protection required reviewers").
  - **iter 3**: Anthropic SDK haiku interpreter 통합 — `harness/signal_io.py` 의 `interpret_signal(..., interpreter=)` swap point 채움. proposal §3 비용 측정 ($0.001/cycle).
  - **iter 4**: ambiguous prose 카탈로그 + 휴리스틱 hit rate 측정 (proposal R1 / R8).
  - **iter 5**: Phase 3 종결 + plugin 배포 dry-run 가이드 정리.
  - **(별도 Task)** 로컬 git commit-msg hook (`scripts/hooks/commit-msg`) 추가 가능 — opt-in. 사용자가 `.git/hooks/commit-msg` 설치하면 push 전 차단.
  - **(측정)** 본 게이트 도입 후 1주 내 false-positive 빈도 측정. 0 이면 안정. > 0 이면 정규식 정정.

### DCN-CHG-20260429-19
- **Date**: 2026-04-29
- **Rationale**:
  - Phase 2 iter 5 (FINAL) = ux-architect + product-planner 짝. PRD 단계의 시작점 (planner = PRD 생성, ux-architect = PRD → UX Flow Doc).
  - 두 에이전트는 RWHarness 에서 가장 큰 docs (633 + 449 = 1082 줄) — 자기인식 경계 ("절대 출력 금지 패턴") + Outline-First + Diff-First + Anti-AI-Smell + 카테고리 클리셰 회피 + thinking 본문 드래프트 금지 등 *정책 밀도가 높음*. 변환 일관성 확보 위해 한 묶음.
  - PR #18 머지로 designer + design-critic 통과 → 마지막 묶음. Phase 2 종결.
- **Alternatives**:
  1. *ux-architect + product-planner + 추가 정리 묶음* — Phase 2 자체 종결이 우선. 추가 정리는 별도 Task. 기각.
  2. *ux + planner 분리 (각각 별도 PR)* — 1 PR 로 종결 시그널이 명확. 분리 시 Phase 2 종결 시점 모호. 기각.
  3. *(채택)* **ux + planner 짝 묶음 + Phase 2 종결 표시**: 13 agent prose-only 완성 시그널.
- **Decision**:
  - 옵션 3. 2 docs 동시 + Phase 2 종결.
  - **자기인식 경계 보존**: ux-architect / product-planner 의 "🔴 정체성" 섹션 + "절대 출력 금지 패턴" 보존 — agent 가 자기 정체 잃고 메인 Claude 로 행동하는 함정 방지. 작업 순서 영역 (proposal §2.5 대 원칙 적용 가능) — agent 호출 라이프사이클의 무결성.
  - **thinking 본문 드래프트 금지**: 비용 폭증 방지 (16KB thinking + 20KB Write 본문 중복). 권고 + 측정 영역 (proposal §2.5 원칙 5).
  - **Outline-First / Diff-First**: thinking 폭증 차단 + 유저 승인 게이트 — 작업 순서 정책. 보존.
  - **Anti-AI-Smell + 카테고리 클리셰 회피**: agent 출력물 품질 가이드 — *권장* 영역. 형식 강제 X.
  - **라이트/다크 두 모드 의무**: 디자인 가이드 작성 시 컬러 팔레트 양 모드 의무 작성. 산출물 품질 게이트.
- **Follow-Up**:
  - **Phase 2 종결 → Phase 3 후보**:
    - 메타 LLM (haiku) interpreter Anthropic SDK 통합 (proposal Phase 1 acceptance 의 미완 항목 — 휴리스틱 → LLM swap)
    - ambiguous prose 카탈로그 (`MissingSignal(ambiguous)` 누적)
    - plugin 배포 dry-run (RWHarness 와 공존 시나리오 검증, proposal §12.3.2)
    - 휴리스틱 interpreter hit rate 측정 (단어경계 매칭 vs ambiguous)
  - **(별도 Task-ID)** Phase 2 종결 후 dcNess 메인 작업 모드의 *self-application* — 본 13 agent docs 가 dcNess 자체 거버넌스 작업 (qa / planner / architect / engineer 위임) 에 사용 가능한 상태인지 검증.
  - **(측정)** Phase 2 5 iterations 누적 LOC / 복잡도 vs RWHarness 원본 비교. 순감소 추세 (proposal §2.5 원칙 1).

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
