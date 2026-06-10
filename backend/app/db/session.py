from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Async engine (for FastAPI endpoints)
engine = create_async_engine(settings.database_url, future=True, echo=False)
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    future=True,
)

# Sync engine (for Celery worker tasks)
sync_database_url = settings.database_url.replace("+asyncpg", "+psycopg")
sync_engine = create_engine(sync_database_url, future=True, echo=False)
sync_session = sessionmaker(
    sync_engine,
    expire_on_commit=False,
    autoflush=False,
    future=True,
)


async def get_async_session() -> AsyncSession:
    async with async_session() as session:
        yield session
