# 릴리즈 노트

> 버전별 변경 요약. 상세 커밋은 `git log {prev_tag}..{tag}` 참조.

---

## v0.2.16 (2026-05-11)

**커밋 범위**: `v0.2.15..(다음 태그)`
**핵심 변경**: TDD 게이트 design pivot — CI 게이트 + commit-msg chain 전체 rollback, PreToolUse tdd-guard 도입

- **이슈 #320 design pivot (PR #339)** — v0.2.10~v0.2.13 의 CI 게이트 (composite
  action) + commit-msg TDD chain 이 monorepo lifecycle hook / pm 다양성 / missing
  test script 등 함정 누적. 사용자 의도 ("구현보다 테스트 먼저") 는 사후 검증
  아니라 *작성 전 차단*. PreToolUse hook 시점 차단으로 전환.
  - **Rollback**:
    - `.github/actions/tdd-gate/action.yml` 삭제
    - `scripts/check_tdd_staged.mjs` 삭제
    - `scripts/hooks/commit-msg` TDD chain 제거 (git-naming 만 남김)
    - `commands/init-dcness.md` Step 2.9 (CI 게이트) + Step 2.10 (commit-msg TDD) 제거
    - **유지**: `scripts/pr-finalize.sh` (사용자 명시 의도)
  - **신규**:
    - `hooks/tdd-guard.sh` — PreToolUse[Edit|Write|NotebookEdit] hook
    - `hooks/hooks.json` matcher 등록
    - `commands/init-dcness.md` Step 2.9 (신규 안내문)
  - **영감**: jha0313/codex-live-demo `.codex/hooks/tdd-guard.sh`
  - **동작**: agent 가 src 파일 Edit/Write 시도 시 매칭 test 파일 존재 검사 →
    없으면 deny + 한국어 안내. TS/JS 한정. 자동 skip (설정/타입/Next.js 특수/비-코드)
    풍부. 다른 언어 영향 0.

**차이** (이전 v0.2.13 commit-msg vs 본 PR PreToolUse):

| | v0.2.13 commit-msg | v0.2.16 PreToolUse |
|---|---|---|
| 시점 | commit 직전 | 코드 작성 *직전* |
| 진짜 TDD | △ 사후 검증 | ✅ 작성 전 차단 |
| 실행 | O test 실행 | ❌ 존재만 |
| 함정 | jajang 사단 (lifecycle / pm) | 적음 (자동 skip 풍부) |
| 범위 | 4 언어 | TS/JS |
| 옵트인 | 마커 파일 | 자동 (TS/JS 검출) |

**실증 검증 8 케이스**:
- test 없는 src → DENY
- test 있는 src → PASS
- 설정 / Next.js / .py / test 자체 / empty → silent skip

**배포 경로** (CLAUDE.md §0.5):
- (1) plug-in 본체 — `hooks/tdd-guard.sh` + `hooks/hooks.json` plug-in 업데이트 자동
- (2) init-dcness 배포 — Step 2.9 안내문. tdd-guard 사용자 repo cp X (plug-in hook 직접 발화)
- (3) SSOT 문서 — N/A

**한계 (v0.2.16)**:
- TS/JS 한정 — 다른 언어 후속
- *test 실행 X* — 존재만 확인 (실행은 사용자 vitest watch / CI 등 개별)
- agent 가 `Bash` 으로 직접 파일 작성 시 차단 X (단 catastrophic-gate 등 다른 hook 이 잡음)

**사용자 적용**:
```sh
claude plugin update dcness@dcness
```

기존 활성화 프로젝트 (jajang — 이전 TDD 인프라 정리):
```sh
cd ~/project/jajang
git rm .github/workflows/tdd-gate.yml
git rm -f .dcness/tdd-gate-enabled
git commit -m "..."
```

이후 agent Edit/Write 시 tdd-guard 자동 발화. 사용자 추가 설정 0.

---

## v0.2.15 (2026-05-11)

**커밋 범위**: `v0.2.14..(다음 태그)`
**핵심 변경**: TDD 게이트 polish — `ignore_scripts` input + `pr-finalize.sh` 한 명령 머지

- **이슈 #320 jajang prepare hook self-block (PR #336)** — composite action 에
  `ignore_scripts` input 추가. monorepo workspace `"prepare": "npm run build"`
  같은 hook 이 root `npm ci` 시 발화 → 빌드 실패 → tdd-gate self-block 회피.
  - `with: { ignore_scripts: true }` 옵트인 시 `--ignore-scripts` flag 적용
  - pnpm / yarn / bun / npm 모두 지원
  - 디폴트 false (기존 행동 유지)
  - thin yml 템플릿에 `fetch-depth: 0` + 옵트인 주석 추가

