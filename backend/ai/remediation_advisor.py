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
        # Load prompt from file
        import os
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "remediation_prompt.txt")
        try:
            with open(prompt_path) as f:
                prompt_template = f.read()
        except FileNotFoundError:
            prompt_template = "Generate a brief remediation for finding: {title} at {affected_component}. Tech: {tech_stack}"
        
        user_prompt = prompt_template.format(
            title=finding.title,
            adjusted_severity=finding.adjusted_severity,
            affected_component=finding.affected_component or "N/A",
            description=finding.description or "No description",
            tech_stack=", ".join(tech_stack) if tech_stack else "Unknown",
        )

        try:
            response = await llm_client.complete(
                system=REMEDIATION_SYSTEM_PROMPT,
                user=user_prompt,
                max_tokens=300,
            )

            if response:
                return response
            return "Remediation advice not available (API not configured)."

        except Exception as e:
            logger.warning(f"[Remediation] LLM call failed, using default remediation: {e}")
            return "## Remediation\nRemediation advice could not be generated automatically due to an AI service error.\n\n## Recommended Actions\n1. Manually research this vulnerability class for your technology stack.\n2. Apply security best practices for the affected component.\n3. Verify the fix with appropriate security testing tools."


# Global instance
remediation_advisor = RemediationAdvisor()