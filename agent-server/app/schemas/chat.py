from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any
import uuid


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1)
    attachments: list[str] = []


class MessageOut(BaseModel):
    id: uuid.UUID          # DB 모델과 타입 일치, JSON 직렬화 시 문자열로 변환됨
    session_id: uuid.UUID
    role: str
    content: str
    msg_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenUsageOut(BaseModel):
    session_id: str
    used_tokens: int
    max_tokens: int
    usage_percent: float
    status: str  # normal | warning | danger


class SessionOut(BaseModel):
    id: uuid.UUID          # DB 모델과 타입 일치, JSON 직렬화 시 문자열로 변환됨
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionCreate(BaseModel):
    title: str = "새 대화"


class TaskOut(BaseModel):
    task_id: str
    type: str       # create | update | backup | email
    status: str     # pending | approved | rejected
    params: dict[str, Any] = {}
    diff: str = ""
    summary: str = ""


class TaskResult(BaseModel):
    task_id: str
    status: str
    result: dict[str, Any] = {}
    message: str = ""
