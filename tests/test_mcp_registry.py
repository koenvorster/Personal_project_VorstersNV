"""
Tests voor MCPToolRegistry — laadt uit de echte .claude/tool-registry.yaml.
"""
import pytest
from pathlib import Path
from ollama.mcp_registry import (
    MCPToolRegistry, MCPToolDefinition, ToolAuthInfo, ToolCostInfo,
    get_mcp_registry
)

EXPECTED_TOOLS = [
    "mollie-payment-status",
    "order-db-readonly",
    "fraud-score-compute",
    "backoffice-write",
    "email-notify",
    "audit-log-write",
]


@pytest.fixture
def registry():
    """Frisse registry instantie per test (geen singleton)."""
    return MCPToolRegistry()


# ── Laden & discovery ──────────────────────────────────────────────────────────

def test_registry_loads_without_crash(registry):
    assert registry.list_all() is not None


def test_list_all_contains_all_six_tools(registry):
    tools = registry.list_all()
    assert len(tools) == 6
    for name in EXPECTED_TOOLS:
        assert name in tools


def test_get_known_tool_returns_definition(registry):
    tool = registry.get("mollie-payment-status")
    assert isinstance(tool, MCPToolDefinition)


def test_get_nonexistent_tool_returns_none(registry):
    assert registry.get("nonexistent-tool") is None


# ── Tool-specifieke metadata ───────────────────────────────────────────────────

def test_mollie_reliability_score(registry):
    tool = registry.get("mollie-payment-status")
    assert tool.reliability_score == pytest.approx(0.99)


def test_mollie_version(registry):
    tool = registry.get("mollie-payment-status")
    assert tool.version == "2.1"


def test_mollie_category_is_external(registry):
    tool = registry.get("mollie-payment-status")
    assert tool.category == "external"


def test_mollie_fallback_tool_name(registry):
    tool = registry.get("mollie-payment-status")
    assert tool.fallback_tool == "order-db-readonly"


def test_mollie_otel_span_enabled(registry):
    tool = registry.get("mollie-payment-status")
    assert tool.otel_span is True


def test_mollie_auth_type_and_env(registry):
    tool = registry.get("mollie-payment-status")
    assert tool.auth.type == "api_key"
    assert tool.auth.env_var == "MOLLIE_API_KEY"


def test_order_db_empty_capabilities(registry):
    tool = registry.get("order-db-readonly")
    assert tool.capabilities == []


def test_order_db_is_allowed_for_any_capability(registry):
    tool = registry.get("order-db-readonly")
    assert tool.is_allowed_for("fraud-detection") is True
    assert tool.is_allowed_for("anything-random") is True


def test_fraud_score_only_allowed_for_fraud_detection(registry):
    tool = registry.get("fraud-score-compute")
    assert tool.is_allowed_for("fraud-detection") is True
    assert tool.is_allowed_for("order-validation") is False
    assert tool.is_allowed_for("customer-service") is False


def test_fraud_score_no_auth_env(registry):
    tool = registry.get("fraud-score-compute")
    assert tool.auth.type == "none"
    assert tool.auth.env_var is None


def test_backoffice_write_requires_hitl(registry):
    tool = registry.get("backoffice-write")
    assert tool.requires_hitl is True


def test_backoffice_write_not_idempotent(registry):
    tool = registry.get("backoffice-write")
    assert tool.idempotent is False


def test_email_notify_not_idempotent(registry):
    tool = registry.get("email-notify")
    assert tool.idempotent is False


def test_email_notify_otel_span_disabled(registry):
    tool = registry.get("email-notify")
    assert tool.otel_span is False


def test_audit_log_idempotent(registry):
    tool = registry.get("audit-log-write")
    assert tool.idempotent is True


def test_audit_log_reliability_score(registry):
    tool = registry.get("audit-log-write")
    assert tool.reliability_score == pytest.approx(0.9999)


# ── Filtering ──────────────────────────────────────────────────────────────────

