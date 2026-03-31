from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AgentException
from app.db.database import init_db, AsyncSessionLocal
from app.api.v1.router import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. DB 초기화 (테이블 생성)
    try:
        await init_db()
        logger.info("DB 초기화 완료")
    except Exception as exc:
        logger.error(
            "DB 초기화 실패 — 채팅/세션 기능이 동작하지 않을 수 있습니다. "
            "PostgreSQL 연결 정보(.env DATABASE_URL)를 확인해 주세요. 오류: %s",
            exc,
        )

    # 2. DB 저장 설정을 runtime settings에 반영
    try:
        from app.api.v1.endpoints.settings_api import load_settings_from_db
        async with AsyncSessionLocal() as db:
            await load_settings_from_db(db)
        logger.info("DB 설정 로드 완료")
    except Exception as exc:
        logger.warning("DB 설정 로드 실패 (기본값 사용): %s", exc)

    yield
    # 종료 처리 (필요 시 추가)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="로컬 PC 전용 맞춤형 AI 비서 백엔드",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 전역 예외 핸들러 ───────────────────────────────────────────────────────────
@app.exception_handler(AgentException)
async def agent_exception_handler(request: Request, exc: AgentException):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": "INTERNAL_ERROR", "message": str(exc)},
    )

# ── 라우터 등록 ───────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}
