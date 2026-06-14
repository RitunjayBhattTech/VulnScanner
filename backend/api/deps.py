from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides an async database session."""
    async for session in get_db():
        yield session