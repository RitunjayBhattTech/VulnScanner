import asyncio
import logging
from typing import List

from backend.scanners.base import BaseScanner
from backend.schemas.finding import RawFinding
from backend.core.security import validate_scope

logger = logging.getLogger(__name__)


class PortScanner(BaseScanner):
    """Nmap port scanner wrapper using python-nmap."""

    def get_scanner_name(self) -> str:
        return "port_scanner"

    async def run(self) -> List[RawFinding]:
        findings = []
        try:
            # Validate scope
            validate_scope(self.target, self.scope)

            import nmap

            nm = nmap.PortScannerAsync()

            def callback_result(host, scan_result):
                if scan_result is None:
                    return
                for proto in scan_result.get("tcp", {}):
                    port_info = scan_result["tcp"][proto]
                    if port_info["state"] != "open":
                        continue
                    finding = RawFinding(
                        title=f"Open Port: {host}:{proto} ({port_info.get('name', 'unknown')})",
                        description=f"Port {proto} is open on {host}. "
                                    f"Service: {port_info.get('product', '')} "
                                    f"v{port_info.get('version', '')} "
                                    f"({port_info.get('extrainfo', '')})",
                        severity="informational",
                        affected_component=f"{host}:{proto}",
                        evidence=str(port_info),
                        scanner_source=self.get_scanner_name(),
                    )
                    findings.append(finding)

            # Use polite timing -T2
            nm.scan(hosts=self.target, arguments="-sV -sC -T2 --open", callback=callback_result)
            while nm.still_scanning():
                await asyncio.sleep(1)

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