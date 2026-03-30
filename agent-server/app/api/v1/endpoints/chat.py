"""POST /api/chat — AI 추론 + SSE 스트리밍 (API-001, API-002)"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import anthropic
import json
import uuid

from app.core.config import settings
from app.core.exceptions import SessionNotFoundError
from app.db.database import get_db, AsyncSessionLocal
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


def _sse(data: dict) -> str:
    """SSE 직렬화 헬퍼.

    프론트엔드(useSSE.js)는 data: 줄만 파싱하고 JSON 내부의 type 필드로 분기한다.
    - type: 'delta'       → event.content  (스트리밍 텍스트 조각)
    - type: 'done'        → event.content, event.token_usage  (스트림 완료)
    - type: 'token_usage' → usage 정보
    - type: 'task_pending'→ event.task  (협의 카드)
    - type: 'error'       → event.message
    """
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _stream_chat(session_id: str, message: str):
    """독립적인 DB 세션을 사용하는 SSE 제너레이터.

    StreamingResponse는 핸들러 반환 후에도 계속 소비되므로
    Depends(get_db)로 주입받은 세션을 그대로 쓰면 세션이 먼저 닫힌다.
    AsyncSessionLocal을 직접 열어 제너레이터 종료 시까지 세션을 유지한다.
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        yield _sse({"type": "error", "message": f"유효하지 않은 세션 ID: {session_id}"})
        return

    async with AsyncSessionLocal() as db:
        # 세션 존재 확인
        session = await db.get(ChatSession, session_uuid)
        if not session:
            yield _sse({"type": "error", "message": f"세션을 찾을 수 없습니다: {session_id}"})
            return

        # 히스토리 로드 (최근 50개)
        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_uuid)
            .order_by(Message.created_at)
            .limit(50)
        )
        history = result.scalars().all()

        messages = [{"role": m.role, "content": m.content} for m in history
                    if m.role in ("user", "assistant")]
        messages.append({"role": "user", "content": message})

        # 사용자 메시지 저장
        db.add(Message(
            session_id=session_uuid,
            role="user",
            content=message,
            msg_type="text",
        ))

        # 토큰 사용량 초기 전송
        used = count_messages_tokens(messages)
        usage = get_usage_status(used)
        yield _sse({"type": "token_usage", **usage, "session_id": session_id})

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
                    yield _sse({"type": "delta", "content": text})

            final = await stream.get_final_message()
            total_used = final.usage.input_tokens + final.usage.output_tokens
            yield _sse({
                "type": "done",
                "content": full_text,
                "token_usage": {
                    **get_usage_status(total_used),
                },
            })

        except anthropic.AuthenticationError:
            yield _sse({
                "type": "error",
                "message": "API 인증 실패: .env의 ANTHROPIC_API_KEY를 확인하세요.",
                "error_code": "auth_failed",
            })
            return

        except anthropic.PermissionDeniedError:
            yield _sse({
                "type": "error",
                "message": "API 접근 권한이 없습니다. API 키 권한을 확인하세요.",
                "error_code": "permission_denied",
            })
            return

        except anthropic.RateLimitError:
            yield _sse({
                "type": "error",
                "message": "API 요청 한도를 초과했습니다. 잠시 후 다시 시도하세요.",
                "error_code": "rate_limit",
            })
            return

        except anthropic.BadRequestError as e:
            # 잔액 부족 (400 invalid_request_error)
            body = getattr(e, "body", {}) or {}
            inner = body.get("error", {}) if isinstance(body, dict) else {}
            raw_msg = inner.get("message", "") or str(e)
            if "credit balance" in raw_msg.lower() or "billing" in raw_msg.lower():
                user_msg = "Anthropic API 크레딧이 부족합니다. Plans & Billing에서 충전 후 다시 시도하세요."
                error_code = "insufficient_credits"
            else:
                user_msg = f"잘못된 요청: {raw_msg}"
                error_code = "bad_request"
            yield _sse({"type": "error", "message": user_msg, "error_code": error_code})
            return

        except anthropic.InternalServerError:
            yield _sse({
                "type": "error",
                "message": "Anthropic 서버 오류가 발생했습니다. 잠시 후 다시 시도하세요.",
                "error_code": "server_error",
            })
            return

        except anthropic.APIConnectionError:
            yield _sse({
                "type": "error",
                "message": "Anthropic API 서버에 연결할 수 없습니다. 네트워크 상태를 확인하세요.",
                "error_code": "connection_error",
            })
            return

        except anthropic.APIError as e:
            yield _sse({"type": "error", "message": f"API 오류: {e}", "error_code": "api_error"})
            return

        # AI 메시지 저장
        db.add(Message(
            session_id=session_uuid,
            role="assistant",
            content=full_text,
            msg_type="text",
        ))

        # 세션 제목 자동 설정 (첫 메시지)
        if session.message_count == 0:
            session.title = message[:40]
        session.message_count += 2
        await db.commit()


@router.post("/chat")
async def chat(request: ChatRequest):
    """SSE 스트리밍 채팅.
    DB 세션은 _stream_chat 내부에서 직접 관리하므로 Depends(get_db) 불필요.
    """
    return StreamingResponse(
        _stream_chat(request.session_id, request.message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/chat/token-usage", response_model=TokenUsageOut)
async def token_usage(
    session_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise SessionNotFoundError(session_id)

    session = await db.get(ChatSession, session_uuid)
    if not session:
        raise SessionNotFoundError(session_id)

    result = await db.execute(
        select(Message).where(Message.session_id == session_uuid)
    )
    messages = [{"role": m.role, "content": m.content} for m in result.scalars()]
    used = count_messages_tokens(messages)
    usage = get_usage_status(used)
    return TokenUsageOut(session_id=session_id, **usage)
