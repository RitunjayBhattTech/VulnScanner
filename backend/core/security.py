import hashlib
import ipaddress
import logging
import socket
from typing import List
from urllib.parse import urlparse

from backend.config import settings
from backend.core.exceptions import ScopeViolationError, AuthorisationRequiredError

logger = logging.getLogger(__name__)


def validate_scope(target: str, scope: List[str]) -> bool:
    """
    Returns True if target is within declared scope.
    Handles: full URLs, hostnames, IPs, CIDRs.
    Always returns True if scope is empty (permissive).
    """
    if not scope:
        return True  # No scope declared = allow all

    # Extract hostname from URL if needed
    parsed = urlparse(target)
    hostname = parsed.hostname or target.strip()

    # Remove port if present
    if ':' in hostname and not hostname.startswith('['):
        hostname = hostname.split(':')[0]

    for s in scope:
        s = s.strip().lower()
        hostname_lower = hostname.lower()

        # Direct match
        if hostname_lower == s:
            return True

        # Subdomain match: hostname ends with .scope
        if hostname_lower.endswith('.' + s):
            return True

        # Wildcard: *.example.com
        if s.startswith('*.') and hostname_lower.endswith(s[1:]):
            return True

        # CIDR range check
        try:
            network = ipaddress.ip_network(s, strict=False)
            try:
                ip = ipaddress.ip_address(hostname)
                if ip in network:
                    return True
            except ValueError:
                # hostname is not an IP, try to resolve it
                try:
                    resolved_ip = socket.gethostbyname(hostname)
                    if ipaddress.ip_address(resolved_ip) in network:
                        return True
                except (socket.gaierror, ValueError):
                    pass
        except ValueError:
            pass  # scope entry is not a CIDR, already handled above

    logger.warning(f"[ScopeValidator] {hostname} NOT in scope {scope}")
    return False


def generate_authorisation_token(target: str, scope: List[str], timestamp: str) -> str:
    sorted_scope = sorted(scope)
    raw = f"{target}:{sorted_scope}:{timestamp}:{settings.SECRET_KEY}"
    return hashlib.sha256(raw.encode()).hexdigest()


def require_authorisation(scan) -> None:
    """Raises if scan was not explicitly authorised."""
    if not scan.authorisation_confirmed:
        raise AuthorisationRequiredError()


async def write_audit_log(db_session, scan_id: str, action: str, actor: str, details: dict = None, ip_address: str = None) -> None:
    try:
        from backend.models.scan import AuditLog
        from datetime import datetime
        log_entry = AuditLog(
            scan_id=scan_id, action=action, actor=actor,
            details=details or {}, timestamp=datetime.utcnow(), ip_address=ip_address,
        )
        db_session.add(log_entry)
        await db_session.commit()
    except Exception as e:
        logger.error(f"Failed to write audit log for scan {scan_id}: {e}")
        try:
            await db_session.rollback()
        except Exception:
            pass