import asyncio
import json
import logging
from typing import List

from backend.scanners.base import BaseScanner
from backend.schemas.finding import RawFinding
from backend.core.security import validate_scope
from backend.core.exceptions import ToolNotInstalledError

logger = logging.getLogger(__name__)

SEVERITY_MAP = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "info": "informational",
    "unknown": "informational",
}


class NucleiRunner(BaseScanner):
    """Nuclei CLI wrapper for template-based vulnerability scanning."""

    def get_scanner_name(self) -> str:
        return "nuclei"

    async def run(self) -> List[RawFinding]:
        findings = []

        try:
            validate_scope(self.target, self.scope)

            # Check if nuclei is installed
            proc = await asyncio.create_subprocess_exec(
                "nuclei", "-version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            if proc.returncode != 0:
                raise ToolNotInstalledError(
                    "nuclei",
                    "Install from: https://github.com/projectdiscovery/nuclei#installation"
                )

            # Run nuclei scan with JSON output
            cmd = [
                "nuclei",
                "-target", self.target,
                "-t", "cves/",
                "-t", "vulnerabilities/",
                "-t", "misconfiguration/",
                "-t", "exposures/",
                "-json",
                "-silent",
                "-rate-limit", "10",
                "-timeout", "30",
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if stdout:
                for line in stdout.decode().strip().split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        result = json.loads(line)
                        severity = SEVERITY_MAP.get(
                            result.get("info", {}).get("severity", "unknown").lower(),
                            "informational"
                        )
                        finding = RawFinding(
                            title=result.get("info", {}).get("name", "Unknown Nuclei Finding"),
                            description=result.get("info", {}).get("description", ""),
                            severity=severity,
                            affected_component=result.get("host", self.target),
                            evidence=json.dumps(result, indent=2),
                            cve_ids=result.get("info", {}).get("classification", {}).get("cve-id", []) if isinstance(result.get("info", {}).get("classification", {}).get("cve-id", []), list) else [result.get("info", {}).get("classification", {}).get("cve-id", "")],
                            cwe_ids=result.get("info", {}).get("classification", {}).get("cwe-id", []) if isinstance(result.get("info", {}).get("classification", {}).get("cwe-id", []), list) else [result.get("info", {}).get("classification", {}).get("cwe-id", "")],
                            scanner_source=self.get_scanner_name(),
                        )
                        findings.append(finding)
                    except json.JSONDecodeError:
                        continue

            if stderr:
                logger.warning(f"Nuclei stderr: {stderr.decode()}")

        except FileNotFoundError:
            raise ToolNotInstalledError(
                "nuclei",
                "Install from: https://github.com/projectdiscovery/nuclei#installation"
            )
        except Exception as e:
            logger.error(f"Nuclei runner error: {e}", exc_info=True)

        return findings