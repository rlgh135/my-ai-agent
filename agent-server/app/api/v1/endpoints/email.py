"""이메일 전송 API (API-014~015)"""
from fastapi import APIRouter
from app.schemas.email import EmailSendRequest, SmtpStatusOut
from app.mcp.email_sender import check_smtp_config, test_smtp_connection
import uuid

router = APIRouter()


@router.post("/email/send", status_code=202)
async def api_send_email(body: EmailSendRequest):
    """이메일 전송 요청 — 작업 협의 카드 반환 (실제 전송은 tasks/approve 후).

    SMTP 미설정 시 협의 카드를 만들지 않고 즉시 400 오류를 반환한다.
    이렇게 함으로써 사용자가 승인 후 실패하는 혼란을 방지한다.
    """
    # ① SMTP 설정 사전 검증 — 미설정이면 협의 카드 생성 없이 즉시 에러 반환
    check_smtp_config()

    task_id = str(uuid.uuid4())
    body_snippet = body.body[:300] + ("..." if len(body.body) > 300 else "")
    return {
        "task_id": task_id,
        "type": "email_send",
        "status": "pending",
        "preview": {
            "to": body.to,
            "subject": body.subject,
            "body_snippet": body_snippet,
        },
    }


@router.get("/email/smtp-status", response_model=SmtpStatusOut)
async def smtp_status():
    """SMTP 연결 상태 확인.

    - configured=False      : .env에 필수 항목 누락
    - test_result='ok'       : 연결 및 인증 성공
    - test_result='auth_failed' : 인증 실패
    - test_result='fail'     : 기타 연결 실패
    설정 확인이 실패해도 예외를 throw하지 않으므로 다른 기능에 영향 없음.
    """
    result = await test_smtp_connection()
    return SmtpStatusOut(**result)
