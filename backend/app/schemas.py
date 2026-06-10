from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ScanCreate(BaseModel):
    target_scope: str = Field(..., example="10.0.0.0/24")
    profile: str = Field(..., example="normal")
    authorized: bool = Field(..., description="Affirmation that the scan is authorized within the declared scope")


class ScanRead(BaseModel):
    id: int
    target_scope: str
    profile: str
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScanListRead(BaseModel):
    id: int
    target_scope: str
    profile: str
    status: str
    created_at: Optional[datetime] = None
    finding_count: Optional[int] = None
    chain_count: Optional[int] = None

    class Config:
        from_attributes = True


class FindingBase(BaseModel):
    host: str
    port: Optional[int]
    service: Optional[str]
    raw_data: dict


class FindingRead(FindingBase):
    id: int
    scan_id: int
    ai_severity: Optional[str] = None
    ai_cvss_score: Optional[float] = None
    ai_false_positive_reasoning: Optional[str] = None
    ai_exploitation_notes: Optional[str] = None
    false_positive: Optional[bool] = None

    class Config:
        from_attributes = True


class AttackChainRead(BaseModel):
    id: int
    scan_id: int
    chain_description: str
    steps: List[Any]
    severity: Optional[str] = None
    likelihood: Optional[str] = None
    mitre_technique_id: Optional[str] = None

    class Config:
        from_attributes = True