import asyncio
import logging
import ssl
import socket
from datetime import datetime, timezone
from typing import List

from backend.scanners.base import BaseScanner
from backend.schemas.finding import RawFinding
from backend.core.security import validate_scope

logger = logging.getLogger(__name__)

# Weak cipher suites as defined by various standards
WEAK_CIPHERS = [
    "RC4", "DES", "3DES", "MD5", "EXPORT", "NULL", "anon",
    "IDEA", "SEED", "CAMELLIA_128", "CAMELLIA_256",
]


class SSLChecker(BaseScanner):
    """SSL/TLS certificate analyzer that checks expiry, cipher suites, protocol versions."""

    def get_scanner_name(self) -> str:
        return "ssl_checker"

    async def run(self) -> List[RawFinding]:
        findings = []

        try:
            validate_scope(self.target, self.scope)

            # Extract hostname from target
            from urllib.parse import urlparse
            parsed = urlparse(self.target)
            hostname = parsed.hostname or self.target
            port = parsed.port or 443

            # Get certificate
            cert_info = await self._get_certificate_info(hostname, port)

            if not cert_info:
                findings.append(RawFinding(
                    title="SSL Certificate Not Found",
                    description=f"Could not retrieve SSL certificate for {hostname}:{port}",
                    severity="medium",
                    affected_component=f"{hostname}:{port}",
                    scanner_source=self.get_scanner_name(),
                ))
                return findings

            # Check expiry
            await self._check_expiry(hostname, cert_info, findings)

            # Check TLS version
            await self._check_tls_version(hostname, port, findings)

            # Check certificate chain
            await self._check_certificate_chain(hostname, port, findings)

        except Exception as e:
            logger.error(f"SSL checker error: {e}", exc_info=True)
            findings.append(RawFinding(
                title="SSL Checker Error",
                description=f"SSL checker encountered an error: {str(e)}",
                severity="informational",
                affected_component=self.target,
                scanner_source=self.get_scanner_name(),
            ))

        return findings

    async def _get_certificate_info(self, hostname: str, port: int) -> dict:
        """Retrieve SSL certificate information."""
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            loop = asyncio.get_event_loop()
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(hostname, port, ssl=ctx),
                timeout=15.0,
            )

            sock = writer.transport.get_extra_info("ssl_object")
            if sock:
                cert = sock.getpeercert()
                cipher = sock.cipher()
                version = sock.version()
                writer.close()
                return {
                    "cert": cert,
                    "cipher": cipher,
                    "version": version,
                }
            writer.close()
            return None
        except Exception as e:
            logger.warning(f"Could not get certificate for {hostname}:{port}: {e}")
            return None

    async def _check_expiry(self, hostname: str, cert_info: dict, findings: List[RawFinding]):
        """Check certificate expiry date."""
        cert = cert_info.get("cert", {})
        if not cert:
            return

        not_after_str = cert.get("notAfter", "")
        if not not_after_str:
            return

        try:
            # Parse the date string
            not_after = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            days_left = (not_after - now).days

            if days_left < 0:
                findings.append(RawFinding(
                    title=f"SSL Certificate Expired",
                    description=f"SSL certificate for {hostname} expired {abs(days_left)} days ago.",
                    severity="high",
                    affected_component=hostname,
                    evidence=f"Expired on: {not_after_str}",
                    scanner_source=self.get_scanner_name(),
                ))
            elif days_left < 7:
                findings.append(RawFinding(
                    title=f"SSL Certificate Expiring Soon ({days_left} days)",
                    description=f"SSL certificate for {hostname} expires in {days_left} days.",
                    severity="high",
                    affected_component=hostname,
                    evidence=f"Expires on: {not_after_str}",
                    scanner_source=self.get_scanner_name(),
                ))
            elif days_left < 30:
                findings.append(RawFinding(
                    title=f"SSL Certificate Expiring in {days_left} days",
                    description=f"SSL certificate for {hostname} expires in {days_left} days.",
                    severity="medium",
                    affected_component=hostname,
                    evidence=f"Expires on: {not_after_str}",
                    scanner_source=self.get_scanner_name(),
                ))
        except Exception as e:
            logger.warning(f"Error parsing certificate expiry: {e}")

    async def _check_tls_version(self, hostname: str, port: int, findings: List[RawFinding]):
        """Check TLS protocol version."""
        for version_name, tls_version in [
            ("TLS 1.0", ssl.TLSVersion.TLSv1),
            ("TLS 1.1", ssl.TLSVersion.TLSv1_1),
        ]:
            try:
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ctx.minimum_version = tls_version
                ctx.maximum_version = tls_version
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                loop = asyncio.get_event_loop()
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(hostname, port, ssl=ctx),
                    timeout=10.0,
                )
                writer.close()

                findings.append(RawFinding(
                    title=f"Outdated TLS Version: {version_name}",
                    description=f"{hostname} supports {version_name}, which is deprecated and insecure.",
                    severity="high",
                    affected_component=f"{hostname}:{port}",
                    evidence=f"Server accepted connection using {version_name}",
                    scanner_source=self.get_scanner_name(),
                ))
            except Exception:
                continue

    async def _check_certificate_chain(self, hostname: str, port: int, findings: List[RawFinding]):
        """Check certificate chain validity."""
        try:
            ctx = ssl.create_default_context()
            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                asyncio.open_connection(hostname, port, ssl=ctx),
                timeout=10.0,
            )
        except ssl.SSLCertVerificationError as e:
            findings.append(RawFinding(
                title="SSL Certificate Verification Failed",
                description=f"SSL certificate chain verification failed for {hostname}: {str(e)}",
                severity="high",
                affected_component=f"{hostname}:{port}",
                evidence=str(e),
                scanner_source=self.get_scanner_name(),
            ))
        except Exception:
            pass