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
    test_result: str = "unknown"   # ok | fail | unknown
