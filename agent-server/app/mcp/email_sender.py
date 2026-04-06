"""Custom SMTP MCP — 이메일 전송"""
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import SmtpNotConfiguredError, SmtpUnavailableError


def check_smtp_config() -> None:
    """SMTP 필수 설정 항목 누락 여부를 확인한다.
    누락이 있으면 SmtpNotConfiguredError를 raise한다.
    이 함수는 이메일 전송 시도 전과 smtp_status 조회 시 사용된다.
    """
    missing = []
    if not settings.SMTP_HOST:
        missing.append("SMTP_HOST")
    if not settings.SMTP_USER:
        missing.append("SMTP_USER")
    if not settings.SMTP_PASSWORD:
        missing.append("SMTP_PASSWORD")

    if missing:
        raise SmtpNotConfiguredError(missing)


async def test_smtp_connection() -> dict:
    """SMTP 서버에 실제로 연결을 시도해 상태를 반환한다.
    설정 미완료 시 configured=False, 연결 실패 시 test_result='fail'을 반환한다.
    예외를 raise하지 않으므로 smtp_status 엔드포인트에서 안전하게 호출할 수 있다.
    """
    if not settings.smtp_configured:
        missing = []
        if not settings.SMTP_HOST:
            missing.append("SMTP_HOST")
        if not settings.SMTP_USER:
            missing.append("SMTP_USER")
        if not settings.SMTP_PASSWORD:
            missing.append("SMTP_PASSWORD")
        return {
            "configured": False,
            "host": settings.SMTP_HOST or "",
            "port": settings.SMTP_PORT,
            "user": settings.SMTP_USER or "",
            "test_result": "not_configured",
            "missing_fields": missing,
        }

    try:
        smtp = aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            timeout=5,
        )
        await smtp.connect()
        # await smtp.starttls()
        await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        await smtp.quit()
        return {
            "configured": True,
            "host": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
            "user": settings.SMTP_USER,
            "test_result": "ok",
            "missing_fields": [],
        }
    except aiosmtplib.SMTPAuthenticationError:
        return {
            "configured": True,
            "host": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
            "user": settings.SMTP_USER,
            "test_result": "auth_failed",
            "error": "SMTP 인증 실패 — 계정 또는 비밀번호를 확인하세요.",
            "missing_fields": [],
        }
    except Exception as e:
        return {
            "configured": True,
            "host": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
            "user": settings.SMTP_USER,
            "test_result": "fail",
            "error": str(e),
            "missing_fields": [],
        }


async def send_email(
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    attachments: list[str] | None = None,
) -> dict:
    """SMTP 설정을 검증하고 이메일을 전송한다.
    설정 미완료 → SmtpNotConfiguredError (400)
    연결/인증 실패 → SmtpUnavailableError (503)
    """
    # ① 설정 사전 검증 — 미설정 시 즉시 중단 (다른 기능에 영향 없음)
    check_smtp_config()

    sender = settings.SMTP_FROM or settings.SMTP_USER

    msg = MIMEMultipart()
    msg["From"] = sender
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
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        return {"status": "ok", "message_id": str(result)}
    except aiosmtplib.SMTPAuthenticationError:
        raise SmtpUnavailableError(
            "SMTP 인증에 실패했습니다. 계정 또는 비밀번호를 확인해 주세요."
        )
    except aiosmtplib.SMTPConnectError as e:
        raise SmtpUnavailableError(
            f"SMTP 서버({settings.SMTP_HOST}:{settings.SMTP_PORT})에 연결할 수 없습니다: {e}"
        )
    except Exception as e:
        raise SmtpUnavailableError(f"이메일 전송 중 오류가 발생했습니다: {e}")
