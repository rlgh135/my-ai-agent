"""filesystem MCP 래퍼 — 파일 Read / Create / Update / Backup"""
import os
import shutil
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import (
    AgentFileNotFoundError,
    AgentFileExistsError,
    PathNotAllowedError,
)


def _assert_allowed(path: str) -> Path:
    p = Path(path).resolve()
    allowed = [Path(d).resolve() for d in settings.ALLOWED_DIRECTORIES]
    if not allowed:
        return p  # 설정 없으면 전체 허용 (개발 중)
    if not any(str(p).startswith(str(a)) for a in allowed):
        raise PathNotAllowedError(path)
    return p


# ── Read ──────────────────────────────────────────────────────────────────────
def list_directory(path: str) -> dict:
    p = _assert_allowed(path)
    if not p.exists():
        raise AgentFileNotFoundError(path)
    items = []
    for item in sorted(p.iterdir()):
        stat = item.stat()
        items.append({
            "name": item.name,
            "type": "directory" if item.is_dir() else "file",
            "size": stat.st_size if item.is_file() else 0,
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return {"path": str(p), "items": items}


def read_file(path: str) -> dict:
    p = _assert_allowed(path)
    if not p.exists():
        raise AgentFileNotFoundError(path)
    content = p.read_text(encoding="utf-8", errors="replace")
    return {"path": str(p), "content": content, "size": p.stat().st_size, "encoding": "utf-8"}


# ── Backup ────────────────────────────────────────────────────────────────────
def backup_file(src_path: str, dest_path: str = "") -> dict:
    src = _assert_allowed(src_path)
    if not src.exists():
        raise AgentFileNotFoundError(src_path)

    if dest_path:
        dst = _assert_allowed(dest_path)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = src.parent / f"{src.stem}.backup_{ts}{src.suffix}"

    shutil.copy2(src, dst)
    return {"src_path": str(src), "backup_path": str(dst)}


# ── Create ────────────────────────────────────────────────────────────────────
def create_file(path: str, content: str, overwrite: bool = False) -> dict:
    p = _assert_allowed(path)
    if p.exists() and not overwrite:
        raise AgentFileExistsError(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return {"path": str(p), "size": p.stat().st_size}


# ── Update ────────────────────────────────────────────────────────────────────
def update_file(path: str, content: str) -> dict:
    p = _assert_allowed(path)
    if not p.exists():
        raise AgentFileNotFoundError(path)
    p.write_text(content, encoding="utf-8")
    return {"path": str(p), "size": p.stat().st_size}
