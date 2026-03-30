from pydantic import BaseModel, EmailStr


class EmailSendRequest(BaseModel):
    to: list[EmailStr]
    subject: str
    body: str
    cc: list[EmailStr] = []
    attachments: list[str] = []


class SmtpStatusOut(BaseModel):
    configured: bool
    host: str = ""
    port: int = 587
    user: str = ""
    test_result: str = "unknown"        # ok | auth_failed | fail | not_configured | unknown
    error: str | None = None            # 연결/인증 실패 시 오류 메시지
    missing_fields: list[str] = []      # not_configured 시 누락 항목 목록
