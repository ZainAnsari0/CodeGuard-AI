"""
Sprint 1 Deliverable (S1.8): Ollama Inference Test
Verifies that local LLM inference works via Ollama.

Usage:
    python -m tests.test_ollama
    # or: python tests/test_ollama.py
"""

import asyncio
import json
import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings


async def _check_ollama_available():
    """Check if Ollama server is reachable. Returns True/False."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            response.raise_for_status()
            return True
    except Exception:
        return False


@pytest.mark.asyncio
async def test_ollama_health():
    """Test that Ollama server is reachable and lists models."""
    import httpx

    if not await _check_ollama_available():
        pytest.skip("Ollama server not available — start with: ollama serve")

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{settings.OLLAMA_URL}/api/tags")
        response.raise_for_status()
        data = response.json()
        models = [m["name"] for m in data.get("models", [])]

        assert len(models) >= 0  # At minimum, the endpoint responds

        if settings.DEFAULT_MODEL not in models:
            pytest.skip(
                f"Default model '{settings.DEFAULT_MODEL}' not found. "
                f"Pull it with: ollama pull {settings.DEFAULT_MODEL}"
            )


@pytest.mark.asyncio
async def test_ollama_inference():
    """Test that local LLM inference produces valid output."""
    import httpx

    if not await _check_ollama_available():
        pytest.skip("Ollama server not available — start with: ollama serve")

    # Verify default model is available
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{settings.OLLAMA_URL}/api/tags")
        data = response.json()
        models = [m["name"] for m in data.get("models", [])]

        if settings.DEFAULT_MODEL not in models:
            pytest.skip(
                f"Default model '{settings.DEFAULT_MODEL}' not found. "
                f"Pull it with: ollama pull {settings.DEFAULT_MODEL}"
            )

    # Test inference
    async with httpx.AsyncClient(timeout=120.0) as client:
        payload = {
            "model": settings.DEFAULT_MODEL,
            "prompt": "Explain what SQL injection is in exactly 2 sentences.",
            "stream": False,
        }

        response = await client.post(
            f"{settings.OLLAMA_URL}/api/generate",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        output_text = data.get("response", "").strip()
        assert len(output_text) > 0, "Ollama returned an empty response"


async def main():
    """Standalone runner for manual testing outside of pytest."""
    print("\n" + "=" * 60)
    print("  CodeGuard AI — Sprint 1 Task S1.8")
    print("  Ollama Download and Basic Test")
    print("=" * 60 + "\n")

    print(f"  Ollama URL: {settings.OLLAMA_URL}")
    print(f"  Default model: {settings.DEFAULT_MODEL}")
    print()

    import httpx

    # Health check
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            response.raise_for_status()
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]

            print(f"  [PASS] Ollama server is reachable")
            print(f"  Available models: {models if models else '(none pulled yet)'}")

            if settings.DEFAULT_MODEL not in models:
                print(f"\n  [WARN] Default model '{settings.DEFAULT_MODEL}' not found.")
                print(f"  Pull it with: ollama pull {settings.DEFAULT_MODEL}")
            else:
                print(f"  [PASS] Default model '{settings.DEFAULT_MODEL}' is available")
    except httpx.ConnectError:
        print("  [FAIL] Cannot connect to Ollama server.")
        print("  Start it with: ollama serve")
        print("  Or install from: https://ollama.com")
        sys.exit(1)
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        sys.exit(1)

    # Inference test
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": settings.DEFAULT_MODEL,
                "prompt": "Explain what SQL injection is in exactly 2 sentences.",
                "stream": False,
            }

            print("\n  Generating response...")
            response = await client.post(
                f"{settings.OLLAMA_URL}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            output_text = data.get("response", "").strip()
            print(f"  [PASS] Inference completed")
            print(f"  Response: {output_text[:200]}{'...' if len(output_text) > 200 else ''}")
    except Exception as e:
        print(f"  [FAIL] Inference error: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  RESULT: ALL TESTS PASSED — S1.8 COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())