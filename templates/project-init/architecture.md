# 아키텍처

> 기획 논의 후 채워넣을 placeholder. `{...}` 자리를 합의된 내용으로 교체한다.

## 디렉토리 구조

```
{예시 — 실제 사용 스택에 맞게 교체}
src/
├── app/               # 페이지 + API 라우트
├── components/        # UI 컴포넌트
├── types/             # 타입 정의
├── lib/               # 유틸리티 + 헬퍼
└── services/          # 외부 API 래퍼
```

## 패턴

{사용하는 디자인 패턴 — 예: Server Components 기본, 인터랙션 필요한 곳만 Client Component}

## 데이터 흐름

```
{데이터가 어떻게 흐르는지 — 예:
사용자 입력 → Client Component → API Route → 외부 API → 응답 → UI 업데이트
}
```

## 상태 관리

{상태 관리 방식 — 예: 서버 상태는 Server Components / 클라이언트 상태는 useState·useReducer}

## 외부 의존성

{외부 서비스·SDK·API 목록 — 예: OpenAI API / Stripe / Firebase Auth}
