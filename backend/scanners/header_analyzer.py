import logging
from typing import List, Dict

import httpx

from backend.scanners.base import BaseScanner
from backend.schemas.finding import RawFinding
from backend.core.security import validate_scope

logger = logging.getLogger(__name__)

# OWASP recommended security headers
SECURITY_HEADERS = {
    "Strict-Transport-Security": {
        "description": "HTTP Strict Transport Security enforces HTTPS connections",
        "recommended": True,
        "severity_missing": "high",
        "severity_misconfigured": "medium",
    },
    "Content-Security-Policy": {
        "description": "Content Security Policy prevents XSS and data injection attacks",
        "recommended": True,
        "severity_missing": "high",
        "severity_misconfigured": "medium",
    },
    "X-Frame-Options": {
        "description": "X-Frame-Options prevents clickjacking attacks",
        "recommended": True,
        "severity_missing": "medium",
        "severity_misconfigured": "low",
    },
    "X-Content-Type-Options": {
        "description": "X-Content-Type-Options prevents MIME type sniffing",
        "recommended": True,
        "severity_missing": "medium",
        "severity_misconfigured": "low",
    },
    "Referrer-Policy": {
        "description": "Referrer-Policy controls how much referrer information is sent",
        "recommended": True,
        "severity_missing": "low",
        "severity_misconfigured": "low",
    },
    "Permissions-Policy": {
        "description": "Permissions-Policy controls which browser features can be used",
        "recommended": True,
        "severity_missing": "low",
        "severity_misconfigured": "low",
    },
}

DEPRECATED_HEADERS = {
    "X-XSS-Protection": {
        "description": "X-XSS-Protection is deprecated and should be removed",
        "severity_present": "informational",
    },
}


class HeaderAnalyzer(BaseScanner):
    """HTTP security header analyzer that checks for OWASP-recommended headers."""

    def get_scanner_name(self) -> str:
        return "header_analyzer"

    async def run(self) -> List[RawFinding]:
        findings = []

        try:
            validate_scope(self.target, self.scope)

            async with self.rate_limiter.limit():
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    response = await client.get(self.target)
                    headers = dict(response.headers)

                    # Check for recommended headers
                    for header, config in SECURITY_HEADERS.items():
                        if header not in headers:
                            findings.append(RawFinding(
                                title=f"Missing Security Header: {header}",
                                description=f"{config['description']}. This header is missing from the response.",
                                severity=config["severity_missing"],
                                affected_component=self.target,
                                evidence=f"Header '{header}' not found in response headers",
                                scanner_source=self.get_scanner_name(),
                            ))
                        else:
                            # Basic validation of header values
                            value = headers[header]
                            if header == "Strict-Transport-Security" and "max-age=0" in value:
                                findings.append(RawFinding(
                                    title=f"Misconfigured Security Header: {header}",
                                    description=f"HSTS is set with max-age=0, effectively disabling it.",
                                    severity=config["severity_misconfigured"],
                                    affected_component=self.target,
                                    evidence=f"{header}: {value}",
                                    scanner_source=self.get_scanner_name(),
                                ))

                    # Check for deprecated headers
                    for header, config in DEPRECATED_HEADERS.items():
                        if header in headers:
                            findings.append(RawFinding(
                                title=f"Deprecated Header Present: {header}",
                                description=config["description"],
                                severity=config["severity_present"],
                                affected_component=self.target,
                                evidence=f"{header}: {headers[header]}",
                                scanner_source=self.get_scanner_name(),
                            ))

                    if not findings:
                        findings.append(RawFinding(
                            title="Security Headers Check Passed",
                            description="All OWASP-recommended security headers are present and properly configured.",
                            severity="informational",
                            affected_component=self.target,
                            scanner_source=self.get_scanner_name(),
                        ))

        except httpx.RequestError as e:
            logger.error(f"Header analyzer HTTP error for {self.target}: {e}")
            findings.append(RawFinding(
                title="Header Analyzer Error",
                description=f"Could not connect to {self.target}: {str(e)}",
                severity="informational",
                affected_component=self.target,
                scanner_source=self.get_scanner_name(),
            ))
        except Exception as e:
            logger.error(f"Header analyzer error: {e}", exc_info=True)

        return findings