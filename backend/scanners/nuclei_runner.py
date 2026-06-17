import asyncio
import json
import logging
import os
import shutil
from typing import List

from backend.scanners.base import BaseScanner
from backend.schemas.finding import RawFinding
from backend.core.security import validate_scope

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
    """Nuclei CLI wrapper with graceful fallback if nuclei is not installed."""

    def get_scanner_name(self) -> str:
        return "nuclei"

    async def run(self) -> List[RawFinding]:
        findings = []

        try:
            validate_scope(self.target, self.scope)
        except Exception as e:
            logger.error(f"[Nuclei] Scope validation failed: {e}")
            return findings

        # Check if nuclei is installed
        nuclei_path = shutil.which("nuclei")
        if not nuclei_path:
            logger.warning("[Nuclei] nuclei binary not found — skipping nuclei scan")
            return findings

        output_file = f"/tmp/nuclei_{self.scan_id}.json"
        cmd = [
            "nuclei",
            "-u", self.target,
            "-json-export", output_file,
            "-rate-limit", "10",
            "-silent",
            "-timeout", "10",
            "-retries", "1",
            "-t", "http/misconfiguration/",
            "-t", "http/exposures/",
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(proc.communicate(), timeout=300)
        except asyncio.TimeoutError:
            logger.warning("[Nuclei] Scan timed out after 5 minutes")
            try:
                proc.kill()
            except Exception:
                pass
        except Exception as e:
            logger.error(f"[Nuclei] Failed to run: {e}")
            return findings

        if os.path.exists(output_file):
            try:
                with open(output_file) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            item = json.loads(line)
                            severity = SEVERITY_MAP.get(
                                item.get("info", {}).get("severity", "unknown").lower(),
                                "informational"
                            )
                            cve_ids_raw = item.get("info", {}).get("classification", {}).get("cve-id", []) or []
                            if isinstance(cve_ids_raw, str):
                                cve_ids = [cve_ids_raw]
                            elif isinstance(cve_ids_raw, list):
                                cve_ids = cve_ids_raw
                            else:
                                cve_ids = []
                            findings.append(RawFinding(
                                title=item.get("info", {}).get("name", "Nuclei Finding"),
                                description=item.get("info", {}).get("description", ""),
                                severity=severity,
                                affected_component=item.get("matched-at", self.target),
                                evidence=str(item.get("extracted-results", "")),
                                scanner_source=self.get_scanner_name(),
                                cve_ids=cve_ids,
                            ))
                        except json.JSONDecodeError:
                            continue
            finally:
                try:
                    os.remove(output_file)
                except Exception:
                    pass

        return findings