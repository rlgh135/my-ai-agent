# agent-server

**로컬 PC 전용 맞춤형 AI 비서 — FastAPI 백엔드**

Claude API + MCP 기반의 AI 에이전트 서버입니다. 파일 작업, 웹 검색, 이메일 발송 등의 로컬 자동화 기능을 REST API + SSE 스트리밍으로 제공합니다.

---

## 기술 스택

| 영역 | 기술 |
|---|---|
| 웹 프레임워크 | FastAPI 0.111 + Uvicorn |
| AI | Anthropic Claude API (claude-sonnet-4-6) |
| 프로토콜 | MCP (Model Context Protocol) |
| 데이터베이스 | PostgreSQL + SQLAlchemy 2.0 async (asyncpg) |
| 마이그레이션 | Alembic |
| 암호화 | cryptography (Fernet) |
| 스트리밍 | SSE (FastAPI StreamingResponse) |
| 검색 | Brave Search · Naver Search · DuckDuckGo |
| 설정 관리 | pydantic-settings + python-dotenv |
| 이메일 | aiosmtplib |
| 토큰 카운팅 | tiktoken |
| Python | 3.11 이상 |

---

## 프로젝트 구조

```
agent-server/
├── app/
│   ├── main.py                  # FastAPI 앱 엔트리포인트
│   ├── core/
│   │   ├── config.py            # 환경변수 설정 (pydantic-settings)
│   │   └── exceptions.py        # 커스텀 예외 클래스
│   ├── db/
│   │   ├── database.py          # SQLAlchemy 비동기 엔진 / 세션
│   │   └── schema.sql           # PostgreSQL DDL (테이블 정의)
│   ├── models/                  # ORM 모델
│   │   ├── session.py           # chat_sessions 테이블
│   │   ├── message.py           # messages 테이블
│   │   └── settings.py          # app_settings 테이블
│   ├── schemas/                 # Pydantic 스키마 (요청/응답)
│   │   ├── chat.py
│   │   ├── files.py
│   │   ├── email.py
│   │   └── search.py
│   ├── services/
│   │   ├── vault.py             # Fernet 암호화/복호화
│   │   └── token_counter.py     # tiktoken 기반 토큰 계산
│   ├── mcp/                     # MCP 도구 구현
│   │   ├── filesystem.py        # 파일 Read/Create/Update/Backup
│   │   ├── search.py            # 웹 검색 (Brave / DuckDuckGo)
│   │   └── email_sender.py      # SMTP 이메일 발송
│   └── api/v1/
│       ├── router.py            # 라우터 집계
│       └── endpoints/
│           ├── chat.py          # POST /api/chat (SSE 스트리밍)
│           ├── sessions.py      # 세션 CRUD
│           ├── tasks.py         # 작업 협의 카드 승인/거부
│           ├── files.py         # 파일 CRUD
│           ├── email.py         # 이메일 발송
│           ├── search.py        # 웹 검색
│           └── settings_api.py  # 앱 설정 조회/수정
├── tests/
│   ├── unit/
│   │   └── test_token_counter.py
│   └── integration/
│       └── test_health.py
├── scripts/
│   ├── setup.sh                 # 개발환경 최초 세팅
│   └── start.sh                 # 서버 실행
├── .env.example                 # 환경변수 템플릿
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

---

## 시작하기

### 0. 사전 요구사항

- **Python 3.11** 이상
- **PostgreSQL 14** 이상 (로컬 또는 Docker)
- **Anthropic API Key** — [console.anthropic.com](https://console.anthropic.com) 에서 발급

---

### 1. PostgreSQL 데이터베이스 생성

**psql 접속 후 실행:**

```sql
-- 데이터베이스 생성
CREATE DATABASE agent_db ENCODING 'UTF8' LC_COLLATE 'en_US.UTF-8' TEMPLATE template0;

-- 전용 사용자 생성 (password는 원하는 값으로 변경)
CREATE USER agent_user WITH PASSWORD 'your_password';

-- 권한 부여
GRANT ALL PRIVILEGES ON DATABASE agent_db TO agent_user;

-- agent_db로 접속
\c agent_db

