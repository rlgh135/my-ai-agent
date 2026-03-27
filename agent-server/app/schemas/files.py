from pydantic import BaseModel
from datetime import datetime


class FileItem(BaseModel):
    name: str
    type: str        # file | directory
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


class FileUpdateRequest(BaseModel):
    path: str
    content: str
    diff: str = ""   # 미리보기용 diff 텍스트


class FileBackupRequest(BaseModel):
    src_path: str
    dest_path: str = ""


class FileBackupOut(BaseModel):
    src_path: str
    backup_path: str
