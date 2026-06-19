# 산출물 지도 (Deliverables Map)

> dcNess 활성 프로젝트의 `docs/` 산출물 **위치·생성 주체·양식·계층 SSOT**.
> "어떤 산출물이 어디에 살고, 누가 어떤 양식으로 만들며, epic 이 늘면 어떻게 증식하는가" 의 단일 진본.
> 흩어진 정의(각 skill·agent 권한 경계·[`issue-lifecycle.md`](issue-lifecycle.md))는 본 문서를 가리킨다.

## 적용 범위

- 본 지도는 **`/init-dcness` 로 활성화한 외부 프로젝트**의 `docs/` 산출물에 적용된다.
- dcNess 저장소 자기 자신은 본 구조를 적용하지 않는다 (self 는 `docs/plugin/**`·`docs/internal/**` 운영 문서 체계를 별도로 쓴다 — [dcness-self 영역](#dcness-self-영역) 참조).

## 2계층 모델

산출물은 두 계층에 산다.

- **프로젝트 전역 (root `docs/`)** — epic 수와 무관하게 프로젝트당 1벌. 시스템 전체를 가로지르는 산출물.
- **epic 단위 (`docs/milestones/vNN/epics/epic-NN-<slug>/`)** — epic 1개당 폴더 1개. epic 이 늘면 폴더가 그만큼 **증식**한다.

epic 폴더 슬러그 규약은 [`issue-lifecycle.md`](issue-lifecycle.md#이슈-계층) 의 epic 단위 정의와 같다 (`docs/milestones/vNN/epics/epic-NN-<slug>/`).

## 프로젝트 전역 산출물 (root)

| 산출물 | 경로 | 생성 주체 | 양식 템플릿 |
|---|---|---|---|
| PRD | `docs/prd.md` | `/spec` (메인 Claude) | `skills/spec/templates/prd.md` |
| 기술 검토 | `docs/tech-review.md` + `docs/tech-review/evidence/**` + `docs/tech-review/report.html` | tech-reviewer | `agents/tech-reviewer/templates/tech-review.md` |
| 루트 아키텍처 | `docs/architecture.md` | system-architect | `agents/system-architect/templates/root-architecture.md` |
| 루트 ADR | `docs/adr.md` | system-architect | `agents/system-architect/templates/root-adr.md` |
| 디자인 시스템 토큰 | `docs/design.md` | ux-architect (system-level token 영역) | [`design.md` 규격](design.md) |
| DB 스키마 (있으면) | `docs/db-schema.md` | 상황별 (architect / 사용자) | 정형 양식 없음 |

- **기술 검토** 는 본문 1파일이 아니라 `docs/tech-review/` 서브트리(증거·HTML 리포트)를 동반한다. 운영 메커니즘은 [`tech-review` skill](../../skills/tech-review/SKILL.md).
- **루트 아키텍처/ADR** 은 epic 단위 산출물과 **공존**한다 (root = cross-epic 시스템 뷰, epic = 국소 detail). 아래 [공존 vs legacy](#공존-vs-legacy) 참조.

## epic 단위 산출물 (epic 늘수록 증식)

각 epic 폴더 `docs/milestones/vNN/epics/epic-NN-<slug>/` 안에 산다.

| 산출물 | 경로 (epic 폴더 기준) | 생성 주체 | 양식 템플릿 |
|---|---|---|---|
| 스토리 정의 | `stories.md` | `/spec` (메인 Claude) | [`git-spec.md` 이슈 등록 양식](git-spec.md#이슈-등록-양식) |
| UX 플로우 | `ux-flow.md` | ux-architect | `agents/ux-architect/templates/ux-flow.md` |
| epic 아키텍처 | `architecture.md` | system-architect / module-architect | `agents/system-architect/templates/epic-architecture.md` |
| epic ADR | `adr.md` | system-architect / module-architect | `agents/system-architect/templates/epic-adr.md` |
| 도메인 모델 | `domain-model.md` | system-architect / module-architect | `agents/system-architect/templates/domain-model.md` |
| impl task | `impl/NN-*.md` | module-architect | `agents/module-architect/templates/impl-task.md` |

- **impl task** 는 PR 1개 = task 1개 추적 단위다 (GitHub 이슈 없음 — [`issue-lifecycle.md`](issue-lifecycle.md#이슈-계층)).
- epic 이 1개 늘면 위 산출물 1세트가 새 epic 폴더에 추가된다. 이것이 프로젝트가 커질 때의 증식 규칙이다.

## 작업용 산출물 (epic 비종속)

epic 계층에 묶이지 않고 작업 단위로 생기는 산출물.

| 산출물 | 경로 | 생성 주체 | 양식 템플릿 |
|---|---|---|---|
| compact plan | `docs/compact-plans/<slug>.md` | module-architect (COMPACT_PLAN) | `agents/module-architect/templates/compact-plan.md` |
| bugfix plan | `docs/bugfix/**` | module-architect | `agents/module-architect/templates/bugfix-plan.md` |

- compact plan 은 `/impl` Standard 진입의 설계 산출물 사전 조건 증거다 ([`compact-design` skill](../../skills/compact-design/SKILL.md)).

## 공존 vs legacy

산출물별로 root 와 epic 단위의 관계가 다르다. 혼동 금지.

- **root + epic 공존 (둘 다 정본)** — `architecture.md`, `adr.md`. root 는 cross-epic 시스템 뷰, epic 단위는 그 epic 의 국소 detail. 둘은 같이 존재한다.
- **epic 단위가 정본, root flat 은 legacy 단일-epic 폴백** — `stories.md`, `ux-flow.md`, `domain-model.md`, `impl/NN-*.md`. 다중 epic 프로젝트의 canonical 위치는 epic 폴더 안이다. root 의 flat 형태(`docs/stories.md`·`docs/ux-flow.md`·`docs/domain-model.md`·`docs/impl/NN-*.md`)는 epic 구조 이전 단일-epic 시절의 폴백이며 신규 산출은 epic 단위로 한다.
- **root 전역 전용** — `prd.md`, `tech-review.md`(+서브트리), `design.md`, `db-schema.md`.

> ux-flow 의 canonical 위치(epic 단위)는 강제 경계에서도 동일하다 — ux-architect 의 Write 허용은 epic 단위 `docs/milestones/.../ux-flow.md` 와 root 폴백 둘 다 포함한다 ([`harness/agent_boundary.py`](../../harness/agent_boundary.py) ALLOW_MATRIX).

## 시드 양식 = 산출 양식 (단일 원본)

`/init-dcness` 가 `docs/prd.md`·`docs/architecture.md`·`docs/adr.md` 를 시드할 때, **시드 전용 복제 양식을 따로 두지 않고** 위 표의 authoring 템플릿을 그대로 복사한다. 시드한 빈 양식과 `/spec`·system-architect 가 나중에 채우는 양식이 동일하다 (양식 드리프트 차단). 배포 메커니즘은 [`commands/init-dcness.md`](../../commands/init-dcness.md) 의 project docs seed 스텝.

## dcness-self 영역

dcNess 저장소 자기 자신의 `docs/` 는 본 활성 프로젝트 구조를 쓰지 않는다.

- `docs/plugin/**` — plug-in 배포 영역 (외부 활성 프로젝트가 받는 SSOT 문서).
- `docs/internal/**` — self 운영·changelog 문서 (배포 안 됨).
- `docs/archive/**` — 폐기/역사 자료 보존.
- `docs/compact-plans/**` — self 작업 중 생기는 compact plan (외부와 경로만 공유).
