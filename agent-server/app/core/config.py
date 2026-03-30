from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "AI Agent Server"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ── Server ───────────────────────────────────────────────────────────────
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # ── Claude API ───────────────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    CLAUDE_MAX_TOKENS: int = 8192

    # ── Database (PostgreSQL + asyncpg) ──────────────────────────────────────
    # 형식: postgresql+asyncpg://<user>:<password>@<host>:<port>/<dbname>
    DATABASE_URL: str = "postgresql+asyncpg://agent_user:password@localhost:5432/agent_db"

    # ── Vault (암호화 키 — 최초 실행 시 자동 생성) ───────────────────────────
    VAULT_KEY: str = ""  # Fernet 키 (base64). 비어있으면 자동 생성 후 .env 저장

    # ── File System ──────────────────────────────────────────────────────────
    ALLOWED_DIRECTORIES: list[str] = []   # 허용 파일 경로 목록 (절대 경로)

    # ── SMTP (이메일) ─────────────────────────────────────────────────────────
    # 비어 있으면 이메일 기능 비활성화 — 다른 기능에 영향 없음
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""                   # 발신자 표시명. 비어있으면 SMTP_USER 사용

    # ── Search ───────────────────────────────────────────────────────────────
    SEARCH_PROVIDER: str = "brave"        # brave | duckduckgo
    BRAVE_API_KEY: str = ""

    # ── Task (협의 카드) ──────────────────────────────────────────────────────
    TASK_TIMEOUT_SECONDS: int = 300       # pending_task 자동 거절 타임아웃 (5분)

    @property
    def smtp_configured(self) -> bool:
        """SMTP 필수 항목(host, user, password)이 모두 설정되어 있는지 확인."""
        return bool(self.SMTP_HOST and self.SMTP_USER and self.SMTP_PASSWORD)


settings = Settings()
