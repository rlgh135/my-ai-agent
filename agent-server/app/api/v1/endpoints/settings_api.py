"""시스템 설정 API (API-017~018)"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/settings")
async def get_settings():
    return {
        "model": settings.CLAUDE_MODEL,
        "max_tokens": settings.CLAUDE_MAX_TOKENS,
        "allowed_directories": settings.ALLOWED_DIRECTORIES,
        "smtp": {"configured": False},
        "search": {"provider": settings.SEARCH_PROVIDER, "configured": bool(settings.BRAVE_API_KEY)},
    }


@router.patch("/settings")
async def update_settings(body: dict, db: AsyncSession = Depends(get_db)):
    # TODO: AppSetting 테이블에 저장, 민감 값은 Vault 암호화
    updated_keys = list(body.keys())
    return {"updated": updated_keys, "message": "설정이 저장되었습니다."}
