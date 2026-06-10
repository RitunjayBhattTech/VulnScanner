import json
import re
from typing import Any, Dict, List, Optional
import httpx


class OllamaClient:
    def __init__(self, base_url: str = "http://ollama:11434"):
        self.base_url = base_url
        self.model = "mistral:7b"  # Use colon notation for Ollama model names

    def _build_prompt(self, findings: List[Dict[str, Any]], cve_context: List[Dict[str, Any]]) -> str:
        findings_json = json.dumps(findings, indent=2)
        return (
            "You are a senior penetration tester. Below is a JSON array of raw scan findings. "
            "For each finding, assign a CVSSv3 score (0.0-10.0), map severity (critical/high/medium/low/info), "
            "evaluate false positive likelihood with reasoning, and provide exploitation notes.\n\n"
            "Additionally, identify multi-step attack chains across related findings. "
            "An attack chain chains two or more findings together (e.g. an open port + a vulnerable service version).\n\n"
            "Return ONLY valid JSON (no markdown, no code fences) with this structure:\n"
            "{\n"
            '  "findings": [\n'
            "    {\n"
            '      "host": "<ip>",\n'
            '      "port": <port>,\n'
            '      "cvss_score": <float>,\n'
            '      "severity": "<critical|high|medium|low|info>",\n'
            '      "false_positive_reasoning": "<explanation or null>",\n'
            '      "exploitation_notes": "<how this could be exploited or null>",\n'
            '      "attack_chain_id": <int or null>\n'
            "    }\n"
            "  ],\n"
            '  "attack_chains": [\n'
            "    {\n"
            '      "chain_id": <int>,\n'
            '      "description": "<description of the attack chain>",\n'
            '      "hosts": ["<ip1>", "<ip2>"],\n'
            '      "severity": "<critical|high|medium|low>",\n'
            '      "likelihood": "<high|medium|low>",\n'
            '      "mitre_technique_id": "<MITRE ID or null>"\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            f"Scan findings:\n{findings_json}\n\n"
            f"CVE context:\n{json.dumps(cve_context, indent=2)}"
        )

    def analyze_findings(self, findings: List[Dict[str, Any]], cve_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send findings to Ollama for AI analysis using the /api/chat endpoint.
        Returns a parsed dict with 'findings' and 'attack_chains' keys.
        """
        prompt = self._build_prompt(findings, cve_context)

        # Use Ollama native /api/chat endpoint (OpenAI compatibility layer is unreliable)
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "options": {
                "temperature": 0.2,
                "num_predict": 2048,
            },
            "stream": False,
        }

        try:
            with httpx.Client(base_url=self.base_url, timeout=300.0) as client:
                response = client.post("/api/chat", json=payload)
                response.raise_for_status()
                raw = response.json()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Ollama API error: {exc.response.status_code} - {exc.response.text[:500]}") from exc
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"Ollama request timed out after 300s") from exc
        except Exception as exc:
            raise RuntimeError(f"Ollama request failed: {str(exc)}") from exc

        # Extract message content from Ollama chat response
        try:
            message_content = raw.get("message", {}).get("content", "")
        except (KeyError, TypeError):
            message_content = ""

        return self._parse_ai_response(message_content, findings)

    def _parse_ai_response(self, response_text: str, original_findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse the AI's JSON response, with fallback to keyword-based severity extraction.
        Returns a dict with 'findings' (enriched) and 'attack_chains' (from AI or empty).
        """
        # Try to extract JSON from the response (handle markdown-wrapped JSON)
        json_str = response_text.strip()
        # Remove markdown code fences if present
        json_str = re.sub(r'^```(?:json)?\s*', '', json_str)
        json_str = re.sub(r'\s*```$', '', json_str)

        parsed = None
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError:
            # Try to find JSON object between braces
            match = re.search(r'\{.*\}', json_str, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                except json.JSONDecodeError:
                    parsed = None

        # Build enriched findings list
        enriched_findings = []
        attack_chains = []

        if parsed and isinstance(parsed, dict):
            # Process AI-structured findings
            ai_findings = parsed.get("findings", [])
            ai_chains = parsed.get("attack_chains", [])

            for original in original_findings:
                # Match by host + port
                matched = None
                for af in ai_findings:
                    if (af.get("host") == original.get("host") and
                            af.get("port") == original.get("port")):
                        matched = af
                        break

                enriched = dict(original)
                if matched:
                    enriched["ai_severity"] = matched.get("severity", "medium")
                    enriched["ai_cvss_score"] = matched.get("cvss_score", 5.0)
                    enriched["ai_false_positive_reasoning"] = matched.get("false_positive_reasoning")
                    enriched["ai_exploitation_notes"] = matched.get("exploitation_notes")
                    enriched["attack_chain_id"] = matched.get("attack_chain_id")
                else:
                    enriched["ai_severity"] = "medium"
                    enriched["ai_cvss_score"] = 5.0
                    enriched["ai_false_positive_reasoning"] = None
                    enriched["ai_exploitation_notes"] = None
                    enriched["attack_chain_id"] = None

                enriched_findings.append(enriched)

            # Process attack chains
            for chain in ai_chains:
                attack_chains.append({
                    "chain_description": chain.get("description", ""),
                    "steps": chain.get("hosts", []),
                    "severity": chain.get("severity", "medium"),
                    "likelihood": chain.get("likelihood", "medium"),
                    "mitre_technique_id": chain.get("mitre_technique_id"),
                })
        else:
            # Fallback: keyword-based severity extraction (when AI output is malformed)
            for original in original_findings:
                enriched = dict(original)
                text_lower = response_text.lower()
                if "critical" in text_lower:
                    enriched["ai_severity"] = "critical"
                    enriched["ai_cvss_score"] = 9.5
                elif "high" in text_lower:
                    enriched["ai_severity"] = "high"
                    enriched["ai_cvss_score"] = 7.5
                elif "medium" in text_lower:
                    enriched["ai_severity"] = "medium"
                    enriched["ai_cvss_score"] = 5.0
                elif "low" in text_lower:
                    enriched["ai_severity"] = "low"
                    enriched["ai_cvss_score"] = 2.5
                else:
                    enriched["ai_severity"] = "info"
                    enriched["ai_cvss_score"] = 0.0
                enriched["ai_false_positive_reasoning"] = None
                enriched["ai_exploitation_notes"] = None
                enriched["attack_chain_id"] = None
                enriched_findings.append(enriched)

        return {
            "findings": enriched_findings,
            "attack_chains": attack_chains,
        }