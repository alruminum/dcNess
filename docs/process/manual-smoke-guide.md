# Manual Smoke Guide — dcness 8 skill 도그푸딩

> **출처**: `DCN-CHG-20260430-10`. 사용자 manual smoke 시 참조용. plugin 재설치 + 8 skill 별 발화 prompt + dcTest 재료 위치 + 기대 동작 명시.
>
> **본 문서 한계**: 발화 prompt 와 기대 동작만 — 실제 결과는 사용자가 직접 확인 + 보고. 자동 회귀 테스트는 `tests/test_multisession_smoke.py` 참조.

---

## 0. 사전 준비

### 0.1 plugin 재설치 (변경 반영)

```sh
# 1. 기존 dcness uninstall (whitelist 도 함께 정리됨 — 의도된 동작)
claude plugin uninstall dcness@dcness

# 2. 재설치 (cache 갱신)
claude plugin install dcness@dcness

# 3. 활성 확인
claude plugin list   # dcness@dcness enabled 인지 / 0.1.0-alpha 버전 보임?
```

마켓플레이스 미등록 환경이면:
```sh
claude plugin marketplace add /Users/dc.kim/project/dcNess
claude plugin install dcness@dcness
```

### 0.2 RWHarness 충돌 회피

dcness + RWHarness 동시 enabled 시 hook race 가능. 둘 중 하나만:
```sh
claude plugin disable realworld-harness@realworld-harness
claude plugin list   # dcness 만 enabled
```

### 0.3 dcTest 현 상태 (smoke target)

```sh
cd ~/project/dcTest
ls -R
git log --oneline
```

기대 (이전 smoke 잔재 보존):
- `src/greet.py` — greet() 가드 적용, `_GREETINGS` dict 정의됨 (단 greet() 가 lang param 없어 다국어 미사용 — 미구현 갭)
- `src/calc.py` — add + subtract 구현, multiply/divide 누락, 주석 typo `숫지`
- `prd.md`, `docs/architecture.md`, `docs/ux-flow.md`, `backlog.md`, `docs/milestones/v0.2/` — 이전 /product-plan 산출
- 2 commit (initial + subtract feat)

remote 부재라 PR 생성은 skip — dcness 의 graceful degrade (`/quick` Step 7 의 "git remote 없음 — local commit only") 검증 가능.

---

## 1. 8 skill 발화 prompt + 기대 동작

각 시나리오: **새 claude 세션 시작 → cd ~/project/dcTest → claude → 발화 입력**.

### Skill 1 — `/init-dcness` (활성화 게이트)

**발화**:
```
/init-dcness
```

**기대 동작**:
1. `dcness-helper status` 호출 → 현재 cwd 의 main repo + 활성 상태 표시
2. inactive 면 `dcness-helper enable` 호출 → whitelist 추가
3. 사용자에게 안내 (활성화 완료 + 다음 세션 재시작 권장)
4. **새 세션 시작 시** SessionStart 훅이 발화 → `~/project/dcTest/.claude/harness-state/.by-pid/{pid}` 생성

**검증 포인트**:
- `~/.claude/plugins/data/dcness-dcness/projects.json` 에 `~/project/dcTest` path 기록
- 다음 세션 시작 후 `ls ~/project/dcTest/.claude/harness-state/.by-pid/`

---

### Skill 2 — `/qa` (이슈 분류)

**발화**:
```
/qa src/greet.py 가 _GREETINGS dict 정의했는데 greet() 가 안 쓰는 것 같은데
```

**기대 동작**:
1. helper `begin-run qa` → run_id 발급
2. `Agent(qa)` 호출 → 분류 prose 생성
3. helper `end-step qa --allowed-enums "..."` → enum 추출 + **prose 요약 stderr 자동 출력** (DCN-CHG-20260430-02)
4. 결과 = `FUNCTIONAL_BUG` (미구현 케이스) 예상
5. 후속 추천: `/quick` 또는 `/product-plan`

**검증 포인트**:
- 매 step 후 stderr 로 `[qa = FUNCTIONAL_BUG]` 헤더 + prose 첫 5~8줄 자동 노출 (ctrl+o 안 눌러도 보임)
- prose 종이: `~/project/dcTest/.claude/harness-state/.sessions/{sid}/runs/run-XXX/qa.md`
- catastrophic 룰 — qa 는 비대상 (silent 통과)

---

### Skill 3 — `/quick` (light path 자동화)

**발화**:
```
/quick src/calc.py 의 "숫지" 오타 → "숫자" 로 고쳐
```

