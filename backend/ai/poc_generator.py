import logging
from typing import Optional

from backend.config import settings
from backend.schemas.finding import TriagedFinding
from backend.ai.claude_client import llm_client

logger = logging.getLogger(__name__)

POC_SYSTEM_PROMPT = """You are a security researcher in a CONTROLLED, AUTHORISED testing environment.
Generate a proof-of-concept (PoC) concept for the given vulnerability. The PoC must be:
1. Clearly labelled as for AUTHORISED TESTING ONLY
2. Include a disclaimer that unauthorised use is illegal
3. Focus on verification, not exploitation
4. Include steps to detect and verify the vulnerability safely

DO NOT generate actual exploit code that could damage systems."""


class PoCGenerator:
    """Proof-of-Concept concept generator. DISABLED by default - requires ENABLE_POC_GENERATION=true."""

    async def generate_poc(self, finding: TriagedFinding) -> Optional[str]:
        """
        Generate a PoC concept for a finding.
        Returns None if PoC generation is disabled.
        """
        if not settings.ENABLE_POC_GENERATION:
            return None

        user_prompt = f"""FINDING:
Title: {finding.title}
Severity: {finding.adjusted_severity}
Description: {finding.description or 'N/A'}
Affected Component: {finding.affected_component or 'N/A'}
Evidence: {finding.evidence or 'N/A'}

Generate a proof-of-concept that verifies this vulnerability exists.
The PoC MUST:
1. Include a clear WARNING label that this is for authorised testing only
2. Be non-destructive
3. Clearly show how to verify the vulnerability
4. Include expected output if the vulnerability is present

Respond with a formatted PoC that a security engineer could use to verify this finding."""

        try:
            response = await llm_client.complete(
                system=POC_SYSTEM_PROMPT,
                user=user_prompt,
                max_tokens=2000,
            )
            return response
        except Exception as e:
            logger.error(f"PoC generator error: {e}")
            return None