import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db_session
from backend.models.scan import Finding
from backend.schemas.finding import FindingResponse, FindingUpdateRequest
from backend.core.security import write_audit_log

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/findings", tags=["findings"])


@router.get("", response_model=list[FindingResponse])
async def list_findings(
    scan_id: str = Query(..., description="Filter by scan ID"),
    severity: Optional[str] = Query(None),
    delta_status: Optional[str] = Query(None),
    is_false_positive: Optional[bool] = Query(None),
    scanner_source: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
):
    """List findings for a scan with optional filters."""
    query = select(Finding).where(Finding.scan_id == scan_id)

    if severity:
        query = query.where(Finding.severity == severity)
    if delta_status:
        query = query.where(Finding.delta_status == delta_status)
    if is_false_positive is not None:
        query = query.where(Finding.is_false_positive == is_false_positive)
    if scanner_source:
        query = query.where(Finding.scanner_source == scanner_source)

    query = query.order_by(desc(Finding.severity), Finding.created_at)
    result = await db.execute(query)
    findings = list(result.scalars().all())

    return [FindingResponse.model_validate(f) for f in findings]


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(
    finding_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Get a single finding by ID."""
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail=f"Finding {finding_id} not found")
    return finding


@router.patch("/{finding_id}", response_model=FindingResponse)
async def update_finding(
    finding_id: str,
    req: FindingUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Update a finding (analyst workflow: mark false positive, override severity)."""
    result = await db.execute(select(Finding).where(Finding.id == finding_id))
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail=f"Finding {finding_id} not found")

    changes = {}
    if req.is_false_positive is not None:
        finding.is_false_positive = req.is_false_positive
        changes["is_false_positive"] = req.is_false_positive
    if req.severity is not None:
        finding.severity = req.severity
        changes["severity"] = req.severity

    if changes:
        await db.commit()
        await write_audit_log(
            db, finding.scan_id, "finding_updated", "analyst",
            {"finding_id": finding_id, "changes": changes},
        )

    await db.refresh(finding)
    return finding