# agent-web

**로컬 PC 전용 맞춤형 AI 비서 — React 프론트엔드**

Claude AI와 실시간으로 대화하고, 파일 작업·웹 검색·이메일 발송을 GUI에서 제어할 수 있는 단일 페이지 애플리케이션입니다.

> **백엔드 필수** — 이 앱은 `agent-server` (FastAPI)가 `localhost:8000`에서 실행 중이어야 동작합니다.

---

## 기술 스택

| 영역 | 기술 |
|---|---|
| 번들러 | Vite 8 |
| UI 프레임워크 | React 19 |
| CSS | Tailwind CSS v4 (`@tailwindcss/vite`) |
| 상태 관리 | Zustand 5 |
| 마크다운 렌더링 | react-markdown + remark-gfm |
| 코드 하이라이팅 | react-syntax-highlighter (Prism) |
| 아이콘 | lucide-react |
| 유틸 | clsx, date-fns |
| 폰트 | Pretendard (한글), Inter (영문), JetBrains Mono (코드) |

---

## 화면 구성

```
┌─ LNB (256px) ──────┬─────── Main ───────────────────────────┐
│  AI 비서 로고       │  Header (제목 / 토큰 게이지 / 설정)      │
│  [새 대화]          ├────────────────────────────────────────│
│                    │                                        │
│  대화 기록           │   채팅 뷰 / 파일 탐색기 / 설정 패널     │
│  ├ 세션 1           │                                        │
│  ├ 세션 2           │                                        │
│  └ …              │                                        │
│                    ├────────────────────────────────────────│
│  [채팅]             │  메시지 입력창 (빠른 명령 / 전송 / 중지)  │
│  [파일 탐색기]       │                                        │
│  [설정]             │                                        │
└─────────────────────┴────────────────────────────────────────┘
```

| 화면 | 설명 |
|---|---|
| 초기 설정 | 최초 실행 시 API 키·사용자명·허용 폴더 경로 입력 |
| 채팅 | SSE 스트리밍 대화, 마크다운 렌더링, 코드 블록 복사 |
| 작업 협의 카드 | 파일 생성·수정·이메일 발송 전 승인/거부 요청 UI |
| SMTP 경고 배너 | SMTP 미설정·연결 실패 시 헤더 하단에 경고 표시 |
| 파일 탐색기 | 서버 허용 디렉토리 탐색 및 코드 미리보기 |
| 설정 패널 | Claude 모델, SMTP, 검색 공급자 등 설정 변경 |

---

## 프로젝트 구조

```
agent-web/
├── public/
├── src/
│   ├── api/                     # fetch 기반 API 클라이언트
│   │   ├── client.js            # 베이스 클라이언트 (get/post/patch/delete)
│   │   ├── chat.js
│   │   ├── sessions.js
│   │   ├── tasks.js
│   │   ├── files.js
│   │   ├── email.js
│   │   ├── search.js
│   │   └── settings.js
│   ├── store/                   # Zustand 전역 상태
│   │   ├── sessionStore.js      # 세션 목록 · 메시지
│   │   ├── chatStore.js         # 스트리밍 상태 · 토큰 사용량
│   │   ├── taskStore.js         # 작업 협의 카드 (승인/거부)
│   │   ├── settingsStore.js     # 앱 설정
│   │   └── uiStore.js           # 뷰 전환 · 사이드바 상태
│   ├── hooks/
│   │   └── useSSE.js            # SSE 스트리밍 (POST /api/chat)
│   ├── utils/
│   │   └── formatters.js        # 시간 · 파일크기 · 토큰 상태 유틸
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.jsx      # 좌측 네비게이션 (LNB)
│   │   │   └── Header.jsx       # 상단 헤더
│   │   ├── chat/
│   │   │   ├── ChatWindow.jsx   # 메시지 목록 · 빈 화면 제안
│   │   │   ├── MessageBubble.jsx # 사용자/AI 메시지 버블
│   │   │   └── MessageInput.jsx  # 입력창 · 빠른 명령
│   │   ├── tasks/
│   │   │   └── TaskCard.jsx     # 작업 협의 카드
│   │   ├── files/
│   │   │   └── FileExplorer.jsx # 파일 트리 · 코드 미리보기
│   │   ├── settings/
│   │   │   └── SettingsPanel.jsx # 설정 모달
│   │   ├── setup/
│   │   │   └── SetupScreen.jsx  # 최초 실행 설정 화면 (API 키, 사용자명, 폴더 경로)
│   │   └── common/
│   │       ├── TokenBadge.jsx   # 토큰 게이지
│   │       ├── ToolBadge.jsx    # MCP 도구 배지
│   │       ├── Modal.jsx        # 공통 모달
│   │       └── SmtpStatusBanner.jsx # SMTP 미설정·연결 실패 경고 배너
│   ├── App.jsx                  # 루트 컴포넌트 · 뷰 라우팅
│   ├── main.jsx                 # React DOM 마운트
│   └── index.css                # Tailwind v4 · 디자인 토큰 · 글로벌 스타일
├── index.html
├── vite.config.js               # Tailwind 플러그인 · @ 경로 alias · API proxy
└── package.json
```

---

## 시작하기

### 0. 사전 요구사항

- **Node.js 18** 이상 (`node --version`으로 확인)
- **npm 9** 이상 (`npm --version`으로 확인)
- **agent-server** 가 `http://localhost:8000` 에서 실행 중이어야 합니다

---

### 1. 패키지 설치

