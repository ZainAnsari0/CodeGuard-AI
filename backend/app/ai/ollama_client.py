"""
CodeGuard AI - Ollama Client
Local LLM inference client for code analysis and explanation.
"""

import json
import logging
import socket
from typing import Optional, Dict, Any, List
from ipaddress import ip_address, ip_network
from urllib.parse import urlparse

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Allowed Ollama hosts (local inference only)
_ALLOWED_OLLAMA_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _validate_ollama_url(url: str) -> str:
    """Validate Ollama URL to prevent SSRF attacks.

    Resolves the hostname and verifies ALL resolved IPs are in the
    loopback/private range. Rejects any hostname that resolves to a
    non-local IP, preventing DNS rebinding and hex-encoded IP bypasses.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    # Quick check: allowlisted hostnames pass without DNS resolution
    if hostname in _ALLOWED_OLLAMA_HOSTS:
        return url

    # Resolve hostname and verify all IPs are loopback/private
    try:
        addr_infos = socket.getaddrinfo(hostname, parsed.port or 11434, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise ValueError(f"Ollama URL hostname could not be resolved: {hostname}")

    _loopback_networks = [
        ip_network("127.0.0.0/8"),
        ip_network("::1/128"),
        ip_network("10.0.0.0/8"),
        ip_network("172.16.0.0/12"),
        ip_network("192.168.0.0/16"),
        ip_network("fc00::/7"),
    ]

    for info in addr_infos:
        ip = ip_address(info[4][0])
        if not any(ip in net for net in _loopback_networks):
            raise ValueError(
                f"Ollama URL resolves to non-local IP {ip}, which is not allowed. "
                f"Hostname {hostname} must resolve to a loopback/private IP."
            )

    # If all resolved IPs are local, allow it
    return url


class OllamaClient:
    """Client for interacting with Ollama LLM inference server."""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        raw_url = (base_url or settings.OLLAMA_URL).rstrip("/")
        self.base_url = _validate_ollama_url(raw_url)
        self.model = model or settings.DEFAULT_MODEL
        self.timeout = 120.0
        self._client: Optional[httpx.AsyncClient] = None
        self.api_key = settings.OLLAMA_API_KEY

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the shared httpx client for connection reuse.

        Properly closes stale connections before creating a new client.
        """
        if self._client is not None:
            if not self._client.is_closed:
                return self._client
            # Close the stale client before creating a new one
            await self._client.aclose()

        # Prepare headers including Authorization if API key is configured
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self._client = httpx.AsyncClient(timeout=self.timeout, headers=headers)
        return self._client

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a response from the local LLM.

        Args:
            prompt: The input prompt
            model: Model name (defaults to configured model)
            system: System prompt for context
            stream: Whether to stream the response
            options: Additional generation options (temperature, top_p, etc.)

        Returns:
            Dictionary with response, model, and timing info
        """
        model = model or self.model
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
        }
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options

        client = await self._get_client()
        response = await client.post(
            f"{self.base_url}/api/generate",
            json=payload,
        )
        response.raise_for_status()

        if stream:
            full_response = ""
            async for line in response.aiter_lines():
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(f"Skipping malformed Ollama stream chunk: {line[:200]}")
                    continue
                full_response += chunk.get("response", "")
                if chunk.get("done", False):
                    return {
                        "response": full_response,
                        "model": chunk.get("model", model),
                        "total_duration": chunk.get("total_duration"),
                        "eval_count": chunk.get("eval_count"),
                    }
            return {"response": full_response, "model": model}
        else:
            return response.json()

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Chat-style interaction with the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name override
            options: Generation options

        Returns:
            Dictionary with response and metadata
        """
        model = model or self.model
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        if options:
            payload["options"] = options

        client = await self._get_client()
        response = await client.post(
            f"{self.base_url}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def check_health(self) -> Dict[str, Any]:
        """
        Check if Ollama server is running and accessible.

        Returns:
            Dictionary with available (bool), models (list), and error (str|None)
        """
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]

            logger.info(f"Ollama server available with models: {models}")
            return {
                "available": True,
                "models": models,
                "error": None,
            }
        except httpx.ConnectError:
            logger.warning("Ollama server not reachable — is it running?")
            return {
                "available": False,
                "models": [],
                "error": "Ollama server not reachable. Start it with: ollama serve",
            }
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return {
                "available": False,
                "models": [],
                "error": str(e),
            }

    async def pull_model(self, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Pull a model from the Ollama registry.

        Args:
            model: Model name to pull (defaults to configured model)

        Returns:
            Status dictionary
        """
        model = model or self.model
        try:
            client = await self._get_client()
            # Use extended timeout for model pulls
            response = await client.post(
                f"{self.base_url}/api/pull",
                json={"name": model, "stream": False},
                timeout=600.0,
            )
            response.raise_for_status()
            logger.info(f"Model {model} pulled successfully")
            return {"success": True, "model": model}
        except Exception as e:
            logger.error(f"Failed to pull model {model}: {e}")
            return {"success": False, "model": model, "error": str(e)}


# Singleton instance
ollama_client = OllamaClient()