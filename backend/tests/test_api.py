"""
Tests voor de VorstersNV AI Backend.

Vereisten voor lokaal testen:
    pip install pytest pytest-asyncio httpx
    Zorg dat Ollama en ChromaDB draaien (via docker compose up ollama chromadb).
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Root endpoint geeft toepassingsinformatie terug."""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "applicatie" in data
    assert "versie" in data


def test_health_endpoint_structuur():
    """Health endpoint geeft de verwachte velden terug (ook als services offline zijn)."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "ollama_bereikbaar" in data
    assert "chroma_bereikbaar" in data
    assert "modellen_beschikbaar" in data


def test_chat_zonder_documenten():
    """Chat-endpoint werkt met gebruik_documenten=False (mock LLM)."""
    with patch("app.services.rag.get_llm") as mock_llm:
        mock_instantie = MagicMock()
        mock_instantie.model = "llama3:8b"
        mock_instantie.invoke.return_value = "Testantwoord van de mock LLM."
        mock_llm.return_value = mock_instantie

        resp = client.post(
            "/chat/",
            json={"vraag": "Wat is de openingstijd?", "gebruik_documenten": False},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "antwoord" in data
        assert data["antwoord"] == "Testantwoord van de mock LLM."
        assert data["bronnen"] == []


def test_document_upload_ongeldig_type():
    """Upload van een niet-ondersteund bestandstype geeft HTTP 415."""
    resp = client.post(
        "/documenten/upload",
        files=[("bestanden", ("test.exe", b"binaire inhoud", "application/octet-stream"))],
    )
    assert resp.status_code == 415


def test_document_upload_geen_bestanden():
    """Upload zonder bestanden geeft HTTP 422 (validatiefout)."""
    resp = client.post("/documenten/upload")
    assert resp.status_code == 422
