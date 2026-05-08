# 릴리즈 노트

> 버전별 변경 요약. 상세 커밋은 `git log {prev_tag}..{tag}` 참조.

---

## v0.2.8 (2026-05-09)

**커밋 범위**: `4926adf..(다음 태그)`
**핵심 변경**: helper picker semver 정렬 — 가장 오래된 cache 선택 회귀 수정 (이슈 #293)

- **이슈 #293** — helper 진입 패턴 `ls -d ${CLAUDE_PLUGIN_ROOT:-.../dcness/dcness/*} | head -1`
  이 알파벳 순 정렬로 *가장 오래된* cache (예: 6 버전 환경에서 0.2.2) 선택. v0.2.7
  의 prose-only mode (이슈 #284 정착) 에 도달 못 해 0.2.2 의 enum-required mode +
  옛 휴리스틱 강제. jajang run-f0c23053 실측에서 휴리스틱 FP 2건 발생 (validator
  prose "0 FAIL" → enum=FAIL 오추출 / pr-reviewer "MUST FIX 없음 + NICE TO HAVE
  4건" → must_fix=true 오판정). 4 파일 (총 9 occurrences) 의 picker glob 패턴
  `head -1` → `sort -V | tail -1` 교체:
  - `docs/plugin/loop-procedure.md` (1)
  - `commands/run-review.md` (1)
  - `commands/init-dcness.md` (5)
  - `commands/efficiency.md` (2)

**영향**:
- v0.2.7 의 prose-only mode 가 picker 가 옛 cache 강제로 도달 못 했던 회귀 수정.
- 본 v0.2.8 부터는 picker 가 항상 최신 semver 선택 → prose-only mode 자연 활용.
- cache 다중 버전 환경 (`claude plugin update` 누적) 에서 모두 영향.

**업데이트**:
```sh
claude plugin update dcness@dcness
```

기존 cache 가 0.2.7 이 아닌 옛 버전을 picker 강제하던 환경 (jajang 실측 사례) 은
본 업데이트 후 정상화.

---

## v0.2.7 (2026-05-08)

**커밋 범위**: `1cff44a..(다음 태그)`
**핵심 변경**: enum 시스템 폐기 → prose-only routing 전환 (epic #280)

- **이슈 #281** — `harness/routing_telemetry.py` 신규. PostToolUse Agent 훅이
  매 sub 종료 시 prose tail (1200자 cap) 을 `.metrics/routing-decisions.jsonl`
  에 1줄 append. 메인이 사용자 위임할 때는 CLI `record-cascade --reason ...`.
  enum heuristic-calls.jsonl 의 prose-only 후속 — 회귀 검증용 raw baseline.
- **이슈 #282** — `docs/plugin/handoff-matrix.md §1` 의 enum 표 12 종을
  자연어 routing 가이드로 재포맷. agent 별 가능한 결론 *유형* + 권장 다음
  처리 흐름을 prose 로 서술. §2 retry / §3 escalate / §4 권한은 보존.
- **이슈 #283** — 22 agent 파일 (12 master + 5 architect sub-mode + 5
  validator sub-mode) 의 enum 표를 자연어 가이드로 환원. frontmatter
  description / leading prose / "## 결론 enum" 표 모두 "결론 + 권장 다음
  단계 자연어 명시" 로 통일. 기존 enum 단어는 *예시 권장 표현* 으로 보존.
- **이슈 #284** — `harness/interpret_strategy.py` telemetry write 코드
  제거 (`.metrics/heuristic-calls.jsonl` 신규 기록 0). `_cli_end_step` 의
  `--allowed-enums` optional. 미지정 시 prose-only mode (stdout
  `PROSE_LOGGED`). legacy `--allowed-enums` 호출은 호환 보존.
  `dcness-rules.md §3.3` / `loop-procedure.md §3.1` prose-only mode 권장
  으로 갱신.
- **이슈 #285** — 배포 경로 검증. 본 epic 모든 변경은 plug-in 본체 (배포
  경로 1) 안. `claude plugin update` 로 자동 전파. init-dcness 가 사용자
  repo 로 복사하는 인프라 (배포 경로 2) 변경 없음. 사용자용 SSOT 문서
  (배포 경로 3) 는 plug-in cache 안 — 자동 갱신.

**전환 모델 (정착 후)**:
1. agent 가 prose 마지막 단락에 *어떤 결과로 끝났는지 + 메인이 누구를
   부르는 게 적절한지* 자유 표현.
2. 메인 Claude 가 prose + handoff-matrix.md §1 자연어 가이드 보고 routing.
3. `routing-decisions.jsonl` raw 누적 → 회고 분석 (#281).
4. 결정 못 하면 `routing_telemetry record-cascade` 후 사용자 위임.

**업데이트**:
```sh
claude plugin update dcness@dcness
```

기존 활성화 프로젝트는 plug-in update 만으로 자동 적용. init-dcness 재실행
불필요. 외부 활성화 프로젝트 동작 확인은 사용자가 일반 작업 진행 중 자연스
럽게 검증 (특별한 검증 절차 없음).

---

## v0.2.6 (2026-05-08)

**커밋 범위**: `09e537f..c69e28a`
**핵심 변경**: engineer 권한 경계 강화 + POLISH self-verify 면제 + Step 7 회고 메모리 의무 + 워크트리 hook 정정 + DeepEval 마이그레이션

- `agents/engineer.md`: 자체 `git commit/push/branch` 호출 + `stories.md/backlog.md/batch-list.md` 직접 수정 사전 차단 (#148). §권한 경계 / §IMPL_PARTIAL / §커밋 단위 규칙 / §1 task = 1 PR 안티패턴 4 군데 정합. POLISH 자가 검증 anchor 면제 명시 (#252)
- `harness/run_review.py`: `MISSING_SELF_VERIFY` 검사에서 `POLISH_DONE` 제외 — POLISH prose 본문 자체가 검증 substance, anchor 강제는 잉여 (#252). 회귀 방지 unittest 추가
- `docs/plugin/loop-procedure.md §5.5`: 7b caveat 보고 양식에 "📝 메모리 candidate" 섹션 + 의무 룰 추가 (#149). 7a clean 도 review report waste finding 시 동일 적용
- `docs/plugin/dcness-rules.md`: "Step 7 회고 → 메모리 저장 의무" 룰 추가 — SessionStart inject 로 매 세션 자동 인지 (#149)
- `scripts/hooks/cc-pre-commit.sh`: cwd 결정 우선순위 뒤집기 — `git rev-parse --show-toplevel` 우선, fallback `CLAUDE_PROJECT_DIR` (#268). 워크트리 안 commit 이 메인 main 으로 오인 차단되던 회귀 수정
- `tests/eval_*.py` + 평가 인프라: AgentEvals → DeepEval 마이그레이션 (#263)

**업데이트**:
```sh
claude plugin update dcness@dcness
```

---

## v0.2.5 (2026-05-07)

**커밋 범위**: `8d097b4..6612db0`  
**핵심 변경**: 루프 종료 후 finalize-run 강제 안전망 + REVIEW_READY 신호

- `loop-procedure.md §3.3`: advance enum 마지막 step → 사용자 대기 없이 즉시 Step 7 명시 (issue-240)
- `loop-procedure.md §5.1`: 트리거 명시 + end-run 안전망 설명 추가
- `session_state.py _cli_finalize_run`: `finalized_at` 플래그 저장 + review → `review.md` 파일 저장 + stderr `[REVIEW_READY]` 신호
- `session_state.py _cli_end_run`: `finalized_at` 없으면 자동 `finalize-run --auto-review` 실행
- `dcness-rules.md`: 파일 경로 채널별 형식 분기 룰 추가 (CC 채팅 = 평문 백틱, 도큐 = 마크다운 링크)

**업데이트**:
```sh
claude plugin update dcness@dcness
```

---

## v0.2.4 (2026-05-07)

**커밋 범위**: `0fb69df..6038ceb`  
**핵심 변경**: PostToolUse prose 추출 전면 실패 수정

- PostToolUse hook 에서 tool_response 가 list 포맷일 때 prose 추출 전면 실패하던 버그 수정 (issue-232)
- `plugin-release.md` 'bump' → '버전 올리기' 표현 개선

---

## v0.2.3 (2026-05-07)

**커밋 범위**: `bfd500d..0fb69df`  
**핵심 변경**: `claude plugin update` 버그 수정

- `marketplace.json` `plugins[].source` 를 github object → `"./"` 로 복구
- 신규 install 은 두 포맷 모두 동작했으나, update 는 `"./"` 만 동작함을 확인 (`e68a440` 에서 잘못 변경된 것)
- git 태그 관리 시작 (이 버전부터 `v{버전}` 태그 병행)

---

## v0.2.2 (2026-05-07)

**커밋 범위**: `ff3ae5b..bfd500d`  
**핵심 변경**: 내부 문서 구조 정리 + dcness-rules 전면 재편

- `dcness-rules.md` 전면 재편 — 대원칙 신설, 루프 구조화, prose-only 통합 (issue-223)
- `main-claude-rules.md`, `self-guidelines.md`, `governance.md`, `branch-protection-setup.md` 삭제 — 역할 흡수 또는 중복 제거
- `CLAUDE.md §3` lazy 표 누락 파일 보완

---

## v0.2.1 (2026-05-07)

**커밋**: `ff3ae5bcdbd62c8f2240ca94f31d593133634101` (release branch HEAD)  
**핵심 변경**: marketplace 배포 경로 정비 + 로컬 게이트 강화

- release 브랜치에서 `marketplace.json` 제거 (sync_local_plugin.sh 폐기, issue-221)
- `dcness-rules.md` 로 rename + 정제 (issue-217)
- cc-pre-commit.sh 브랜치명·PR 제목 로컬 게이트 추가 (issue-171)
- run_review false positive 수정 (issue-171)
