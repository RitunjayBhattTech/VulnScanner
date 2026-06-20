import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from backend.database import Base


class ScanStatus:
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    target = Column(String, nullable=False)
    scope = Column(JSON, nullable=False, default=list)
    status = Column(String, default=ScanStatus.pending, nullable=False)
    scan_types = Column(JSON, nullable=False, default=list)
    authorisation_confirmed = Column(Boolean, default=False, nullable=False)
    authorisation_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)
    total_findings = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    info_count = Column(Integer, default=0)
    previous_scan_id = Column(String, nullable=True)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="scan", cascade="all, delete-orphan")
    owner = relationship("User", back_populates="scans")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String, default="medium", nullable=False)
    cvss_score = Column(Float, nullable=True)
    cve_ids = Column(JSON, nullable=True, default=list)
    cwe_ids = Column(JSON, nullable=True, default=list)
    affected_component = Column(String, nullable=True)
    evidence = Column(Text, nullable=True)
    ai_triage_notes = Column(Text, nullable=True)
    ai_remediation = Column(Text, nullable=True)
    false_positive_probability = Column(Float, nullable=True)
    is_false_positive = Column(Boolean, default=False)
    delta_status = Column(String, nullable=True)
    scanner_source = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    scan = relationship("Scan", back_populates="findings")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id = Column(String, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    action = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    details = Column(JSON, nullable=True, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String, nullable=True)

    scan = relationship("Scan", back_populates="audit_logs")