# design.md 규격

> dcness 디자인 시스템 SSOT.
> Google `design.md` 공식 spec 채택 + dcness 적용 룰 추가.
> 원본: https://github.com/google-labs-code/design.md `docs/spec.md`

---

## 1. 파일 구조

`design.md` 파일은 두 부분으로 구성된다:

- **YAML 프론트매터**: 머신이 읽는 디자인 토큰
- **마크다운 본문**: 사람이 읽는 설명과 가이드

---

## 2. 프론트매터 스키마 (Google spec `## Schema`)

```yaml
version: <string>          # 선택. 알파 채널용.
name: <string>             # 필수.
description: <string>      # 선택.
colors:
  <token-name>: <Color>
typography:
  <token-name>: <Typography>
rounded:
  <scale-level>: <Dimension>
spacing:
  <scale-level>: <Dimension | number>
components:
  <component-name>:
    <token-name>: <string | token-reference>
```

**타입 정의**

| 타입 | 형식 |
|---|---|
| `Color` | `#` 로 시작하는 16진수 색상 코드 |
| `Typography` | `fontFamily` / `fontSize` / `fontWeight` / `lineHeight` / `letterSpacing` / `fontFeature` / `fontVariation` |
| `Dimension` | `px` / `em` / `rem` 단위 포함 문자열 |
| `token-reference` | `{path.to.token}` 형식 (아래 §3 참조) |

---

## 3. 토큰 참조 문법 (Google spec `# Design Tokens`)

```
{path.to.token}
```

- 프론트매터 안에서 다른 토큰을 가리킬 때 사용.
- `components` 섹션에서는 복합 토큰도 참조 가능. 예: `{typography.label-md}`
- 참조 대상이 프론트매터에 실재해야 함 — 유효하지 않은 참조는 validator 가 오류로 처리 (§5.2).

---

## 4. 본문 섹션 순서 (Google spec `# Sections` → `### Section Order`)

| 순서 | 영문 헤더 | 한글 표기 |
|---|---|---|
| 1 | Overview | 개요 (브랜드 & 스타일) |
| 2 | Colors | 색상 |
| 3 | Typography | 타이포그래피 |
| 4 | Layout | 레이아웃 (레이아웃 & 간격) |
| 5 | Elevation & Depth | 고도 & 깊이 |
| 6 | Shapes | 도형 |
| 7 | Components | 컴포넌트 |
| 8 | Do's and Don'ts | 권장 사항 및 금지 사항 |

헤더는 영문을 기준으로 하며 한글 병기는 선택.

---

## 5. dcness 적용 룰

### 5.1 조건부 read

UI 없는 프로젝트 (dcness self 포함) 에서 `design.md` 미존재 시 silent skip.
agent 는 파일 부재를 오류로 처리하지 않는다.

### 5.2 토큰 참조 무결성 검증

`{colors.X}` 등 참조가 프론트매터에 실재해야 함.
**검증 담당**: `agents/validator/code-validation.md` (해당 파일에서 신규 체크 항목으로 추가 — Story #126).
`plan-validation` / `design-validation` 은 본 검증 비대상.

### 5.3 외부 import 1회 변환

VoltAgent ecosystem (getdesign.md) 등 외부 `design.md` 가져올 때 LLM 1회 변환으로 dcness 룰 정합.
호환 변환 레이어 별도 신설 없음.

### 5.4 작성 스타일

본 spec 본문은 `CLAUDE.md §0.4` 정합 — "주의사항" / "추후 결정" 등 명확한 한글 사용.
외부 spec 에서 인용하는 라인 (Atmosphere / Tonal Layers 등) 은 영어 그대로 유지 (의미 정확성 우선).

### 5.5 권장 토큰 이름 (Google spec `# Recommended Token Names (Non-Normative)`)

표준 권장 이름을 따르면 외부 ecosystem import / export 호환성이 높아진다. 다른 이름도 spec 상 허용.

**colors**: `primary` / `secondary` / `tertiary` / `neutral` / `surface` / `on-surface` / `error`

**typography**: `headline-display` / `body-lg` / `body-md` / `label-sm`

**rounded**: `none` / `sm` / `md` / `lg` / `xl` / `full`

---

## 6. 알 수 없는 내용 처리 (Google spec `# Consumer Behavior for Unknown Content`)

| 시나리오 | 처리 방식 |
|---|---|
| 알 수 없는 섹션 헤딩 | 보존 (무시하지 않음) |
| 알 수 없는 토큰 이름 | 값이 유효하면 허용 |
| 알 수 없는 컴포넌트 속성 | 경고와 함께 허용 |
| 중복 섹션 헤딩 | 오류 — 거부 |

---

## 7. 사용 예시

아래는 새 프로젝트에서 처음 만들 때 복사할 수 있는 최소 구성이다.

```markdown
---
name: MyApp
colors:
  primary: "#6750A4"
  on-surface: "#1C1B1F"
  surface: "#FFFBFE"
typography:
  body-md:
    fontFamily: "Roboto"
    fontSize: "14px"
    fontWeight: "400"
    lineHeight: "20px"
---

## Overview

MyApp 의 기본 색상은 보라색 계열이며 Material You 기반이다.

## Colors

- `primary`: 주요 액션, 버튼 배경
- `on-surface`: 본문 텍스트
- `surface`: 배경 기본값
```

> `init-dcness` 실행 시 본 예시를 프로젝트에 inline 으로 embed 한다 (Story #128).
# test
