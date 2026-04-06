# my-ai-agent

**MCP 기반 로컬 AI 어시스턴트**

Claude AI를 활용해 파일 작업, 웹 검색, 이메일 발송 등 로컬 PC 자동화를 수행하는 개인용 AI 비서입니다. 최종적으로 `.exe` / `.dmg` 패키지 배포를 목표로 합니다.

---

## 프로젝트 구조

```
my-ai-agent/
├── agent-server/    # Python FastAPI 백엔드
└── agent-web/       # React + Vite 프론트엔드
```

| 서브프로젝트 | 기술 | 포트 |
|---|---|---|
| `agent-server` | Python 3.11 · FastAPI · PostgreSQL · Claude API | 8000 |
| `agent-web` | Node 18 · React 19 · Vite · Tailwind CSS v4 | 5173 |

---

## 주요 기능

- **AI 채팅** — Claude와의 실시간 SSE 스트리밍 대화, 세션 히스토리 보존
- **파일 작업** — 지정 디렉토리 내 파일 읽기·쓰기·수정·백업·삭제 (Word, Excel 포함)
- **웹 검색** — Brave(영문) / Naver(한국어) / DuckDuckGo(무료 폴백)
- **이메일 발송** — SMTP 기반 비동기 이메일 전송
- **작업 협의 카드** — 파일 수정·이메일 발송 등 위험 작업은 사용자 승인 후 실행
- **컨텍스트 게이지** — 세션별 남은 토큰 용량 실시간 표시

---

## 빠른 시작

### 1. 백엔드 실행

```bash
cd agent-server
cp .env.example .env          # ANTHROPIC_API_KEY, DATABASE_URL 필수 입력
python3 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. 프론트엔드 실행

```bash
cd agent-web
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속

---

## 상세 문서

- [agent-server README](agent-server/README.md) — 백엔드 설치·환경변수·API 목록
- [agent-web README](agent-web/README.md) — 프론트엔드 설치·컴포넌트 구조
