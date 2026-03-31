"""filesystem MCP 래퍼 — 파일 Read / Create / Update / Backup / Delete
지원 포맷: 텍스트 (utf-8), Word (.docx), Excel (.xlsx)
"""
import os
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import (
    AgentFileExistsError,
    AgentFileNotFoundError,
    PathNotAllowedError,
)

# Office 포맷 지원 (ImportError 시 graceful degradation)
try:
    import docx as _docx          # python-docx
    _DOCX_OK = True
except ImportError:
    _DOCX_OK = False

try:
    import openpyxl as _openpyxl  # openpyxl
    _XLSX_OK = True
except ImportError:
    _XLSX_OK = False


# ── 경로 검증 ──────────────────────────────────────────────────────────────────

def _nfc(p: Path) -> str:
    """macOS APFS는 경로를 NFD로 반환하고 Python str은 NFC — 양쪽을 NFC로 통일."""
    return unicodedata.normalize("NFC", str(p))


def _assert_allowed(path: str) -> Path:
    p = Path(path.strip()).resolve()
    allowed = [Path(d.strip()).resolve() for d in settings.ALLOWED_DIRECTORIES if d.strip()]
    if not allowed:
        return p  # 허용 경로 미설정 시 전체 허용 (개발 환경)
    p_str = _nfc(p)
    for a in allowed:
        a_str = _nfc(a)
        # os.sep 경계 검사 — /foo/bar2 가 /foo/bar 허용 시 통과되는 오류 방지
        if p_str == a_str or p_str.startswith(a_str + os.sep):
            return p
    raise PathNotAllowedError(path)


def _full_path(parent: Path, name: str) -> str:
    """디렉토리 항목의 절대 경로 문자열을 반환."""
    return str(parent / name)


# ── 디렉토리 조회 ─────────────────────────────────────────────────────────────

def list_directory(path: str) -> dict:
    p = _assert_allowed(path)
    if not p.exists():
        raise AgentFileNotFoundError(path)
    if not p.is_dir():
        raise AgentFileNotFoundError(path)

    items = []
    for item in sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
        stat = item.stat()
        items.append({
            "name":        item.name,
            "path":        str(item),          # 절대 경로 (프론트엔드 탐색 / AI 도구 호출용)
            "type":        "directory" if item.is_dir() else "file",
            "size":        stat.st_size if item.is_file() else 0,
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return {"path": str(p), "items": items}


# ── 파일 읽기 ─────────────────────────────────────────────────────────────────

def read_file(path: str) -> dict:
    p = _assert_allowed(path)
    if not p.exists():
        raise AgentFileNotFoundError(path)

    ext = p.suffix.lower()

    if ext == ".docx":
        content = _read_docx(p)
        return {"path": str(p), "content": content, "size": p.stat().st_size, "encoding": "docx"}

    if ext == ".xlsx":
        content = _read_xlsx(p)
        return {"path": str(p), "content": content, "size": p.stat().st_size, "encoding": "xlsx"}

    # 기본: UTF-8 텍스트
    content = p.read_text(encoding="utf-8", errors="replace")
    return {"path": str(p), "content": content, "size": p.stat().st_size, "encoding": "utf-8"}


def _read_docx(p: Path) -> str:
    if not _DOCX_OK:
        return "[python-docx 미설치 — Word 파일을 읽으려면 pip install python-docx 를 실행하세요]"
    doc = _docx.Document(str(p))
    lines = []
    for para in doc.paragraphs:
        lines.append(para.text)
    # 표 내용도 포함
    for table in doc.tables:
        for row in table.rows:
            lines.append("\t".join(cell.text for cell in row.cells))
    return "\n".join(lines)


def _read_xlsx(p: Path) -> str:
    if not _XLSX_OK:
        return "[openpyxl 미설치 — Excel 파일을 읽으려면 pip install openpyxl 을 실행하세요]"
    wb = _openpyxl.load_workbook(str(p), data_only=True)
    sections = []
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = []
        for row in ws.iter_rows(values_only=True):
            # None 셀을 빈 문자열로
            rows.append("\t".join("" if v is None else str(v) for v in row))
        sections.append(f"=== {sheet_name} ===\n" + "\n".join(rows))
    return "\n\n".join(sections)


# ── 백업 ────────────────────────────────────────────────────────────────────

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


# ── 파일 생성 ─────────────────────────────────────────────────────────────────

def create_file(path: str, content: str, overwrite: bool = False) -> dict:
    p = _assert_allowed(path)
    if p.exists() and not overwrite:
        raise AgentFileExistsError(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    ext = p.suffix.lower()
    if ext == ".docx":
        _write_docx(p, content)
    elif ext == ".xlsx":
        _write_xlsx(p, content)
    else:
        p.write_text(content, encoding="utf-8")

    return {"path": str(p), "size": p.stat().st_size}


# ── 파일 수정 ─────────────────────────────────────────────────────────────────

def update_file(path: str, content: str) -> dict:
    p = _assert_allowed(path)
    if not p.exists():
        raise AgentFileNotFoundError(path)

    ext = p.suffix.lower()
    if ext == ".docx":
        _write_docx(p, content)
    elif ext == ".xlsx":
        _write_xlsx(p, content)
    else:
        p.write_text(content, encoding="utf-8")

    return {"path": str(p), "size": p.stat().st_size}


def _write_docx(p: Path, content: str) -> None:
    if not _DOCX_OK:
        raise RuntimeError("python-docx 미설치 — pip install python-docx")
    doc = _docx.Document()
    for line in content.splitlines():
        doc.add_paragraph(line)
    doc.save(str(p))


def _write_xlsx(p: Path, content: str) -> None:
    """탭 또는 쉼표로 구분된 텍스트를 xlsx로 저장.
    첫 번째 구분자 우선: 탭 → 쉼표 → 단일 셀.
    """
    if not _XLSX_OK:
        raise RuntimeError("openpyxl 미설치 — pip install openpyxl")
    wb = _openpyxl.Workbook()
    ws = wb.active
    for line in content.splitlines():
        if "\t" in line:
            ws.append(line.split("\t"))
        elif "," in line:
            ws.append(line.split(","))
        else:
            ws.append([line])
    wb.save(str(p))


# ── 파일 삭제 ─────────────────────────────────────────────────────────────────

def delete_file(path: str) -> dict:
    """파일 삭제 전 자동 백업을 생성한다. 디렉토리는 삭제 불가."""
    p = _assert_allowed(path)
    if not p.exists():
        raise AgentFileNotFoundError(path)
    if p.is_dir():
        raise AgentFileNotFoundError(f"{path} (디렉토리는 삭제할 수 없습니다)")

    # 자동 백업
    backup = backup_file(path)
    p.unlink()
    return {"deleted_path": str(p), "backup_path": backup["backup_path"]}
