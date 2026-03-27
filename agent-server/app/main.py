from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AgentException
from app.db.database import init_db
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 DB 초기화
    await init_db()
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