**기대 동작**:
1. 5 task 등록 (qa / architect LIGHT_PLAN / engineer / validator BUGFIX_VALIDATION / pr-reviewer)
2. 각 단계마다 begin-step + Agent + end-step (prose 요약 stderr 자동)
3. PreToolUse 훅 §2.3.3 (engineer 직전 LIGHT_PLAN_READY 확인) silent 통과
4. PreToolUse 훅 §2.3.1 (pr-reviewer 직전 BUGFIX_VALIDATION PASS 확인) silent 통과
5. **Step 7a clean 자동** — 모든 enum expected (CLEANUP / LIGHT_PLAN_READY / IMPL_DONE / PASS / LGTM) + MUST FIX 0 → 자동 git branch + commit (remote 없으니 local commit only — graceful degrade)

**검증 포인트**:
- `dcTest` 의 `git log` 에 새 commit 추가됨 (`chore/fix-typo` 브랜치 → main 머지 또는 사용자 결정)
- 사용자 confirm prompt 0 (clean 시 7a 자동)
- prose 5 종이 모두 저장됨

### Skill 3b — `/quick worktree` (격리 + auto chain)

**발화**:
```
/quick worktree calc.py 에 multiply 함수 추가
```

**기대 동작**:
1. Step 0a `EnterWorktree(name="quick-...")` 발화 → cwd 가 `.claude/worktrees/quick-.../` 로 변경
2. 사용자에게 worktree 진입 1줄 보고
3. Step 1~6 위와 동일 (단 변경은 worktree 안 src/calc.py 만)
4. Step 7a clean 자동 commit + worktree squash 흡수 검사 → `discard_changes=true` 자동 적용 → ExitWorktree(remove) 깔끔 정리

**검증 포인트**:
- `.claude/worktrees/quick-...` 디렉토리 진입 + 종료 시 자동 정리
- worktree branch tip 이 main 의 squash 커밋으로 흡수 → ExitWorktree(remove) silent 성공 (이전 smoke 의 "1 commit unmerged" 에러 부재)
- `git diff main..worktree-branch` 결과 빈 줄 → discard_changes=true 자동

### Skill 3c — `/quick yolo` (옵션)

**발화**:
```
/quick yolo src/greet.py shout() 에 docstring 추가
```

**기대 동작**:
- yolo keyword 감지 보고
- 어디선가 AMBIGUOUS / ESCALATE 떴을 시 `auto-resolve` 호출 → 권장 액션 자동 적용 (사용자 위임 X)
- catastrophic 훅은 그대로 — yolo 가 hard safety 우회 X

---

### Skill 4 — `/product-plan` (spec/design 흐름)

**발화**:
```
/product-plan v0.3 — calc 에 modulo + power 추가, greet 의 다국어 실 적용 (lang 인자)
```

**기대 동작**:
1. 7 task 등록 (product-planner / plan-reviewer / ux-architect / validator UX / architect SD / **validator DESIGN_VALIDATION** / architect TASK_DECOMPOSE) — DCN-CHG-20260430-05 정합
2. product-planner 가 PRD 작성 (CLARITY_INSUFFICIENT 면 사용자 역질문)
3. plan-reviewer → 8 차원 심사 → PLAN_REVIEW_PASS
4. ux-architect → minimal UX_FLOW (CLI 라 PATCHED 가능)
5. validator UX_VALIDATION → PASS
6. architect SYSTEM_DESIGN → SYSTEM_DESIGN_READY
7. **validator DESIGN_VALIDATION → DESIGN_REVIEW_PASS (신규 step, DCN-CHG-20260430-05)** — PreToolUse 훅 §2.3.5 가 다음 step 직전 검사 발동
8. architect TASK_DECOMPOSE → READY_FOR_IMPL + impl batch 산출

**검증 포인트**:
- Step 6.5 (DESIGN_VALIDATION) 가 명시적으로 등장 (이전 smoke 엔 누락)
- prose 종이: `validator-DESIGN_VALIDATION.md` 안 `DESIGN_REVIEW_PASS` 명시
- TASK_DECOMPOSE 직전 PreToolUse 훅 §2.3.5 silent 통과 (catastrophic 검증 추가)

### Skill 4b — `/product-plan yolo` (옵션)

**발화**:
```
/product-plan yolo 새 기능: calc 에 평균/표준편차 추가
```

**기대**: CLARITY_INSUFFICIENT / UX_FLOW_ESCALATE 시 사용자 위임 안 하고 권고안 자동 채택.

---

### Skill 5 — `/impl` (per-batch 정식 루프)

전제: `/product-plan` 후 산출된 impl batch 1개 선택.

