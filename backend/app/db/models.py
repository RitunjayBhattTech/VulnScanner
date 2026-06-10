from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, func, Boolean, Float
from sqlalchemy.orm import relationship

from app.db.base import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    target_scope = Column(String, nullable=False)
    profile = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")
    attack_chains = relationship("AttackChain", back_populates="scan", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=True)
    service = Column(String, nullable=True)
    raw_data = Column(JSON, nullable=False)
    ai_severity = Column(String, nullable=True)
    ai_cvss_score = Column(Float, nullable=True)
    ai_false_positive_reasoning = Column(String, nullable=True)
    ai_exploitation_notes = Column(String, nullable=True)
    false_positive = Column(Boolean, default=False)

    scan = relationship("Scan", back_populates="findings")


class AttackChain(Base):
    __tablename__ = "attack_chains"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    chain_description = Column(String, nullable=False)
    steps = Column(JSON, nullable=False)  # List of finding IDs and how they chain
    severity = Column(String, nullable=True)
    likelihood = Column(String, nullable=True)
    mitre_technique_id = Column(String, nullable=True)

    scan = relationship("Scan", back_populates="attack_chains")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, nullable=False)
    user = Column(String, nullable=False)
    target_scope = Column(String, nullable=False)
    action = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FalsePositiveFeedback(Base):
    __tablename__ = "false_positive_feedback"

    id = Column(Integer, primary_key=True, index=True)
    finding_id = Column(Integer, ForeignKey("findings.id", ondelete="CASCADE"), nullable=False)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())