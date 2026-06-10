from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import create_scan, get_scan, get_scans, get_scan_findings, get_scan_chains
from app.db.session import get_async_session
from app.schemas import ScanCreate, ScanRead, ScanListRead, FindingRead, AttackChainRead
from app.tasks.scan_task import run_scan
from app.utils.scope import enforce_scope

router = APIRouter()


@router.post("/", response_model=ScanRead, status_code=status.HTTP_202_ACCEPTED)
async def create_scan_job(scan_in: ScanCreate, db: AsyncSession = Depends(get_async_session)):
    enforce_scope(scan_in.target_scope)
    scan = await create_scan(db, scan_in)
    run_scan.delay(scan.id, scan_in.target_scope, scan_in.profile, scan_in.authorized)
    return scan


@router.get("/", response_model=list[ScanListRead])
async def list_scans(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_async_session),
):
    """List all scans with finding and chain counts."""
    scans = await get_scans(db, skip=skip, limit=limit)
    return scans


@router.get("/{scan_id}", response_model=ScanRead)
async def get_scan_by_id(scan_id: int, db: AsyncSession = Depends(get_async_session)):
    """Get a single scan by ID."""
    scan = await get_scan(db, scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found",
        )
    return scan


@router.get("/{scan_id}/findings", response_model=list[FindingRead])
async def list_scan_findings(
    scan_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_async_session),
):
    """List all findings for a given scan."""
    scan = await get_scan(db, scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found",
        )
    findings = await get_scan_findings(db, scan_id, skip=skip, limit=limit)
    return findings


@router.get("/{scan_id}/chains", response_model=list[AttackChainRead])
async def list_scan_chains(
    scan_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    """List all attack chains identified for a given scan."""
    scan = await get_scan(db, scan_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found",
        )
    chains = await get_scan_chains(db, scan_id)
    return chains