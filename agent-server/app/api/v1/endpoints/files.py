"""파일 시스템 API (API-009~013)"""
from fastapi import APIRouter, Query
from app.mcp import filesystem as fs
from app.schemas.files import (
    DirectoryListOut, FileContentOut,
    FileCreateRequest, FileUpdateRequest,
    FileBackupRequest, FileBackupOut,
)
import uuid

router = APIRouter()


@router.get("/files", response_model=DirectoryListOut)
async def list_directory(path: str = Query(...)):
    return fs.list_directory(path)


@router.get("/files/content", response_model=FileContentOut)
async def read_file(path: str = Query(...)):
    return fs.read_file(path)


@router.post("/files", status_code=202)
async def create_file(body: FileCreateRequest):
    # 협의 카드 반환 (실행 보류)
    task_id = str(uuid.uuid4())
    preview = body.content[:200] + ("..." if len(body.content) > 200 else "")
    return {
        "task_id": task_id,
        "type": "create",
        "status": "pending",
        "params": {"path": body.path},
        "preview": preview,
    }


@router.put("/files", status_code=202)
async def update_file(body: FileUpdateRequest):
    # 백업 자동 실행 → 협의 카드 반환
    backup_result = fs.backup_file(body.path)
    task_id = str(uuid.uuid4())
    return {
        "task_id": task_id,
        "type": "update",
        "status": "pending",
        "backup_path": backup_result["backup_path"],
        "diff": body.diff,
        "params": {"path": body.path},
    }


@router.post("/files/backup", response_model=FileBackupOut)
async def backup_file(body: FileBackupRequest):
    return fs.backup_file(body.src_path, body.dest_path)