- **이슈 #320 pr-finalize helper (PR #337)** — 머지 절차 5 명령 → 1 명령.
  사용자 피드백 "머지되면 main 으로 다시 되돌아가고 pull 까지 했으면" 대응.
  - `scripts/pr-finalize.sh` 신규
  - 흐름: gh pr merge --auto → gh pr checks --watch → auto-merge 완료 대기 → checkout main + pull
  - argument 없으면 current branch 의 open PR 자동 검출
  - working tree dirty 시 사용자 확인 후 sync skip
  - CI FAIL / 머지 안 됨 시 exit 1 + 안내
  - `git-naming-spec.md §6` + `CLAUDE.md §5` 머지 절차 갱신 — 1 명령으로 통합

**배포 경로** (CLAUDE.md §0.5):
- (1) plug-in 본체 — `.github/actions/tdd-gate/action.yml` + `scripts/pr-finalize.sh`
- (2) init-dcness 배포 — Step 2.9 thin yml 갱신 (옵트인 주석 + fetch-depth)
- (3) SSOT 문서 — `git-naming-spec.md` §6 + `CLAUDE.md` §5

**jajang 즉시 적용**:
```sh
claude plugin update dcness@dcness
/init-dcness   # 새 thin yml 받음
# .github/workflows/tdd-gate.yml 에서 with: ignore_scripts: true 박음 (monorepo prepare hook self-block 회피 시)
bash scripts/pr-finalize.sh   # 머지 + main sync 자동
```

---

## v0.2.14 (2026-05-11)

**커밋 범위**: `v0.2.13..(다음 태그)`
**핵심 변경**: init-dcness Step 2.11 — 인프라 머지 자동화 (사용자 부담 0)

- **이슈 #320 (사용자 피드백) (PR #334)** — `/init-dcness` 가 cp 만 하고 git
  add/commit/PR 사용자 부담. 까먹으면 workflow yml 이 main 미반영 → CI 게이트
  dead code. 본 release 가 자동 commit + PR 까지 끝까지 진행.
  - `commands/init-dcness.md` Step 2.11 신규
  - 변경 파일 검출: `.github/workflows/` + `.dcness/` 명시 path
  - branch 검사: main 일 때만 자동 진행 (사용자 작업 보호)
  - 사용자 동의 (Y/n) 후: branch → stage → commit → push → PR
  - branch 패턴: `docs/dcness_init_{timestamp}` (git-naming-spec 정합)
  - 자동 머지 X — 인프라 PR 은 사용자 검토 후 머지 권장

**jajang 사단 (실측)**:
- 기존: `git-naming-validation.yml` 만 main 등록. `tdd-gate.yml` + `pr-body-validation.yml` working tree 잔존
- 본 release 후 `/init-dcness` 재실행 → Step 2.11 발화 → 자동 PR → 머지하면 모든 workflow 정상

**배포 경로** (CLAUDE.md §0.5):
- (1) plug-in 본체 — `commands/init-dcness.md` plug-in 업데이트 자동
- (2) init-dcness 배포 — Step 2.11 신규. 기존 활성 프로젝트는 `/init-dcness` 재실행 시 발화
- (3) SSOT 문서 — N/A

**한계**:
- 사용자가 이미 PR 만든 인프라 변경 있을 때 중복 시도 가능 (메인 Claude 가 사전 `gh pr list --search` 검사 권장)
- `gh` CLI 미설치 환경 → push 까지만 + 사용자 수동 PR 권유

**업데이트**:
```sh
claude plugin update dcness@dcness
```

기존 활성화 프로젝트:
```sh
/init-dcness   # Step 2.11 발화 — working tree 인프라 변경 검출 시 자동 PR 제안
```

---

## v0.2.13 (2026-05-11)

**커밋 범위**: `v0.2.12..(다음 태그)`
**핵심 변경**: TDD 게이트 phase 4 — pre-commit (commit 단 차단, 자체완결 wall)

- **이슈 #320 #1 phase 4 (PR #332)** — commit-msg hook chain 에 TDD 게이트 추가.
  staged src 변경 = test 변경 함께 + 변경분 test 실행 PASS 강제. branch protection
  의존성 0 → 진짜 자체완결 wall.
  - `scripts/check_tdd_staged.mjs` 신규 — 본체 (옵트인 마커 + skip marker + 분기 + 실행)
  - `scripts/hooks/commit-msg` 갱신 — git-naming 후 TDD 게이트 chain
  - `commands/init-dcness.md` Step 2.10 신규 — 옵트인 + 3-commit 구조 정합 안내
