import pytest
from backend.schemas.finding import RawFinding, TriagedFinding


class TestTriageAgent:
    """Tests for the TriageAgent (unit tests without actual LLM calls)."""

    def test_raw_finding_to_triaged_finding(self):
        """Test conversion from RawFinding to TriagedFinding structure."""
        raw = RawFinding(
            title="SQL Injection in Login Form",
            description="User input not sanitized in login form",
            severity="high",
            cvss_score=8.5,
            cve_ids=["CVE-2023-1234"],
            cwe_ids=["CWE-89"],
            affected_component="https://example.com/login",
            evidence="' OR '1'='1",
            scanner_source="nuclei",
        )
        assert raw.title == "SQL Injection in Login Form"
        assert raw.severity == "high"

        # Simulate triage result
        triaged = TriagedFinding(
            title=raw.title,
            description=raw.description,
            severity=raw.severity,
            adjusted_severity="critical",
            severity_changed=True,
            severity_change_reason="Public exploit available, no auth required",
            cvss_score=raw.cvss_score,
            cve_ids=raw.cve_ids,
            cwe_ids=raw.cwe_ids,
            affected_component=raw.affected_component,
            evidence=raw.evidence,
            ai_triage_notes="Finding is easily exploitable",
            exploitability_notes="No authentication required, public PoC available",
            business_impact="Data breach risk: all user credentials exposed",
            recommended_priority=1,
            scanner_source=raw.scanner_source,
        )
        assert triaged.adjusted_severity == "critical"
        assert triaged.severity_changed is True
        assert triaged.recommended_priority == 1