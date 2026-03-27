from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


# PostgreSQL 비동기 엔진 (asyncpg 드라이버)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,   # 연결 유효성 선제 확인 (재연결 방지)
    pool_recycle=1800,    # 30분마다 커넥션 재생성 (idle 단절 방지)
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """앱 시작 시 테이블 자동 생성 (Alembic 미사용 환경용).
    프로덕션에서는 app/db/schema.sql 또는 Alembic 마이그레이션을 권장합니다."""
    from app.models import session as _s, message as _m, settings as _st  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
