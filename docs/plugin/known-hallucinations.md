# Known Hallucinations Catalog

> 외부 도구·라이브러리 config 키 / API / 옵션 중 LLM 학습 데이터 노이즈로 *잘못 출력되기 쉬운* 항목 누적. 의심 시 공식 docs WebFetch 권고. agent prompt cross-ref 1줄로 활용.

본 카탈로그는 정보 제공 — *강제 X*. agent (특히 architect MODULE_PLAN / TASK_DECOMPOSE / LIGHT_PLAN, validator CODE_VALIDATION) 가 자율 활용.

## 1. testing — jest

| ❌ hallucinated | ✅ 정확 | 출처 |
|---|---|---|
| `setupFilesAfterFramework` | `setupFilesAfterEnv` | jajang epic-08 (run-91180b34/architect-TASK_DECOMPOSE.md) |

배경: jest 의 setup 키는 `setupFiles` (env 전) + `setupFilesAfterEnv` (env 후, framework 도입 후 실행). `setupFilesAfterFramework` 는 *존재하지 않음* — 다른 testing tool 의 키와 혼동.

공식 docs: [jest configuration — setupFilesAfterEnv](https://jestjs.io/docs/configuration#setupfilesafterenv-array)

---

## 2. 누적 룰

새 hallucination 발견 시 본 파일에 추가:
1. 카테고리 (testing / lint / type / bundler / runtime 등)
2. ❌ hallucinated → ✅ 정확
3. 출처 (Task-ID 또는 incident reference)
4. 배경 1~2줄 (왜 혼동되는지)
5. 공식 docs URL

기준: agent prose 또는 production 환경에서 *2회 이상 동일 패턴 발견* 시 추가. 1회는 케이스 바이 케이스 정정.

dcness governance follow-up — `change_rationale_history` 의 alternatives / 발견 사례 자동 추출 후보 (별도 Task).

## 3. cross-ref

다음 agent prompt 가 본 카탈로그를 1줄 reference:
- `agents/architect/task-decompose.md`
- `agents/architect/module-plan.md`
- `agents/architect/light-plan.md`
- `agents/validator/code-validation.md` (config schema 검증 시)

agent 자체에 catalog 박지 않음 — 토큰 누적 방지 + SSOT 단일.
