"""Custom SMTP MCP — 이메일 전송"""
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

from app.core.exceptions import SmtpUnavailableError


async def send_email(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    attachments: list[str] | None = None,
) -> dict:
    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = ", ".join(to)
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg.attach(MIMEText(body, "html" if body.strip().startswith("<") else "plain", "utf-8"))

    for att_path in (attachments or []):
        p = Path(att_path)
        if p.exists():
            part = MIMEBase("application", "octet-stream")
            part.set_payload(p.read_bytes())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{p.name}"')
            msg.attach(part)

    try:
        result = await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            start_tls=True,
        )
        return {"status": "ok", "message_id": str(result)}
    except Exception as e:
        raise SmtpUnavailableError(str(e))
