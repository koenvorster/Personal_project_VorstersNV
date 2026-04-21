"""
Tests voor ollama/tool_executor.py

Dekt: ToolRegistry, ToolDefinition, ToolExecutor, default tools en singleton.
"""
import asyncio
import pytest

from ollama.tool_executor import (
    ToolRegistry,
    ToolExecutor,
    ToolDefinition,
    ToolCall,
    ToolResult,
    ToolCategory,
    ToolNotFoundError,
    ToolNotAllowedError,
    get_tool_registry,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_tool(
    name: str = "test-tool",
    category: ToolCategory = ToolCategory.COMPUTE,
    whitelist: list[str] | None = None,
    requires_hitl: bool = False,
    fn=None,
    timeout: float = 5.0,
) -> ToolDefinition:
    return ToolDefinition(
        name=name,
        description=f"Tool {name}",
        category=category,
        capability_whitelist=whitelist if whitelist is not None else [],
        requires_hitl=requires_hitl,
        timeout_seconds=timeout,
        fn=fn,
    )


def make_call(tool_name: str = "test-tool", capability: str = "cap-a", args: dict | None = None) -> ToolCall:
    return ToolCall(tool_name=tool_name, capability=capability, arguments=args or {})


def run(coro):
    """Helper voor asyncio.run() in sync tests."""
    return asyncio.run(coro)


# ── ToolRegistry ──────────────────────────────────────────────────────────────

class TestToolRegistry:

    def test_register_and_get(self):
        reg = ToolRegistry()
        tool = make_tool("my-tool")
        reg.register(tool)
        assert reg.get("my-tool") is tool

    def test_get_nonexistent_returns_none(self):
        reg = ToolRegistry()
        assert reg.get("ghost") is None

    def test_list_all_contains_registered_names(self):
        reg = ToolRegistry()
        reg.register(make_tool("alpha"))
        reg.register(make_tool("beta"))
        names = reg.list_all()
        assert "alpha" in names
        assert "beta" in names

    def test_list_all_empty_on_new_registry(self):
        reg = ToolRegistry()
        assert reg.list_all() == []

    def test_register_overwrites_existing(self):
        reg = ToolRegistry()
        t1 = make_tool("dup", category=ToolCategory.READ)
        t2 = make_tool("dup", category=ToolCategory.WRITE)
        reg.register(t1)
        reg.register(t2)
        assert reg.get("dup").category == ToolCategory.WRITE

    def test_list_by_category_filters_correctly(self):
        reg = ToolRegistry()
        reg.register(make_tool("r1", category=ToolCategory.READ))
        reg.register(make_tool("r2", category=ToolCategory.READ))
        reg.register(make_tool("w1", category=ToolCategory.WRITE))
        reads = reg.list_by_category(ToolCategory.READ)
        assert len(reads) == 2
        assert all(t.category == ToolCategory.READ for t in reads)

    def test_list_by_category_returns_empty_when_none_match(self):
        reg = ToolRegistry()
        reg.register(make_tool("x", category=ToolCategory.COMPUTE))
        assert reg.list_by_category(ToolCategory.EXTERNAL) == []

    def test_list_for_capability_open_whitelist(self):
        """Tool met lege whitelist is beschikbaar voor alle capabilities."""
        reg = ToolRegistry()
        reg.register(make_tool("open-tool", whitelist=[]))
        result = reg.list_for_capability("any-cap")
        assert any(t.name == "open-tool" for t in result)

    def test_list_for_capability_restricts_whitelist(self):
        reg = ToolRegistry()
        reg.register(make_tool("restricted", whitelist=["cap-x"]))
        assert any(t.name == "restricted" for t in reg.list_for_capability("cap-x"))
        assert not any(t.name == "restricted" for t in reg.list_for_capability("cap-y"))

    def test_list_for_capability_mixed(self):
        reg = ToolRegistry()
        reg.register(make_tool("open", whitelist=[]))
        reg.register(make_tool("exclusive", whitelist=["cap-a"]))
        for_a = reg.list_for_capability("cap-a")
        for_b = reg.list_for_capability("cap-b")
        assert len(for_a) == 2
        assert len(for_b) == 1
        assert for_b[0].name == "open"


# ── ToolDefinition ────────────────────────────────────────────────────────────

class TestToolDefinition:

    def test_is_allowed_empty_whitelist_always_true(self):
        tool = make_tool(whitelist=[])
        assert tool.is_allowed_for("anything") is True
        assert tool.is_allowed_for("other") is True

    def test_is_allowed_whitelist_match(self):
        tool = make_tool(whitelist=["fraud-detection", "order-validation"])
        assert tool.is_allowed_for("fraud-detection") is True
        assert tool.is_allowed_for("order-validation") is True

    def test_is_allowed_whitelist_no_match(self):
        tool = make_tool(whitelist=["fraud-detection"])
        assert tool.is_allowed_for("customer-service") is False

    def test_requires_hitl_default_false(self):
        tool = make_tool()
        assert tool.requires_hitl is False

    def test_requires_hitl_can_be_true(self):
        tool = make_tool(requires_hitl=True)
        assert tool.requires_hitl is True

    def test_idempotent_default_true(self):
        tool = make_tool()
        assert tool.idempotent is True


# ── ToolExecutor ──────────────────────────────────────────────────────────────

class TestToolExecutorNotFound:

    def test_unknown_tool_returns_failure(self):
        reg = ToolRegistry()
        ex = ToolExecutor(registry=reg)
        result = run(ex.execute(make_call("ghost")))
        assert result.success is False
        assert "ghost" in result.error

    def test_unknown_tool_error_contains_tool_name(self):
        reg = ToolRegistry()
        ex = ToolExecutor(registry=reg)
        result = run(ex.execute(make_call("nonexistent-tool")))
        assert "nonexistent-tool" in result.error


class TestToolExecutorNotAllowed:

    def test_disallowed_capability_returns_failure(self):
        reg = ToolRegistry()
        reg.register(make_tool("locked", whitelist=["allowed-cap"]))
        ex = ToolExecutor(registry=reg)
        result = run(ex.execute(make_call("locked", capability="other-cap")))
        assert result.success is False

    def test_disallowed_capability_error_message(self):
        reg = ToolRegistry()
        reg.register(make_tool("locked", whitelist=["allowed-cap"]))
        ex = ToolExecutor(registry=reg)
        result = run(ex.execute(make_call("locked", capability="bad-cap")))
        assert "bad-cap" in result.error or "locked" in result.error


class TestToolExecutorHITL:

    def test_hitl_tool_returns_hitl_required(self):
        reg = ToolRegistry()
        reg.register(make_tool("hitl-tool", requires_hitl=True))
        ex = ToolExecutor(registry=reg)
        result = run(ex.execute(make_call("hitl-tool")))
        assert result.hitl_required is True
        assert result.success is False

    def test_hitl_tool_error_mentions_approval(self):
        reg = ToolRegistry()
        reg.register(make_tool("hitl-tool", requires_hitl=True))
        ex = ToolExecutor(registry=reg)
        result = run(ex.execute(make_call("hitl-tool")))
        assert result.error is not None
        assert "approval" in result.error.lower() or "human" in result.error.lower()


class TestToolExecutorMockFn:

    def test_tool_without_fn_returns_mock_output(self):
        reg = ToolRegistry()
        reg.register(make_tool("no-fn-tool"))
        ex = ToolExecutor(registry=reg)
        result = run(ex.execute(make_call("no-fn-tool")))
        assert result.success is True
        assert result.output["mock"] is True
        assert result.output["tool"] == "no-fn-tool"

    def test_tool_without_fn_includes_args_in_output(self):
        reg = ToolRegistry()
        reg.register(make_tool("no-fn-tool"))
        ex = ToolExecutor(registry=reg)
        call = make_call("no-fn-tool", args={"order_id": "abc123"})
        result = run(ex.execute(call))
        assert result.output["args"]["order_id"] == "abc123"

    def test_tool_without_fn_has_duration(self):
        reg = ToolRegistry()
        reg.register(make_tool("no-fn-tool"))
        ex = ToolExecutor(registry=reg)
        result = run(ex.execute(make_call("no-fn-tool")))
        assert result.duration_ms >= 0.0


class TestToolExecutorSyncFn:

    def test_sync_fn_returns_correct_output(self):
        def my_fn(x: int, y: int) -> int:
            return x + y

        reg = ToolRegistry()
        reg.register(make_tool("add-tool", fn=my_fn))
        ex = ToolExecutor(registry=reg)
        result = run(ex.execute(make_call("add-tool", args={"x": 3, "y": 4})))
        assert result.success is True
        assert result.output == 7

    def test_sync_fn_exception_captured(self):
        def boom():
            raise ValueError("intentional error")

        reg = ToolRegistry()
        reg.register(make_tool("boom-tool", fn=boom))
        ex = ToolExecutor(registry=reg)
        result = run(ex.execute(make_call("boom-tool")))
        assert result.success is False
        assert "intentional error" in result.error


class TestToolExecutorAsyncFn:

    def test_async_fn_returns_correct_output(self):
        async def async_fn(val: str) -> str:
            await asyncio.sleep(0)
            return val.upper()

        reg = ToolRegistry()
        reg.register(make_tool("upper-tool", fn=async_fn))
        ex = ToolExecutor(registry=reg)
        result = run(ex.execute(make_call("upper-tool", args={"val": "hello"})))
        assert result.success is True
        assert result.output == "HELLO"

    def test_async_fn_timeout_returns_failure(self):
        async def slow_fn():
            await asyncio.sleep(10)

        reg = ToolRegistry()
        reg.register(make_tool("slow-tool", fn=slow_fn, timeout=0.05))
        ex = ToolExecutor(registry=reg)
        result = run(ex.execute(make_call("slow-tool")))
        assert result.success is False
        assert "timed out" in result.error.lower() or "timeout" in result.error.lower()


# ── ToolExecutor logging ──────────────────────────────────────────────────────

class TestToolExecutorLogging:

    def _setup(self) -> ToolExecutor:
        reg = ToolRegistry()
        reg.register(make_tool("tool-a"))
        reg.register(make_tool("tool-b"))
        return ToolExecutor(registry=reg)

    def test_get_call_count_without_filter(self):
        ex = self._setup()
        run(ex.execute(make_call("tool-a")))
        run(ex.execute(make_call("tool-b")))
        assert ex.get_call_count() == 2

    def test_get_call_count_with_filter(self):
        ex = self._setup()
        run(ex.execute(make_call("tool-a")))
        run(ex.execute(make_call("tool-a")))
        run(ex.execute(make_call("tool-b")))
        assert ex.get_call_count("tool-a") == 2
        assert ex.get_call_count("tool-b") == 1

    def test_get_success_rate_all_success(self):
        ex = self._setup()
        run(ex.execute(make_call("tool-a")))
        run(ex.execute(make_call("tool-a")))
        assert ex.get_success_rate("tool-a") == 1.0

    def test_get_success_rate_mixed(self):
        reg = ToolRegistry()
        reg.register(make_tool("good"))
        reg.register(make_tool("locked", whitelist=["only-this"]))
        ex = ToolExecutor(registry=reg)
        run(ex.execute(make_call("good")))          # success
        run(ex.execute(make_call("locked", capability="wrong")))  # failure (not allowed, not logged)
        # 'locked' failure from not-allowed path is not appended to _result_log
        # only 'good' is in results
        assert ex.get_success_rate() == 1.0

    def test_get_success_rate_empty_returns_zero(self):
        ex = self._setup()
        assert ex.get_success_rate() == 0.0

    def test_clear_logs_resets_counts(self):
        ex = self._setup()
        run(ex.execute(make_call("tool-a")))
        run(ex.execute(make_call("tool-b")))
        ex.clear_logs()
        assert ex.get_call_count() == 0
        assert ex.get_success_rate() == 0.0

    def test_hitl_not_counted_in_call_log(self):
        reg = ToolRegistry()
        reg.register(make_tool("hitl", requires_hitl=True))
        ex = ToolExecutor(registry=reg)
        run(ex.execute(make_call("hitl")))
        # HITL tools skip the call_log append
        assert ex.get_call_count("hitl") == 0


# ── Default tools ─────────────────────────────────────────────────────────────

class TestDefaultTools:

    def setup_method(self):
        """Gebruik een verse registry per test, niet de singleton."""
        from ollama.tool_executor import _register_default_tools
        self.reg = ToolRegistry()
        _register_default_tools(self.reg)

    def test_mollie_payment_status_registered(self):
        assert self.reg.get("mollie-payment-status") is not None

    def test_order_db_readonly_registered(self):
        assert self.reg.get("order-db-readonly") is not None

    def test_fraud_score_compute_registered(self):
        assert self.reg.get("fraud-score-compute") is not None

    def test_backoffice_write_requires_hitl(self):
        tool = self.reg.get("backoffice-write")
        assert tool is not None
        assert tool.requires_hitl is True

    def test_order_db_readonly_open_whitelist(self):
        tool = self.reg.get("order-db-readonly")
        assert tool.is_allowed_for("any-capability") is True
        assert tool.is_allowed_for("random") is True

    def test_fraud_score_compute_only_fraud_detection(self):
        tool = self.reg.get("fraud-score-compute")
        assert tool.is_allowed_for("fraud-detection") is True
        assert tool.is_allowed_for("customer-service") is False
        assert tool.is_allowed_for("order-validation") is False

    def test_mollie_allowed_for_order_validation(self):
        tool = self.reg.get("mollie-payment-status")
        assert tool.is_allowed_for("order-validation") is True

    def test_mollie_allowed_for_fraud_detection(self):
        tool = self.reg.get("mollie-payment-status")
        assert tool.is_allowed_for("fraud-detection") is True

    def test_mollie_not_allowed_for_customer_service(self):
        tool = self.reg.get("mollie-payment-status")
        assert tool.is_allowed_for("customer-service") is False

    def test_audit_log_write_open_whitelist(self):
        tool = self.reg.get("audit-log-write")
        assert tool.is_allowed_for("any-cap") is True

    def test_email_notify_allowed_for_customer_service(self):
        tool = self.reg.get("email-notify")
        assert tool.is_allowed_for("customer-service") is True

    def test_email_notify_not_allowed_for_fraud_detection(self):
        tool = self.reg.get("email-notify")
        assert tool.is_allowed_for("fraud-detection") is False

    def test_backoffice_write_not_idempotent(self):
        tool = self.reg.get("backoffice-write")
        assert tool.idempotent is False

    def test_fraud_score_compute_category_is_compute(self):
        tool = self.reg.get("fraud-score-compute")
        assert tool.category == ToolCategory.COMPUTE

    def test_order_db_readonly_category_is_read(self):
        tool = self.reg.get("order-db-readonly")
        assert tool.category == ToolCategory.READ

    def test_mollie_timeout_is_ten_seconds(self):
        tool = self.reg.get("mollie-payment-status")
        assert tool.timeout_seconds == 10.0


# ── Singleton ─────────────────────────────────────────────────────────────────

class TestSingleton:

    def test_get_tool_registry_returns_same_instance(self):
        r1 = get_tool_registry()
        r2 = get_tool_registry()
        assert r1 is r2

    def test_singleton_has_default_tools(self):
        reg = get_tool_registry()
        assert "order-db-readonly" in reg.list_all()
        assert "fraud-score-compute" in reg.list_all()
        assert "audit-log-write" in reg.list_all()
