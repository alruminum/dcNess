# dcness Self Guidelines (dcness 내부 협업 룰)

> dcness 저장소 자체 작업 시 메인 Claude 가 따르는 내부 룰.
> 외부 활성화 프로젝트 사용자에게는 해당 없음.

## 1. 행동지침 md 300줄 cap (DCN-30-30)

dcness 행동지침 문서 (메인 Claude 또는 sub-agent 가 의사결정 시 *직접 read* 하는 md) 는 **파일당 300줄 cap**. 초과 시 책임 분리 축으로 split.

**대상 파일 (예시)**:
- `docs/plugin/loop-procedure.md` (loop mechanics SSOT)
- `docs/plugin/dcness-rules.md` (dcness rules)
- `docs/internal/self-guidelines.md` (본 가이드라인)
- `docs/plugin/orchestration.md` (loop spec SSOT — DCN-CHG-20260505-03 후 cap 500 예외)
- `commands/*.md` (skill prompt)
- `agents/**/*.md` (agent prompt)

**대상 외 (cap 미적용)**:
- `PROGRESS.md` (스냅샷)
- `docs/spec/**` / `docs/proposals/**` (긴 사양 문서 — 의사결정 직접 read X)
- `tests/**` / `harness/**` 등 코드
- `docs/archive/**` (역사 자료 — read-only)

**Why**:
- 메인 Claude / sub-agent 가 매 결정 시 read → 토큰 누적 + thinking 시간 ↑.
- 300줄 = 한 read 호출에서 파악 가능한 임계 (RWHarness 경험치 정합).
- 초과 시 *책임 축* 분리 (mechanics vs catalog / 시퀀스 vs 절차 등) — 복붙 분할 X.

**How to apply**:
- 새 행동지침 md 작성 시 300줄 목표.
- 기존 파일 라인 수 모니터링 — 초과 발견 시 split PR (별도 Task-ID).
- split 시 cross-ref 양방향 갱신.

**현재 알려진 위반**: 없음. 이전 위반 (orchestration.md 540줄) 은 DCN-30-32 에서 handoff-matrix.md 분리로 해소 (각각 298 / 256 줄).

## 2. 진단/제안 self-verify 원칙 (글로벌 제1룰 정합)

> 글로벌 `~/.claude/CLAUDE.md` 제1룰이 SSOT. 본 절은 dcness 컨텍스트 특화 추가분.

### 룰 (MUST)

모든 사용자-facing 진단 / 제안 *제출 전*:
- 등장하는 파일 경로 / 함수명 / CLI 옵션 → `grep` / `ls` / `Read` 실측 후 단언
- 등장하는 테스트 결과 / 숫자 / 변경 규모 → 명령 실행 후 인용
- Bash `sed -i` / `awk -i` / 광역 변환 후 *전·후* 실측 필수 (`git diff --stat` 또는 결과 grep)
- 자기 박은 hook / inject / 자동화 도입 시 *실 작동 검증 후* 후속 PR 진행
- CI 결과 확인 — "local PASS" 만으로 머지 금지
- 추측 표현 (`아마`, `보통`, `대략`, `~ 정도`) 금지

위반 패턴 발견 시 즉시 검증 단계로 되돌아가 사실 확인 후 재구성.

### dcness 특화 안티패턴

❌ Bash sed/awk 후 "X개 fix" 즉시 단언 — 전·후 실측 없이 숫자 인용  
❌ engineer 보고 즉시 신뢰 — end-step echo 읽고 실측 후 평가  
❌ 자기 박은 SessionStart inject 작동 가정 → 실측 없이 후속 PR 진행  
❌ CI 결과 확인 안 함 → "earlier tests passed" 단언  

### 자율 보존

*검증 방법은 자율* — grep / ls / Read / Bash / 외부 docs WebFetch 중 자기 판단. 형식 강제 X. 추측 금지 + 실측 후 단언만 강제.
