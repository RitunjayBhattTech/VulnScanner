import pytest
from backend.schemas.finding import RawFinding


class TestPortScanner:
    """Tests for the PortScanner (unit tests without actual nmap)."""

    def test_raw_finding_creation(self):
        """Test that RawFinding can be created with expected fields."""
        finding = RawFinding(
            title="Open Port: 127.0.0.1:80 (http)",
            description="Port 80 is open on 127.0.0.1.",
            severity="informational",
            affected_component="127.0.0.1:80",
            evidence="{'state': 'open', 'name': 'http'}",
            scanner_source="port_scanner",
        )
        assert finding.title == "Open Port: 127.0.0.1:80 (http)"
        assert finding.severity == "informational"
        assert finding.scanner_source == "port_scanner"
        assert finding.affected_component == "127.0.0.1:80"