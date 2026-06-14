import pytest
from datetime import datetime
from unittest.mock import MagicMock
from backend.pipeline.delta_engine import DeltaEngine


class MockFinding:
    """Mock Finding for testing delta engine."""
    def __init__(self, title: str, severity: str, affected_component: str, delta_status=None):
        self.title = title
        self.severity = severity
        self.affected_component = affected_component
        self.delta_status = delta_status
        self.description = f"Description for {title}"
        self.cvss_score = None
        self.cve_ids = []
        self.cwe_ids = []
        self.evidence = None
        self.scanner_source = "test"
        self.is_false_positive = False
        self.created_at = datetime.utcnow()


class TestDeltaEngine:
    """Tests for the DeltaEngine."""

    def setup_method(self):
        self.engine = DeltaEngine()

    def test_finding_in_current_only_is_new(self):
        """Finding in current only should be marked as new."""
        current = [MockFinding("Vuln A", "high", "192.168.1.1:80")]
        previous = []
        result = self.engine.compare(current, previous)
        assert result[0].delta_status == "new"
        assert len(result) == 1

    def test_finding_in_both_same_severity_is_existing(self):
        """Finding in both with same severity should be marked as existing."""
        current = [MockFinding("Vuln A", "high", "192.168.1.1:80")]
        previous = [MockFinding("Vuln A", "high", "192.168.1.1:80")]
        result = self.engine.compare(current, previous)
        assert result[0].delta_status == "existing"
        assert len(result) == 1

    def test_finding_in_previous_only_is_fixed(self):
        """Finding in previous only should be marked as fixed (synthetic)."""
        current = []
        previous = [MockFinding("Vuln A", "high", "192.168.1.1:80")]
        result = self.engine.compare(current, previous)
        assert len(result) == 1
        assert result[0].delta_status == "fixed"

    def test_finding_in_both_severity_increased_is_regressed(self):
        """Finding in both but severity increased should be marked as regressed."""
        current = [MockFinding("Vuln A", "critical", "192.168.1.1:80")]
        previous = [MockFinding("Vuln A", "high", "192.168.1.1:80")]
        result = self.engine.compare(current, previous)
        assert result[0].delta_status == "regressed"

    def test_empty_current_non_empty_previous_all_fixed(self):
        """Empty current findings, non-empty previous should all be fixed."""
        current = []
        previous = [
            MockFinding("Vuln A", "high", "192.168.1.1:80"),
            MockFinding("Vuln B", "medium", "10.0.0.1:443"),
        ]
        result = self.engine.compare(current, previous)
        assert len(result) == 2
        assert all(f.delta_status == "fixed" for f in result)

    def test_mixed_scenario(self):
        """Mixed scenario with new, existing, fixed, and regressed findings."""
        current = [
            MockFinding("Vuln A", "high", "host:80"),       # existing
            MockFinding("Vuln C", "critical", "host:443"),  # regressed (was high)
            MockFinding("Vuln D", "medium", "host:22"),     # new
        ]
        previous = [
            MockFinding("Vuln A", "high", "host:80"),       # existing
            MockFinding("Vuln B", "low", "host:8080"),      # fixed
            MockFinding("Vuln C", "high", "host:443"),      # regressed
        ]

        result = self.engine.compare(current, previous)
        result_statuses = {f.title: f.delta_status for f in result}

        assert result_statuses["Vuln A"] == "existing"
        assert result_statuses["Vuln C"] == "regressed"
        assert result_statuses["Vuln D"] == "new"
        assert result_statuses["Vuln B"] == "fixed"
        assert len(result) == 4