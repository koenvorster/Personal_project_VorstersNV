"""
VorstersNV Ollama Client
Lokale AI-integratie via Ollama voor agent-aanroepen.
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Generator

import httpx

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("OLLAMA_DEFAULT_MODEL", "llama3")


class OllamaClient:
    """Client voor communicatie met de lokale Ollama instantie."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self._http = httpx.AsyncClient(timeout=360.0)

    async def is_available(self) -> bool:
        """Controleer of Ollama beschikbaar is."""
        try:
            response = await self._http.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """Geef een lijst van beschikbare modellen terug."""
        response = await self._http.get(f"{self.base_url}/api/tags")
        response.raise_for_status()
        data = response.json()
        return [m["name"] for m in data.get("models", [])]

    async def generate(
        self,
        prompt: str,
        model: str = DEFAULT_MODEL,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> str:
        """
        Genereer een antwoord van Ollama.

        Args:
            prompt: De gebruikersvraag of input
            model: Het te gebruiken model (bijv. llama3, mistral)
            system: System prompt
            temperature: Temperatuur (0.0 = deterministisch, 1.0 = creatief)
            max_tokens: Maximum aantal tokens in het antwoord
            stream: Of het antwoord gestreamd moet worden

        Returns:
            Het gegenereerde antwoord als string
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        logger.debug("Ollama aanroep: model=%s temperature=%s", model, temperature)

        response = await self._http.post(
            f"{self.base_url}/api/generate",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """
        Chat-interface voor multi-turn gesprekken.

        Args:
            messages: Lijst van berichten in chat-formaat
                      [{"role": "user/assistant/system", "content": "..."}]
            model: Het te gebruiken model
            temperature: Temperatuur instelling
            max_tokens: Maximum tokens

        Returns:
            Het antwoord van de assistent
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        response = await self._http.post(
            f"{self.base_url}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "")

    async def close(self):
        """Sluit de HTTP-client."""
        await self._http.aclose()


# Singleton client
_client: OllamaClient | None = None


def get_client() -> OllamaClient:
    """Geef de singleton Ollama client terug."""
    global _client
    if _client is None:
        _client = OllamaClient()
    return _client
