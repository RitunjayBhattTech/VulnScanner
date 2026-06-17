import asyncio
import logging
import shutil
from typing import List
from urllib.parse import urlparse

from backend.scanners.base import BaseScanner
from backend.schemas.finding import RawFinding
from backend.core.security import validate_scope
from backend.core.exceptions import ScopeViolationError

logger = logging.getLogger(__name__)


class PortScanner(BaseScanner):
    """Nmap port scanner wrapper using python-nmap with asyncio.to_thread."""

    def get_scanner_name(self) -> str:
        return "port_scanner"

    async def run(self) -> List[RawFinding]:
        findings = []

        # Verify nmap is available
        nmap_path = shutil.which("nmap")
        if not nmap_path:
            logger.error("[PortScanner] nmap not found in container PATH")
            return []

        # Extract hostname from URL if full URL was provided
        parsed = urlparse(self.target)
        nmap_target = parsed.hostname or self.target
        logger.info(f"[PortScanner] nmap found at {nmap_path}, scanning {nmap_target}")

        try:
            import nmap

            scanner = nmap.PortScanner()

            # Validate scope first
            if not validate_scope(self.target, self.scope):
                raise ScopeViolationError(f"Target {self.target} is outside declared scope")

            # Run nmap in a thread (blocking call)
            logger.info(f"[PortScanner] Scanning host: {nmap_target}")
            await asyncio.to_thread(
                scanner.scan,
                nmap_target,
                arguments="-sV -T2 --open -p 21,22,23,25,53,80,443,445,3306,3389,8080,8443"
            )

            for host in scanner.all_hosts():
                for proto in scanner[host].all_protocols():
                    for port in scanner[host][proto].keys():
                        service = scanner[host][proto][port]
                        if service['state'] == 'open':
                            findings.append(RawFinding(
                                title=f"Open Port: {port}/{proto} ({service.get('name', 'unknown')})",
                                description=f"Port {port} is open running {service.get('name','unknown')} {service.get('version','')}",
                                severity="informational",
                                affected_component=f"{host}:{port}",
                                evidence=f"Service: {service.get('name','')} {service.get('version','')} {service.get('extrainfo','')}",
                                scanner_source=self.get_scanner_name()
                            ))

        except ScopeViolationError:
            raise
        except Exception as e:
            logger.error(f"Port scanner error for {self.target}: {e}", exc_info=True)
            findings.append(RawFinding(
                title="Port Scanner Error",
                description=f"Port scanner encountered an error: {str(e)}",
                severity="informational",
                affected_component=self.target,
                scanner_source=self.get_scanner_name(),
            ))

        return findings