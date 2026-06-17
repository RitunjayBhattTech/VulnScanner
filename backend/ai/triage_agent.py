import json
import logging
from typing import Optional

from backend.schemas.finding import RawFinding, TriagedFinding
from backend.ai.claude_client import llm_client, parse_llm_json
from backend.ai.rag_pipeline import rag_pipeline

logger = logging.getLogger(__name__)

TRIAGE_SYSTEM_PROMPT = """You are a senior penetration tester and vulnerability analyst. You triage security findings by assessing real exploitability, not just CVSS scores. Consider network exposure, authentication requirements, and actual reachability."""


class TriageAgent:
    """LLM-based finding triage and prioritization."""

    async def triage_finding(
        self,
        finding: RawFinding,
        scan_context: dict,
    ) -> Optional[TriagedFinding]:
        """
        Triage a raw finding using AI analysis enriched with RAG context.
        Returns a TriagedFinding or None on failure.
        """
        try:
            # Get RAG context
            rag_context = await rag_pipeline.get_context_for_finding(finding)

            exposure = scan_context.get("exposure", "unknown")
            authenticated = scan_context.get("authenticated", False)
            previous_count = scan_context.get("previous_count", 0)

            user_prompt = f"""FINDING:
Title: {finding.title}
Original Severity: {finding.severity}
CVSS Score: {finding.cvss_score or 'N/A'}
Description: {finding.description or 'N/A'}
Affected Component: {finding.affected_component or 'N/A'}
Evidence: {finding.evidence or 'N/A'}
Scanner: {finding.scanner_source}

SCAN CONTEXT:
Target Exposure: {exposure} (internet-facing / internal-only / unknown)
Authenticated Scan: {authenticated}
Previous occurrences: {previous_count} times in prior scans

RELEVANT CVE/CWE/OWASP CONTEXT:
{rag_context}

Your task:
1. Assess the REAL exploitability of this finding given the context (not just the theoretical CVSS score)
2. Consider: Is this finding actually reachable? Is authentication required? Is there a known public exploit?
3. Determine if the severity should be adjusted UP or DOWN from the original
4. Assess business impact (data breach? service disruption? lateral movement?)

Respond ONLY in this exact JSON format, with no preamble:
{{
  "adjusted_severity": "critical|high|medium|low|informational",
  "severity_changed": true/false,
  "severity_change_reason": "explanation if changed, null if not",
  "exploitability_notes": "2-3 sentences on real-world exploitability",
  "business_impact": "1-2 sentences on business risk",
  "contextual_notes": "any other analyst notes",
  "recommended_priority": 1-10
}}"""

            response = await llm_client.complete(
                system=TRIAGE_SYSTEM_PROMPT,
                user=user_prompt,
                max_tokens=1024,
            )

            if not response:
                return None

            result = parse_llm_json(response)

            adjusted = result.get("adjusted_severity", finding.severity)
            severity_changed = result.get("severity_changed", False)

            return TriagedFinding(
                title=finding.title,
                description=finding.description,
                severity=finding.severity,
                adjusted_severity=adjusted,
                severity_changed=severity_changed,
                severity_change_reason=result.get("severity_change_reason"),
                cvss_score=finding.cvss_score,
                cve_ids=finding.cve_ids,
                cwe_ids=finding.cwe_ids,
                affected_component=finding.affected_component,
                evidence=finding.evidence,
                ai_triage_notes=result.get("contextual_notes", ""),
                exploitability_notes=result.get("exploitability_notes", ""),
                business_impact=result.get("business_impact", ""),
                contextual_notes=result.get("contextual_notes", ""),
                false_positive_probability=0.0,
                recommended_priority=result.get("recommended_priority", 5),
                scanner_source=finding.scanner_source,
            )

        except Exception as e:
            logger.warning(f"[Triage] LLM call failed, using default triage: {e}")
            return TriagedFinding(
                title=finding.title,
                description=finding.description,
                severity=finding.severity,
                adjusted_severity=finding.severity,
                severity_changed=False,
                severity_change_reason=None,
                cvss_score=finding.cvss_score,
                cve_ids=finding.cve_ids,
                cwe_ids=finding.cwe_ids,
                affected_component=finding.affected_component,
                evidence=finding.evidence,
                ai_triage_notes="Automated triage unavailable. Manual review required.",
                ai_remediation=None,
                exploitability_notes="Automated triage unavailable. Manual review required.",
                business_impact="Unknown — manual assessment needed.",
                contextual_notes=f"LLM triage failed: {str(e)[:100]}",
                false_positive_probability=0.0,
                is_false_positive=False,
                recommended_priority=5,
                scanner_source=finding.scanner_source,
                delta_status=None,
            )


# Global instance
triage_agent = TriageAgent()