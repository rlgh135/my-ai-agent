from pydantic import BaseModel
from datetime import datetime


class FileItem(BaseModel):
    name: str
    path: str          # 절대 경로 (탐색기 / AI 도구 호출용)
    type: str          # file | directory
    size: int = 0
    modified_at: datetime | None = None


class DirectoryListOut(BaseModel):
    path: str
    items: list[FileItem]


class FileContentOut(BaseModel):
    path: str
    content: str
    size: int
    encoding: str = "utf-8"


class FileCreateRequest(BaseModel):
    path: str
    content: str
    overwrite: bool = False


class FileUpdateRequest(BaseModel):
    path: str
    content: str
    diff: str = ""


class FileBackupRequest(BaseModel):
    src_path: str
    dest_path: str = ""


class FileBackupOut(BaseModel):
    src_path: str
    backup_path: str


class FileDeleteRequest(BaseModel):
    path: str


class FileDeleteOut(BaseModel):
    deleted_path: str
    backup_path: str
