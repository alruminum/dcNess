---
depth: simple|std|deep
design: optional|required
story: <N|공통>
task_index: <i>/<total>|—
depends_on:             # [<NN-slug>, ...] 선행 task (contract/ordering 의존 흡수). 선행 없으면 [] 로 명시. 비운 채로 두면(미작성) 미상 → 병렬에서 직렬 강등
contract:
  produces:             # 이 task 가 만드는 public contract
  consumes:             # 소비하는 contract → 그 producer task 를 depends_on 에 반영
---

# <NN-task-slug>

## 사전 준비

- 읽을 문서:
- 읽을 코드:
- 선행 task:

## 무엇을 만드나

-

## 왜 만드나

-

## Scope

### 수정 허용

> repo-relative 파일 경로 단위로 적는다 (자유 서술 금지). 이 목록의 교집합으로 병렬 wave 충돌이 판정된다 — [`parallel-policy.md`](../../../docs/plugin/parallel-policy.md) 의 독립성 판정 참조.

-

### 수정 금지

-

## Contract

| contract | owner | producer | consumer | invariant | ordering | error mode | config | forbidden alternative |
|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |

## 인터페이스

-

## 수용 기준

| REQ | 내용 | 검증 | 통과 조건 |
|---|---|---|---|
| REQ-001 |  | (TEST) |  |

## Module Design Check

- Deep module:
- DI/의존 주입:
- 공개 표면:
- 의존 차단:

## 주의사항

-
