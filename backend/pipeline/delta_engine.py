import logging
from typing import List

from backend.models.scan import Finding

logger = logging.getLogger(__name__)


class DeltaEngine:
    """
    Compares two scan results to determine what's new, fixed, or regressed.
    Two findings are considered the "same" if they share the same affected_component + title (normalised).
    """

    @staticmethod
    def _normalise(text: str) -> str:
        """Normalise a string for comparison."""
        return text.lower().strip()

    @staticmethod
    def _finding_key(finding) -> str:
        """Generate a unique key for a finding based on affected_component + title."""
        component = DeltaEngine._normalise(finding.affected_component or "")
        title = DeltaEngine._normalise(finding.title or "")
        return f"{component}:{title}"

    @staticmethod
    def _severity_weight(severity: str) -> int:
        """Convert severity string to numeric weight for comparison."""
        weights = {
            "critical": 5,
            "high": 4,
            "medium": 3,
            "low": 2,
            "informational": 1,
        }
        return weights.get(severity.lower(), 0)

    def compare(
        self,
        current_findings: List[Finding],
        previous_findings: List[Finding],
    ) -> List[Finding]:
        """
        Compare current findings to previous findings and update delta_status.
        Returns current findings with delta_status set appropriately, plus synthetic
        entries for findings that were fixed.
        """
        if not previous_findings:
            # All findings are new
            for finding in current_findings:
                finding.delta_status = "new"
            return current_findings

        # Build lookup of previous findings
        previous_map = {}
        for pf in previous_findings:
            key = self._finding_key(pf)
            if key not in previous_map:
                previous_map[key] = pf

        # Build lookup of current findings
        current_map = {}
        for cf in current_findings:
            key = self._finding_key(cf)
            if key not in current_map:
                current_map[key] = cf

        # Process current findings
        result = []
        for finding in current_findings:
            key = self._finding_key(finding)
            prev = previous_map.get(key)

            if prev is None:
                finding.delta_status = "new"
            else:
                # Check if severity increased
                current_weight = self._severity_weight(finding.severity)
                prev_weight = self._severity_weight(prev.severity)

                if current_weight > prev_weight:
                    finding.delta_status = "regressed"
                else:
                    finding.delta_status = "existing"

            result.append(finding)

        # Find fixed findings (in previous but not in current)
        for key, prev_finding in previous_map.items():
            if key not in current_map:
                # Create synthetic finding to show what was fixed
                from backend.models.scan import Finding as FindingModel
                from datetime import datetime

                fixed_finding = FindingModel(
                    title=prev_finding.title,
                    description=prev_finding.description,
                    severity=prev_finding.severity,
                    cvss_score=prev_finding.cvss_score,
                    cve_ids=prev_finding.cve_ids,
                    cwe_ids=prev_finding.cwe_ids,
                    affected_component=prev_finding.affected_component,
                    evidence=prev_finding.evidence,
                    scanner_source=prev_finding.scanner_source,
                    delta_status="fixed",
                    is_false_positive=False,
                    created_at=datetime.utcnow(),
                )
                result.append(fixed_finding)

        return result