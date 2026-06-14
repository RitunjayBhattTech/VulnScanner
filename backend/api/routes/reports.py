import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_db_session
from backend.models.scan import Scan, Finding, AuditLog
from backend.reporting.pdf_generator import PDFGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{scan_id}/pdf")
async def generate_pdf_report(
    scan_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Generate and return a PDF report for a scan."""
    # Verify scan exists
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")

    # Get findings
    result = await db.execute(select(Finding).where(Finding.scan_id == scan_id))
    findings = list(result.scalars().all())

    # Get audit logs
    result = await db.execute(
        select(AuditLog).where(AuditLog.scan_id == scan_id).order_by(AuditLog.timestamp)
    )
    audit_logs = list(result.scalars().all())

    # Generate PDF
    generator = PDFGenerator()
    pdf_bytes = await generator.generate(scan, findings, audit_logs)

    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")

    filename = f"vulnAI_report_{scan_id[:8]}.pdf"
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )