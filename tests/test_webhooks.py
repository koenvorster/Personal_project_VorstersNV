"""Tests voor de webhook FastAPI applicatie."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from webhooks.app import app

MOCK_AGENT_RESPONSE = "Dit is een testantwoord van de agent."


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.fixture(autouse=True)
def mock_agent_runner(monkeypatch):
    """Mock de AgentRunner zodat er geen echte Ollama aanroepen worden gedaan."""
    mock_runner = MagicMock()
    mock_runner.run_agent = AsyncMock(return_value=MOCK_AGENT_RESPONSE)
    monkeypatch.setattr("ollama.agent_runner._runner", mock_runner)
    monkeypatch.setattr("webhooks.handlers.order_handler.get_runner", lambda: mock_runner)
    monkeypatch.setattr("webhooks.handlers.payment_handler.get_runner", lambda: mock_runner)
    monkeypatch.setattr("webhooks.handlers.inventory_handler.get_runner", lambda: mock_runner)
    return mock_runner


class TestHealthEndpoint:
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data


class TestOrderWebhooks:
    async def test_order_created_valid_payload(self, client):
        payload = {
            "order_id": "ORD-001",
            "customer": {"email": "test@voorbeeld.nl", "name": "Jan Jansen"},
            "items": [{"product_id": "P1", "qty": 2}],
            "total": 49.99,
        }
        response = await client.post(
            "/webhooks/order-created",
            json=payload,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "verwerkt"
        assert data["order_id"] == "ORD-001"
        assert "agent_output" in data

    async def test_order_created_invalid_json(self, client):
        response = await client.post(
            "/webhooks/order-created",
            content=b"dit is geen json",
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 400

    async def test_order_shipped_returns_tracking(self, client):
        payload = {
            "order_id": "ORD-002",
            "tracking_code": "NL123456789",
            "carrier": "PostNL",
        }
        response = await client.post("/webhooks/order-shipped", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["tracking_code"] == "NL123456789"
        assert "agent_output" in data

    async def test_order_returned_valid(self, client):
        payload = {
            "order_id": "ORD-003",
            "return_reason": "Verkeerde maat",
            "items": ["ITEM-1"],
        }
        response = await client.post("/webhooks/order-returned", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "verwerkt"
        assert "agent_output" in data


class TestPaymentWebhooks:
    async def test_order_paid_valid(self, client):
        payload = {
            "order_id": "ORD-004",
            "payment_id": "PAY-XYZ",
            "amount": 99.95,
            "method": "ideal",
        }
        response = await client.post("/webhooks/order-paid", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "verwerkt"
        assert data["payment_id"] == "PAY-XYZ"
        assert "agent_output" in data


class TestInventoryWebhooks:
    async def test_stock_low_valid(self, client):
        payload = {
            "product_id": "PROD-100",
            "product_name": "Test Product",
            "current_stock": 3,
            "threshold": 5,
        }
        response = await client.post("/webhooks/stock-low", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "verwerkt"
        assert "agent_output" in data


class TestAgentFeedbackWebhook:
    async def test_agent_feedback_valid(self, client):
        payload = {
            "agent": "klantenservice_agent",
            "rating": 4,
            "feedback": "Goed antwoord, maar kon specifieker",
        }
        response = await client.post("/webhooks/agent-feedback", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ontvangen"
        assert data["agent"] == "klantenservice_agent"
        assert data["rating"] == 4
        assert "timestamp" in data

    async def test_agent_feedback_missing_agent(self, client):
        payload = {"rating": 3}
        response = await client.post("/webhooks/agent-feedback", json=payload)
        assert response.status_code == 400

    async def test_agent_feedback_invalid_rating(self, client):
        payload = {"agent": "klantenservice_agent", "rating": 9}
        response = await client.post("/webhooks/agent-feedback", json=payload)
        assert response.status_code == 400


class TestWebhookSignatureVerification:
    def test_invalid_signature_returns_401(self):
        import hmac
        import hashlib
        from webhooks.app import verify_signature

        payload = b'{"test": "data"}'
        wrong_sig = "sha256=incorrecte_handtekening"
        assert not verify_signature(payload, wrong_sig, "geheim")

    def test_valid_signature_passes(self):
        import hmac
        import hashlib
        from webhooks.app import verify_signature

        secret = "test_geheim"
        payload = b'{"order_id": "123"}'
        expected = "sha256=" + hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        assert verify_signature(payload, expected, secret)

    def test_no_secret_always_passes(self):
        from webhooks.app import verify_signature
        assert verify_signature(b"data", "some_sig", "")
