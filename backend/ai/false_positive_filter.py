import json
import logging
from typing import Tuple

from backend.schemas.finding import RawFinding
from backend.ai.claude_client import llm_client, parse_llm_json

logger = logging.getLogger(__name__)

FP_SYSTEM_PROMPT = """You are a security analysis expert specializing in identifying false positive vulnerability findings. 
Analyze the given finding and determine the probability that it is a false positive.
Consider: scanner noise patterns, evidence quality, whether the finding makes sense for the technology detected, 
and whether the evidence convincingly demonstrates the vulnerability."""


class FalsePositiveFilter:
    """LLM-based false positive classifier for security findings."""

    async def assess(self, finding: RawFinding) -> Tuple[float, str]:
        """
        Assess the false positive probability of a finding.
        Returns (probability 0.0-1.0, reasoning).
        """
        user_prompt = f"""Analyze this security finding for false positive potential:

FINDING:
Title: {finding.title}
Severity: {finding.severity}
Description: {finding.description or 'N/A'}
Affected Component: {finding.affected_component or 'N/A'}
Evidence: {finding.evidence or 'N/A'}
Scanner: {finding.scanner_source}
CVE IDs: {', '.join(finding.cve_ids) if finding.cve_ids else 'None'}

Based on the evidence provided, determine the probability (0.0 to 1.0) that this finding is a false positive.
Return ONLY JSON:
{{
  "false_positive_probability": 0.0-1.0,
  "reasoning": "your analysis here"
}}"""

        try:
            response = await llm_client.complete(
                system=FP_SYSTEM_PROMPT,
                user=user_prompt,
                max_tokens=500,
            )

            if not response:
                return 0.1, "No AI assessment available (API not configured)"

            result = parse_llm_json(response)
            prob = float(result.get("false_positive_probability", 0.1))
            reasoning = result.get("reasoning", "AI analysis completed")
            return min(max(prob, 0.0), 1.0), reasoning

        except Exception as e:
            logger.warning(f"[FalsePositiveFilter] LLM call failed, using default: {e}")
            return 0.1, f"AI assessment unavailable. Defaulting to 0.1 probability. Error: {str(e)[:100]}"


# Global instance
false_positive_filter = FalsePositiveFilter()