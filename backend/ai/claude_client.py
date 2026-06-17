import json
import re
import asyncio
import logging
import httpx
from backend.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Universal LLM client. Supports Ollama, Anthropic, Groq, Gemini.
    All providers use the same interface:
        await client.complete(system="...", user="...", max_tokens=1024)
    """

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        logger.info(f"[LLM] Provider initialized: {self.provider}")

    async def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        if self.provider == "ollama":
            return await self._ollama(system, user, max_tokens)
        elif self.provider == "anthropic":
            return await self._anthropic(system, user, max_tokens)
        elif self.provider == "groq":
            return await self._groq(system, user, max_tokens)
        elif self.provider == "gemini":
            return await self._gemini(system, user, max_tokens)
        else:
            raise ValueError(f"Unknown LLM_PROVIDER: {self.provider}. "
                             f"Valid options: ollama, anthropic, groq, gemini")

    # ─────────────────────────────────────────────────────────────
    # OLLAMA
    # ─────────────────────────────────────────────────────────────
    async def _ollama(self, system: str, user: str, max_tokens: int) -> str:
        url = f"{settings.OLLAMA_BASE_URL}/api/chat"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.1,   # low temp = more consistent JSON output
            },
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
        }
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(
                        connect=10.0,
                        read=120.0,
                        write=10.0,
                        pool=5.0
                    )
                ) as client:
                    logger.info(f"[Ollama] Sending request to {url} (attempt {attempt+1})")
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    content = data["message"]["content"]
                    logger.info(f"[Ollama] Response received ({len(content)} chars)")
                    return content
            except httpx.ConnectError:
                logger.error(
                    f"[Ollama] Cannot connect to {settings.OLLAMA_BASE_URL}. "
                    f"Is Ollama running on your host? Run: ollama serve"
                )
                raise RuntimeError(
                    f"Cannot reach Ollama at {settings.OLLAMA_BASE_URL}. "
                    f"Make sure Ollama is running on your Windows machine."
                )
            except httpx.HTTPStatusError as e:
                logger.warning(f"[Ollama] HTTP error attempt {attempt+1}: {e}")
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise RuntimeError(f"Ollama HTTP error after 3 attempts: {e}")
            except Exception as e:
                logger.error(f"[Ollama] Unexpected error: {e}")
                if attempt < 2:
                    await asyncio.sleep(2)
                else:
                    raise

        raise RuntimeError("Ollama failed after 3 retries")

    # ─────────────────────────────────────────────────────────────
    # ANTHROPIC
    # ─────────────────────────────────────────────────────────────
    async def _anthropic(self, system: str, user: str, max_tokens: int) -> str:
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is not set in .env")

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        for attempt in range(3):
            try:
                resp = await client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=max_tokens,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
                return resp.content[0].text
            except anthropic.RateLimitError:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt * 5)
        raise RuntimeError("Anthropic failed after 3 retries")

    # ─────────────────────────────────────────────────────────────
    # GROQ
    # ─────────────────────────────────────────────────────────────
    async def _groq(self, system: str, user: str, max_tokens: int) -> str:
        try:
            from groq import AsyncGroq
        except ImportError:
            raise ImportError("groq package not installed. Run: pip install groq")

        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in .env")

        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        resp = await client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
        )
        return resp.choices[0].message.content

    # ─────────────────────────────────────────────────────────────
    # GEMINI
    # ─────────────────────────────────────────────────────────────
    async def _gemini(self, system: str, user: str, max_tokens: int) -> str:
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")

        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in .env")

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system,
        )
        resp = await asyncio.to_thread(
            model.generate_content,
            user,
            generation_config={"max_output_tokens": max_tokens},
        )
        return resp.text


def parse_llm_json(response: str) -> dict:
    """
    Safely extract and parse JSON from LLM output.
    Handles markdown code fences, extra text before/after JSON, etc.
    Returns empty dict on failure — never raises.
    """
    if not response:
        return {}

    # Strip markdown code fences
    cleaned = re.sub(r'^```(?:json)?\n?', '', response.strip())
    cleaned = re.sub(r'\n?```$', '', cleaned)

    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON object from within the text
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    logger.error(f"[LLM] Could not parse JSON from response: {response[:300]}")
    return {}


# Global singleton — import this everywhere
llm_client = LLMClient()