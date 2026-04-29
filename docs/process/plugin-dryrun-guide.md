# Plugin 배포 Dry-Run 가이드

> 규칙 정의: 본 가이드는 `docs/status-json-mutate-pattern.md` §12 (RWHarness → 신규 Plugin 전환 절차) 의 *적용 운영 가이드*.
> Origin: `DCN-CHG-20260429-24` (Phase 3 종결 + dry-run 인프라 정리).

## 0. 목적

dcNess Phase 1~3 통과 후, 실 사용자 프로젝트에 plugin 으로 배포하기 *전* RWHarness 와의 공존 시나리오 + 회귀 안전망을 단계별로 검증한다. 본 가이드는 **호스트 머신** (사용자 dev 환경) 에서 실행한다.

**전제**:
- dcNess 자체 Phase 1~3 통과 (PROGRESS.md 확인)
- (선택) ANTHROPIC_API_KEY — heuristic-only 정착으로 dcness 자체엔 불필요. CC 메인 사용 등 외부 호출 시만 필요.
- RWHarness 가 이미 설치된 환경 (`~/.claude/plugins/cache/realworld-harness/...`)
- plugin admin 권한 있는 사용자 프로젝트 1개 (도그푸딩 대상)

**비목표**:
- production 사용자 프로젝트 강제 배포
- RWHarness 파일 직접 변경

---

## 1. 사전 검증 (proposal §12.1 정합)

```sh
# RWHarness 설치 위치 확인
ls ~/.claude/plugins/cache/realworld-harness/realworld-harness/

# 활성 화이트리스트 확인
cat ~/.claude/harness-projects.json

# 플러그인 매니저 동작 확인
claude plugin list
```

기대: RWHarness 가 정상 enabled 상태. 화이트리스트 백업 가능.

---

## 2. dcNess plugin manifest 검증

```sh
cd ~/project/dcNess
cat .claude-plugin/plugin.json   # name=dcness, version=0.1.0-alpha 확인
cat .claude-plugin/marketplace.json
claude plugin validate .claude-plugin
```

기대: validate 통과. name 충돌 0 (RWHarness=`realworld-harness`, dcNess=`dcness`).

---

## 3. 신규 marketplace 등록 (proposal §12.3.1)

```sh
# 로컬 path 또는 GitHub
claude plugin marketplace add /Users/dc.kim/project/dcNess/.claude-plugin
# 또는: claude plugin marketplace add github:alruminum/dcNess

claude plugin marketplace list
```

기대: `dcness` marketplace 가 신규 entry 로 등록.

---

## 4. plugin 설치 + 충돌 회피 (proposal §12.3.2)

```sh
claude plugin install dcness@dcness
claude plugin disable realworld-harness@realworld-harness  # 충돌 회피
claude plugin list
```

**중요**: 두 plugin 동시 enabled 시 `prose-only` 패턴(dcness) vs `marker/Flag` 패턴(RWHarness) 가 *같은 hook* 을 등록하면 race condition 발생 가능. 항상 한쪽만 enabled.

---

## 5. Smoke Test — 실 LLM 호출 1회

```sh
cd ~/project/dcNess

# 5.1) 환경변수 (heuristic-only 정착 — DCN-CHG-20260430-04 — 후 ANTHROPIC_API_KEY 불필요)
export DCNESS_LLM_TELEMETRY=1   # 기본값, 명시 (telemetry 켜짐)

# 5.2) 1 호출 (Python REPL 또는 작은 스크립트)
python3 << 'EOF'
from harness.interpret_strategy import interpret_with_fallback

prose = """
검증 결과: 5 파일 수정. 테스트 모두 통과.

## 결론
PASS — 코드가 계획과 일치.
"""

result = interpret_with_fallback(prose, ["PASS", "FAIL", "SPEC_MISSING"])
print(f"Result: {result}")
EOF

# 5.3) telemetry 확인
ls -la .metrics/
cat .metrics/heuristic-calls.jsonl | tail -3

# 5.4) 분석기 실행
node scripts/analyze_metrics.mjs
```

**기대**:
- `Result: PASS` (휴리스틱 단어경계 매칭 hit)
- `.metrics/heuristic-calls.jsonl` 에 `outcome: "heuristic_hit"` 1줄
- analyzer 가 `heuristic_hit_rate` 비율 출력

**추가**: 의도적 ambiguous 케이스 — heuristic-only 라 MissingSignal propagate:

```python
from harness.signal_io import MissingSignal
prose = "검증 진행 중. 결론 미확정."  # 휴리스틱 0 hit → ambiguous
try:
    interpret_with_fallback(prose, ["PASS", "FAIL"])
except MissingSignal as e:
    print(f"ambiguous: {e.detail}")
```

기대: `MissingSignal` raise, `.metrics/heuristic-calls.jsonl` 에 `outcome: "heuristic_ambiguous"` entry. 메인 Claude 가 cascade (재호출 / 사용자 위임) 결정.

