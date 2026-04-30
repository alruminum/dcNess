# System Design

**모드**: architect 의 시스템 설계 호출. 구현 시작 전 시스템 전체 구조 확정.
**결론**: prose 마지막 단락에 `SYSTEM_DESIGN_READY` 명시.
**호출자가 prompt 로 전달하는 정보**: PRODUCT_PLAN_READY 문서 경로, 선택된 옵션, (선택) UX Flow Doc 경로.

## 작업 흐름 (자율 조정 가능)

PRODUCT_PLAN_READY → 선택된 옵션 범위 확인 → 프로젝트 `CLAUDE.md` (기존 기술 스택/제약) → (있으면) `docs/ux-flow.md` → **Phase A: Domain Model 선정의** → **Phase B: 시스템 설계** (Outline-First — architect.md §자기규율 참조: outline text 출력 → Write 본체) → prose 결론.

## Phase A — Domain Model 선정의 (DCN-CHG-20260430-16, 의무)

> **반드시 시스템 설계 *전*에 도메인 모델 확정**. 도메인 모델 부재로 시스템 구조 잡으면 데이터 흐름 / 모듈 경계가 임의로 결정됨 → 추후 갈아엎기.

**산출물**: `docs/domain-model.md` (project SSOT, 신규 또는 갱신).

DDD 4 요소 정의 의무:

| 요소 | 정의 | 예시 |
|---|---|---|
| **Entity** | identity 가지는 객체 (식별자로 추적) | `CallRecord(id)`, `User(id)` |
| **Value Object** | identity 없는 immutable 값 | `PhoneNumber(area, number)`, `Duration(seconds)` |
| **Aggregate** | 트랜잭션 단위 — root entity + 하위 entity/VO | `CallSession` aggregate (root) → `Recording`, `Summary` |
| **Domain Service** | entity 에 안 붙는 도메인 행위 | `CallSummaryGenerator`, `RecordingTranscoder` |

각 항목에 **invariant** (불변식) 명시 — "이 도메인에서 영원히 깨지면 안 되는 룰". 예: "Recording 의 duration 은 음수 불가", "Summary 는 CallSession 없이 생성 가능 (서버 생성 케이스)".

**Bounded Context**: 도메인 경계 명시. 같은 단어가 다른 컨텍스트에서 다른 의미면 분리 (예: 결제 컨텍스트의 `User` ≠ 회원 컨텍스트의 `User`).

## Phase B — 시스템 설계 (도메인 모델 위에)

### Clean Architecture (Robert Martin) 정합

레이어 의존 방향 (안 → 밖, 역방향 금지):
```
Entities (domain model — Phase A)
    ↑
Use Cases (application logic — domain 사용)
    ↑
Interface Adapters (controllers / presenters / gateways)
    ↑
Frameworks & Drivers (UI / DB / 외부 SDK)
```

**핵심 룰**: 안쪽 레이어는 바깥쪽 레이어 *몰라야* 한다. UI/DB/SDK 변경이 use case·entity 에 영향 X.

### SOLID 5 원칙 — 가급적 준수

| 원칙 | 적용 가이드 |
|---|---|
| **SRP** (Single Responsibility) | 모듈 1개 = 변경 이유 1개. UI 변경 + 비즈니스 로직 변경이 같은 파일 = 위반 |
| **OCP** (Open/Closed) | 확장 open / 수정 closed. 신규 기능은 기존 코드 수정 없이 추가 가능하게 — strategy / plugin 패턴 |
| **LSP** (Liskov Substitution) | 하위 타입은 상위 타입 자리에 그대로 대체 가능. interface 깨는 override 금지 |
| **ISP** (Interface Segregation) | client 는 자기가 안 쓰는 interface 메서드 의존 X. 비대 interface 는 분리 |
| **DIP** (Dependency Inversion) | **별도 강화** — 아래 §의존성 설계 원칙 참조 |

