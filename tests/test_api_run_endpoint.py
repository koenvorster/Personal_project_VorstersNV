"""
Integration tests voor POST /api/ai/run endpoint.
Mockt get_platform_adapter() via unittest.mock.patch zodat de echte
Ollama/LLM stack niet wordt aangesproken.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from api.auth.jwt import TokenData, require_admin_or_tester
from api.main import app
from db.models.user import UserRole
from ollama.platform_adapter import CapabilityResult

# ── Dummy auth ────────────────────────────────────────────────────────────────

DUMMY_TOKEN = TokenData(
    user_id="test-runner-1",
    email="tester@vorsternv.be",
    naam="Test Runner",
    rol=UserRole.admin,
)


def override_auth():
    return DUMMY_TOKEN


# ── Default mock result ───────────────────────────────────────────────────────

def _make_result(**overrides) -> CapabilityResult:
    defaults = dict(
        capability_id="fraud-detection",
        trace_id="trace-abc-123",
        agent_name="fraude_detectie_agent",
        model_used="llama3",
        response="Geen fraude gedetecteerd.",
        validated_output={"confidence": 0.95, "verdict": "clean"},
        execution_path="advisory/llama3",
        policy_violations=[],
        cost_eur=0.0012,
        latency_ms=210.5,
        success=True,
        error=None,
    )
    defaults.update(overrides)
    return CapabilityResult(**defaults)


def _mock_adapter(result: CapabilityResult | None = None):
    """Return a patched get_platform_adapter that yields a mock adapter."""
    if result is None:
        result = _make_result()
    adapter = MagicMock()
    adapter.run_capability = AsyncMock(return_value=result)
    return adapter


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture()
async def client():
    app.dependency_overrides[require_admin_or_tester] = override_auth
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(require_admin_or_tester, None)


@pytest.fixture()
async def unauthed_client():
    app.dependency_overrides.pop(require_admin_or_tester, None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ── Helpers ───────────────────────────────────────────────────────────────────

_VALID_BODY = {
    "capability_id": "fraud-detection",
    "user_input": "Controleer bestelling 9988 op fraude",
    "context": {"order_id": "9988"},
    "environment": "dev",
}

_MODULE = "api.routers.ai_platform.get_platform_adapter"


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_run_valid_body_returns_200(client):
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=_VALID_BODY)
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_run_response_has_capability_id(client):
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=_VALID_BODY)
    assert resp.json()["capability_id"] == "fraud-detection"


@pytest.mark.anyio
async def test_run_response_has_trace_id(client):
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=_VALID_BODY)
    assert resp.json()["trace_id"] == "trace-abc-123"


@pytest.mark.anyio
async def test_run_response_has_agent_name(client):
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=_VALID_BODY)
    assert resp.json()["agent_name"] == "fraude_detectie_agent"


@pytest.mark.anyio
async def test_run_response_has_model_used(client):
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=_VALID_BODY)
    assert resp.json()["model_used"] == "llama3"


@pytest.mark.anyio
async def test_run_response_has_execution_path(client):
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=_VALID_BODY)
    assert "execution_path" in resp.json()


@pytest.mark.anyio
async def test_run_response_has_policy_violations_list(client):
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=_VALID_BODY)
    assert isinstance(resp.json()["policy_violations"], list)


@pytest.mark.anyio
async def test_run_response_success_true_on_success(client):
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=_VALID_BODY)
    assert resp.json()["success"] is True


@pytest.mark.anyio
async def test_run_response_error_none_on_success(client):
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=_VALID_BODY)
    assert resp.json()["error"] is None


@pytest.mark.anyio
async def test_run_latency_ms_positive(client):
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=_VALID_BODY)
    assert resp.json()["latency_ms"] > 0


@pytest.mark.anyio
async def test_run_cost_eur_non_negative(client):
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=_VALID_BODY)
    assert resp.json()["cost_eur"] >= 0


@pytest.mark.anyio
async def test_run_validated_output_present_when_success(client):
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=_VALID_BODY)
    assert resp.json()["validated_output"] is not None


@pytest.mark.anyio
async def test_run_validated_output_can_be_none(client):
    result = _make_result(validated_output=None)
    with patch(_MODULE, return_value=_mock_adapter(result)):
        resp = await client.post("/api/ai/run", json=_VALID_BODY)
    assert resp.json()["validated_output"] is None


@pytest.mark.anyio
async def test_run_missing_user_input_returns_422(client):
    body = {**_VALID_BODY}
    body.pop("user_input")
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=body)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_run_empty_user_input_returns_422(client):
    body = {**_VALID_BODY, "user_input": ""}
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=body)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_run_invalid_environment_returns_422(client):
    body = {**_VALID_BODY, "environment": "production"}
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=body)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_run_risk_score_below_0_returns_422(client):
    body = {**_VALID_BODY, "risk_score": -1}
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=body)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_run_risk_score_above_100_returns_422(client):
    body = {**_VALID_BODY, "risk_score": 101}
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=body)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_run_missing_capability_id_returns_422(client):
    body = {**_VALID_BODY}
    body.pop("capability_id")
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=body)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_run_policy_violation_returns_200_with_success_false(client):
    result = _make_result(
        success=False,
        policy_violations=["HIGH_RISK_SCORE_BLOCKER"],
        response="",
        validated_output=None,
        error="HIGH_RISK_SCORE_BLOCKER",
        cost_eur=0.0,
    )
    with patch(_MODULE, return_value=_mock_adapter(result)):
        resp = await client.post("/api/ai/run", json=_VALID_BODY)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert len(data["policy_violations"]) > 0


@pytest.mark.anyio
async def test_run_policy_violation_has_error_message(client):
    result = _make_result(
        success=False,
        policy_violations=["POLICY_BREACH"],
        error="POLICY_BREACH",
        cost_eur=0.0,
        response="",
        validated_output=None,
    )
    with patch(_MODULE, return_value=_mock_adapter(result)):
        resp = await client.post("/api/ai/run", json=_VALID_BODY)
    assert resp.json()["error"] is not None


@pytest.mark.anyio
async def test_run_capability_fraud_detection(client):
    result = _make_result(capability_id="fraud-detection", agent_name="fraude_detectie_agent")
    body = {**_VALID_BODY, "capability_id": "fraud-detection"}
    with patch(_MODULE, return_value=_mock_adapter(result)):
        resp = await client.post("/api/ai/run", json=body)
    assert resp.status_code == 200
    assert resp.json()["capability_id"] == "fraud-detection"


@pytest.mark.anyio
async def test_run_capability_order_validation(client):
    result = _make_result(capability_id="order-validation", agent_name="order_verwerking_agent")
    body = {**_VALID_BODY, "capability_id": "order-validation"}
    with patch(_MODULE, return_value=_mock_adapter(result)):
        resp = await client.post("/api/ai/run", json=body)
    assert resp.status_code == 200
    assert resp.json()["capability_id"] == "order-validation"


@pytest.mark.anyio
async def test_run_capability_content_generation(client):
    result = _make_result(capability_id="content-generation", agent_name="product_beschrijving_agent")
    body = {**_VALID_BODY, "capability_id": "content-generation"}
    with patch(_MODULE, return_value=_mock_adapter(result)):
        resp = await client.post("/api/ai/run", json=body)
    assert resp.status_code == 200
    assert resp.json()["capability_id"] == "content-generation"


@pytest.mark.anyio
async def test_run_context_passed_through(client):
    """Verify adapter.run_capability is called with the correct context."""
    adapter = _mock_adapter()
    body = {**_VALID_BODY, "context": {"order_id": "XYZ-42", "region": "BE"}}
    with patch(_MODULE, return_value=adapter):
        await client.post("/api/ai/run", json=body)
    called_request = adapter.run_capability.call_args[0][0]
    assert called_request.context == {"order_id": "XYZ-42", "region": "BE"}


@pytest.mark.anyio
async def test_run_session_id_passed_through(client):
    adapter = _mock_adapter()
    body = {**_VALID_BODY, "session_id": "sess-999"}
    with patch(_MODULE, return_value=adapter):
        await client.post("/api/ai/run", json=body)
    called_request = adapter.run_capability.call_args[0][0]
    assert called_request.session_id == "sess-999"


@pytest.mark.anyio
async def test_run_tools_requested_passed_through(client):
    adapter = _mock_adapter()
    body = {**_VALID_BODY, "tools_requested": ["web_search", "calculator"]}
    with patch(_MODULE, return_value=adapter):
        await client.post("/api/ai/run", json=body)
    called_request = adapter.run_capability.call_args[0][0]
    assert called_request.tools_requested == ["web_search", "calculator"]


@pytest.mark.anyio
async def test_run_risk_score_boundary_0(client):
    body = {**_VALID_BODY, "risk_score": 0}
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=body)
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_run_risk_score_boundary_100(client):
    body = {**_VALID_BODY, "risk_score": 100}
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=body)
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_run_environment_test_valid(client):
    body = {**_VALID_BODY, "environment": "test"}
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=body)
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_run_environment_staging_valid(client):
    body = {**_VALID_BODY, "environment": "staging"}
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=body)
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_run_environment_prod_valid(client):
    body = {**_VALID_BODY, "environment": "prod"}
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=body)
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_run_without_auth_returns_401(unauthed_client):
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await unauthed_client.post("/api/ai/run", json=_VALID_BODY)
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_run_response_has_response_field(client):
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=_VALID_BODY)
    assert "response" in resp.json()
    assert resp.json()["response"] == "Geen fraude gedetecteerd."


@pytest.mark.anyio
async def test_run_empty_tools_requested_by_default(client):
    adapter = _mock_adapter()
    with patch(_MODULE, return_value=adapter):
        await client.post("/api/ai/run", json=_VALID_BODY)
    called_request = adapter.run_capability.call_args[0][0]
    assert called_request.tools_requested == []


@pytest.mark.anyio
async def test_run_default_session_id_empty_string(client):
    adapter = _mock_adapter()
    with patch(_MODULE, return_value=adapter):
        await client.post("/api/ai/run", json=_VALID_BODY)
    called_request = adapter.run_capability.call_args[0][0]
    assert called_request.session_id == ""


@pytest.mark.anyio
async def test_run_all_required_response_fields_present(client):
    required = {
        "capability_id", "trace_id", "agent_name", "model_used",
        "response", "validated_output", "execution_path",
        "policy_violations", "cost_eur", "latency_ms", "success", "error",
    }
    with patch(_MODULE, return_value=_mock_adapter()):
        resp = await client.post("/api/ai/run", json=_VALID_BODY)
    assert required.issubset(resp.json().keys())