def test_list_for_capability_fraud_detection_includes_fraud_compute(registry):
    names = [t.name for t in registry.list_for_capability("fraud-detection")]
    assert "fraud-score-compute" in names


def test_list_for_capability_fraud_detection_includes_mollie(registry):
    names = [t.name for t in registry.list_for_capability("fraud-detection")]
    assert "mollie-payment-status" in names


def test_list_for_capability_fraud_detection_includes_open_whitelist_tools(registry):
    """order-db-readonly en audit-log-write hebben lege capabilities → altijd toegestaan."""
    names = [t.name for t in registry.list_for_capability("fraud-detection")]
    assert "order-db-readonly" in names
    assert "audit-log-write" in names


def test_list_by_category_external(registry):
    names = [t.name for t in registry.list_by_category("external")]
    assert "mollie-payment-status" in names
    assert len(names) == 1


def test_list_by_category_write_contains_both_write_tools(registry):
    names = [t.name for t in registry.list_by_category("write")]
    assert "backoffice-write" in names
    assert "audit-log-write" in names
    assert len(names) == 2


def test_list_by_category_read(registry):
    names = [t.name for t in registry.list_by_category("read")]
    assert "order-db-readonly" in names


# ── Fallback routing ───────────────────────────────────────────────────────────

def test_resolve_fallback_mollie_returns_order_db(registry):
    fallback = registry.resolve_fallback("mollie-payment-status")
    assert fallback is not None
    assert fallback.name == "order-db-readonly"
    assert isinstance(fallback, MCPToolDefinition)


def test_resolve_fallback_fraud_score_returns_none(registry):
    assert registry.resolve_fallback("fraud-score-compute") is None


def test_resolve_fallback_unknown_tool_returns_none(registry):
    assert registry.resolve_fallback("does-not-exist") is None


def test_get_fallback_method_on_definition(registry):
    tool = registry.get("mollie-payment-status")
    assert tool.get_fallback() == "order-db-readonly"


# ── Kostenschatting ────────────────────────────────────────────────────────────

def test_total_cost_estimate_mollie_and_audit(registry):
    # 0.0001 + 0.000005 = 0.000105
    cost = registry.get_total_cost_estimate(["mollie-payment-status", "audit-log-write"])
    assert cost == pytest.approx(0.000105, rel=1e-5)


def test_total_cost_estimate_multiple_calls(registry):
    # mollie: 0.0001 * 5 = 0.0005, audit: 0.000005 * 5 = 0.000025 → 0.000525
    cost = registry.get_total_cost_estimate(["mollie-payment-status", "audit-log-write"], calls_each=5)
    assert cost == pytest.approx(0.000525, rel=1e-5)


def test_estimated_cost_eur_single_call(registry):
    tool = registry.get("fraud-score-compute")
    assert tool.estimated_cost_eur(1) == pytest.approx(0.0005)


def test_estimated_cost_eur_ten_calls(registry):
    tool = registry.get("fraud-score-compute")
    assert tool.estimated_cost_eur(10) == pytest.approx(0.005)


def test_total_cost_estimate_empty_list(registry):
    assert registry.get_total_cost_estimate([]) == 0.0


def test_total_cost_estimate_unknown_tool_ignored(registry):
    cost = registry.get_total_cost_estimate(["nonexistent"])
    assert cost == 0.0


# ── is_allowed_for edge cases ──────────────────────────────────────────────────

def test_is_allowed_for_empty_capabilities_always_true(registry):
    tool = registry.get("audit-log-write")
    for cap in ["fraud-detection", "order-validation", "customer-service", "anything"]:
        assert tool.is_allowed_for(cap) is True


def test_is_allowed_for_with_nonempty_capabilities_exact_match(registry):
    tool = registry.get("email-notify")
    assert tool.is_allowed_for("customer-service") is True
    assert tool.is_allowed_for("order-validation") is True
    assert tool.is_allowed_for("fraud-detection") is False


# ── ToolAuthInfo ───────────────────────────────────────────────────────────────

