"""
Tests voor de AI Platform API endpoints.
GET /api/ai/health, /api/ai/quality/report, /api/ai/quality/alerts,
POST /api/ai/quality/record-run, GET /api/ai/decisions,
GET /api/ai/observability/dashboard, GET /api/ai/capabilities,
GET /api/ai/capabilities/{id}
"""
import pytest
from httpx import ASGITransport, AsyncClient

from api.auth.jwt import TokenData, require_admin_or_tester
from api.main import app
from db.models.user import UserRole
from ollama.capability_registry import CapabilityDefinition, CapabilityMaturity, CapabilityOperational, CapabilityRelease, get_capability_registry
from ollama.decision_journal import JournalEntry, get_decision_journal
from ollama.observability import get_observability_collector
from ollama.quality_monitor import get_quality_monitor

# ── Dummy auth ────────────────────────────────────────────────────────────────

DUMMY_TOKEN = TokenData(
    user_id="test-user-1",
    email="tester@vorsternv.be",
    naam="Test User",
    rol=UserRole.admin,
)


def override_auth():
    return DUMMY_TOKEN


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture()
async def client():
    """HTTP test client with auth overridden and AI platform singletons reset."""
    # Reset singletons so tests are isolated
    monitor = get_quality_monitor()
    monitor.reset()

    journal = get_decision_journal()
    journal.clear()

    collector = get_observability_collector()
    collector.clear()

    registry = get_capability_registry()
    registry._capabilities = {}
    registry._loaded = True  # Prevent loading from disk

    app.dependency_overrides[require_admin_or_tester] = override_auth
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(require_admin_or_tester, None)


