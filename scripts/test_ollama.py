"""
Run this to verify Ollama is reachable from inside Docker.
Usage: docker compose exec backend python scripts/test_ollama.py
"""
import asyncio
import httpx
import sys
import os

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5")


async def test_connection():
    print(f"\n{'='*50}")
    print(f"  Ollama Connection Test")
    print(f"{'='*50}")
    print(f"  URL:   {OLLAMA_URL}")
    print(f"  Model: {MODEL}")
    print(f"{'='*50}\n")

    # Test 1: Can we reach Ollama?
    print("[1/3] Testing connection to Ollama...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            resp.raise_for_status()
            models = resp.json().get("models", [])
            model_names = [m["name"] for m in models]
            print(f"      ✅ Connected! Models available: {model_names}")
    except Exception as e:
        print(f"      ❌ FAILED: {e}")
        print(f"\n  SOLUTION: Make sure Ollama is running on your Windows machine.")
        print(f"  Open PowerShell and run: ollama serve")
        sys.exit(1)

    # Test 2: Is our model available?
    print(f"\n[2/3] Checking if model '{MODEL}' is available...")
    if any(MODEL in name for name in model_names):
        print(f"      ✅ Model '{MODEL}' is ready")
    else:
        print(f"      ❌ Model '{MODEL}' not found!")
        print(f"      Available models: {model_names}")
        print(f"      SOLUTION: Run in PowerShell: ollama pull {MODEL}")
        sys.exit(1)

    # Test 3: Can the model respond with JSON?
    print(f"\n[3/3] Testing LLM response (JSON output test)...")
    test_payload = {
        "model": MODEL,
        "stream": False,
        "options": {"num_predict": 100, "temperature": 0.1},
        "messages": [
            {
                "role": "system",
                "content": "You are a JSON API. Always respond with valid JSON only."
            },
            {
                "role": "user",
                "content": 'Respond with exactly this JSON: {"status": "ok", "message": "Ollama is working"}'
            }
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/chat", json=test_payload)
            resp.raise_for_status()
            content = resp.json()["message"]["content"]
            print(f"      ✅ Model responded: {content[:100]}")
    except Exception as e:
        print(f"      ❌ FAILED: {e}")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"  ✅ ALL TESTS PASSED — Ollama is ready for VulnAI Scanner")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    asyncio.run(test_connection())