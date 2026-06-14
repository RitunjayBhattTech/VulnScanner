import hashlib
import ipaddress
import logging
from typing import List
from urllib.parse import urlparse

from backend.config import settings
from backend.core.exceptions import ScopeViolationError, AuthorisationRequiredError

logger = logging.getLogger(__name__)


def validate_scope(target: str, scope: List[str]) -> bool:
    """Validate that a target is within the declared scope."""
    if not scope:
        raise ScopeViolationError(target, scope)

    parsed = urlparse(target)
    target_host = parsed.hostname or target

    try:
        target_ip = ipaddress.ip_address(target_host)
        return _validate_ip_in_scope(target_ip, scope)
    except ValueError:
        pass

    return _validate_domain_in_scope(target_host, scope)


def _validate_ip_in_scope(target_ip, scope: List[str]) -> bool:
    for scope_entry in scope:
        scope_entry = scope_entry.strip()
        try:
            network = ipaddress.ip_network(scope_entry, strict=False)
            if target_ip in network:
                return True
        except ValueError:
            continue
    raise ScopeViolationError(str(target_ip), scope)


def _validate_domain_in_scope(hostname: str, scope: List[str]) -> bool:
    hostname = hostname.lower().strip()
    for scope_entry in scope:
        scope_entry = scope_entry.lower().strip()
        try:
            ipaddress.ip_address(scope_entry)
            if hostname == scope_entry:
                return True
            continue
        except ValueError:
            pass
        try:
            ipaddress.ip_network(scope_entry, strict=False)
            continue
        except ValueError:
            pass
        if hostname == scope_entry or hostname.endswith("." + scope_entry):
            return True
    raise ScopeViolationError(hostname, scope)


def generate_authorisation_token(target: str, scope: List[str], timestamp: str) -> str:
    sorted_scope = sorted(scope)
    raw = f"{target}:{sorted_scope}:{timestamp}:{settings.SECRET_KEY}"
    return hashlib.sha256(raw.encode()).hexdigest()


def require_authorisation(scan) -> None:
    if not scan.authorisation_confirmed:
        raise AuthorisationRequiredError()
    if not scan.authorisation_token:
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