@pytest.fixture()
async def unauthed_client():
    """HTTP test client without auth override (401 expected)."""
    app.dependency_overrides.pop(require_admin_or_tester, None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture()
async def client_with_data(client):
    """Client pre-loaded with quality metrics, decisions and capabilities."""
    monitor = get_quality_monitor()
    monitor.record_run(
        agent_name="fraud-agent",
        capability="fraud-detection",
        success=True,
        score=0.92,
        latency_ms=320.0,
        cost_eur=0.05,
        human_escalated=False,
    )
    monitor.record_run(
        agent_name="kyc-agent",
        capability="kyc-check",
        success=False,
        score=0.45,
        latency_ms=7000.0,
        cost_eur=0.10,
        human_escalated=True,
    )

    journal = get_decision_journal()
    journal.record(JournalEntry(
        capability="fraud-detection",
        agent_name="fraud-agent",
        model_used="llama3",
        verdict="APPROVED",
        risk_score=30.0,
    ))
    journal.record(JournalEntry(
        capability="kyc-check",
        agent_name="kyc-agent",
        model_used="llama3.1",
        verdict="REVIEW",
        risk_score=70.0,
    ))

    registry = get_capability_registry()
    registry.register(CapabilityDefinition(
        name="fraud-detection",
        version="2.0",
        description="AI fraud detection",
        lane="autonomous",
        audience="internal",
        risk="high",
        maturity=CapabilityMaturity(level="L3", label="team-production"),
        operational=CapabilityOperational(
            owner="risk-team",
            sla_tier="gold",
            cost_budget_monthly_eur=500.0,
        ),
        release=CapabilityRelease(rollout_ring="ring-2", feature_flag="ai.capability.fraud-detection"),
    ))
    registry.register(CapabilityDefinition(
        name="kyc-check",
        version="1.0",
        description="KYC verification",
        lane="hitl",
        audience="internal",
        risk="medium",
        maturity=CapabilityMaturity(level="L1", label="experimental"),
        operational=CapabilityOperational(
            owner="compliance-team",
            sla_tier="silver",
            cost_budget_monthly_eur=200.0,
        ),
        release=CapabilityRelease(rollout_ring="ring-0", feature_flag="ai.capability.kyc-check"),
    ))

    return client


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/ai/health
# ─────────────────────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    async def test_returns_200(self, client):
        r = await client.get("/api/ai/health")
        assert r.status_code == 200

    async def test_no_auth_required(self, unauthed_client):
        r = await unauthed_client.get("/api/ai/health")
        assert r.status_code == 200

    async def test_status_ok(self, client):
        data = (await client.get("/api/ai/health")).json()
        assert data["status"] == "ok"

    async def test_platform_version(self, client):
        data = (await client.get("/api/ai/health")).json()
        assert data["platform_version"] == "5.0"

    async def test_components_present(self, client):
        data = (await client.get("/api/ai/health")).json()
        components = data["components"]
        assert "quality_monitor" in components
        assert "decision_journal" in components
        assert "observability" in components
        assert "capability_registry" in components

    async def test_all_components_active(self, client):
        data = (await client.get("/api/ai/health")).json()
        for v in data["components"].values():
            assert v == "active"


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/ai/quality/report
# ─────────────────────────────────────────────────────────────────────────────

class TestQualityReport:
    async def test_returns_200_authed(self, client):
        r = await client.get("/api/ai/quality/report")
        assert r.status_code == 200

    async def test_requires_auth(self, unauthed_client):
        r = await unauthed_client.get("/api/ai/quality/report")
        assert r.status_code == 401

    async def test_structure_has_required_keys(self, client):
        data = (await client.get("/api/ai/quality/report")).json()
        for key in [
            "generated_at", "total_agents", "healthy_agents", "degraded_agents",
            "critical_agents", "platform_avg_score", "platform_avg_latency_ms",
            "total_cost_eur", "agents", "alerts", "recommendations",
        ]:
            assert key in data, f"Missing key: {key}"

    async def test_empty_report_defaults(self, client):
        data = (await client.get("/api/ai/quality/report")).json()
        assert data["total_agents"] == 0
        assert data["agents"] == []

    async def test_report_counts_agents(self, client_with_data):
        data = (await client_with_data.get("/api/ai/quality/report")).json()
        assert data["total_agents"] == 2

    async def test_report_healthy_agents(self, client_with_data):
        data = (await client_with_data.get("/api/ai/quality/report")).json()
        assert data["healthy_agents"] >= 0

    async def test_report_critical_agents_flagged(self, client_with_data):
        data = (await client_with_data.get("/api/ai/quality/report")).json()
        # kyc-agent has 0% success rate → critical
        assert data["critical_agents"] >= 1

    async def test_report_agents_list_structure(self, client_with_data):
        data = (await client_with_data.get("/api/ai/quality/report")).json()
        agent = data["agents"][0]
        for key in ["agent_name", "capability", "total_runs", "success_rate", "avg_score"]:
            assert key in agent

    async def test_report_alerts_is_list(self, client):
        data = (await client.get("/api/ai/quality/report")).json()
        assert isinstance(data["alerts"], list)

    async def test_report_recommendations_is_list(self, client):
        data = (await client.get("/api/ai/quality/report")).json()
        assert isinstance(data["recommendations"], list)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/ai/quality/alerts
# ─────────────────────────────────────────────────────────────────────────────

class TestQualityAlerts:
    async def test_returns_200(self, client):
        r = await client.get("/api/ai/quality/alerts")
        assert r.status_code == 200

    async def test_requires_auth(self, unauthed_client):
        r = await unauthed_client.get("/api/ai/quality/alerts")
        assert r.status_code == 401

    async def test_returns_list(self, client):
        data = (await client.get("/api/ai/quality/alerts")).json()
        assert isinstance(data, list)

    async def test_empty_when_no_agents(self, client):
        data = (await client.get("/api/ai/quality/alerts")).json()
        assert data == []

    async def test_alerts_generated_for_bad_agent(self, client_with_data):
        data = (await client_with_data.get("/api/ai/quality/alerts")).json()
        assert len(data) > 0

    async def test_alerts_are_strings(self, client_with_data):
        data = (await client_with_data.get("/api/ai/quality/alerts")).json()
        for alert in data:
            assert isinstance(alert, str)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/ai/quality/record-run
# ─────────────────────────────────────────────────────────────────────────────

class TestRecordRun:
    def _body(self, **kwargs):
        base = {
            "agent_name": "test-agent",
            "capability": "test-capability",
            "success": True,
            "score": 0.85,
            "latency_ms": 200.0,
            "cost_eur": 0.02,
            "human_escalated": False,
        }
        base.update(kwargs)
        return base

    async def test_returns_200(self, client):
        r = await client.post("/api/ai/quality/record-run", json=self._body())
        assert r.status_code == 200

    async def test_requires_auth(self, unauthed_client):
        r = await unauthed_client.post("/api/ai/quality/record-run", json=self._body())
        assert r.status_code == 401

    async def test_response_has_recorded_true(self, client):
        data = (await client.post("/api/ai/quality/record-run", json=self._body())).json()
        assert data["recorded"] is True

    async def test_response_has_agent_name(self, client):
        data = (await client.post("/api/ai/quality/record-run", json=self._body())).json()
        assert data["agent_name"] == "test-agent"

    async def test_invalid_score_too_high(self, client):
        r = await client.post("/api/ai/quality/record-run", json=self._body(score=1.5))
        assert r.status_code == 422

    async def test_invalid_score_negative(self, client):
        r = await client.post("/api/ai/quality/record-run", json=self._body(score=-0.1))
        assert r.status_code == 422

    async def test_invalid_latency_negative(self, client):
        r = await client.post("/api/ai/quality/record-run", json=self._body(latency_ms=-1.0))
        assert r.status_code == 422

    async def test_missing_required_field(self, client):
        body = self._body()
        del body["agent_name"]
        r = await client.post("/api/ai/quality/record-run", json=body)
        assert r.status_code == 422

    async def test_run_updates_quality_report(self, client):
        await client.post("/api/ai/quality/record-run", json=self._body(agent_name="new-agent"))
        report = (await client.get("/api/ai/quality/report")).json()
        agent_names = [a["agent_name"] for a in report["agents"]]
        assert "new-agent" in agent_names

    async def test_default_cost_zero(self, client):
        body = {
            "agent_name": "agent-x",
            "capability": "cap-x",
            "success": True,
            "score": 0.9,
            "latency_ms": 100.0,
        }
        r = await client.post("/api/ai/quality/record-run", json=body)
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/ai/decisions
# ─────────────────────────────────────────────────────────────────────────────

class TestDecisions:
    async def test_returns_200(self, client):
        r = await client.get("/api/ai/decisions")
        assert r.status_code == 200

    async def test_requires_auth(self, unauthed_client):
        r = await unauthed_client.get("/api/ai/decisions")
        assert r.status_code == 401

    async def test_returns_list(self, client):
        data = (await client.get("/api/ai/decisions")).json()
        assert isinstance(data, list)

    async def test_empty_journal(self, client):
        data = (await client.get("/api/ai/decisions")).json()
        assert data == []

    async def test_returns_all_entries(self, client_with_data):
        data = (await client_with_data.get("/api/ai/decisions")).json()
        assert len(data) == 2

    async def test_entry_structure(self, client_with_data):
        data = (await client_with_data.get("/api/ai/decisions")).json()
        entry = data[0]
        for key in ["trace_id", "capability", "agent_name", "model_used", "verdict", "timestamp"]:
            assert key in entry

    async def test_filter_by_capability(self, client_with_data):
        data = (await client_with_data.get("/api/ai/decisions?capability=fraud-detection")).json()
        assert all(e["capability"] == "fraud-detection" for e in data)
        assert len(data) == 1

    async def test_filter_unknown_capability_returns_empty(self, client_with_data):
        data = (await client_with_data.get("/api/ai/decisions?capability=nonexistent")).json()
        assert data == []

    async def test_limit_param(self, client):
        journal = get_decision_journal()
        for i in range(30):
            journal.record(JournalEntry(
                capability=f"cap-{i}",
                agent_name="agent",
                model_used="llama3",
                verdict="APPROVED",
            ))
        data = (await client.get("/api/ai/decisions?limit=10")).json()
        assert len(data) <= 10

    async def test_limit_max_100(self, client):
        r = await client.get("/api/ai/decisions?limit=200")
        assert r.status_code == 422

    async def test_timestamp_is_string(self, client_with_data):
        data = (await client_with_data.get("/api/ai/decisions")).json()
        for entry in data:
            assert isinstance(entry["timestamp"], str)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/ai/observability/dashboard
# ─────────────────────────────────────────────────────────────────────────────

class TestObservabilityDashboard:
    async def test_returns_200(self, client):
        r = await client.get("/api/ai/observability/dashboard")
        assert r.status_code == 200

    async def test_requires_auth(self, unauthed_client):
        r = await unauthed_client.get("/api/ai/observability/dashboard")
        assert r.status_code == 401

    async def test_returns_dict(self, client):
        data = (await client.get("/api/ai/observability/dashboard")).json()
        assert isinstance(data, dict)

    async def test_n1_section_present(self, client):
        data = (await client.get("/api/ai/observability/dashboard")).json()
        assert "n1_request" in data

    async def test_n2_section_present(self, client):
        data = (await client.get("/api/ai/observability/dashboard")).json()
        assert "n2_agent" in data

    async def test_n3_section_present(self, client):
        data = (await client.get("/api/ai/observability/dashboard")).json()
        assert "n3_business" in data

    async def test_n1_structure(self, client):
        data = (await client.get("/api/ai/observability/dashboard")).json()
        n1 = data["n1_request"]
        assert "total_requests" in n1
        assert "avg_latency_ms" in n1
        assert "total_tokens" in n1

    async def test_n2_structure(self, client):
        data = (await client.get("/api/ai/observability/dashboard")).json()
        n2 = data["n2_agent"]
        assert "total_agent_calls" in n2
        assert "escalation_rate" in n2

    async def test_empty_dashboard_returns_zeros(self, client):
        data = (await client.get("/api/ai/observability/dashboard")).json()
        assert data["n1_request"]["total_requests"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/ai/capabilities
# ─────────────────────────────────────────────────────────────────────────────

class TestCapabilities:
    async def test_returns_200(self, client):
        r = await client.get("/api/ai/capabilities")
        assert r.status_code == 200

    async def test_requires_auth(self, unauthed_client):
        r = await unauthed_client.get("/api/ai/capabilities")
        assert r.status_code == 401

    async def test_returns_list(self, client):
        data = (await client.get("/api/ai/capabilities")).json()
        assert isinstance(data, list)

    async def test_empty_when_no_capabilities(self, client):
        data = (await client.get("/api/ai/capabilities")).json()
        assert data == []

    async def test_returns_registered_capabilities(self, client_with_data):
        data = (await client_with_data.get("/api/ai/capabilities")).json()
        assert len(data) == 2

    async def test_capability_structure(self, client_with_data):
        data = (await client_with_data.get("/api/ai/capabilities")).json()
        cap = data[0]
        for key in ["id", "maturity_level", "lane", "ring", "is_production_ready", "owner"]:
            assert key in cap

    async def test_production_ready_flag(self, client_with_data):
        data = (await client_with_data.get("/api/ai/capabilities")).json()
        caps = {c["id"]: c for c in data}
        assert caps["fraud-detection"]["is_production_ready"] is True  # L3
        assert caps["kyc-check"]["is_production_ready"] is False       # L1


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/ai/capabilities/{id}
# ─────────────────────────────────────────────────────────────────────────────

class TestCapabilityDetail:
    async def test_returns_200_for_existing(self, client_with_data):
        r = await client_with_data.get("/api/ai/capabilities/fraud-detection")
        assert r.status_code == 200

    async def test_requires_auth(self, unauthed_client):
        r = await unauthed_client.get("/api/ai/capabilities/fraud-detection")
        assert r.status_code == 401

    async def test_404_for_unknown(self, client):
        r = await client.get("/api/ai/capabilities/does-not-exist")
        assert r.status_code == 404

    async def test_returns_full_definition(self, client_with_data):
        data = (await client_with_data.get("/api/ai/capabilities/fraud-detection")).json()
        assert data["name"] == "fraud-detection"
        assert data["version"] == "2.0"
        assert "maturity" in data
        assert "operational" in data
        assert "release" in data

    async def test_maturity_detail(self, client_with_data):
        data = (await client_with_data.get("/api/ai/capabilities/fraud-detection")).json()
        assert data["maturity"]["level"] == "L3"

    async def test_owner_in_operational(self, client_with_data):
        data = (await client_with_data.get("/api/ai/capabilities/fraud-detection")).json()
        assert data["operational"]["owner"] == "risk-team"

    async def test_is_production_ready_in_detail(self, client_with_data):
        data = (await client_with_data.get("/api/ai/capabilities/fraud-detection")).json()
        assert data["is_production_ready"] is True

    async def test_kyc_not_production_ready(self, client_with_data):
        data = (await client_with_data.get("/api/ai/capabilities/kyc-check")).json()
        assert data["is_production_ready"] is False
