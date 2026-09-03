import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from apps.api.app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Determine initial database URL (Default to local SQLite if USE_SQLITE_FALLBACK is True)
_db_url = settings.SQLITE_URL if settings.USE_SQLITE_FALLBACK else settings.DATABASE_URL

async_engine: AsyncEngine = create_async_engine(
    _db_url,
    echo=False,
    future=True,
    pool_pre_ping=True if "postgresql" in _db_url else False,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def init_db_engines() -> None:
    global async_engine, AsyncSessionLocal
    logger.info(f"Database initialized with URL target: {_db_url}")


def set_sqlite_fallback() -> None:
    global async_engine, AsyncSessionLocal
    async_engine = create_async_engine(
        "sqlite+aiosqlite:///./order_supervisor.db",
        echo=False,
        future=True,
    )
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def create_db_tables() -> None:
    global async_engine, AsyncSessionLocal
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.warning(f"Primary database connection failed ({e}). Switching to local SQLite database.")
        set_sqlite_fallback()
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully via SQLite fallback.")