**발화**:
```
/impl docs/milestones/v0.3/epics/epic-01-calc-mod-pow/impl/01-modulo.md
```

(또는 사용자가 추론 가능한 표현: `/impl impl-1` 등)

**기대 동작**:
1. 5 sub-task 등록 (architect MODULE_PLAN / test-engineer / engineer / validator CODE_VALIDATION / pr-reviewer)
2. architect MODULE_PLAN → READY_FOR_IMPL
3. **test-engineer (TDD attempt 0)** → TESTS_WRITTEN — `/quick` 과 차이점 (test 미생략)
4. engineer IMPL → IMPL_DONE
5. validator CODE_VALIDATION → PASS (CODE 영역, BUGFIX 와 별개)
6. pr-reviewer → LGTM
7. Step 7a clean 자동 commit/PR (remote 없으면 local 만)

**검증 포인트**:
- 5 sub-task 가 외부 task 와 별개로 진행 (이전 smoke 의 "단계가 task 화 안 됨" 지적 정합)
- test-engineer 가 src/ 읽기 X (impl 의 ## 생성/수정 파일 경로만 사용 — catastrophic-prevention)

### Skill 5b — `/impl-loop` (multi-batch chain)

**발화**:
```
/impl-loop yolo
```

(또는 batch list 명시)

**기대 동작**:
1. `BATCH_LIST=$(ls docs/milestones/v*/epics/epic-*/impl/*.md | sort)` 으로 자동 추출
2. 각 batch 마다 inner /impl run 진행
3. clean → 자동 commit/PR + 다음 batch
4. caveat → 멈춤 + 사용자 위임

**검증 포인트**:
- 외부 task = N batch entry, 각 batch 의 inner 5 sub-task 도 visible
- caveat 발생 시 정확한 멈춤 메시지 + 처리한/남은 batch 명시

---

### Skill 6 — `/smart-compact` (컨텍스트 압축)

**발화**:
```
/smart-compact
```

**기대 동작**:
1. 현 세션 transcript 분석 — git log + governance docs + PROGRESS + TaskList + 미해결 의논
2. 다음 세션용 single-message resume prompt 자동 생성 (정해진 템플릿)
3. clipboard 복사 (`pbcopy`)
4. transcript 출력 (사용자 직접 복사 가능)
5. 파일 백업: `~/project/dcTest/.claude/resume-prompts/{YYYYMMDD-HHMMSS}.md`

**검증 포인트**:
- clipboard 안 prompt = 다음 세션 첫 발화로 그대로 사용 가능
- 백업 파일 존재 + 내용 일치
- 추출 우선순위 정합 (미해결 결정 / 핵심 reasoning / 다음 step 후보)

---

### Skill 7 — `/efficiency` (Claude Code 세션 비용 분석)

dcTest 가 CC 로 한 번도 안 열렸을 가능성 → **dcness repo 에서 시도 권장** (CC history 풍부).

**발화** (dcness repo cwd):
```
/efficiency
```

또는:
```
/efficiency 비용 분석해줘
```

**기대 동작**:
1. `scripts/dcness-efficiency full --repo "$(pwd)" --out-dir /tmp/dcness-efficiency`
2. analyze_sessions → JSON (`/tmp/dcness-efficiency/session_analysis.json`)
3. build_dashboard → HTML (`/tmp/dcness-efficiency/efficiency_report.html`)
4. 사용자 보고 (Korean, 2~3줄 요약):
   ```
   [efficiency] N 세션 / $X / 평균 등급 Y
   - 캐시 히트율: Z%
   - 상위 N 세션이 전체 비용의 Q% 차지
   - 가장 큰 절감 후보 (3개): ...
   ```

**검증 포인트**:
- HTML 대시보드 열기 가능 (`open /tmp/dcness-efficiency/efficiency_report.html`)
- DCN-CHG-20260430-08 fix 2건 정합 — `/Users/dc.kim/...` (dotted username) sessions dir 정상 발견 + `claude-haiku-4-5-20251001` haiku 가격 적용 (Opus default fallback X)
- 4 지표 (Cache 40% / Output 20% / Read redundancy 20% / Tool economy 20%) + 등급 (A+~F) + Pareto

dcTest 에서 시도 시 "분석할 세션 없음" graceful exit (오류 없이 안내 + 종료).

---

## 2. 검증 체크리스트 (8 skill 통합)

각 skill 시도 후 사용자가 보고할 핵심:

| 항목 | 확인 |
|---|---|
| skill 발화 인식 (`/...`) | ✅/❌ |
| helper 호출 정상 (PYTHONPATH 정합, sid/rid 발급) | ✅/❌ |
| Agent 호출 정상 (subagent_type 매칭) | ✅/❌ |
| prose 종이 저장 (`.claude/harness-state/.sessions/{sid}/runs/{rid}/`) | ✅/❌ |
| stderr 자동 prose 요약 (DCN-CHG-30-2) | ✅/❌ |
| catastrophic 훅 silent 통과 (시퀀스 정합 시) | ✅/❌ |
| catastrophic 훅 차단 (시퀀스 위반 시) | ✅/❌ |
| clean 자동 commit/PR (Step 7a) | ✅/❌ |
| caveat 사용자 확인 (Step 7b) | ✅/❌ |
| yolo keyword 감지 + 폴백 적용 | ✅/❌ |
| worktree keyword 감지 + EnterWorktree | ✅/❌ |
| worktree squash 흡수 자동 (DCN-CHG-30-2) | ✅/❌ |
| /efficiency dotted username path 정합 (DCN-CHG-30-8) | ✅/❌ |
| /efficiency 신모델 가격 prefix 매칭 (DCN-CHG-30-8) | ✅/❌ |

각 항목 1줄 코멘트 포함. 어느 항목 ❌ 면 즉시 디버그 진입.

---

## 3. 기대 시간 (참고)

| skill | 평균 소요 |
|---|---|
| /init-dcness | 5초 + 세션 재시작 |
| /qa | 30~60초 |
| /quick | 3~5분 (5 단계) |
| /product-plan | 8~15분 (7 단계, CLARITY 1회 cycle 시 +30초) |
| /impl | 5~10분 (5 단계 + test-engineer) |
| /impl-loop | N × /impl + 자동 chain |
| /smart-compact | 30초 ~ 1분 |
| /efficiency | 5초 (read-only 분석) |

8 skill 전체 smoke = 약 30~60분 예상.

---

## 4. 트러블슈팅

### 4.1 `[error] sessions dir not found`

cwd 가 dcTest 같은 dotted username 환경 + 한 번도 CC 로 안 열린 케이스.
- dcness fix 적용 확인: `python3 -c "from harness.efficiency.analyze_sessions import encode_repo_path; print(encode_repo_path('/Users/dc.kim/project/dcTest'))"` → `-Users-dc-kim-project-dcTest` 결과 정합인가?
- 결과가 `-Users-dc.kim-...` 이면 fix 미적용 → plugin 재설치 (`/Users/dc.kim/.claude/plugins/cache/dcness/...` 의 캐시 갱신).

### 4.2 `[catastrophic §2.3.X] ... 필수`

PreToolUse 훅이 시퀀스 위반 차단. 정상 동작.
- 메시지의 §2.3.N 번호로 룰 확인 (`docs/orchestration.md` §2.3)
- 누락된 prose 종이 검사: `ls ~/project/<...>/.claude/harness-state/.sessions/{sid}/runs/{rid}/`

### 4.3 `[session_state] sid 미해결`

SessionStart 훅이 발화 안 했음.
- whitelist 활성 확인: `python3 -m harness.session_state status` (또는 `dcness-helper status`)
- 활성 상태 + 새 세션이어야 함. `/init-dcness` 후 claude 재시작 필수.

### 4.4 hook silent 차단 (이유 모름)

cwd 가 dcness 활성 프로젝트 (whitelist 등록) 인지 확인:
```sh
DCNESS_FORCE_ENABLE=1 python3 -m harness.session_state status
```
환경변수로 강제 활성화 후 재시도.

---

## 5. 보고 양식 (사용자 → 메인 Claude)

각 skill smoke 후:

```
## [skill 이름] smoke 결과

- 발화: <사용자 입력 그대로>
- 결과: ✅ 정상 / ⚠️ 부분 정상 / ❌ 실패
- 핵심 관찰:
  - <stderr 요약 정상 보였나>
  - <자동 commit/PR 됐나>
  - <prose 파일 생성됐나>
- 에러 (있을 시):
  ```
  <stderr 또는 transcript 발췌>
  ```
- 다음 디버그 항목: <있으면>
```

---

## 6. 참조

- `commands/*.md` — 8 skill prompt 정의
- `docs/orchestration.md` §2.3 — catastrophic 룰
- `docs/conveyor-design.md` — Task tool + helper + 훅 패턴
- `docs/process/branch-surface-tracking.md` — 사다리 진입 self-check
- `tests/test_multisession_smoke.py` — 자동 회귀 테스트
- `docs/process/plugin-dryrun-guide.md` — plugin 배포 dry-run 절차
