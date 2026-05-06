# Branch Surface Tracking — 사다리 진입 조기 감지

> **출처**: 2026-04-30 RWH 에이전트 진단 + 본 저장소 응답 (`docs/process/change_rationale_history.md` `DCN-CHG-20260430-03`).
>
> **목적**: dcNess 가 RWH 가 빠진 *patch-of-patch 사다리* (특히 사다리 #2 = 내부 state hole) 에 진입하는 시점을 가능한 한 조기에 자각.
>
> **본 문서가 정의하는 것**: 신규 분기 / 진입경로 추가 PR 의 self-check + 사다리 시그널 분류 + 임계 도달 시 대응.
>
> **본 문서가 정의하지 *않는* 것**: 사다리 자체를 *방지* 하는 메커니즘 (그건 운영적 절제 — `docs/archive/migration-decisions.md` §7 참조).

---

## 1. 사다리 분류 (3 종)

RWH 깃 로그 분석 + dcness 자기 점검 결과 3 가지 구분:

| # | 이름 | 원인 layer | RWH 사례 | dcness 상태 |
|---|---|---|---|---|
| 1 | **형식 사다리** | LLM 출력 형식 강제 | `MARKER_ALIASES ×12`, parse_marker alias map | **자연 부재** — prose-only 가 발생 자리를 없앰 |
| 2 | **state hole 사다리** | 내부 상태기계 분기 × 진입경로 | plan_loop checkpoint hole, worktree 재사용 untracked plan 미복사 | **아직 시작 X** — by-pid 가 첫 분기 케이스, sweep/orphan patch 0회 |
| 2.5 | **외부 환경 사다리** | 외부 시스템 (CC plugin install / marketplace 컨벤션) 미공식 | RWH PLUGIN_ROOT self-detect | DCN-CHG-41/42 (PYTHONPATH wrapper / cache glob fallback) |

**핵심 구분**:
- 사다리 #2 와 #2.5 는 *형식 같지만 layer 다름*. 사다리 #2 는 dcness 자체 코드 안 분기, 사다리 #2.5 는 외부 시스템과의 인터페이스.
- 형식 강제 정조준 타격 (#1) 은 #2/#2.5 에 무력.
- 분기 폐기 (#2 회피 전략) 는 #2.5 에 무력.

---

## 2. 신규 분기 추가 PR 의 self-check

다음 변경을 포함하는 PR 작성자는 본 절 체크리스트를 PR body 에 붙인다 (governance §2.6 의 `harness` / `hooks` / `spec` 카테고리 PR 한정 — `docs-only` / `test` 면제):

```markdown
## Branch Surface Self-Check

- 이 PR 이 추가하는 분기 / 진입경로 수: <N>
- 추가된 분기 종류:
  - [ ] 새 함수 분기 (if/else / match)
  - [ ] 새 진입점 (CLI subcommand / hook 새 trigger / skill 새 step)
  - [ ] 폴백 분기 (예: env 미설정 시 default path)
  - [ ] 외부 시스템 인터페이스 분기 (plugin / git / CC / OS 등)
- hole 후보 자리 (분기 안 *상태 보존 의무* 자리):
  - <list — 또는 "없음 (분기가 stateless)">
- 직전 30 일 동일 패턴 PR:
  - <Task-ID 들 + 짧은 설명, 또는 "없음">
- 사다리 진입 자가 판정:
  - [ ] 사다리 #1 (형식) — 해당 없음 (prose-only)
  - [ ] 사다리 #2 (state hole) — <yes/no + 이유>
  - [ ] 사다리 #2.5 (외부 환경) — <yes/no + 이유>
```

작성 가이드:

- **분기 / 진입경로 수**: `if` / `match` / `try` / 새 CLI subcommand / hook trigger 등 사람 눈으로 추가된 분지점. 한 줄 1점.
- **hole 후보 자리**: 그 분기 안에서 상태 (파일 / live.json / by-pid / .steps.jsonl 등) 가 갱신/저장되는 자리. 분기 추가 시 자주 누락.
- **30 일 동일 패턴 PR**: `git log --since='30 days ago' --grep='<keyword>'` 으로 검색. 동일 모듈에 같은 종류의 분기 patch 가 3 회 이상 누적이면 사다리 시그널.

---

## 3. 사다리 임계 신호 (warning / critical)

| 신호 | 임계 (warning) | 임계 (critical) |
|---|---|---|
| 동일 모듈에 같은 종류 hole patch | 30 일 안 3 회 | 30 일 안 5 회 |
| 한 함수의 분기 수 | 7 이상 | 12 이상 |
| 한 PR 에서 추가되는 분기 수 | 5 이상 | 10 이상 |
| 폴백 분기 (env 미설정 / 파일 미존재 등) 의 케이스 다중화 | 3 단 이상 | 4 단 이상 |
| `harness/` 단일 파일 LOC | 1500 이상 | 2500 이상 |

### 3.1 warning 도달 시

PR body 에 명시:
```
⚠️ Branch Surface Warning — <임계 항목 + 수치>
완화안: <분기 통합 / 진입점 단일화 / 폐기 검토 등>
```

다음 PR 부터 분기 추가 신중. 리뷰어 (현재는 사용자 / 메인 Claude 자가 점검) 가 폐기 가능 분기 적극 탐색.

### 3.2 critical 도달 시

다음 작업 중단 + spec 발상 전환 협의:

1. 신규 Task-ID 발급 (`docs/process/document_update_record.md` 안 별도 entry)
2. 회의 — 현재 사다리 진입 사실 명시 + RWH 사례 비교 + 발상 전환 후보
3. `docs/archive/migration-decisions.md` 확인 — 임계 도달 패턴 + 결정

발상 전환 후보 (참고):
- 분기 자체 폐기 (가능하면)
- 진입점 단일화 (여러 hook → 단일 dispatcher)
- 외부 시스템 의존 격리 (예: CC plugin path 검색을 helper 1곳에 집중)
- spec 자체 변경 (예: state 위치 통합)

---

## 4. dcness 의 한계 (RWH 진단 인용)

RWH 에이전트 (2026-04-30):

> ▎ State hole 은 발상 전환으로 안 사라짐. 분기가 있는 한 자리는 있음. dcness 의 답 = 분기 자체를 줄임. 분기를 줄일 수 있는 동안만 유효한 답.

dcness 의 베팅:
- 사다리 #1 차단 = 발상 (prose-only) 으로 영구 해결
- 사다리 #2 회피 = *작은 표면적 유지* — 분기 늘면 동일 사다리 진입 가능
- 사다리 #2.5 = 양쪽 공통 부담, dcness 가 더 유리하지도 불리하지도 않음

**즉, dcness 의 self-discipline 은 "분기 늘리지 않기" 가 1차 룰**. 본 추적 문서가 그 자가 점검 회로.

---

## 5. 본 문서 자체의 한계

- **추적 대상 ≠ 사다리 방지**: 신호 보고 자가 멈출지 결정은 사람의 판단. 자동 차단 메커니즘 없음.
- **임계 수치는 추정**: 30/3, 30/5, 1500/2500 LOC 등은 RWH 데이터를 1-time snapshot 본 추정. 30 회 이상 dcness 자가 데이터 쌓이면 보정 필요.
- **layer 구분 회색지대**: 사다리 #2 vs #2.5 가 명확히 구분 안 되는 케이스 존재 (예: hook 의 PYTHONPATH 처리는 외부 환경이지만 hook 코드의 분기이기도). 자가 판정 시 보수적으로 (#2 분류 — 더 엄격) 처리.

---

## 6. 운영 절차

1. 매 `harness` / `hooks` / `spec` PR 작성 시 §2 self-check 첨부
2. warning 도달 시 §3.1 절차
3. critical 도달 시 §3.2 절차
4. 30 일 단위 회고 — `docs/process/branch-surface-tracking-log.md` (별도, 본 PR 에선 생성 안 함) 에 누적 기록 → 임계 수치 보정

본 문서는 sticky — RWH 가 dcness 에 던진 가장 가치 있는 외부 시각이라 dcness governance 의 영구 자리에 박는다.

---

## 7. 참조

- `docs/process/governance.md` — PR 일반 절차
- `docs/process/document_update_record.md` `DCN-CHG-20260430-03` — 본 문서 신규 entry
- `docs/process/change_rationale_history.md` `DCN-CHG-20260430-03` — 채택 동기 + RWH 진단 인용 + 행동 결정
- `docs/archive/migration-decisions.md` §7 — RWH 사다리 카탈로그 + dcness 한계 명시 (역사 자료)
- `docs/plugin/prose-only-principle.md` §2 — Anti-Pattern 5원칙 (룰 순감소 / catastrophic-prevention 등)
