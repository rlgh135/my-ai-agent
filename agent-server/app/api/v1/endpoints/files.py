"""파일 시스템 API (API-009~013)"""
from fastapi import APIRouter, Query
from app.mcp import filesystem as fs
from app.schemas.files import (
    DirectoryListOut, FileContentOut,
    FileCreateRequest, FileUpdateRequest,
    FileBackupRequest, FileBackupOut,
    FileDeleteRequest, FileDeleteOut,
)

router = APIRouter()


@router.get("/files", response_model=DirectoryListOut)
async def list_directory(path: str = Query(...)):
    return fs.list_directory(path)


@router.get("/files/content", response_model=FileContentOut)
async def read_file(path: str = Query(...)):
    return fs.read_file(path)


@router.post("/files", response_model=dict, status_code=201)
async def create_file(body: FileCreateRequest):
    return fs.create_file(body.path, body.content, body.overwrite)


@router.put("/files", response_model=dict)
async def update_file(body: FileUpdateRequest):
    return fs.update_file(body.path, body.content)


@router.post("/files/backup", response_model=FileBackupOut)
async def backup_file(body: FileBackupRequest):
    return fs.backup_file(body.src_path, body.dest_path)


@router.delete("/files", response_model=FileDeleteOut)
async def delete_file(body: FileDeleteRequest):
    return fs.delete_file(body.path)
