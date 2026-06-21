# 02-speaker-split-panel

## 무엇을 만드나

쇼츠 편집 화면에 화자분리 패널을 추가한다.

## Agent Workability

- owner flow/module: app.py
- entrypoint role: main editor render, panel render, helper orchestration
- state owner: st.session_state["speaker_segments"] in app.py
- allowed touch: app.py
- forbidden touch: none
- validation path: run the app manually
- future change scenario: add more sidebar helpers in app.py

## Scope

### 수정 허용

- app.py

### 수정 금지

-

## 수용 기준

| REQ | 내용 | 검증 | 통과 조건 |
|---|---|---|---|
| REQ-001 | 사용자가 화자분리 패널에서 segment 를 편집한다 | manual smoke | 저장 버튼 후 session_state 에 반영 |