GRANT ALL ON SCHEMA public TO agent_user;
```

**DDL 실행 (스키마 초기화):**

```bash
psql -U agent_user -d agent_db -f app/db/schema.sql
```

> 개발 환경에서는 서버 최초 실행 시 `init_db()`가 자동으로 테이블을 생성합니다.
> 프로덕션에서는 반드시 `schema.sql` 또는 Alembic 마이그레이션을 사용하세요.

---

### 2. 가상환경 생성 및 패키지 설치

**Windows (PowerShell):**

```powershell
cd C:\path\to\agent-server

# 가상환경 생성
python -m venv .venv

# 활성화
.venv\Scripts\Activate.ps1

# 패키지 설치
pip install --upgrade pip
pip install -r requirements-dev.txt
```

**macOS / Linux:**

```bash
cd /path/to/agent-server

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
```

---

### 3. 환경변수 설정

```bash
# .env.example을 복사
cp .env.example .env
```

`.env` 파일을 열어 아래 항목을 반드시 입력합니다:

```dotenv
# ── Claude API (필수) ──────────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-api03-...

# ── Database (필수) ────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://agent_user:your_password@localhost:5432/agent_db

# ── 허용 파일 경로 ──────────────────────────────────────────
# Windows 예시
ALLOWED_DIRECTORIES=["C:/Users/me/Projects","C:/Users/me/Documents"]
# macOS 예시
# ALLOWED_DIRECTORIES=["/Users/me/projects","/Users/me/documents"]

# ── 웹 검색 (선택) ─────────────────────────────────────────
SEARCH_PROVIDER=brave          # brave | naver | duckduckgo
BRAVE_API_KEY=BSA-...          # Brave Search API Key (brave 사용 시)
NAVER_CLIENT_ID=...            # Naver Client ID (naver 사용 시)
NAVER_API_KEY=...              # Naver Client Secret (naver 사용 시)
```

**선택 항목 — SMTP 이메일 설정 (이메일 기능 사용 시):**

```dotenv
# Gmail 예시 (앱 비밀번호 사용 필요)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=abcd-efgh-ijkl-mnop   # Gmail 앱 비밀번호
SMTP_FROM=AI 비서 <your.email@gmail.com>
```

> SMTP 비밀번호 등 민감 정보는 서버 최초 실행 시 Fernet으로 암호화되어 DB에 저장됩니다.
> `.env`의 `VAULT_KEY`는 비워두면 자동 생성됩니다.

---

### 4. 서버 실행

**개발 모드 (자동 리로드):**

```powershell
# Windows
.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload

# macOS / Linux
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

또는 제공된 스크립트 사용 (macOS/Linux):

```bash
bash scripts/start.sh
```

**서버 실행 확인:**

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

### 5. API 문서 확인

| 주소 | 설명 |
|---|---|
| `http://localhost:8000/docs` | Swagger UI (인터랙티브 API 탐색) |
| `http://localhost:8000/redoc` | ReDoc (읽기 전용 문서) |
| `http://localhost:8000/health` | 서버 상태 확인 |

---

## API 엔드포인트 요약

| 그룹 | 메서드 | 경로 | 설명 |
|---|---|---|---|
| **Chat** | POST | `/api/chat` | 메시지 전송 (SSE 스트리밍) |
| | GET | `/api/chat/token-usage` | 토큰 사용량 조회 |
| **Sessions** | GET | `/api/sessions` | 세션 목록 |
| | POST | `/api/sessions` | 세션 생성 |
| | GET | `/api/sessions/{id}` | 세션 메시지 조회 |
| | DELETE | `/api/sessions/{id}` | 세션 삭제 |
| **Tasks** | POST | `/api/tasks/{id}/approve` | 작업 승인 |
| | POST | `/api/tasks/{id}/reject` | 작업 거부 |
| **Files** | GET | `/api/files` | 디렉토리 목록 |
| | GET | `/api/files/content` | 파일 내용 조회 |
| | POST | `/api/files` | 파일 생성 (승인 필요) |
| | PUT | `/api/files` | 파일 수정 (승인 필요) |
| | POST | `/api/files/backup` | 파일 백업 |
| | DELETE | `/api/files` | 파일 삭제 |
| **Email** | POST | `/api/email/send` | 이메일 발송 (승인 필요) |
| | GET | `/api/email/smtp-status` | SMTP 연결 상태 |
| **Search** | POST | `/api/search` | 웹 검색 |
| **Settings** | GET | `/api/settings` | 설정 조회 |
| | PATCH | `/api/settings` | 설정 수정 |
| | POST | `/api/settings/validate-key` | API 키 검증 |

---

## 테스트 실행

