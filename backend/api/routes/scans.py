import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db_session
from backend.config import settings
from backend.models.scan import Scan, Finding, AuditLog, ScanStatus
from backend.schemas.scan import (
    ScanCreateRequest,
    ScanResponse,
    ScanListResponse,
    ScanStatusResponse,
)
from backend.core.security import generate_authorisation_token, write_audit_log

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scans", tags=["scans"])


@router.post("", response_model=ScanResponse, status_code=201)
async def create_scan(
    req: ScanCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """Create and queue a new scan."""
    # Validate scope is non-empty
    if not req.scope or len(req.scope) == 0:
        raise HTTPException(status_code=400, detail="Scope must not be empty")

    # Validate authorisation gate - enforced at API level, not just UI
    if not req.authorisation_confirmed:
        raise HTTPException(
            status_code=400,
            detail="Authorisation not confirmed. You must confirm you have written "
                   "authorisation from the system owner before running a scan.",
        )

    # Generate authorisation token
    auth_token = generate_authorisation_token(
        req.target, req.scope, datetime.utcnow().isoformat()
    )

    # Create scan record
    scan = Scan(
        target=req.target,
        scope=req.scope,
        scan_types=req.scan_types,
        authorisation_confirmed=True,
        authorisation_token=auth_token,
        status=ScanStatus.pending,
        previous_scan_id=req.previous_scan_id,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    # Write audit log
    await write_audit_log(
        db,
        scan.id,
        "scan_created",
        "user",
        {
            "target": req.target,
            "scope": req.scope,
            "scan_types": req.scan_types,
            "authorisation_token": auth_token,
        },
        ip_address=request.client.host if request.client else None,
    )

    # Dispatch to Celery (non-blocking)
    try:
        from backend.pipeline.tasks import run_scan_task
        run_scan_task.delay(scan.id)
        logger.info(f"Dispatched scan task for {scan.id}")
    except Exception as e:
        logger.error(f"Failed to dispatch Celery task for scan {scan.id}: {e}")
        # Still return success - the scan can be picked up later

    return scan


@router.get("", response_model=ScanListResponse)
async def list_scans(
    status: Optional[str] = Query(None),
    target: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
):
    """List all scans with pagination and optional filters."""
    query = select(Scan)

    if status:
        query = query.where(Scan.status == status)
    if target:
        query = query.where(Scan.target.contains(target))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(desc(Scan.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    scans = list(result.scalars().all())

    return ScanListResponse(
        items=[ScanResponse.model_validate(s) for s in scans],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Get scan details by ID."""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    return scan


@router.get("/{scan_id}/status", response_model=ScanStatusResponse)
async def get_scan_status(
    scan_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Lightweight status polling endpoint."""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")

    return ScanStatusResponse(
        id=scan.id,
        status=scan.status,
        total_findings=scan.total_findings,
    )


@router.delete("/{scan_id}/cancel")
async def cancel_scan(
    scan_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """Cancel a running scan."""
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")

    if scan.status not in [ScanStatus.pending, ScanStatus.running]:
        raise HTTPException(
            status_code=400,
            detail=f"Scan is in status '{scan.status}' and cannot be cancelled",
        )

    scan.status = ScanStatus.cancelled
    await db.commit()

    # Try to revoke Celery task
    try:
        from backend.pipeline.tasks import celery_app
        celery_app.control.revoke(scan_id, terminate=True)
    except Exception as e:
        logger.warning(f"Could not revoke Celery task for {scan_id}: {e}")

    await write_audit_log(
        db, scan.id, "scan_cancelled", "user", {},
        ip_address=request.client.host if request.client else None,
    )

    return {"message": f"Scan {scan_id} cancelled successfully"}