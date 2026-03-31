"""POST /api/chat — AI 추론 + SSE 스트리밍 + Agentic Tool Loop (API-001, API-002)"""
import json
import logging
import uuid
from datetime import datetime, timezone

import anthropic
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import SessionNotFoundError
from app.db.database import AsyncSessionLocal, get_db
from app.models.message import Message
from app.models.session import ChatSession
from app.schemas.chat import ChatRequest, TokenUsageOut
from app.services.token_counter import count_messages_tokens, get_usage_status

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_TOOL_TURNS = 5  # 무한 루프 방지


# ── Claude Tool 정의 ───────────────────────────────────────────────────────────

TOOLS: list[dict] = [
    {
        "name": "web_search",
        "description": (
            "웹에서 정보를 검색합니다. "
            "한국어 쿼리는 Naver API, 영문 쿼리는 Brave API를 우선 사용합니다. "
            "API 키가 설정되지 않은 경우 DuckDuckGo로 대체합니다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "검색 쿼리"},
                "limit": {"type": "integer", "description": "최대 결과 수 (기본 5)", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "list_directory",
        "description": "지정된 절대 경로의 디렉토리 목록을 조회합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "조회할 디렉토리 절대 경로"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "read_file",
        "description": "파일의 내용을 읽어 반환합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "읽을 파일 절대 경로"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "create_file",
        "description": "새 파일을 생성합니다. 실행 전 사용자 승인이 필요합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path":      {"type": "string",  "description": "생성할 파일 절대 경로"},
                "content":   {"type": "string",  "description": "파일 내용"},
                "overwrite": {"type": "boolean", "description": "동명 파일 덮어쓰기 여부 (기본 false)"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "update_file",
        "description": (
            "기존 파일을 수정합니다. "
            "수정 전 자동으로 백업 파일이 생성됩니다. "
            "실행 전 사용자 승인이 필요합니다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path":    {"type": "string", "description": "수정할 파일 절대 경로"},
                "content": {"type": "string", "description": "새로운 파일 전체 내용"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "backup_file",
        "description": "파일을 백업합니다. 실행 전 사용자 승인이 필요합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path":      {"type": "string", "description": "백업할 파일 절대 경로"},
                "dest_path": {"type": "string", "description": "백업 저장 경로 (생략 시 타임스탬프로 자동 생성)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "delete_file",
        "description": (
            "파일을 삭제합니다. 삭제 전 자동으로 백업이 생성됩니다. "
            "디렉토리는 삭제할 수 없습니다. "
            "실행 전 사용자 승인이 필요합니다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "삭제할 파일 절대 경로"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "send_email",
        "description": (
            "이메일을 전송합니다. SMTP 설정이 되어 있어야 하며, "
            "실행 전 사용자 승인이 필요합니다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "to":          {"type": "array",  "items": {"type": "string"}, "description": "수신자 이메일 목록"},
                "subject":     {"type": "string", "description": "이메일 제목"},
                "body":        {"type": "string", "description": "이메일 본문 (HTML 또는 텍스트)"},
                "cc":          {"type": "array",  "items": {"type": "string"}, "description": "참조 이메일 목록"},
                "attachments": {"type": "array",  "items": {"type": "string"}, "description": "첨부파일 절대 경로 목록"},
            },
            "required": ["to", "subject", "body"],
        },
    },
]

# 사용자 승인이 필요한 도구 → 프론트엔드 task type 매핑
_RISKY_TOOLS: dict[str, str] = {
    "create_file": "filesystem_create",
    "update_file": "filesystem_update",
    "backup_file": "filesystem_backup",
    "delete_file": "filesystem_delete",
    "send_email":  "email_send",
}

SYSTEM_PROMPT = """당신은 SI 개발자를 위한 로컬 AI 에이전트입니다.
사용자의 자연어 지시를 받아 파일 탐색/생성/수정/백업, 이메일 전송, 웹 검색 등의 작업을 수행합니다.

규칙:
- 파일 수정·생성·삭제·이메일 발송 등 리스크가 있는 작업은 반드시 도구(create_file, update_file, backup_file, send_email)를 통해 사용자 승인을 요청하십시오.
- 파일 수정(update_file) 전에는 항상 백업(backup_file)을 먼저 요청하십시오.
- 읽기 전용 작업(web_search, list_directory, read_file)은 즉시 수행합니다.
- 작업 결과를 한국어로 사용자에게 명확히 알려주십시오."""


# ── 헬퍼 함수들 ───────────────────────────────────────────────────────────────

def _sse(data: dict) -> str:
    """SSE 직렬화. 프론트엔드 useSSE.js의 type 필드 기반 분기와 매핑됨."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _get_client() -> anthropic.AsyncAnthropic:
    """매 호출 시 최신 settings.ANTHROPIC_API_KEY를 반영한 클라이언트 반환."""
    return anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


def _build_history(messages_from_db: list) -> list[dict]:
    """DB 메시지 목록에서 Anthropic API 형식의 messages 배열 재구성.
    tool_use_response / tool_result 타입은 JSON으로 저장되어 있어 파싱 후 반환.
    """
    result = []
    for m in messages_from_db:
        if m.msg_type in ("tool_use_response", "tool_result"):
            try:
                content = json.loads(m.content)
            except (json.JSONDecodeError, TypeError):
                continue  # 파싱 실패 시 이 메시지 건너뜀
        elif m.role in ("user", "assistant"):
            content = m.content
        else:
            continue
        result.append({"role": m.role, "content": content})
    return result


def _make_task_event(tool_name: str, params: dict, task_id: str) -> dict:
    """프론트엔드 TaskCard가 기대하는 task_pending SSE 페이로드 생성."""
    if tool_name in ("create_file", "update_file", "backup_file", "delete_file"):
        payload = {"path": params.get("path", ""), "content": params.get("content")}
    elif tool_name == "send_email":
        payload = {
            "to": ", ".join(params.get("to", [])),
            "subject": params.get("subject", ""),
            "content": params.get("body", ""),
        }
    else:
        payload = params

    if tool_name == "create_file":
        description = f"'{params.get('path', '')}' 파일을 생성합니다."
    elif tool_name == "update_file":
        description = f"'{params.get('path', '')}' 파일을 수정합니다. (수정 전 자동 백업 포함)"
    elif tool_name == "backup_file":
        description = f"'{params.get('path', '')}' 파일을 백업합니다."
    elif tool_name == "delete_file":
        description = f"'{params.get('path', '')}' 파일을 삭제합니다. (삭제 전 자동 백업 포함)"
    elif tool_name == "send_email":
        recipients = ", ".join(params.get("to", []))
        description = f"{recipients}에게 '{params.get('subject', '')}' 이메일을 발송합니다."
    else:
        description = tool_name

    return {
        "type": "task_pending",
        "task": {
            "id":          task_id,
            "type":        _RISKY_TOOLS[tool_name],
            "description": description,
            "payload":     payload,
            "createdAt":   datetime.now(timezone.utc).isoformat(),
        },
    }


async def _run_safe_tool(tool_name: str, params: dict) -> str:
    """읽기 전용 도구를 즉시 실행하고 결과 문자열을 반환."""
    from app.mcp import filesystem, search as search_mcp
    try:
        if tool_name == "web_search":
            result = await search_mcp.web_search(params["query"], params.get("limit", 5))
            return json.dumps(result, ensure_ascii=False)
        if tool_name == "list_directory":
            result = filesystem.list_directory(params["path"])
            return json.dumps(result, ensure_ascii=False)
        if tool_name == "read_file":
            result = filesystem.read_file(params["path"])
            return result["content"]
    except Exception as exc:
        logger.warning("safe tool %s 실행 오류: %s", tool_name, exc)
        return f"오류: {exc}"
    return f"알 수 없는 도구: {tool_name}"


async def _run_risky_tool(tool_name: str, params: dict) -> str:
    """사용자가 승인한 위험 도구를 실행하고 결과 문자열을 반환."""
    from app.mcp import filesystem, email_sender
    try:
        if tool_name == "create_file":
            result = filesystem.create_file(
                params["path"], params["content"], params.get("overwrite", False)
            )
            return f"파일 생성 완료: {result['path']} ({result['size']} bytes)"

        if tool_name == "update_file":
            # 백업 먼저 — 실패해도 업데이트는 진행
            backup_info = ""
            try:
                backup = filesystem.backup_file(params["path"])
                backup_info = f" | 백업: {backup['backup_path']}"
            except Exception as be:
                logger.warning("자동 백업 실패 (업데이트는 계속): %s", be)
            result = filesystem.update_file(params["path"], params["content"])
            return f"파일 수정 완료: {result['path']} ({result['size']} bytes){backup_info}"

        if tool_name == "backup_file":
            result = filesystem.backup_file(params["path"], params.get("dest_path", ""))
            return f"백업 완료: {result['backup_path']}"

        if tool_name == "delete_file":
            result = filesystem.delete_file(params["path"])
            return f"파일 삭제 완료: {result['deleted_path']} | 백업: {result['backup_path']}"

        if tool_name == "send_email":
            result = await email_sender.send_email(
                to=params["to"],
                subject=params["subject"],
                body=params["body"],
                cc=params.get("cc"),
                attachments=params.get("attachments"),
            )
            return f"이메일 전송 완료. (message_id: {result.get('message_id', 'N/A')})"

    except Exception as exc:
        logger.error("risky tool %s 실행 오류: %s", tool_name, exc)
        return f"실행 오류: {exc}"

    return f"알 수 없는 도구: {tool_name}"


async def _process_tool_block(block):
    """도구 블록 하나를 처리하는 비동기 제너레이터.

    흐름:
      1. 위험 도구: task_pending 이벤트 dict를 yield → 호출자가 SSE 전송 후 재개
      2. (내부) asyncio.Future 대기 — 이 시간 동안 이벤트 루프가 approve/reject HTTP 요청을 처리
      3. 최종적으로 {"_tool_result": {...}} 내부 마커를 yield

    호출자 패턴:
      async for event in _process_tool_block(block):
          if "_tool_result" in event:
              tool_result = event["_tool_result"]
          else:
              yield _sse(event)   # task_pending 등 실제 SSE 이벤트
    """
    from app.api.v1.endpoints.tasks import register_task

    tool_name: str = block.name
    params: dict   = block.input
    tool_use_id: str = block.id

    if tool_name in _RISKY_TOOLS:
        task_id = str(uuid.uuid4())

        # ① future 등록을 먼저 (yield 전에) 해야 race condition 없음
        future = register_task(task_id, tool_name, params)

        # ② task_pending 이벤트를 yield → 호출자가 SSE 전송
        yield _make_task_event(tool_name, params, task_id)

        # ③ future 대기 (register_task 내부의 _timeout task가 5분 후 자동 거부)
        try:
            decision = await future  # "approved" | "rejected"
        except Exception:
            decision = "rejected"

        if decision == "rejected":
            content = "사용자가 작업을 취소했습니다."
        else:
            content = await _run_risky_tool(tool_name, params)
    else:
        content = await _run_safe_tool(tool_name, params)

    yield {"_tool_result": {"type": "tool_result", "tool_use_id": tool_use_id, "content": content}}


# ── 핵심 SSE 스트리밍 제너레이터 ─────────────────────────────────────────────

async def _stream_chat(session_id: str, message: str):
    """Agentic loop: Claude ↔ Tool 반복 호출을 SSE로 스트리밍."""
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

        # 히스토리 로드 (최근 50개 — tool 메시지 포함)
        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_uuid)
            .order_by(Message.created_at)
            .limit(50)
        )
        history = result.scalars().all()
        messages = _build_history(history)
        messages.append({"role": "user", "content": message})

        # 사용자 메시지 DB 저장 — Claude API 호출 전에 즉시 커밋하여
        # 장시간 대기 중 asyncpg 커넥션 만료로 인한 commit 실패 방지
        db.add(Message(
            session_id=session_uuid,
            role="user",
            content=message,
            msg_type="text",
        ))
        is_first_message = (session.message_count == 0)
        try:
            await db.commit()
        except Exception as exc:
            logger.error("사용자 메시지 DB 저장 실패: %s", exc)

        # 초기 토큰 사용량 전송
        used = count_messages_tokens(messages)
        yield _sse({"type": "token_usage", **get_usage_status(used), "session_id": session_id})

        client = _get_client()
        final_text = ""    # 최종 assistant 텍스트 (done 이벤트용)
        tool_turns = 0

        try:
            # ── Agentic Loop ────────────────────────────────────────────────
            while tool_turns <= MAX_TOOL_TURNS:
                full_text = ""

                async with client.messages.stream(
                    model=settings.CLAUDE_MODEL,
                    max_tokens=settings.CLAUDE_MAX_TOKENS,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=messages,
                ) as stream:
                    async for text in stream.text_stream:
                        full_text += text
                        yield _sse({"type": "delta", "content": text})

                    final_msg = await stream.get_final_message()

                final_text = full_text

                # ── 순수 텍스트 응답 → 루프 종료 ─────────────────────────────
                if final_msg.stop_reason == "end_turn":
                    total_tokens = final_msg.usage.input_tokens + final_msg.usage.output_tokens
                    db.add(Message(
                        session_id=session_uuid,
                        role="assistant",
                        content=final_text,
                        msg_type="text",
                    ))
                    if is_first_message:
                        session.title = message[:40]
                    session.message_count += 2
                    try:
                        await db.commit()
                    except Exception as db_exc:
                        logger.error("DB commit 실패 (end_turn): %s", db_exc)
                    # done은 DB 성공/실패 무관하게 반드시 전송 — 미전송 시 커넥션이 열린 채로 남아 버튼 고착
                    yield _sse({
                        "type": "done",
                        "content": final_text,
                        "token_usage": get_usage_status(total_tokens),
                    })
                    return  # 제너레이터 즉시 종료 → 커넥션 닫힘 → clearStreaming() 호출

                # ── tool_use 응답 → 도구 실행 후 계속 ────────────────────────
                elif final_msg.stop_reason == "tool_use":
                    tool_turns += 1

                    # assistant 응답(tool_use 포함) messages에 추가
                    # Anthropic API가 허용하는 필드만 명시적으로 추출 (parsed_output 등 내부 필드 제외)
                    assistant_content = []
                    for block in final_msg.content:
                        if getattr(block, "type", None) == "text":
                            assistant_content.append({"type": "text", "text": block.text})
                        elif getattr(block, "type", None) == "tool_use":
                            assistant_content.append({
                                "type":  "tool_use",
                                "id":    block.id,
                                "name":  block.name,
                                "input": block.input,
                            })
                        # 그 외 block 타입은 건너뜀
                    messages.append({"role": "assistant", "content": assistant_content})

                    # tool_use_response DB 저장 (히스토리 재구성용)
                    db.add(Message(
                        session_id=session_uuid,
                        role="assistant",
                        content=json.dumps(assistant_content, ensure_ascii=False),
                        msg_type="tool_use_response",
                    ))

                    # 도구 실행
                    tool_results: list[dict] = []
                    tool_blocks = [b for b in final_msg.content if b.type == "tool_use"]

                    for block in tool_blocks:
                        async for event in _process_tool_block(block):
                            if "_tool_result" in event:
                                tool_results.append(event["_tool_result"])
                            else:
                                yield _sse(event)  # task_pending 등

                    # tool_result messages에 추가
                    messages.append({"role": "user", "content": tool_results})

                    # tool_result DB 저장 후 즉시 커밋 — 도구 메시지는 각 턴마다 저장하여
                    # 다음 Claude API 호출 전 커넥션을 해제하고 트랜잭션 만료 방지
                    db.add(Message(
                        session_id=session_uuid,
                        role="user",
                        content=json.dumps(tool_results, ensure_ascii=False),
                        msg_type="tool_result",
                    ))
                    try:
                        await db.commit()
                    except Exception as exc:
                        logger.error("도구 메시지 DB 저장 실패 (turn %d): %s", tool_turns, exc)

                # ── max_tokens 등 기타 stop_reason ────────────────────────────
                else:
                    total_tokens = final_msg.usage.input_tokens + final_msg.usage.output_tokens
                    db.add(Message(
                        session_id=session_uuid,
                        role="assistant",
                        content=final_text,
                        msg_type="text",
                    ))
                    if is_first_message:
                        session.title = message[:40]
                    session.message_count += 2
                    try:
                        await db.commit()
                    except Exception as db_exc:
                        logger.error("DB commit 실패 (stop_reason=%s): %s", final_msg.stop_reason, db_exc)
                    yield _sse({
                        "type": "done",
                        "content": final_text,
                        "token_usage": get_usage_status(total_tokens),
                    })
                    return  # 제너레이터 즉시 종료

            else:
                # MAX_TOOL_TURNS 초과
                if is_first_message:
                    session.title = message[:40]
                session.message_count += 2
                try:
                    await db.commit()
                except Exception as db_exc:
                    logger.error("DB commit 실패 (max_tool_turns): %s", db_exc)
                yield _sse({
                    "type": "error",
                    "message": "도구 호출 최대 횟수를 초과했습니다. 더 구체적인 요청을 시도해 주세요.",
                    "error_code": "max_tool_turns",
                })
                return  # 제너레이터 즉시 종료

        # ── Anthropic API 예외 처리 ──────────────────────────────────────────
        except anthropic.AuthenticationError:
            yield _sse({"type": "error", "message": "API 인증 실패: 설정의 ANTHROPIC_API_KEY를 확인하세요.", "error_code": "auth_failed"})
            return
        except anthropic.PermissionDeniedError:
            yield _sse({"type": "error", "message": "API 접근 권한이 없습니다.", "error_code": "permission_denied"})
            return
        except anthropic.RateLimitError:
            yield _sse({"type": "error", "message": "API 요청 한도를 초과했습니다. 잠시 후 다시 시도하세요.", "error_code": "rate_limit"})
            return
        except anthropic.BadRequestError as e:
            body = getattr(e, "body", {}) or {}
            inner = body.get("error", {}) if isinstance(body, dict) else {}
            raw_msg = inner.get("message", "") or str(e)
            if "credit balance" in raw_msg.lower() or "billing" in raw_msg.lower():
                yield _sse({"type": "error", "message": "Anthropic API 크레딧이 부족합니다.", "error_code": "insufficient_credits"})
            else:
                yield _sse({"type": "error", "message": f"잘못된 요청: {raw_msg}", "error_code": "bad_request"})
            return
        except anthropic.InternalServerError:
            yield _sse({"type": "error", "message": "Anthropic 서버 오류입니다. 잠시 후 다시 시도하세요.", "error_code": "server_error"})
            return
        except anthropic.APIConnectionError:
            yield _sse({"type": "error", "message": "Anthropic API 서버에 연결할 수 없습니다.", "error_code": "connection_error"})
            return
        except anthropic.APIError as e:
            yield _sse({"type": "error", "message": f"API 오류: {e}", "error_code": "api_error"})
            return
        except Exception as e:
            # DB 오류 등 예상치 못한 예외 — done/error를 반드시 전송해 커넥션을 닫아 버튼 고착 방지
            logger.error("예상치 못한 오류: %s(%s)", type(e).__name__, e)
            yield _sse({"type": "error", "message": "서버 내부 오류가 발생했습니다.", "error_code": "server_error"})
            return


# ── 라우터 ────────────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(request: ChatRequest):
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

    result = await db.execute(select(Message).where(Message.session_id == session_uuid))
    messages = [
        {"role": m.role, "content": m.content}
        for m in result.scalars()
        if m.role in ("user", "assistant") and m.msg_type == "text"
    ]
    used = count_messages_tokens(messages)
    return TokenUsageOut(session_id=session_id, **get_usage_status(used))
