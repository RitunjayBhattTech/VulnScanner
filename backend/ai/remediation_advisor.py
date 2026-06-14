import logging
from typing import List

from backend.schemas.finding import TriagedFinding
from backend.ai.claude_client import llm_client

logger = logging.getLogger(__name__)

REMEDIATION_SYSTEM_PROMPT = """You are a senior security engineer. A vulnerability has been found in a system you are responsible for fixing. Generate specific, actionable remediation advice with actual code/config snippets."""


class RemediationAdvisor:
    """LLM-based remediation suggestion generator."""

    async def generate_remediation(
        self,
        finding: TriagedFinding,
        tech_stack: List[str],
    ) -> str:
        """
        Generate a remediation guide for a finding.
        Returns formatted markdown with immediate mitigation, permanent fix, and verification steps.
        """
        user_prompt = f"""FINDING:
Title: {finding.title}
Severity: {finding.adjusted_severity}
Description: {finding.description or 'N/A'}
Affected Component: {finding.affected_component or 'N/A'}
Evidence: {finding.evidence or 'N/A'}
CVE IDs: {', '.join(finding.cve_ids) if finding.cve_ids else 'None'}
CWE IDs: {', '.join(finding.cwe_ids) if finding.cwe_ids else 'None'}

DETECTED TECHNOLOGY STACK:
{', '.join(tech_stack) if tech_stack else 'Unknown'}

Generate a remediation guide with exactly three sections:

## Immediate Mitigation
What can be done RIGHT NOW to reduce risk, even before a full fix (e.g. WAF rule, disable feature, restrict access). Be specific to the technology stack above.

## Permanent Fix
Provide the actual fix. If this is a code issue, write the corrected code snippet. If this is a configuration issue, write the corrected config. Be specific to the technology stack. Include library versions where relevant.

## Verification
Explain exactly how to verify the fix worked. Include a specific command, HTTP request, or test case the engineer can run.

Keep the total response under 500 words. Be direct and technical. No boilerplate."""

        try:
            response = await llm_client.complete(
                system=REMEDIATION_SYSTEM_PROMPT,
                user=user_prompt,
                max_tokens=1500,
            )

            if response:
                return response
            return "Remediation advice not available (API not configured)."

        except Exception as e:
            logger.error(f"Remediation advisor error: {e}")
            return f"Error generating remediation: {str(e)}"


# Global instance
remediation_advisor = RemediationAdvisor()