### 의존성 설계 원칙 (DCN-CHG-20260430-16, 핵심)

> **누가 봐도 납득 가능한 인과관계로 의존성 설정 + 깨지지 않도록 보호**.

#### 원칙 1 — 모든 의존성 화살표에 인과관계 1줄

다이어그램 옆에 *왜 의존하는가* 명시. 추측 0:

```
[잘못된 예]
모듈A → 모듈B
모듈B → 모듈C
(왜? 모름)

[올바른 예]
모듈A → 모듈B (모듈B 의 결과를 입력으로 사용 — 비즈니스 흐름상 필수)
모듈B → 모듈C (모듈C 의 lifecycle event 구독 — UI 갱신 트리거)
```

#### 원칙 2 — 독립성 자가 검증 표

각 모듈마다:

| 모듈 | 단독 lifecycle 가능? | 의존 대상 부재 시 동작 | DIP 필요 여부 |
|---|---|---|---|
| 녹음 | ✓ (어디에도 안 의존) | N/A | X |
| 요약 | △ (재생 시 녹음 필요) | "녹음 없음" 표시, 텍스트만 보여줌 | X |
| 기록 | X (요약·녹음 둘 다 알아야 UI 분기) | 요약 없음 → 텍스트 영역 숨김 / 녹음 없음 → 재생 버튼 숨김 | X |

#### 원칙 3 — 역방향 cascade 필요 시 DIP 의무

의존 방향 깨질 상황 (lifecycle 동기화, cascade delete 등) 만나면 *직접 호출 금지*. lifecycle event interface 박고 의존자가 listener 등록. 의존 방향 보존.

```
[잘못된 예 — 의존 방향 역전]
녹음 모듈이 요약 모듈을 import 해서 직접 호출:
  recording.delete() {
    summary.deletePending(this.id);  ← 녹음이 요약 의존하게 됨
  }

[올바른 예 — DIP 로 의존 방향 보존]
녹음 모듈은 lifecycle event 발행 interface 만 알음:
  interface RecordingLifecycleListener {
    onRecordingDeleted(id: RecordingId): void;
  }
  recording.delete() {
    this.listeners.forEach(l => l.onRecordingDeleted(this.id));
  }
요약 모듈이 listener 로 등록:
  summary.register(recording);  ← 요약이 녹음 의존 (원래 방향 유지)
  summary.onRecordingDeleted(id) { this.deletePending(id); }
```

DIP 사용 조건 (남용 금지):
- ✓ lifecycle 동기화 (cascade delete, 상태 전파)
- ✓ 외부 의존 추상화 (DB / SDK 모킹 위해)
- ✓ 플러그인 / strategy 교체
- ✗ 단순 함수 호출에 굳이 interface 박지 X — *필요한 곳에만*

### 모듈 분할 = 테스트 단위 = 의존성 1 묶음

> **모듈 분할의 *3 정합 기준*** (system-design 산출 시 의무):
>
> 1. **Bounded context 정합** — 같은 도메인 컨텍스트 = 같은 모듈 후보
> 2. **테스트 단위 정합** — test-engineer 가 명확한 PASS/FAIL 짤 수 있는 범위
> 3. **의존성 1 묶음 정합** — 모듈 내부는 강결합 OK / 모듈 간 의존은 명시적 interface

세 기준 동시 충족하는 분할이 좋은 분할. 충돌 시 *test-engineer 가 명확히 테스트 가능한지* 우선 (사용자 룰).

## 산출물 정보 의무 (형식 자유, 단 ## Domain Model 섹션 분리 권장)

**기술 스택 선정 (ADR)**:
- 영역별 (프레임워크 / DB / 상태관리 / 인증 등) 선택 + 이유 + 버린 대안 + 이유
- ADR 상태: `Proposed` → `Accepted` → `Deprecated` / `Superseded by ADR-NN`
- 기존 ADR 이 새 설계와 충돌하면 `Superseded by ADR-NN` 표시 + 새 ADR