```powershell
cd C:\path\to\agent-web

npm install
```

설치되는 주요 패키지:

| 패키지 | 버전 | 용도 |
|---|---|---|
| `tailwindcss` | ^4.1.8 | CSS 유틸리티 |
| `@tailwindcss/vite` | ^4.1.8 | Vite Tailwind 플러그인 |
| `zustand` | ^5.0.5 | 전역 상태 관리 |
| `react-markdown` | ^9.0.1 | 마크다운 렌더링 |
| `react-syntax-highlighter` | ^15.6.1 | 코드 하이라이팅 |
| `lucide-react` | ^0.511.0 | 아이콘 |
| `clsx` | ^2.1.1 | 조건부 클래스 결합 |
| `date-fns` | ^4.1.0 | 날짜 포매팅 |

---

### 2. 개발 서버 실행

```powershell
npm run dev
```

정상 실행 시 출력:

```
  VITE v8.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

브라우저에서 `http://localhost:5173` 접속

> **API 프록시 설정됨** — `/api/*` 요청은 자동으로 `http://localhost:8000`으로 전달됩니다.
> `agent-server`가 먼저 실행되어 있어야 채팅 기능이 동작합니다.

---

### 3. 프로덕션 빌드

```powershell
npm run build
```

빌드 결과물은 `dist/` 폴더에 생성됩니다.

```powershell
# 빌드 결과 미리보기
npm run preview
```

---

## 개발 워크플로우

### 백엔드와 함께 실행하는 순서

```
1. agent-server 실행  →  http://localhost:8000
2. agent-web 실행     →  http://localhost:5173
```

**PowerShell 두 창에서 각각 실행:**

```powershell
# 창 1 — 백엔드
cd C:\path\to\agent-server
.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000

# 창 2 — 프론트엔드
cd C:\path\to\agent-web
npm run dev
```

---

### 디자인 토큰 (`src/index.css`)

`@theme` 블록에 선언된 CSS 변수를 Tailwind 클래스로 사용합니다:

| 토큰 접두사 | 예시 클래스 | 용도 |
|---|---|---|
| `brand-*` | `bg-brand-600`, `text-brand-500` | 브랜드 (Indigo) |
| `surface-*` | `bg-surface-50`, `border-surface-200` | 배경·경계선 |
| `ink-*` | `text-ink-900`, `text-ink-500` | 텍스트 색상 |
| `navy-*` | `bg-navy-950`, `bg-navy-800` | LNB 다크 배경 |
| `success-500` | `text-success-500` | 성공/승인 |
| `warning-400` | `text-warning-400` | 경고 |
| `danger-500` | `text-danger-500` | 위험/삭제 |

---

### @ 경로 alias

`src/` 디렉토리를 `@`로 단축해 임포트합니다:

```javascript
// 긴 경로 대신
import { useSessionStore } from '../../../store/sessionStore'

// 짧게 사용 가능
import { useSessionStore } from '@/store/sessionStore'
```

---

## 주요 기능 흐름

### SSE 채팅 스트리밍

```
사용자 입력
  → useSSE.sendMessage()
  → POST /api/chat  (Accept: text/event-stream)
  → 스트리밍 이벤트 수신:
      data: {"type": "delta", "content": "..."}   → 메시지 버블에 실시간 추가
      data: {"type": "done", ...}                  → 스트리밍 완료, 토큰 사용량 갱신
      data: {"type": "task_pending", "task": {...}} → TaskCard 팝업
      data: {"type": "error", "message": "..."}    → 오류 표시
```

### 작업 협의 카드

파일 생성·수정, 이메일 발송 등 위험한 작업은 AI가 먼저 실행하지 않고 사용자 승인을 기다립니다:

```
AI 응답 중 task_pending 이벤트
  → TaskCard 컴포넌트 렌더링
  → [승인] 클릭 → POST /api/tasks/{id}/approve → 작업 실행
  → [거부] 클릭 → POST /api/tasks/{id}/reject  → 작업 취소
  → 5분 내 미응답  → 서버에서 자동 거부
```

---

## 트러블슈팅

### `npm install` 실패 — 네트워크 오류

사내 네트워크 또는 프록시 환경에서는 레지스트리를 변경해 보세요:

```powershell
npm config set registry https://registry.npmjs.org/
npm install
```

---

### `Cannot find module '@tailwindcss/vite'`

```powershell
npm install @tailwindcss/vite tailwindcss --save-dev
```

---

### 채팅 메시지 전송 시 `Failed to fetch` 오류

백엔드 서버가 실행 중인지 확인하세요:

```powershell
# 백엔드 상태 확인
curl http://localhost:8000/health
# 또는 브라우저에서 http://localhost:8000/health 접속
```

백엔드가 8000이 아닌 다른 포트라면 `vite.config.js`의 proxy 설정을 수정하세요:

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',  // ← 포트 변경
    changeOrigin: true,
  },
},
```

---

### HMR (Hot Module Replacement)이 동작하지 않을 때

Windows의 경우 파일 감시 이슈가 발생할 수 있습니다:

```powershell
# 개발 서버를 polling 모드로 실행
$env:VITE_HMR_PROTOCOL="ws"; npm run dev
```

또는 `vite.config.js`에 추가:

```javascript
server: {
  watch: {
    usePolling: true,
  },
}
```

---

### `SyntaxError: Cannot use import statement` 오류

`package.json`에 `"type": "module"`이 선언되어 있는지 확인하세요. 없으면 추가합니다.
