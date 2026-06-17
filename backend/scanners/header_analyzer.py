import logging
from typing import List
from urllib.parse import urlparse

import httpx

from backend.scanners.base import BaseScanner
from backend.schemas.finding import RawFinding
from backend.core.security import validate_scope

logger = logging.getLogger(__name__)

SECURITY_HEADERS = {
    'strict-transport-security': {
        'name': 'Missing HSTS Header',
        'desc': 'Strict-Transport-Security header is missing. Browsers may allow HTTP connections.',
        'severity': 'medium',
        'recommendation': 'Add: Strict-Transport-Security: max-age=31536000; includeSubDomains'
    },
    'content-security-policy': {
        'name': 'Missing Content-Security-Policy',
        'desc': 'No CSP header found. The site is vulnerable to XSS attacks.',
        'severity': 'medium',
        'recommendation': "Add: Content-Security-Policy: default-src 'self'"
    },
    'x-frame-options': {
        'name': 'Missing X-Frame-Options',
        'desc': 'X-Frame-Options header is missing. Site may be vulnerable to clickjacking.',
        'severity': 'low',
        'recommendation': 'Add: X-Frame-Options: DENY'
    },
    'x-content-type-options': {
        'name': 'Missing X-Content-Type-Options',
        'desc': 'X-Content-Type-Options header missing. MIME sniffing attacks possible.',
        'severity': 'low',
        'recommendation': 'Add: X-Content-Type-Options: nosniff'
    },
    'referrer-policy': {
        'name': 'Missing Referrer-Policy',
        'desc': 'Referrer-Policy header is missing.',
        'severity': 'informational',
        'recommendation': 'Add: Referrer-Policy: strict-origin-when-cross-origin'
    },
    'permissions-policy': {
        'name': 'Missing Permissions-Policy',
        'desc': 'Permissions-Policy header is missing.',
        'severity': 'informational',
        'recommendation': 'Add: Permissions-Policy: geolocation=(), camera=(), microphone=()'
    },
}


class HeaderAnalyzer(BaseScanner):
    """HTTP security header analyzer that checks for OWASP-recommended headers."""

    def get_scanner_name(self) -> str:
        return "header_analyzer"

    async def run(self) -> List[RawFinding]:
        findings = []

        # Ensure URL has scheme
        target = self.target
        if not target.startswith(('http://', 'https://')):
            target = 'http://' + target

        try:
            validate_scope(self.target, self.scope)
        except Exception as e:
            logger.warning(f"[HeaderAnalyzer] Scope validation: {e}")
            return findings

        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                verify=False,
                headers={'User-Agent': 'VulnAI-Scanner/1.0 (Authorised Security Testing)'}
            ) as client:
                logger.info(f"[HeaderAnalyzer] Checking headers for {target}")
                response = await client.get(target)
                response_headers = {k.lower(): v for k, v in response.headers.items()}
                logger.info(f"[HeaderAnalyzer] Got {len(response_headers)} headers, status {response.status_code}")

                # Check each security header
                for header_key, config in SECURITY_HEADERS.items():
                    if header_key not in response_headers:
                        findings.append(RawFinding(
                            title=config['name'],
                            description=config['desc'],
                            severity=config['severity'],
                            affected_component=target,
                            evidence=f"Header '{header_key}' not present in response.\nPresent headers: {', '.join(sorted(response_headers.keys())[:15])}",
                            scanner_source=self.get_scanner_name(),
                        ))

                # Check for server header (information disclosure)
                if 'server' in response_headers:
                    server = response_headers['server']
                    findings.append(RawFinding(
                        title='Server Version Disclosed',
                        description=f'The Server header reveals software version: {server}',
                        severity='informational',
                        affected_component=target,
                        evidence=f'Server: {server}',
                        scanner_source=self.get_scanner_name(),
                    ))

                logger.info(f"[HeaderAnalyzer] Found {len(findings)} header issues")

        except httpx.RequestError as e:
            logger.error(f"[HeaderAnalyzer] HTTP error for {target}: {e}")
            findings.append(RawFinding(
                title="Header Analyzer Error",
                description=f"Could not connect to {target}: {str(e)}",
                severity="informational",
                affected_component=self.target,
                scanner_source=self.get_scanner_name(),
            ))
        except Exception as e:
            logger.error(f"[HeaderAnalyzer] Error: {e}", exc_info=True)

        return findings