**도메인 모델** (Phase A 산출 — `docs/domain-model.md` 신규/갱신):
- Entity / Value Object / Aggregate / Domain Service 정의
- 각 invariant 명시
- Bounded context 경계
- (선택) Mermaid class diagram

**시스템 구조**:
- 주요 모듈 목록 + 각 역할 (한 줄)
- 모듈 간 의존 관계 (텍스트 다이어그램 + 인과관계 1줄씩)
- 데이터 흐름 (입력 → 처리 → 출력)
- 독립성 자가 검증 표 (위 §원칙 2)

**구현 순서**: 의존성 기반 모듈 구현 순서 + 이유 (전제조건 관계).

**기술 리스크**: 리스크 항목 + 완화 방법.

**NFR 목표** (해당 없는 항목은 "N/A — 이유" 명시):
- 성능: 목표 응답 시간 또는 처리량 (예: p95 < 200ms)
- 가용성: 허용 다운타임 / 장애 시 fallback 전략
- 보안: 인증/인가 방식, 민감 데이터 처리, 시크릿 관리 위치
- 관찰가능성: 로깅 전략, 에러 추적 방식
- 비용: 예산 제약 있으면 상한 명시

## 문서 크기 룰 (DCN-CHG-20260430-16)

> **시스템 설계 문서 1개 = 300줄 이하**. 초과 시 상세도면을 별도 .md 로 분리 + 링크.

```
docs/architecture.md (300줄 이하 — overview)
  ├─ 시스템 구조 (텍스트 다이어그램 + 인과관계)
  ├─ 모듈 목록 (한 줄씩)
  ├─ 데이터 흐름
  ├─ 독립성 자가 검증 표
  └─ 링크: 상세
       ├─ docs/architecture/data-flow-detail.md (상세 sequence)
       ├─ docs/architecture/module-X-internals.md
       └─ docs/architecture/dip-interfaces.md (역방향 cascade interface 모음)

docs/domain-model.md (300줄 이하)
  └─ 초과 시 docs/domain/<aggregate>.md 로 분리
```

이유: 한 파일 300줄 넘으면 컨텍스트 길이 부담 + 변경 시 충돌 위험 + 읽는 사람 집중력 저하.

## 현행화 룰 (DCN-CHG-20260430-16, 의무)

> **설계 문서는 항상 코드/PRD 와 정합 유지**. 코드/PRD 변경 시 즉시 반영 — 누락 = bug.

architect 가 SYSTEM_DESIGN / SPEC_GAP 호출될 때마다 다음 검사:
1. `docs/architecture.md` (또는 분리된 detail) 와 실제 src/ 모듈 목록 정합?
2. `docs/domain-model.md` 와 실제 src/ 도메인 코드 정합?
3. PRD (`prd.md`) 의 요구사항이 시스템 설계에 반영됐는가?

불일치 발견 시:
- architect 가 *직접 sync* (SYSTEM_DESIGN 모드)
- 또는 SPEC_GAP cycle 에서 sync (`spec-gap.md` §설계 문서 동기화 절)

엔지니어 (engineer / test-engineer) 가 코드 변경 후 도메인 모델 / 시스템 구조 변경이 필요하면 *직접 수정 금지* → SPEC_GAP_FOUND escalate.

## Spike Gate — 핵심 가치 의존성 실측 의무 (DCN-CHG-20260430-18)

> **추상 인터페이스 (ABC / Protocol) + Mock 구현만으로 SYSTEM_DESIGN_READY 통과 금지**.
>
> PRD Must 기능의 핵심 가치 (functional core) 직결되는 외부 의존 (모델·SDK·API) 은 시스템 설계 *전* 또는 *중* 에 *실제 1개 spike* 로 검증.

### 적용 대상

다음 모두 해당 시 spike 의무:

