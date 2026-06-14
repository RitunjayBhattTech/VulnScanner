import asyncio
import json
import logging
from typing import List

from backend.scanners.base import BaseScanner
from backend.schemas.finding import RawFinding
from backend.core.exceptions import ToolNotInstalledError

logger = logging.getLogger(__name__)


class SemgrepRunner(BaseScanner):
    """Semgrep CLI wrapper for static analysis (SAST). Only runs on local directory targets."""

    def get_scanner_name(self) -> str:
        return "semgrep"

    async def run(self) -> List[RawFinding]:
        findings = []

        try:
            # Only run if target is a local directory
            import os
            if not os.path.isdir(self.target):
                logger.info(f"Semgrep skipped: '{self.target}' is not a local directory")
                return findings

            # Check semgrep is installed
            proc = await asyncio.create_subprocess_exec(
                "semgrep", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            if proc.returncode != 0:
                raise ToolNotInstalledError(
                    "semgrep",
                    "Install with: pip install semgrep"
                )

            # Run semgrep with OWASP Top 10 + security rulesets
            cmd = [
                "semgrep",
                "--config", "p/owasp-top-ten",
                "--config", "p/python",
                "--config", "p/javascript",
                "--config", "p/secrets",
                "--json",
                "--quiet",
                self.target,
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if stdout:
                try:
                    result = json.loads(stdout.decode())
                    for semgrep_result in result.get("results", []):
                        severity = semgrep_result.get("extra", {}).get("severity", "WARNING").lower()
                        if severity == "warning":
                            severity = "medium"
                        elif severity == "error":
                            severity = "high"
                        elif severity == "info":
                            severity = "informational"
                        else:
                            severity = "medium"

                        path = semgrep_result.get("path", "")
                        line = semgrep_result.get("start", {}).get("line", 0)
                        finding = RawFinding(
                            title=semgrep_result.get("check_id", "Semgrep Finding").split(".")[-1],
                            description=semgrep_result.get("extra", {}).get("message", ""),
                            severity=severity,
                            affected_component=f"{path}:{line}",
                            evidence=semgrep_result.get("extra", {}).get("lines", "") or json.dumps({
                                "path": path,
                                "line": line,
                                "check_id": semgrep_result.get("check_id"),
                                "message": semgrep_result.get("extra", {}).get("message"),
                            }),
                            cwe_ids=[semgrep_result.get("extra", {}).get("metadata", {}).get("cwe", "")],
                            scanner_source=self.get_scanner_name(),
                        )
                        findings.append(finding)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse semgrep JSON output")

            if stderr:
                logger.warning(f"Semgrep stderr: {stderr.decode()}")

        except FileNotFoundError:
            raise ToolNotInstalledError(
                "semgrep",
                "Install with: pip install semgrep"
            )
        except Exception as e:
            logger.error(f"Semgrep runner error: {e}", exc_info=True)

        return findings