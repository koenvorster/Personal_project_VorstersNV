"""
Tool Executor — registry en executor voor agent tool-calls.

Tools zijn benoemde functies die agents kunnen aanroepen.
De executor controleert policies, logt usage en handelt errors af.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from enum import Enum
import asyncio
import functools


class ToolCategory(Enum):
    READ = "read"           # read-only data access
    WRITE = "write"         # data mutatie
    EXTERNAL = "external"   # externe API call
    COMPUTE = "compute"     # berekening zonder side effects
    NOTIFY = "notify"       # notificatie versturen


@dataclass
class ToolDefinition:
    name: str
    description: str
    category: ToolCategory
    capability_whitelist: list[str]    # welke capabilities mogen dit gebruiken (leeg = allen)
    requires_hitl: bool = False        # vereist menselijke goedkeuring?
    idempotent: bool = True            # veilig om te herhalen?
    timeout_seconds: float = 30.0
    fn: Optional[Callable] = field(default=None, repr=False)

    def is_allowed_for(self, capability: str) -> bool:
        if not self.capability_whitelist:
            return True
        return capability in self.capability_whitelist


@dataclass
class ToolCall:
    tool_name: str
    capability: str
    arguments: dict[str, Any]
    trace_id: str = ""


@dataclass
class ToolResult:
    tool_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    duration_ms: float = 0.0
    hitl_required: bool = False
    hitl_approved: Optional[bool] = None


class ToolNotFoundError(Exception):
    pass

class ToolNotAllowedError(Exception):
    pass

class ToolTimeoutError(Exception):
    pass


class ToolRegistry:
    """Beheert alle beschikbare tools."""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_all(self) -> list[str]:
        return list(self._tools.keys())

    def list_by_category(self, category: ToolCategory) -> list[ToolDefinition]:
        return [t for t in self._tools.values() if t.category == category]

    def list_for_capability(self, capability: str) -> list[ToolDefinition]:
        return [t for t in self._tools.values() if t.is_allowed_for(capability)]


class ToolExecutor:
    """Voert tool calls uit met policy check, timeout en logging."""

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self._registry = registry or get_tool_registry()
        self._call_log: list[ToolCall] = []
        self._result_log: list[ToolResult] = []

    async def execute(self, call: ToolCall) -> ToolResult:
        import time
        start = time.monotonic()

        tool = self._registry.get(call.tool_name)
        if tool is None:
            return ToolResult(
                tool_name=call.tool_name,
                success=False,
                output=None,
                error=f"Tool '{call.tool_name}' not found",
            )

        if not tool.is_allowed_for(call.capability):
            return ToolResult(
                tool_name=call.tool_name,
                success=False,
                output=None,
                error=f"Tool '{call.tool_name}' not allowed for capability '{call.capability}'",
            )

        if tool.requires_hitl:
            result = ToolResult(
                tool_name=call.tool_name,
                success=False,
                output=None,
                hitl_required=True,
                error="Human approval required before executing this tool",
            )
            self._result_log.append(result)
            return result

        if tool.fn is None:
            duration = (time.monotonic() - start) * 1000
            result = ToolResult(
                tool_name=call.tool_name,
                success=True,
                output={"mock": True, "tool": call.tool_name, "args": call.arguments},
                duration_ms=round(duration, 2),
            )
            self._call_log.append(call)
            self._result_log.append(result)
            return result

        try:
            if asyncio.iscoroutinefunction(tool.fn):
                output = await asyncio.wait_for(
                    tool.fn(**call.arguments),
                    timeout=tool.timeout_seconds,
                )
            else:
                output = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, functools.partial(tool.fn, **call.arguments)),
                    timeout=tool.timeout_seconds,
                )
            duration = (time.monotonic() - start) * 1000
            result = ToolResult(
                tool_name=call.tool_name,
                success=True,
                output=output,
                duration_ms=round(duration, 2),
            )
        except asyncio.TimeoutError:
            duration = (time.monotonic() - start) * 1000
            result = ToolResult(
                tool_name=call.tool_name,
                success=False,
                output=None,
                error=f"Tool '{call.tool_name}' timed out after {tool.timeout_seconds}s",
                duration_ms=round(duration, 2),
            )
        except Exception as e:
            duration = (time.monotonic() - start) * 1000
            result = ToolResult(
                tool_name=call.tool_name,
                success=False,
                output=None,
                error=str(e),
                duration_ms=round(duration, 2),
            )

        self._call_log.append(call)
        self._result_log.append(result)
        return result

    def get_call_count(self, tool_name: Optional[str] = None) -> int:
        if tool_name:
            return sum(1 for c in self._call_log if c.tool_name == tool_name)
        return len(self._call_log)

    def get_success_rate(self, tool_name: Optional[str] = None) -> float:
        results = self._result_log
        if tool_name:
            results = [r for r in results if r.tool_name == tool_name]
        if not results:
            return 0.0
        return sum(1 for r in results if r.success) / len(results)

    def clear_logs(self):
        self._call_log = []
        self._result_log = []


# Singleton registry met standaard tools
_registry: Optional[ToolRegistry] = None

def get_tool_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _register_default_tools(_registry)
    return _registry

def _register_default_tools(registry: ToolRegistry):
    """Registreert standaard VorstersNV tools."""
    defaults = [
        ToolDefinition(
            name="mollie-payment-status",
            description="Haalt betalingsstatus op van Mollie",
            category=ToolCategory.EXTERNAL,
            capability_whitelist=["order-validation", "fraud-detection"],
            idempotent=True,
            timeout_seconds=10.0,
        ),
        ToolDefinition(
            name="order-db-readonly",
            description="Leest orderdata uit de database (read-only)",
            category=ToolCategory.READ,
            capability_whitelist=[],  # allen toegestaan
            idempotent=True,
        ),
        ToolDefinition(
            name="fraud-score-compute",
            description="Berekent fraudescore op basis van orderdata",
            category=ToolCategory.COMPUTE,
            capability_whitelist=["fraud-detection"],
            idempotent=True,
        ),
        ToolDefinition(
            name="backoffice-write",
            description="Schrijft naar backoffice systeem (HITL vereist)",
            category=ToolCategory.WRITE,
            capability_whitelist=["order-validation"],
            requires_hitl=True,
            idempotent=False,
        ),
        ToolDefinition(
            name="email-notify",
            description="Verstuurt e-mailnotificatie naar klant",
            category=ToolCategory.NOTIFY,
            capability_whitelist=["customer-service", "order-validation"],
            idempotent=False,
        ),
        ToolDefinition(
            name="audit-log-write",
            description="Schrijft audit entry naar compliance log",
            category=ToolCategory.WRITE,
            capability_whitelist=[],  # allen toegestaan
            idempotent=True,
        ),
    ]
    for tool in defaults:
        registry.register(tool)
