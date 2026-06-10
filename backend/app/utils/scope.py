import ipaddress

from app.core.config import settings


def enforce_scope(target_scope: str) -> None:
    allowed = settings.allowed_scopes.strip()
    if not allowed:
        return

    try:
        requested = ipaddress.ip_network(target_scope, strict=False)
        allowed_networks = [ipaddress.ip_network(item.strip(), strict=False) for item in allowed.split(",") if item.strip()]
    except ValueError as exc:
        raise ValueError(f"Invalid scope declaration: {exc}") from exc

    if not any(requested.subnet_of(network) or requested == network for network in allowed_networks):
        raise ValueError("Target scope is outside the authorized scanning range.")
