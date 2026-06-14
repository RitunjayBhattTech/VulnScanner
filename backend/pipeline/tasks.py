import asyncio
import logging
from celery import Celery

from backend.config import settings
from backend.database import get_async_session_maker

logger = logging.getLogger(__name__)

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["backend.pipeline.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={"backend.pipeline.tasks.run_scan_task": {"queue": "scans"}},
    task_time_limit=3600,
    task_soft_time_limit=3300,
)


@celery_app.task(bind=True, max_retries=3, name="run_scan_task")
def run_scan_task(self, scan_id: str):
    """Celery task to run a scan asynchronously - uses async internally."""
    logger.info(f"Celery task starting for scan {scan_id}")

    async def _run():
        session_maker = get_async_session_maker()
        async with session_maker() as db:
            from sqlalchemy import select
            from backend.models.scan import Scan
            from backend.pipeline.orchestrator import ScanOrchestrator

            result = await db.execute(select(Scan).where(Scan.id == scan_id))
            scan = result.scalar_one_or_none()

            if not scan:
                logger.error(f"Scan {scan_id} not found")
                return {"status": "error", "message": "Scan not found"}

            orchestrator = ScanOrchestrator(db)
            await orchestrator.run_scan(scan)
            return {"status": "completed", "scan_id": scan_id}

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_run())
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Task failed for scan {scan_id}: {e}", exc_info=True)
        return {"status": "failed", "scan_id": scan_id, "error": str(e)}