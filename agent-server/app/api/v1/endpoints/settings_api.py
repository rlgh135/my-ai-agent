"""시스템 설정 API (API-017~018)"""
import json
import logging

import anthropic
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AgentException
from app.db.database import get_db
from app.models.settings import AppSetting
from app.services import vault

logger = logging.getLogger(__name__)

router = APIRouter()

# 암호화가 필요한 설정 키 목록
_SENSITIVE_KEYS = {"anthropic_api_key", "smtp_password", "brave_api_key", "naver_api_key"}

# DB 키 → runtime settings 속성명 매핑
_KEY_TO_ATTR: dict[str, str] = {
    "anthropic_api_key":   "ANTHROPIC_API_KEY",
    "user_name":           "USER_NAME",
    "claude_model":        "CLAUDE_MODEL",
    "allowed_directories": "ALLOWED_DIRECTORIES",
    "smtp_host":           "SMTP_HOST",
    "smtp_port":           "SMTP_PORT",
    "smtp_user":           "SMTP_USER",
    "smtp_password":       "SMTP_PASSWORD",
    "smtp_from":           "SMTP_FROM",
    "brave_api_key":       "BRAVE_API_KEY",
    "naver_client_id":     "NAVER_CLIENT_ID",
    "naver_api_key":       "NAVER_API_KEY",
}


# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────────

async def load_settings_from_db(db: AsyncSession) -> None:
    """DB app_settings를 읽어 runtime settings 객체에 반영한다."""
    result = await db.execute(select(AppSetting))
    rows: list[AppSetting] = result.scalars().all()
    for row in rows:
        attr = _KEY_TO_ATTR.get(row.key)
        if attr is None:
            continue
        try:
            value = vault.decrypt(row.value) if row.is_encrypted else row.value
            # allowed_directories는 JSON 배열로 저장
            if row.key == "allowed_directories":
                value = json.loads(value) if value else []
            elif row.key == "smtp_port":
                value = int(value) if value else 587
            object.__setattr__(settings, attr, value)
        except Exception as exc:
            logger.warning("settings 로드 실패 key=%s: %s", row.key, exc)


async def _upsert_setting(db: AsyncSession, key: str, value: str, is_encrypted: bool) -> None:
    result = await db.execute(select(AppSetting).where(AppSetting.key == key))
    row = result.scalar_one_or_none()
    if row is None:
        row = AppSetting(key=key, value=value, is_encrypted=is_encrypted)
        db.add(row)
    else:
        row.value = value
        row.is_encrypted = is_encrypted


# ── GET /settings ─────────────────────────────────────────────────────────────

@router.get("/settings")
async def get_settings():
    """현재 설정 반환. 민감한 값은 마스킹 처리."""
    return {
        "user_name":                settings.USER_NAME,
        "anthropic_api_key_configured": bool(settings.ANTHROPIC_API_KEY),
        "model":                    settings.CLAUDE_MODEL,
        "max_tokens":               settings.CLAUDE_MAX_TOKENS,
        "allowed_directories":      settings.ALLOWED_DIRECTORIES,
        "smtp": {
            "configured": settings.smtp_configured,
            "host":  settings.SMTP_HOST,
            "port":  settings.SMTP_PORT,
            "user":  settings.SMTP_USER,
            "from_": settings.SMTP_FROM,
        },
        "search": {
            "provider":   settings.SEARCH_PROVIDER,
            "brave_configured": bool(settings.BRAVE_API_KEY),
            "naver_configured": bool(getattr(settings, "NAVER_API_KEY", "")),
        },
    }


# ── PATCH /settings ───────────────────────────────────────────────────────────

@router.patch("/settings")
async def update_settings(body: dict, db: AsyncSession = Depends(get_db)):
    """설정 저장. 민감 값은 Vault 암호화 후 DB에 upsert."""
    updated: list[str] = []

    for key, value in body.items():
        if key not in _KEY_TO_ATTR:
            continue  # 알 수 없는 키는 무시

        is_sensitive = key in _SENSITIVE_KEYS

        # 직렬화
        if isinstance(value, list):
            raw = json.dumps(value, ensure_ascii=False)
        else:
            raw = str(value) if value is not None else ""

        stored = vault.encrypt(raw) if is_sensitive and raw else raw
        await _upsert_setting(db, key, stored, is_encrypted=(is_sensitive and bool(raw)))

        # runtime 즉시 반영
        attr = _KEY_TO_ATTR[key]
        if key == "allowed_directories":
            rt_val = value if isinstance(value, list) else json.loads(raw) if raw else []
        elif key == "smtp_port":
            rt_val = int(value) if value else 587
        else:
            rt_val = value if value is not None else ""
        object.__setattr__(settings, attr, rt_val)

        updated.append(key)

    return {"updated": updated, "message": "설정이 저장되었습니다."}


# ── POST /settings/validate-key ───────────────────────────────────────────────

class ValidateKeyRequest(BaseModel):
    api_key: str


@router.post("/settings/validate-key")
async def validate_api_key(body: ValidateKeyRequest):
    """Anthropic API Key 유효성 검증. 실제 API 호출로 확인."""
    if not body.api_key or not body.api_key.startswith("sk-ant-"):
        raise AgentException(
            status_code=400,
            detail={"code": "INVALID_KEY_FORMAT", "message": "올바른 API Key 형식이 아닙니다. (sk-ant- 로 시작해야 합니다)"},
        )

    try:
        client = anthropic.Anthropic(api_key=body.api_key)
        # 최소 비용의 API 호출로 키 유효성 확인
        client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1,
            messages=[{"role": "user", "content": "hi"}],
        )
        return {"valid": True, "message": "API Key가 유효합니다."}
    except anthropic.AuthenticationError:
        raise AgentException(
            status_code=401,
            detail={"code": "INVALID_API_KEY", "message": "유효하지 않은 API Key입니다."},
        )
    except anthropic.APIConnectionError:
        raise AgentException(
            status_code=503,
            detail={"code": "CONNECTION_ERROR", "message": "Anthropic 서버에 연결할 수 없습니다. 네트워크를 확인해 주세요."},
        )
    except Exception as exc:
        logger.error("API Key 검증 중 오류: %s", exc)
        raise AgentException(
            status_code=500,
            detail={"code": "VALIDATION_ERROR", "message": f"키 검증 중 오류가 발생했습니다: {exc}"},
        )
