import pytest


@pytest.fixture
def sample_scope():
    """Sample scope for testing."""
    return ["10.0.0.0/8", "192.168.1.0/24", "example.com"]


@pytest.fixture
def sample_finding_data():
    """Sample finding data for testing."""
    return {
        "title": "Test Finding",
        "description": "A test finding for unit tests",
        "severity": "medium",
        "affected_component": "192.168.1.1:80",
        "evidence": "Test evidence",
        "scanner_source": "test_scanner",
    }