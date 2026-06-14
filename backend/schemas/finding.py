from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class RawFinding(BaseModel):
    """Raw finding from a scanner before AI processing."""
    title: str
    description: Optional[str] = None
    severity: str = "medium"
    cvss_score: Optional[float] = None
    cve_ids: List[str] = []
    cwe_ids: List[str] = []
    affected_component: Optional[str] = None
    evidence: Optional[str] = None
    scanner_source: str = ""


class TriagedFinding(BaseModel):
    """Finding after AI triage processing."""
    title: str
    description: Optional[str] = None
    severity: str = "medium"
    adjusted_severity: str = "medium"
    severity_changed: bool = False
    severity_change_reason: Optional[str] = None
    cvss_score: Optional[float] = None
    cve_ids: List[str] = []
    cwe_ids: List[str] = []
    affected_component: Optional[str] = None
    evidence: Optional[str] = None
    ai_triage_notes: Optional[str] = None
    ai_remediation: Optional[str] = None
    exploitability_notes: Optional[str] = None
    business_impact: Optional[str] = None
    contextual_notes: Optional[str] = None
    false_positive_probability: float = 0.0
    is_false_positive: bool = False
    recommended_priority: int = 5
    scanner_source: str = ""
    delta_status: Optional[str] = None


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    scan_id: str
    title: str
    description: Optional[str] = None
    severity: str
    cvss_score: Optional[float] = None
    cve_ids: List[str] = []
    cwe_ids: List[str] = []
    affected_component: Optional[str] = None
    evidence: Optional[str] = None
    ai_triage_notes: Optional[str] = None
    ai_remediation: Optional[str] = None
    false_positive_probability: Optional[float] = None
    is_false_positive: bool = False
    delta_status: Optional[str] = None
    scanner_source: Optional[str] = None
    created_at: datetime


class FindingUpdateRequest(BaseModel):
    is_false_positive: Optional[bool] = None
    severity: Optional[str] = None