```powershell
# 전체 테스트
.venv\Scripts\pytest.exe

# 커버리지 포함
.venv\Scripts\pytest.exe --cov=app --cov-report=term-missing

# 특정 테스트만
.venv\Scripts\pytest.exe tests/unit/
.venv\Scripts\pytest.exe tests/integration/
```

---

## 코드 품질 검사

```powershell
# Ruff (lint + format check)
.venv\Scripts\ruff.exe check app/
.venv\Scripts\ruff.exe format app/ --check

# 자동 수정
.venv\Scripts\ruff.exe check app/ --fix
.venv\Scripts\ruff.exe format app/

# 타입 검사
.venv\Scripts\mypy.exe app/
```

---

## 환경변수 전체 목록

| 변수명 | 기본값 | 설명 |
|---|---|---|
| `APP_NAME` | `AI Agent Server` | 앱 이름 |
| `DEBUG` | `false` | 디버그 모드 (SQL 로그 출력) |
| `HOST` | `127.0.0.1` | 서버 바인딩 호스트 |
| `PORT` | `8000` | 서버 포트 |
| `ANTHROPIC_API_KEY` | _(필수)_ | Claude API 키 |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | 사용할 Claude 모델 |
| `CLAUDE_MAX_TOKENS` | `8192` | 응답 최대 토큰 수 |
| `DATABASE_URL` | _(필수)_ | PostgreSQL 연결 URL |
| `VAULT_KEY` | _(자동 생성)_ | Fernet 암호화 키 |
| `ALLOWED_DIRECTORIES` | `[]` | AI 파일 접근 허용 경로 목록 |
| `SMTP_HOST` | _(선택)_ | SMTP 서버 호스트 (예: `smtp.gmail.com`) |
| `SMTP_PORT` | `587` | SMTP 포트 |
| `SMTP_USER` | _(선택)_ | SMTP 계정 이메일 |
| `SMTP_PASSWORD` | _(선택)_ | SMTP 앱 비밀번호 |
| `SMTP_FROM` | _(선택)_ | 발신자 표시명 (미입력 시 `SMTP_USER` 사용) |
| `SEARCH_PROVIDER` | `duckduckgo` | 검색 공급자 (`brave` \| `naver` \| `duckduckgo`) |
| `BRAVE_API_KEY` | _(선택)_ | Brave Search API 키 |
| `NAVER_CLIENT_ID` | _(선택)_ | 네이버 검색 API Client ID |
| `NAVER_API_KEY` | _(선택)_ | 네이버 검색 API Client Secret |
| `USER_NAME` | _(선택)_ | 사용자 이름 (UI에서 설정 가능) |
| `TASK_TIMEOUT_SECONDS` | `300` | 작업 협의 카드 자동 거부 시간 (초) |

---

## 트러블슈팅

### `asyncpg.exceptions.InvalidCatalogNameError` — DB가 없을 때

```
asyncpg.exceptions.InvalidCatalogNameError: database "agent_db" does not exist
```

→ PostgreSQL에 `agent_db` 데이터베이스를 생성했는지 확인하세요. ([1. PostgreSQL 데이터베이스 생성](#1-postgresql-데이터베이스-생성) 참고)

---

### `asyncpg.exceptions.InvalidPasswordError` — 비밀번호 오류

```
asyncpg.exceptions.InvalidPasswordError: password authentication failed
```

→ `.env`의 `DATABASE_URL`에 입력한 비밀번호와 PostgreSQL 사용자 비밀번호가 일치하는지 확인하세요.

---

### `ModuleNotFoundError: No module named 'asyncpg'`

→ 가상환경이 활성화된 상태에서 패키지가 설치되어 있는지 확인:

```powershell
.venv\Scripts\pip.exe list | findstr asyncpg
```

설치가 안 되어 있다면:

```powershell
.venv\Scripts\pip.exe install -r requirements.txt
```

---

### Windows에서 `.venv\Scripts\Activate.ps1` 실행 오류

PowerShell 실행 정책 문제입니다:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

이후 다시 `.venv\Scripts\Activate.ps1`을 실행하세요.

---

### `VAULT_KEY` 관련 오류

최초 실행 시 `VAULT_KEY`가 자동 생성되어 `.env`에 추가됩니다.
수동으로 키를 생성하려면:

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

출력된 값을 `.env`의 `VAULT_KEY=`에 입력합니다.
