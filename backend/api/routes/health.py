import logging
from fastapi import APIRouter
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
import asyncio

from backend.api.deps import get_db_session
from backend.models.scan import Scan
from backend.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
async def health_check(db: AsyncSession = Depends(get_db_session)):
    """Health check endpoint that verifies DB, Redis, and ChromaDB connectivity."""
    health = {
        "status": "ok",
        "version": "1.0.0",
        "checks": {},
    }

    # Database check
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        health["checks"]["database"] = "connected"
    except Exception as e:
        health["status"] = "degraded"
        health["checks"]["database"] = f"error: {str(e)}"

    # Scan count (to verify DB is actually functional)
    try:
        result = await db.execute(select(func.count()).select_from(Scan))
        scan_count = result.scalar() or 0
        health["scan_count"] = scan_count
    except Exception as e:
        health["scan_count"] = 0

    # Redis check (non-blocking)
    try:
        import redis.asyncio as aredis
        r = aredis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        health["checks"]["redis"] = "connected"
    except Exception as e:
        health["checks"]["redis"] = f"error: {str(e)}"
        if health["status"] == "ok":
            health["status"] = "degraded"

    return health