"""GET|POST|DELETE /api/sessions (API-003~006)"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from typing import Any
import uuid

from app.core.exceptions import SessionNotFoundError
from app.db.database import get_db
from app.models.session import ChatSession
from app.models.message import Message
from app.schemas.chat import SessionOut, SessionCreate, MessageOut

router = APIRouter()


def _parse_uuid(session_id: str) -> uuid.UUID:
    """str → uuid.UUID 변환. 실패 시 SessionNotFoundError."""
    try:
        return uuid.UUID(session_id)
    except ValueError:
        raise SessionNotFoundError(session_id)


@router.get("/sessions", response_model=dict[str, Any])
async def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).order_by(ChatSession.updated_at.desc()).limit(limit).offset(offset)
    )
    sessions = result.scalars().all()
    # COUNT(*) 로 전체 수 조회 (전체 row fetch 방지)
    count_result = await db.execute(select(func.count()).select_from(ChatSession))
    total = count_result.scalar_one()
    return {"sessions": [SessionOut.model_validate(s) for s in sessions], "total": total}


@router.post("/sessions", response_model=SessionOut, status_code=201)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    session = ChatSession(title=body.title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions/{session_id}", response_model=dict[str, Any])
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session_uuid = _parse_uuid(session_id)
    session = await db.get(ChatSession, session_uuid)
    if not session:
        raise SessionNotFoundError(session_id)
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_uuid)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return {
        "session_id": session_id,
        "messages": [MessageOut.model_validate(m) for m in messages],
    }


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session_uuid = _parse_uuid(session_id)
    session = await db.get(ChatSession, session_uuid)
    if not session:
        raise SessionNotFoundError(session_id)
    # CASCADE DELETE가 설정되어 있으나 명시적으로도 삭제 (UUID 타입 일치)
    await db.execute(delete(Message).where(Message.session_id == session_uuid))
    await db.delete(session)
    await db.commit()
