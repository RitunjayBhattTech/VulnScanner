import pytest
from backend.core.security import validate_scope, _validate_ip_in_scope, _validate_domain_in_scope
from backend.core.exceptions import ScopeViolationError


class TestScopeValidator:
    """Tests for the scope validator function."""

    def test_ip_inside_declared_cidr(self):
        """IP inside declared CIDR should pass."""
        result = validate_scope("192.168.1.50", ["192.168.1.0/24"])
        assert result is True

    def test_ip_outside_declared_cidr(self):
        """IP outside declared CIDR should raise ScopeViolationError."""
        with pytest.raises(ScopeViolationError):
            validate_scope("10.0.0.1", ["192.168.1.0/24"])

    def test_subdomain_of_declared_domain(self):
        """Subdomain of declared domain should pass."""
        result = validate_scope("sub.example.com", ["example.com"])
        assert result is True

    def test_completely_different_domain(self):
        """Completely different domain should raise ScopeViolationError."""
        with pytest.raises(ScopeViolationError):
            validate_scope("evil.com", ["example.com"])

    def test_empty_scope_list(self):
        """Empty scope list should raise ScopeViolationError."""
        with pytest.raises(ScopeViolationError):
            validate_scope("192.168.1.1", [])

    def test_url_target_with_protocol(self):
        """URL with protocol should be parsed and validated correctly."""
        result = validate_scope("https://example.com/page", ["example.com"])
        assert result is True

    def test_multiple_scope_entries_ip_match(self):
        """Multiple scope entries - IP matching first CIDR."""
        result = validate_scope("10.0.0.5", ["10.0.0.0/8", "192.168.0.0/16"])
        assert result is True

    def test_multiple_scope_entries_domain_match(self):
        """Multiple scope entries - domain matching second entry."""
        result = validate_scope("test.example.com", ["10.0.0.0/8", "example.com"])
        assert result is True

    def test_exact_ip_match_in_scope(self):
        """Exact IP match should pass."""
        result = validate_scope("10.0.0.1", ["10.0.0.1", "192.168.0.0/16"])
        assert result is True

    def test_domain_mismatch_with_similar_name(self):
        """Similar but different domain should fail."""
        with pytest.raises(ScopeViolationError):
            validate_scope("notexample.com", ["example.com"])