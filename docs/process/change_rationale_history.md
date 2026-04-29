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