- **옵트인 메커니즘**: `.dcness/tdd-gate-enabled` 마커 파일 활성화 신호. 부재 시 silent pass.
  다른 프로젝트 영향 0 (외부 활성화 프로젝트가 옵트인 안 한 경우 자동 발화 X).
- **skip marker**: commit message 안 `[skip-test: <사유>]` 매치 시 우회 — 단순 typo /
  문서 변경 / refactor 무영향 케이스 정당 우회.
- **변경분만 실행**: test-engineer 작성 task 용 test (5~15개) 만 실행 = 수초. 풀
  스위트 아님.
- **4 언어 자동 검출**: jest / vitest (deps 검사) / pytest / cargo test / go test.

**3-commit 구조 정합** (loop-procedure §3.4):

| commit | stage | TDD 게이트 |
|---|---|---|
| commit1 (docs) | `docs/impl/NN.md` | PASS (src 0) |
| commit2 (tests) | `src/__tests__/**` | PASS (test 만) |
| commit3 (src) | `src/**` + stories.md | PASS (branch diff test 인지) |
| 위반: src 만 | `src/bar.ts` | BLOCK |

**6 케이스 실측 검증** 완료 (PR #332 body 참조).

**layered defense 완성**:

| 단 | 어디서 | dcness 도입 |
|---|---|---|
| 1 | **commit 단** (commit-msg hook) | **v0.2.13 phase 4 ← 본 release** |
| 2 | CI workflow (affected) | v0.2.12 phase 3 |
| 3 | Branch Protection | 사용자 수동 (안내문) |

**배포 경로** (CLAUDE.md §0.5):
- (1) plug-in 본체 — `scripts/check_tdd_staged.mjs` + `scripts/hooks/commit-msg`
  chain — plug-in 업데이트 자동 반영
- (2) init-dcness 배포 — Step 2.10 신규. 기존 활성 프로젝트는 `/init-dcness` 재실행
  시 발화. commit-msg shim 은 이미 chain 로직 박혀있어 사용자가 옵트인 마커만 작성하면
  즉시 동작.
- (3) SSOT 문서 — N/A

**한계 (phase 4)**:
- node test runner: jest / vitest 자동. 그 외 (mocha / ava 등) → `npm test` 폴백
- rust: 단순화 — `cargo test` 풀 폴백 (변경 test 파일만 native 한계)
- python: pytest 만 (unittest 만 쓰는 프로젝트면 `[skip-test]` 우회)
- `--watch` 룰 (git-naming-spec §6) 그대로 — commit 단 차단으로 CI 우회 위험 ↓
  단 룰 완화는 별도 결정

**업데이트**:
```sh
claude plugin update dcness@dcness
```

기존 활성화 프로젝트:
```sh
/init-dcness   # Step 2.10 발화 — 옵트인 (Y) 시 .dcness/tdd-gate-enabled 마커 작성
git add .dcness/tdd-gate-enabled  # 팀 공유
```

---

## v0.2.12 (2026-05-11)

**커밋 범위**: `v0.2.11..(다음 태그)`
**핵심 변경**: TDD 게이트 phase 3 — affected detection 자동 (CI 병목 해소, 사용자 설정 0)

- **이슈 #320 #1 phase 3 (PR #330)** — composite action 이 4 언어 변경분 affected
  만 자동 실행. v0.2.11 phase 2 풀 스위트의 CI watch 병목 (2~5분/PR × N task)
  해소.
  - **node**: nx.json / turbo.json / pnpm-workspace.yaml 자동 검출 →
    `nx affected` / `turbo run test --filter=...[<base>]` /
    `pnpm -F "...[<base>]" test`. dependency 그래프 자동 포함.
    - 미검출 (yarn classic / npm workspaces / bun / 단일) → 풀 폴백
  - **python**: 변경 .py 파일의 가장 가까운 상위 `pyproject.toml` / `setup.py` /
    `setup.cfg` 식별 → 그 root 별 pip install + pytest. 변경 0건 → skip.
  - **rust**: Cargo.toml `[workspace]` 검출 시 변경 파일 → member 매핑 →
    `cargo test -p <member>`. 단일 crate → `cargo test`. 변경 0건 → skip.
  - **go**: 변경 .go 의 dirname (유니크) → `go test ./<path>/...`. 변경 0건 → skip.
  - **PR base 자동 추출**: `github.event.pull_request.base.sha` 또는 origin/main 폴백

**jajang 효과**:
- apps/mobile (js + pnpm workspaces) 변경 → 해당 workspace + dependents 만 jest
- apps/api (python) 변경 → apps/api 안 pytest 만
- 둘 다 변경 안 됐으면 skip
- 사용자 작업 0 — `package.json["dcness"]["testCommand"]` override 박을 필요 없음

**배포 경로** (CLAUDE.md §0.5):
- (1) plug-in 본체 — `.github/actions/tdd-gate/action.yml` plug-in 업데이트 자동
- (2) init-dcness 배포 — Step 2.9 안내문 갱신. thin yml unchanged (composite action
  호출 1줄만 박힘 → 자동 phase 3 적용)
- (3) SSOT 문서 — N/A (capability 확장)

**한계 (phase 3)**:
- python/rust/go dependency 그래프 자동 포함 = phase 4 (현재 path 기반)
- yarn classic / npm workspaces / bun affected = 풀 폴백 (native filter 약함)
- 비-지원 언어 (Elixir/Ruby/Java/.NET/PHP/Swift) = phase 4

**업데이트**:
```sh
claude plugin update dcness@dcness
```

기존 활성화 프로젝트는 thin yml 그대로 — composite action 만 phase 3 자동 적용 (다음 PR 부터).

---

## v0.2.11 (2026-05-11)

**커밋 범위**: `v0.2.10..(다음 태그)`
**핵심 변경**: TDD 게이트 phase 1 → phase 2 — polyglot universal (#320 #1 확장)

- **이슈 #320 #1 phase 2 (PR #328)** — TDD 게이트가 node 한정에서 4 언어 universal
  로 확장. v0.2.10 phase 1 의 *node + root `scripts.test` 단일 명령* 가정이
  polyglot 모노레포 (jajang = apps/mobile=js + apps/api=python) 에 안 맞아 root fix.
  - `.github/actions/tdd-gate/action.yml` — 4 언어 검출 + 매트릭스 실행
    - node: package.json + pm 자동 (pnpm/yarn/bun/npm)
    - python: pyproject.toml / setup.py / setup.cfg / requirements*.txt + pytest (unittest 자동 cover)
    - rust: Cargo.toml + cargo test --all
    - go: go.mod + go test ./...
  - 검출된 *모든* 언어 PASS 필요 (polyglot matrix 결합)
  - 4 언어 모두 미검출 시 fail (비-지원 언어 phase 3 대기)
  - `commands/init-dcness.md` Step 2.9: 4 언어 안내문 + polyglot 가이드

**배포 경로** (CLAUDE.md §0.5):
- (1) plug-in 본체 — `.github/actions/tdd-gate/action.yml` plug-in 업데이트 자동 반영
- (2) init-dcness 배포 — Step 2.9 안내문 갱신. 기존 활성 프로젝트는 `/init-dcness`
  재실행 시 새 안내문 받음. thin yml 은 unchanged (외부 composite action 호출 1줄만
  박혀있어 자동 phase 2 적용)
- (3) SSOT 문서 — N/A (capability 확장)

**polyglot 적용 효과**:
- jajang (mobile=js + api=python): plugin update + `/init-dcness` 재실행만으로
  자동 cover. root `scripts.test` 위임 명령 / 별도 pytest workflow 작성 불필요.
- 향후 polyglot 활성 프로젝트들 모두 자동 혜택.

**한계 (phase 2)**:
- 지원 외 (Elixir / Ruby / Java / .NET / PHP / Swift) — phase 3 후속
- Python tooling = pip 만 (poetry / pdm / uv 는 phase 3)
- 풀 스위트만 — incremental 로컬 hook 은 phase 4

**업데이트**:
```sh
claude plugin update dcness@dcness
```

기존 활성화 프로젝트:
```sh
/init-dcness   # Step 2.9 발화 — TDD 게이트 옵트인 + 4 언어 안내문
```

---

## v0.2.10 (2026-05-10)

**커밋 범위**: `9a63e28..(다음 태그)`
**핵심 변경**: jajang Epic 12 회고 통합 — 진짜 bug 5건 root fix (이슈 #320 / #302 / #321 C / #292)

- **이슈 #320 #1 — TDD 게이트 3 단 (PR #322)**: jajang Epic 12 task 03 cascade 26
  cases 사단 root fix. engineer 의 prompt-level boundary 룰 (echo / grep) 은 차단력
  0 → mechanical wall 도입. 산업 표준 (incremental pre-commit → CI 풀 → branch
  protection) 중 *CI 풀* + *branch protection* 단을 dcness 가 배포.
  - `.github/actions/tdd-gate/action.yml` 신규 (node 전용, pm 자동 검출)
  - `commands/init-dcness.md` Step 2.9 추가 — 옵트인 thin yml + branch protection 안내

- **이슈 #320 #2 — PR body Closes pre-flight (PR #324)**: jajang Story 2 #239 OPEN
  영구 잔존 사단. `loop-procedure.md §3.4` 의 PR body 자동 판단 bash 가 stories.md
  *전체* `[ ]` 카운트 → 다른 Story 미완 task 와 섞임 → 본 task 가 부모 Story 마지막
  이라도 `Part of` 박힘. awk 으로 부모 Story 섹션 한정 카운트로 교체.
  - `docs/plugin/loop-procedure.md` §3.4 bash 골격 수정
  - `docs/plugin/issue-lifecycle.md` §1.4 적용 절차 4 step 명문화 추가

- **이슈 #302 #1 — RETRY_SAME_FAIL allow-list 보강 (PR #323)**: jajang run-cf83861d
  false positive 3건 — architect MODULE_PLAN × 4 task 정상 호출이 retry 오인 → review
  trust 저하. `harness/run_review.py` allow-list 에 `PROSE_LOGGED` (#284 prose-only
  mode 표준 sentinel) 추가 + prose 내용 다르면 다른 invocation 으로 판정 룰 추가.
  - 회귀 테스트 2 추가 (test_retry_same_fail_prose_logged_skip /
    test_retry_same_fail_different_prose_skip)

- **이슈 #321 C 1/4 — STRAY_DIR_LEAK detector (PR #325)**: jajang run-dbd49faf
  `.claire` × 3 회 연속 typo 사례. `harness/run_review.py:detect_wastes` 에 typo
  의심 디렉토리 검출 추가 (difflib similarity 0.70 threshold + KNOWN_INFRA_DIR_NAMES
  allow-list).
  - 회귀 테스트 3 추가. false positive 후보 9개 검증 (.vscode/.cargo/.cache 등
    모두 0.70 미만)

- **이슈 #292 partial — Step 4.5 범위 외 path 명문화 (PR #326)**: jajang main
  stories.md drift 177건의 root cause 일부 명문화. `loop-procedure.md §4` 본문에
  `quick-bugfix-loop` / engineer 직접 호출 / 메인 직접 commit / dcness 도입 이전
  잔재 — 사용자 책임 path 명시 + backfill 가이드 cross-link.

**배포 경로** (CLAUDE.md §0.5):
- (1) plug-in 본체 — `harness/`, `agents/` 변경은 plug-in 업데이트 자동 반영
- (2) init-dcness 배포 — Step 2.9 신규 (TDD 게이트). 기존 활성 프로젝트는
  `/init-dcness` 재실행 필요 — Step 2.9 자동 발화하여 thin yml 옵트인
- (3) SSOT 문서 — `loop-procedure.md` / `issue-lifecycle.md` plug-in cache 직접 read

**업데이트**:
```sh
claude plugin update dcness@dcness
```

기존 활성화 프로젝트는 추가로 `/init-dcness` 재실행 (Step 2.9 발화 + TDD 게이트
옵트인 + branch protection 안내). 멱등 — 다른 Step 들은 이미 적용된 경우 skip.

---

## v0.2.9 (2026-05-09)

**커밋 범위**: `156691f..(다음 태그)`
**핵심 변경**: init-dcness 신규 프로젝트 초기 docs 폼 시드 (이슈 #296)

- **이슈 #296** — `/init-dcness` 실행 시 `docs/PRD.md` / `docs/ARCHITECTURE.md` /
  `docs/ADR.md` 3개 파일 시드 (부재 시만, 멱등). 사용자가 PRD 논의 후 채워넣을
  표준 placeholder 제공 — 매 프로젝트마다 다른 형태로 시작하던 분산 해소.
  - `templates/project-init/{PRD,ARCHITECTURE,ADR}.md` 신규.
  - `commands/init-dcness.md` Step 2.8 추가 — 부재 시 사용자 동의 받고 cp.
  - 짧고 placeholder 위주 (한 화면 내 완결).

**배포 경로**: 본 변경은 init-dcness 가 사용자 repo 로 *복사·배포* 하는
인프라 (배포 경로 2). 기존 활성화 프로젝트는 자동 적용 안 됨 — `/init-dcness`
재실행 시 부재 파일만 시드 (멱등). 신규 프로젝트는 이번 release 부터 자동 시드.

**업데이트**:
```sh
claude plugin update dcness@dcness
```

기존 활성화 프로젝트에서 docs 폼 받고 싶으면 `/init-dcness` 재실행 (멱등).

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
