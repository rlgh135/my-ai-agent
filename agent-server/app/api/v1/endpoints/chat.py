"""POST /api/chat — AI 추론 + SSE 스트리밍 (API-001, API-002)"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import anthropic
import json
import uuid

from app.core.config import settings
from app.core.exceptions import LLMError, SessionNotFoundError
from app.db.database import get_db
from app.models.session import ChatSession
from app.models.message import Message
from app.schemas.chat import ChatRequest, TokenUsageOut
from app.services.token_counter import count_messages_tokens, get_usage_status

router = APIRouter()

_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """당신은 SI 개발자를 위한 로컬 AI 에이전트입니다.
사용자의 자연어 지시를 받아 파일 탐색/생성/수정/백업, 이메일 전송, 웹 검색 등의 작업을 수행합니다.
파일 수정·생성·삭제·이메일 발송 등 리스크가 있는 작업은 반드시 사용자 승인을 받은 후 실행합니다.
파일 수정 전에는 항상 백업을 먼저 수행합니다."""


async def _stream_chat(request: ChatRequest, db: AsyncSession):
    # 세션 존재 확인
    session = await db.get(ChatSession, request.session_id)
    if not session:
        raise SessionNotFoundError(request.session_id)

    # 히스토리 로드
    result = await db.execute(
        select(Message)
        .where(Message.session_id == request.session_id)
        .order_by(Message.created_at)
        .limit(50)
    )
    history = result.scalars().all()

    messages = [{"role": m.role, "content": m.content} for m in history
                if m.role in ("user", "assistant")]
    messages.append({"role": "user", "content": request.message})

    # 사용자 메시지 저장
    user_msg = Message(
        session_id=request.session_id,
        role="user",
        content=request.message,
        msg_type="text",
    )
    db.add(user_msg)

    # 토큰 카운트
    used = count_messages_tokens(messages)
    usage = get_usage_status(used)

    # SSE yield helper
    def sse(event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    yield sse("token_usage", {**usage, "session_id": request.session_id})

    full_text = ""
    try:
        async with _client.messages.stream(
            model=settings.CLAUDE_MODEL,
            max_tokens=settings.CLAUDE_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                full_text += text
                yield sse("message_delta", {"delta": text, "type": "text"})

        final = await stream.get_final_message()
        yield sse("message_done", {
            "usage": {
                "input_tokens": final.usage.input_tokens,
                "output_tokens": final.usage.output_tokens,
            }
        })

    except anthropic.APIError as e:
        yield sse("error", {"code": "LLM_ERROR", "message": str(e)})
        return

    # AI 메시지 저장
    ai_msg = Message(
        session_id=request.session_id,
        role="assistant",
        content=full_text,
        msg_type="text",
    )
    db.add(ai_msg)

    # 세션 제목 자동 설정 (첫 메시지)
    if session.message_count == 0:
        session.title = request.message[:40]
    session.message_count += 2
    await db.commit()


@router.post("/chat")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    return StreamingResponse(
        _stream_chat(request, db),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/chat/token-usage", response_model=TokenUsageOut)
async def token_usage(session_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    session = await db.get(ChatSession, session_id)
    if not session:
        raise SessionNotFoundError(session_id)

    result = await db.execute(
        select(Message).where(Message.session_id == session_id)
    )
    messages = [{"role": m.role, "content": m.content} for m in result.scalars()]
    used = count_messages_tokens(messages)
    usage = get_usage_status(used)
    return TokenUsageOut(session_id=session_id, **usage)