1. PRD Must 기능 (Should/Could 제외) 에 직결
2. 외부 의존 (in-house 코드 X — 외부 모델·SDK·API·서비스)
3. *미검증* 영역 (사내 사용 이력 0)

### Spike 절차 (architect 가 직접 또는 사용자에게 권고)

```
1. 후보 SDK / 모델 1개 선정 (PRD 후보 list 우선)
2. 공식 문서 fetch + 실제 README / API 검증 (WebFetch)
3. 5~10 라인 minimal example 작성 + 실행 (사용자 환경 / Replicate / Modal 등)
4. 핵심 입출력 검증 — PRD 시나리오 (예: "30초 허밍 → 음색 보존 자장가") 그대로 통과?
5. 결과를 docs/sdk.md / docs/reference.md 에 기록 — 추측 / placeholder 금지
```

architect 가 직접 spike 실행 권한 / 도구 없으면 *사용자에게 명시 요청*. "Replicate API 키 / 5분 실행 시간" 등 구체 요청.

### 통과 금지 패턴 — Mock + ABC 만

다음 패턴 발견 시 SYSTEM_DESIGN_READY *불가* (architect 자기 차단):

- `class XxxClient(ABC)` 만 정의 + `class MockXxxClient(XxxClient)` 만 구현 + `class ReplicateXxxClient(XxxClient): NotImplementedError`
- `docs/sdk.md` / `docs/reference.md` 에 `[미기록]` / `[미결]` / `M0 이후 결정` placeholder 가 *PRD Must 기능 직결*
- "후보 N개 중 M0 에서 비교 선정" 식 결정 미루기

→ 이 상태로 SYSTEM_DESIGN_READY 출력하지 말 것. *spike 실행 후* 또는 *PRD 재정의 후* 진입.

### Spike 결과를 설계에 반영

spike PASS:
- 선정된 SDK / 모델로 추상 인터페이스 *concrete* 화 (실제 구현 클래스 1개 작성)
- `docs/sdk.md` / `docs/reference.md` 에 검증된 API call signature / 응답 형식 기록
- `docs/architecture.md` 모듈 의존성 그래프 갱신

spike FAIL (PRD 시나리오 통과 못 함):
- *조용히 다른 후보로 진행 X* — 결론 `TECH_CONSTRAINT_CONFLICT` emit
- 본문에 (실측 결과 / 어떤 가정 깨졌는지 / 옵션 권고) 명시
- product-planner 재호출 권고 (PRD 시나리오 재정의 필요)

### 근거 — jajang 사례

2026-04 jajang 사례. PRD 가 "30초 허밍 → 부모 음색 자장가" 약속하고 후보 4개 (OpenVoice V2 / F5-TTS / RVC / CosyVoice) 비교 검증을 "M0" 로 미룸. M0 한 번도 실행 안 됨. architect 가 추상 ABC + Mock 으로 SYSTEM_DESIGN_READY 통과 → engineer 가 F1~F14 전체 구현 → PR #144/#145 까지 와서야 *핵심 가치 0% 검증* 발견. 후보 4개 모두 *허밍 합성 불가* (speech TTS only) 로 판명.

= "미래의 약속은 검증이 아니다". Spike 1개 실측이 PRD 통과 *전* 게이트.

## 호출자에게 결론 보고

`SYSTEM_DESIGN_READY` 직전 prose 에 다음 명시:
- `docs/domain-model.md` 갱신 여부 (신규 / 변경 / 변경 없음)
- `docs/architecture.md` 갱신 여부 + 분리된 detail 파일 list
- 모듈 분할 = 의존성 1 묶음 + 테스트 단위 정합 self-check 결과
- **Spike Gate 결과 (DCN-CHG-20260430-18)** — PRD Must 직결 외부 의존 list + 각 spike 통과 여부 + 검증된 SDK/모델 명. spike 미실행 시 SYSTEM_DESIGN_READY 출력 X.
