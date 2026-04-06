"""중앙 로거 설정 — 카테고리별 파일 로거를 반환한다.

로그 폴더 구조:
  agent-server/logs/
  ├── chat/   chat.log    — Agentic loop 흐름 (Claude 호출, stop_reason, done 전송 등)
  ├── tools/  tools.log   — MCP 도구 실행 (safe / risky, 입력·결과·오류)
  ├── tasks/  tasks.log   — Task 승인 흐름 (register / approve / reject / timeout)
  └── errors/ errors.log  — 모든 ERROR 이상 이벤트 (카테고리 무관)

파일은 매일 자정 로테이션되며 최대 14일치 보관.
"""
import logging
import logging.handlers
from pathlib import Path

_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"

_FMT = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def _file_handler(subdir: str, filename: str) -> logging.handlers.TimedRotatingFileHandler:
    path = _LOG_DIR / subdir
    path.mkdir(parents=True, exist_ok=True)
    h = logging.handlers.TimedRotatingFileHandler(
        path / filename,
        when="midnight",
        backupCount=14,
        encoding="utf-8",
    )
    h.setFormatter(_FMT)
    return h


def _make_logger(name: str, subdir: str, filename: str, level: int = logging.DEBUG) -> logging.Logger:
    lg = logging.getLogger(name)
    if not lg.handlers:
        lg.addHandler(_file_handler(subdir, filename))
        lg.setLevel(level)
        lg.propagate = False
    return lg


# ── 공개 API ────────────────────────────────────────────────────────────────

def get_chat_logger() -> logging.Logger:
    """Agentic loop 흐름 로거 — Claude 호출·stop_reason·도구 목록·done 이벤트."""
    return _make_logger("agent.chat", "chat", "chat.log")


def get_tool_logger() -> logging.Logger:
    """MCP 도구 실행 로거 — 입력 파라미터·결과 요약·오류."""
    return _make_logger("agent.tools", "tools", "tools.log")


def get_task_logger() -> logging.Logger:
    """Task 승인 흐름 로거 — register·approve·reject·timeout."""
    return _make_logger("agent.tasks", "tasks", "tasks.log")


def get_error_logger() -> logging.Logger:
    """전역 오류 로거 — ERROR 이상 이벤트."""
    return _make_logger("agent.errors", "errors", "errors.log", level=logging.ERROR)
