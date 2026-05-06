# Prose-Only 원칙 — 형식 강제 폐기 + heuristic enum 추출

> **현행 SSOT** — 핵심 원리만 추출. proposal 전문 (Phase 분할 / 전환 절차 / Risks 등) 은 [`docs/archive/status-json-mutate-pattern.md`](../archive/status-json-mutate-pattern.md).

---

## 대 원칙

> **harness 가 강제하는 것은 단 2가지 — (1) 작업 순서, (2) 접근 영역. 그 외 모두 agent 자율.**

- **작업 순서** = 시퀀스 (validator → engineer → pr-reviewer 등) + retry 정책
- **접근 영역** = file path 경계 (agent-boundary ALLOW/READ_DENY) + 외부 시스템 mutation 차단 (push, gh issue, plugin 디렉토리)
- **출력 형식 / handoff 형식 / marker / status JSON / Flag / 모든 형식적 강제 = agent 자율. harness 가 강제하지 않는다.**

---

## Anti-Pattern 원칙 5가지

**원칙 1: 룰이 룰을 부르는 reactive cycle 차단**
- 신규 룰 추가 전 기존 룰 제거 가능성 우선 검토. 추가→제거 비대칭이 부채.

**원칙 2: 강제 vs 권고 분리**
- **강제(deny/block)**: catastrophic 만 (plugin-write-guard, agent-boundary 인프라 차단)
- **권고(warn/log)**: 그 외. 형식 위반, 비용 폭증 등은 측정 + 경고 + 사용자 개입
- 권고 → 강제 자동 승격 금지 (30일 데이터 + 결정 PR 필수)

**원칙 3: agent 자율성 최대화**
- agent prompt 의 강제 형식 0
- prose 작성 가이드(결론 + 이유 명확히) 만 — 형식이 아니라 의미
- agent 가 빠뜨림 = prompt 명료화 우선 (룰 추가 X)

**원칙 4: 흐름 강제는 catastrophic 시퀀스만**
- impl_loop 시퀀스 보존. 시퀀스 내부 행동 = agent 자율.

**원칙 5: 신규 hook 추가 전 30일 측정**
- "사고 발생 → hook" 이 아니라 "사고 발생 → 30일 빈도 → 정당화 후 hook"

---

## heuristic-only 정착 (2026-04-30 확정)

원래 비전(메타 LLM haiku 해석)에서 heuristic-only 로 변경. 이유:

1. **API 키 의존 회피** — plugin 사용자 환경에 ANTHROPIC_API_KEY 강제 = 진입 장벽
2. **메인 Claude = LLM** — 별도 judge 호출 = 2-LLM 패턴, 비용 + latency 증가
3. **충분성 검증** — prose 마지막 영역에 enum 단어 명시 시 단어경계 매칭 ≥ 80%

**현재 인프라**: `harness/interpret_strategy.py` (heuristic-only) + `harness/signal_io.interpret_signal` (heuristic default + DI swap option).

---

## 도입 안 할 것

- 출력 형식 강제 (marker / status JSON / @OUTPUT_SCHEMA)
- handoff 형식 (next_actions[] 같은 구조 강제)
- Flag 시스템 (boolean flag 파일)
- preamble 자동 주입
- schema / alias map / parse_marker 사다리
