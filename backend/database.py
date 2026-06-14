import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

# Create engine lazily - only when needed
_engine = None
_async_session_maker = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(settings.DATABASE_URL, echo=False)
    return _engine


def get_async_session_maker():
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _async_session_maker


AsyncSessionLocal = async_sessionmaker(
    get_engine(), class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_all_tables():
    """Create all tables on startup."""
    from backend.models.scan import Scan, Finding, AuditLog
    from backend.models.user import User
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)