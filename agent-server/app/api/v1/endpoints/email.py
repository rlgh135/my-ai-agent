"""이메일 전송 API (API-014~015)"""
from fastapi import APIRouter
from app.schemas.email import EmailSendRequest, SmtpStatusOut
import uuid

router = APIRouter()


@router.post("/email/send", status_code=202)
async def send_email(body: EmailSendRequest):
    # 협의 카드 반환 (실행 보류 — 실제 전송은 tasks/approve 후)
    task_id = str(uuid.uuid4())
    body_snippet = body.body[:300] + ("..." if len(body.body) > 300 else "")
    return {
        "task_id": task_id,
        "type": "email",
        "status": "pending",
        "preview": {
            "to": body.to,
            "subject": body.subject,
            "body_snippet": body_snippet,
        },
    }


@router.get("/email/smtp-status", response_model=SmtpStatusOut)
async def smtp_status():
    # TODO: AppSetting DB에서 SMTP 설정 조회
    return SmtpStatusOut(configured=False)
