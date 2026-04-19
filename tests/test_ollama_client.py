"""Tests voor de OllamaClient HTTP-laag."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from ollama.client import OllamaClient

_DUMMY_URL = "http://localhost:11434/api/generate"


def _mock_response(status_code: int = 200, body: dict | None = None, url: str = _DUMMY_URL) -> httpx.Response:
    """Maak een nep-httpx Response object met een request zodat raise_for_status() werkt."""
    request = httpx.Request("POST", url)
    content = json.dumps(body or {}).encode()
    return httpx.Response(status_code, content=content, request=request)


# ─────────────────────────────────────────────────────────
# generate()
# ─────────────────────────────────────────────────────────

class TestOllamaClientGenerate:
    @pytest.fixture
    def client(self):
        return OllamaClient(base_url="http://localhost:11434")

    @pytest.mark.asyncio
    async def test_generate_returns_response_text(self, client):
        mock_resp = _mock_response(200, {"response": "Hallo wereld!"})
        client._http = AsyncMock()
        client._http.post = AsyncMock(return_value=mock_resp)

        result = await client.generate("Zeg hallo", model="llama3")
        assert result == "Hallo wereld!"

    @pytest.mark.asyncio
    async def test_generate_sends_correct_payload(self, client):
        mock_resp = _mock_response(200, {"response": "OK"})
        client._http = AsyncMock()
        client._http.post = AsyncMock(return_value=mock_resp)

        await client.generate("test prompt", model="mistral", system="Je bent een expert.", temperature=0.3)

        call_kwargs = client._http.post.call_args
        payload = call_kwargs.kwargs["json"]
        assert payload["model"] == "mistral"
        assert payload["prompt"] == "test prompt"
        assert payload["system"] == "Je bent een expert."
        assert payload["options"]["temperature"] == 0.3

    @pytest.mark.asyncio
    async def test_generate_without_system_omits_system_key(self, client):
        mock_resp = _mock_response(200, {"response": "OK"})
        client._http = AsyncMock()
        client._http.post = AsyncMock(return_value=mock_resp)

        await client.generate("prompt zonder system")

        payload = client._http.post.call_args.kwargs["json"]
        assert "system" not in payload

    @pytest.mark.asyncio
    async def test_generate_empty_response_returns_empty_string(self, client):
        mock_resp = _mock_response(200, {})
        client._http = AsyncMock()
        client._http.post = AsyncMock(return_value=mock_resp)

        result = await client.generate("test")
        assert result == ""

    @pytest.mark.asyncio
    async def test_generate_http_error_raises(self, client):
        mock_resp = _mock_response(500, {"error": "Internal Server Error"})
        client._http = AsyncMock()
        client._http.post = AsyncMock(return_value=mock_resp)

        with pytest.raises(httpx.HTTPStatusError):
            await client.generate("test")


# ─────────────────────────────────────────────────────────
# chat()
# ─────────────────────────────────────────────────────────

class TestOllamaClientChat:
    @pytest.fixture
    def client(self):
        return OllamaClient(base_url="http://localhost:11434")

    def _chat_response(self, body: dict) -> httpx.Response:
        return httpx.Response(
            200,
            content=json.dumps(body).encode(),
            request=httpx.Request("POST", "http://localhost:11434/api/chat"),
        )

    @pytest.mark.asyncio
    async def test_chat_returns_message_content(self, client):
        mock_resp = self._chat_response({"message": {"content": "Chat antwoord!"}})
        client._http = AsyncMock()
        client._http.post = AsyncMock(return_value=mock_resp)

        messages = [{"role": "user", "content": "Hallo"}]
        result = await client.chat(messages, model="llama3")
        assert result == "Chat antwoord!"

    @pytest.mark.asyncio
    async def test_chat_sends_correct_format(self, client):
        mock_resp = self._chat_response({"message": {"content": "OK"}})
        client._http = AsyncMock()
        client._http.post = AsyncMock(return_value=mock_resp)

        messages = [
            {"role": "system", "content": "Je bent een assistent."},
            {"role": "user", "content": "Vraag"},
        ]
        await client.chat(messages, model="mistral", temperature=0.5)

        payload = client._http.post.call_args.kwargs["json"]
        assert payload["messages"] == messages
        assert payload["model"] == "mistral"
        assert payload["stream"] is False

    @pytest.mark.asyncio
    async def test_chat_empty_response_returns_empty_string(self, client):
        mock_resp = self._chat_response({"message": {}})
        client._http = AsyncMock()
        client._http.post = AsyncMock(return_value=mock_resp)

        result = await client.chat([{"role": "user", "content": "test"}])
        assert result == ""


# ─────────────────────────────────────────────────────────
# is_available() + list_models()
# ─────────────────────────────────────────────────────────

class TestOllamaClientAvailability:
    @pytest.fixture
    def client(self):
        return OllamaClient(base_url="http://localhost:11434")

    @pytest.mark.asyncio
    async def test_is_available_returns_true_on_200(self, client):
        mock_resp = _mock_response(200, {"models": []}, url="http://localhost:11434/api/tags")
        mock_resp = httpx.Response(200, content=b'{"models":[]}', request=httpx.Request("GET", "http://localhost:11434/api/tags"))
        client._http = AsyncMock()
        client._http.get = AsyncMock(return_value=mock_resp)

        assert await client.is_available() is True

    @pytest.mark.asyncio
    async def test_is_available_returns_false_on_connection_error(self, client):
        client._http = AsyncMock()
        client._http.get = AsyncMock(side_effect=httpx.ConnectError("Ollama niet bereikbaar"))

        assert await client.is_available() is False

    @pytest.mark.asyncio
    async def test_list_models_parses_names(self, client):
        body = {"models": [{"name": "llama3:latest"}, {"name": "mistral:latest"}]}
        mock_resp = httpx.Response(
            200,
            content=json.dumps(body).encode(),
            request=httpx.Request("GET", "http://localhost:11434/api/tags"),
        )
        client._http = AsyncMock()
        client._http.get = AsyncMock(return_value=mock_resp)

        models = await client.list_models()
        assert "llama3:latest" in models
        assert "mistral:latest" in models
        assert len(models) == 2

    @pytest.mark.asyncio
    async def test_list_models_empty_when_no_models(self, client):
        mock_resp = httpx.Response(
            200,
            content=b'{"models":[]}',
            request=httpx.Request("GET", "http://localhost:11434/api/tags"),
        )
        client._http = AsyncMock()
        client._http.get = AsyncMock(return_value=mock_resp)

        assert await client.list_models() == []
