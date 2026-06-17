import asyncio
import logging
import ssl
import socket
from datetime import datetime, timezone
from typing import List
from urllib.parse import urlparse

from backend.scanners.base import BaseScanner
from backend.schemas.finding import RawFinding

logger = logging.getLogger(__name__)


class SSLChecker(BaseScanner):
    """SSL/TLS certificate analyzer with robust error handling."""

    def get_scanner_name(self) -> str:
        return "ssl_checker"

    async def run(self) -> List[RawFinding]:
        findings = []

        target = self.target
        parsed = urlparse(target if '://' in target else 'https://' + target)
        hostname = parsed.hostname or target
        port = parsed.port or 443

        # Only check SSL for HTTPS or port 443
        if parsed.scheme == 'http' and port != 443:
            findings.append(RawFinding(
                title='No HTTPS / SSL Not Configured',
                description=f'The target {target} is using plain HTTP with no SSL/TLS encryption.',
                severity='high',
                affected_component=target,
                evidence='Protocol: HTTP (no SSL)',
                scanner_source=self.get_scanner_name(),
            ))
            return findings

        def _check_ssl():
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            try:
                with socket.create_connection((hostname, port), timeout=15) as sock:
                    with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        cipher = ssock.cipher()
                        version = ssock.version()
                        return cert, cipher, version
            except Exception as e:
                return None, None, str(e)

        try:
            cert, cipher, version = await asyncio.to_thread(_check_ssl)

            if cert is None:
                findings.append(RawFinding(
                    title='SSL Certificate Error',
                    description=f'Could not retrieve SSL certificate for {hostname}:{port}: {version}',
                    severity='medium',
                    affected_component=f'{hostname}:{port}',
                    evidence=f'Error: {version}',
                    scanner_source=self.get_scanner_name(),
                ))
                return findings

            # Check TLS version
            if version and version in ('TLSv1', 'TLSv1.1', 'SSLv2', 'SSLv3'):
                findings.append(RawFinding(
                    title=f'Deprecated TLS Version: {version}',
                    description=f'Server supports {version} which is deprecated and insecure.',
                    severity='high',
                    affected_component=f'{hostname}:{port}',
                    evidence=f'TLS Version: {version}',
                    scanner_source=self.get_scanner_name(),
                ))

            # Check cert expiry
            if cert and 'notAfter' in cert:
                expiry = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                days_left = (expiry - now).days

                if days_left < 0:
                    findings.append(RawFinding(
                        title='SSL Certificate Expired',
                        description=f'The SSL certificate expired {abs(days_left)} days ago on {cert["notAfter"]}.',
                        severity='critical',
                        affected_component=f'{hostname}:{port}',
                        evidence=f'Certificate expired: {cert["notAfter"]}\nDays overdue: {abs(days_left)}',
                        scanner_source=self.get_scanner_name(),
                    ))
                elif days_left < 30:
                    findings.append(RawFinding(
                        title=f'SSL Certificate Expires in {days_left} Days',
                        description=f'Certificate will expire on {cert["notAfter"]} ({days_left} days).',
                        severity='high' if days_left < 14 else 'medium',
                        affected_component=f'{hostname}:{port}',
                        evidence=f'Expiry: {cert["notAfter"]}\nDays remaining: {days_left}',
                        scanner_source=self.get_scanner_name(),
                    ))
                else:
                    # Certificate is valid
                    findings.append(RawFinding(
                        title='SSL Certificate Valid',
                        description=f'SSL certificate is valid for {days_left} more days.',
                        severity='informational',
                        affected_component=f'{hostname}:{port}',
                        evidence=f'Expiry: {cert["notAfter"]}\nDays remaining: {days_left}\nTLS: {version}',
                        scanner_source=self.get_scanner_name(),
                    ))

            logger.info(f"[SSLChecker] Found {len(findings)} SSL issues for {hostname}:{port}")

        except Exception as e:
            logger.error(f"[SSLChecker] Error checking {hostname}:{port}: {e}")
            findings.append(RawFinding(
                title='SSL Check Failed',
                description=f'Could not complete SSL check: {str(e)}',
                severity='informational',
                affected_component=f'{hostname}:{port}',
                evidence=str(e),
                scanner_source=self.get_scanner_name(),
            ))

        return findings