from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Scan, Finding, AttackChain
from app.schemas import ScanCreate


async def create_scan(db: AsyncSession, scan_in: ScanCreate) -> Scan:
    scan = Scan(
        target_scope=scan_in.target_scope,
        profile=scan_in.profile,
        status="queued",
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    return scan


async def get_scan(db: AsyncSession, scan_id: int) -> Optional[Scan]:
    result = await db.execute(select(Scan).where(Scan.id == scan_id))
    return result.scalar_one_or_none()


async def get_scans(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
) -> list:
    """List scans with finding and chain counts."""
    stmt = (
        select(
            Scan.id,
            Scan.target_scope,
            Scan.profile,
            Scan.status,
            Scan.created_at,
            func.count(func.distinct(Finding.id)).label("finding_count"),
            func.count(func.distinct(AttackChain.id)).label("chain_count"),
        )
        .outerjoin(Finding, Finding.scan_id == Scan.id)
        .outerjoin(AttackChain, AttackChain.scan_id == Scan.id)
        .group_by(Scan.id)
        .order_by(Scan.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "id": row.id,
            "target_scope": row.target_scope,
            "profile": row.profile,
            "status": row.status,
            "created_at": row.created_at,
            "finding_count": row.finding_count,
            "chain_count": row.chain_count,
        }
        for row in rows
    ]


async def get_scan_findings(
    db: AsyncSession,
    scan_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list:
    stmt = (
        select(Finding)
        .where(Finding.scan_id == scan_id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_scan_chains(
    db: AsyncSession,
    scan_id: int,
) -> list:
    stmt = select(AttackChain).where(AttackChain.scan_id == scan_id)
    result = await db.execute(stmt)
    return result.scalars().all()