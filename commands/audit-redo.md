---
name: audit-redo
description: dcness conveyor run 의 redo-log + agent-trace 결합 분석 skill. (sub, mode) 별 redo 빈도 추출 + Layer 1 (현 프로젝트 1차 prompt 첨가) + Layer 2 (dcness plugin agent definition 영구 patch) 후보 제안. 사용자가 "/audit-redo", "redo 분석", "감시자 학습", "패턴 환류" 등을 말할 때 사용. /run-review 와 직교 — /run-review = waste/good findings, /audit-redo = redo 패턴 학습.
---

# Audit Redo Skill — 메인 감시자 학습 진화 (Layer 1 + Layer 2)

> sub completion 평가 결과 (`redo-log.jsonl`) 와 sub 행동 trace (`agent-trace.jsonl`) 를 결합 분석. 자주 redo 부르는 (sub, mode) 패턴 추출 → 1차 prompt 풍부화 후보 제안. 룰 추가 X, prompt 풍부화 ✅.

## 언제 사용

- 사용자 발화: "/audit-redo", "redo 분석", "감시자 학습", "패턴 환류", "어떤 sub 자주 redo"
- impl-loop 종료 후 redo 누적 분석
- 주기 (월 1회 권고) — Layer 2 환류 시점

## 언제 사용하지 않음

- waste / good findings 추출 → `/run-review` (직교 skill)
- 단일 sub spawn 1회 결과 평가 → SessionStart 메시지의 즉시 평가 (skill 불필요)
- run 진행 중 → 적어도 1 cycle (sub completion + 메인 평가) 끝난 후

## 핵심 동작

`.sessions/{sid}/runs/{rid}/redo-log.jsonl` + `agent-trace.jsonl` 를 cross-correlation 해서:

1. **(sub, mode) 별 결정 분포** — PASS / REDO_SAME / REDO_BACK / REDO_DIFF 카운트
2. **REDO 사유 카테고리** — 자유 텍스트 reason 클러스터링 (해시태그 / 키워드)
3. **trace 패턴 매칭** — 각 redo entry 의 trace 시퀀스 (어떤 tool 어디 썼나) 공통점
4. **Layer 1 후보** — (sub, mode) 의 redo 비율 임계 초과 시 "다음 spawn 1차 prompt 에 X 사전 보강" 제안
5. **Layer 2 후보** — Layer 1 적용이 N 프로젝트 / N 회 검증되면 `agents/{sub}.md` 영구 patch 제안

## 절차

### Step 0 — run 식별 (선택)

단일 run 분석 또는 다중 run 누적. 인자:

- 무인자 → 현재 active run (live.json) 단일
- `--run-id <RID>` → 명시 run 단일
- `--all-runs` → 본 sid 의 모든 run 누적
- `--list` → run 목록 (run_id + redo-log entry 수)

### Step 1 — redo-log + trace read

```python
from harness.redo_log import read_all as read_redos
from harness.agent_trace import read_all as read_trace

redos = read_redos(sid, rid)
traces = read_trace(sid, rid)
```

`redos` 가 비어있으면 → "본 run 평가 기록 0건 — 메인 SessionStart 감시자 hat 비활성 의심" 보고 후 종료.

### Step 2 — (sub, mode) 분포 + REDO 사유 추출

각 redo entry 에서 `sub`, `mode`, `decision` 키로 그룹핑:

```
engineer / IMPL: PASS=12 / REDO_SAME=2 / REDO_BACK=5 (redo 비율 37%)
architect / MODULE_PLAN: PASS=8 / REDO_BACK=1 (redo 비율 11%)
validator / CODE_VALIDATION: PASS=10 (redo 비율 0%)
```

각 redo entry 의 `reason` 자유 텍스트에서 키워드 추출 (예: "module plan 모호", "테스트 미통과", "boundary 위반"). 동일 키워드 N 회 누적 시 클러스터.

### Step 3 — trace 패턴 매칭

각 REDO entry 의 발생 직전 trace 시퀀스 (마지막 N 줄, agent_id 매칭) 추출. 공통 패턴 (예: "Bash 5회 반복 + exit≠0 무시") 식별.

### Step 4 — Layer 1 / Layer 2 후보 출력

리포트 형식:

```markdown
## (sub, mode) 별 결정 분포

| sub | mode | total | PASS | REDO_SAME | REDO_BACK | REDO_DIFF | redo 비율 |
|---|---|---|---|---|---|---|---|
| engineer | IMPL | 19 | 12 | 2 | 5 | 0 | 37% |
| ...

## 자주 REDO 부르는 (sub, mode)

### engineer / IMPL — redo 37% (임계 초과)

REDO 사유 클러스터:
- "module plan 모호" — 4 / 7
- "테스트 통과 못함" — 2 / 7
- 기타 — 1 / 7

trace 패턴:
- 직전 5줄 평균 — Read×3, Edit×1, Bash×2 (exit≠0 1회)
- 공통 — `Bash pytest exit=1` 후 추가 Edit 없이 종료

### Layer 1 후보 (현 프로젝트 즉시 적용)

다음 architect MODULE_PLAN sub spawn 시 1차 prompt 끝에 추가:
> "이 프로젝트에서 module plan 모호로 인한 engineer redo 비율 37%. 인터페이스 시그니처 + 의사코드 명시 의무."

### Layer 2 후보 (인프라 환류 — 검증 후)

위 Layer 1 적용이 N 회 (또는 N 프로젝트) 검증되면 `agents/architect/module-plan.md` system prompt 영구 patch 제안:
> "MODULE_PLAN 산출 시 engineer 가 즉시 구현 가능한 수준 — 인터페이스 시그니처 (타입) + 핵심 로직 의사코드 강제."

→ PR 작성 후 governance §2.2 `agent` Change-Type 으로 머지.
```

### Step 5 — 후속 액션 권고 (1-3 줄)

리포트 끝에 메인이 1-3 줄로 후속 결정 권고:
- Layer 1 후보 N 개 → 다음 spawn 시 메인이 직접 prompt 첨가
- Layer 2 후보 1 개 → 별도 Task-ID 발급 후 PR 진행
- 후보 0 개 → "본 run 의 redo 패턴 결정적 X — 다음 cycle 모니터 지속"

## 출력 룰

`/run-review` 와 동일 — Bash stdout 리포트를 한 글자도 바꾸지 않고 그대로 응답에 복사. 자체 해석 / 압축 X.

## 호출 예시

```
사용자: /audit-redo
메인: (현재 run 분석) → 리포트 그대로 출력 → "Layer 1 후보 1개 (architect MODULE_PLAN 보강) 적용 권고. Layer 2 는 다음 프로젝트 검증 후."

사용자: /audit-redo --all-runs
메인: (본 sid 의 모든 run 누적) → 더 강한 패턴 → Layer 2 patch 제안 N 개

사용자: 어떤 sub 가 자주 redo?
메인: /audit-redo skill 호출 → (sub, mode) 분포 표 + 임계 초과 카테고리
```

## 한계 (정직)

- Hook trace = sub *행동* 만 (thinking / 중간 message X). 추론 사유 분석은 P7 미래 (`.output` 가공)
- 도구 0번 쓰는 sub turn = trace 텅 빔 → 본 분석 부정확
- 단일 run 표본 작음 — `--all-runs` 또는 다중 sid 누적이 통계 신뢰 ↑
- REDO 사유 클러스터링은 자유 텍스트 키워드 매칭 — 정밀도 한계, 메인 정성 판단 보조 필요