def test_tool_auth_info_with_env_var():
    auth = ToolAuthInfo(type="api_key", env_var="MY_SECRET")
    assert auth.type == "api_key"
    assert auth.env_var == "MY_SECRET"


def test_tool_auth_info_without_env_var():
    auth = ToolAuthInfo(type="none")
    assert auth.env_var is None


# ── register() ────────────────────────────────────────────────────────────────

def test_register_adds_new_tool(registry):
    new_tool = MCPToolDefinition(
        name="custom-tool",
        version="0.1",
        owner="team-test",
        description="Test tool",
        category="compute",
        capabilities=["test-cap"],
        auth=ToolAuthInfo(type="none"),
        cost_per_call=ToolCostInfo(unit="call", estimated_eur=0.0),
        reliability_score=1.0,
        timeout_seconds=5.0,
        idempotent=True,
        requires_hitl=False,
        input_schema={},
        output_schema={},
        fallback_tool=None,
        otel_span=False,
    )
    registry.register(new_tool)
    assert registry.get("custom-tool") is new_tool
    assert "custom-tool" in registry.list_all()


def test_register_overwrites_existing_tool(registry):
    original = registry.get("email-notify")
    assert original is not None
    replacement = MCPToolDefinition(
        name="email-notify",
        version="99.0",
        owner="team-test",
        description="Replaced",
        category="notify",
        capabilities=[],
        auth=ToolAuthInfo(type="none"),
        cost_per_call=ToolCostInfo(unit="call", estimated_eur=0.0),
        reliability_score=1.0,
        timeout_seconds=5.0,
        idempotent=True,
        requires_hitl=False,
        input_schema={},
        output_schema={},
        fallback_tool=None,
        otel_span=False,
    )
    registry.register(replacement)
    assert registry.get("email-notify").version == "99.0"


# ── Singleton get_mcp_registry() ──────────────────────────────────────────────

def test_get_mcp_registry_returns_registry_instance():
    r = get_mcp_registry()
    assert isinstance(r, MCPToolRegistry)


def test_get_mcp_registry_is_singleton():
    r1 = get_mcp_registry()
    r2 = get_mcp_registry()
    assert r1 is r2


def test_get_mcp_registry_contains_tools():
    r = get_mcp_registry()
    assert len(r.list_all()) == 6


# ── reload() ──────────────────────────────────────────────────────────────────

def test_reload_does_not_crash(registry):
    registry.reload()
    assert len(registry.list_all()) == 6


def test_reload_restores_all_tools_after_register(registry):
    """Na register + reload zijn alleen de YAML-tools aanwezig."""
    new_tool = MCPToolDefinition(
        name="temp-tool",
        version="0.1",
        owner="test",
        description="",
        category="compute",
        capabilities=[],
        auth=ToolAuthInfo(type="none"),
        cost_per_call=ToolCostInfo(unit="call", estimated_eur=0.0),
        reliability_score=1.0,
        timeout_seconds=5.0,
        idempotent=True,
        requires_hitl=False,
        input_schema={},
        output_schema={},
        fallback_tool=None,
        otel_span=False,
    )
    registry.register(new_tool)
    assert "temp-tool" in registry.list_all()
    registry.reload()
    assert "temp-tool" not in registry.list_all()
    assert len(registry.list_all()) == 6


# ── Input/output schema aanwezig ──────────────────────────────────────────────

def test_mollie_input_schema_has_required_payment_id(registry):
    tool = registry.get("mollie-payment-status")
    assert "payment_id" in tool.input_schema.get("required", [])


def test_fraud_score_output_schema_has_score(registry):
    tool = registry.get("fraud-score-compute")
    assert "score" in tool.output_schema.get("properties", {})


def test_audit_log_input_schema_required_fields(registry):
    tool = registry.get("audit-log-write")
    required = tool.input_schema.get("required", [])
    assert "trace_id" in required
    assert "action" in required
    assert "capability" in required