---

## 6. 1 cycle 도그푸딩 (proposal §12.3.3 정합)

dcNess agents/*.md 의 작성 가이드대로 *실 작업 1 cycle* (예: 작은 PR 자동 생성) 진행 후 분석:

```sh
# 1 cycle = 임의 변경 → validator agent 호출 → engineer agent 호출 → pr-reviewer agent 호출
#         (메인 Claude 가 Task 도구로 dcness agent docs 따라 호출)
# 본 step 은 사용자 환경 + Claude Code 통합이 필요 — 본 가이드는 절차만 명시.

# 분석
node scripts/analyze_metrics.mjs --json > .metrics/cycle1-summary.json
```

**fitness 기준** (proposal §5 Phase 4):

| 측정 | 목표 | analyzer 항목 |
|---|---|---|
| 휴리스틱 hit rate | ≥ 80% | `heuristic_hit_rate` |
| LLM cycle 비용 | < $0.10 | `cost_projection.per_cycle_65_calls_usd` |
| ambiguous (모호 propagate) | < 5건/cycle | `ambiguous_rate * 65` |
| catastrophic 가드 | 무손실 | `agent-boundary` 동작 (RWHarness 측 확인) |

---

## 7. 통과 시 RWHarness 완전 제거 (proposal §12.3.4)

```sh
claude plugin disable realworld-harness@realworld-harness
claude plugin enable dcness@dcness

# 추가 1~2 cycle 도그푸딩 검증 (다른 프로젝트)

claude plugin uninstall realworld-harness@realworld-harness
rm -rf ~/.claude/plugins/cache/realworld-harness
rm -rf ~/.claude/plugins/marketplaces/realworld-harness
claude plugin marketplace remove realworld-harness
```

**🔴 주의**: 본 단계는 *destructive*. 반드시 사용자 명시 동의 후만 실행.

---

## 8. 즉시 롤백 시나리오 (proposal §12.3.5)

문제 발견 시:

```sh
claude plugin disable dcness@dcness
claude plugin enable realworld-harness@realworld-harness
cp ~/.claude/harness-projects.json.bak ~/.claude/harness-projects.json
```

dcNess 의 `.metrics/` 와 `.claude/harness-state/` 는 보존 (분석 자료).

---

## 9. Acceptance — 전환 완료 기준 (proposal §12.5 정합)

| 항목 | 검증 방법 |
|---|---|
| 1 프로젝트 1 cycle 도그푸딩 무사고 | analyzer fitness PASS |
| 추가 1 프로젝트 1 cycle 도그푸딩 무사고 | 같은 fitness 두 번째 cycle PASS |
| cache hit / poor_cache_util RWHarness baseline 동등+ | `improve-token-efficiency` 스킬 실행 비교 |
| 형식 강제 사고 (marker fragility) 0건 | dcNess 는 marker 폐기 → 자연 만족 |
| catastrophic 가드 작동 검증 | 의도적 src/ 외 수정 → 차단 (RWHarness agent-boundary 동작 확인) |
| 메타 LLM 비용 (heuristic-only 정착으로 0 — DCN-CHG-20260430-04) | `analyze_metrics.mjs` `cost_projection` 비대상 |
| 롤백 절차 1회 dry-run 검증 | §8 절차 한 번 실행 → 정상 복귀 확인 |
| RWHarness 완전 uninstall 후 7일 무사고 | 운영 모니터링 |

---

## 10. 본 가이드와 다른 문서 관계

| 문서 | 역할 |
|---|---|
| [`status-json-mutate-pattern.md`](../status-json-mutate-pattern.md) §12 | proposal SSOT — 절차의 의도/근거 |
| [`migration-decisions.md`](../migration-decisions.md) | 모듈 분류 결과 (DISCARD / PRESERVE / REFACTOR) |
| [`branch-protection-setup.md`](branch-protection-setup.md) | main 브랜치 보호 (Phase 3 iter 2) |
| [`governance.md`](governance.md) | dcNess 자체 거버넌스 (commit/PR 룰) |
| 본 가이드 | proposal §12 의 *적용 운영 절차* (Phase 3 iter 5) |

---

## 11. 후속 작업 (Phase 4)

본 가이드 통과 후 proposal §5 Phase 4 (4 기둥 fitness 측정 도그푸딩 1 cycle) 진입. 측정 항목:

- 컨텍스트 layer (CLAUDE.md + agents/*.md + ...) — 5 → 2
- hook 갯수 — 7 → 3 (catastrophic 만)
- LOC 순감소 — 5000 → 2500~3000
- 형식 강제 호출지 — 0 (dcNess 자연 만족)
- poor_cache_util 비용 — $507 → $200 미만
- jajang marker fragility — 0 (자연 만족)
- 메타 LLM cycle 당 — 0 (heuristic-only, DCN-CHG-20260430-04)
- catastrophic 가드 — 무손실
