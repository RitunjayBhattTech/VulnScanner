from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class ScanCreateRequest(BaseModel):
    target: str
    scope: List[str] = Field(..., min_length=1)
    scan_types: List[str] = Field(default=["port", "web", "nuclei", "header", "ssl"])
    authorisation_confirmed: bool = False
    previous_scan_id: Optional[str] = None


class ScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    target: str
    scope: List[str]
    status: str
    scan_types: List[str]
    authorisation_confirmed: bool
    authorisation_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    summary: Optional[str] = None
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    previous_scan_id: Optional[str] = None


class ScanListResponse(BaseModel):
    items: List[ScanResponse]
    total: int
    page: int
    page_size: int


class ScanStatusResponse(BaseModel):
    id: str
    status: str
    total_findings: int = 0