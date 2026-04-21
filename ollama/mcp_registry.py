"""
MCP Tool Registry — laadt tool metadata uit YAML en ondersteunt
dynamic discovery, fallback routing en OTel span tracking.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any
from pathlib import Path


@dataclass
class ToolCostInfo:
    unit: str
    estimated_eur: float


@dataclass
class ToolAuthInfo:
    type: str          # api_key | service_account | none
    env_var: Optional[str] = None


@dataclass
class MCPToolDefinition:
    name: str
    version: str
    owner: str
    description: str
    category: str
    capabilities: list[str]    # leeg = allen toegestaan
    auth: ToolAuthInfo
    cost_per_call: ToolCostInfo
    reliability_score: float
    timeout_seconds: float
    idempotent: bool
    requires_hitl: bool
    input_schema: dict
    output_schema: dict
    fallback_tool: Optional[str]
    otel_span: bool

    def is_allowed_for(self, capability: str) -> bool:
        if not self.capabilities:
            return True
        return capability in self.capabilities

    def get_fallback(self) -> Optional[str]:
        return self.fallback_tool

    def estimated_cost_eur(self, calls: int = 1) -> float:
        return self.cost_per_call.estimated_eur * calls


class MCPToolRegistry:
    """
    Laadt en beheert MCP tool metadata uit .claude/tool-registry.yaml.
    Ondersteunt fallback routing en dynamic discovery.
    """

    REGISTRY_FILE = Path(__file__).parent.parent / ".claude" / "tool-registry.yaml"

    def __init__(self, registry_file: Optional[Path] = None):
        self._file = registry_file or self.REGISTRY_FILE
        self._tools: dict[str, MCPToolDefinition] = {}
        self._loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            self._load()
            self._loaded = True

    def _load(self):
        if not self._file.exists():
            return
        try:
            import yaml
            data = yaml.safe_load(self._file.read_text(encoding="utf-8"))
            for tool_data in data.get("tools", []):
                tool = self._parse(tool_data)
                self._tools[tool.name] = tool
        except Exception:
            pass

    def _parse(self, data: dict) -> MCPToolDefinition:
        auth_data = data.get("auth", {})
        cost_data = data.get("cost_per_call", {})
        return MCPToolDefinition(
            name=data["name"],
            version=data.get("version", "1.0"),
            owner=data.get("owner", "unknown"),
            description=data.get("description", ""),
            category=data.get("category", "compute"),
            capabilities=data.get("capabilities") or [],
            auth=ToolAuthInfo(
                type=auth_data.get("type", "none"),
                env_var=auth_data.get("env_var"),
            ),
            cost_per_call=ToolCostInfo(
                unit=cost_data.get("unit", "call"),
                estimated_eur=cost_data.get("estimated_eur", 0.0),
            ),
            reliability_score=data.get("reliability_score", 1.0),
            timeout_seconds=data.get("timeout_seconds", 30.0),
            idempotent=data.get("idempotent", True),
            requires_hitl=data.get("requires_hitl", False),
            input_schema=data.get("input_schema", {}),
            output_schema=data.get("output_schema", {}),
            fallback_tool=data.get("fallback_tool"),
            otel_span=data.get("otel_span", False),
        )

    def get(self, name: str) -> Optional[MCPToolDefinition]:
        self._ensure_loaded()
        return self._tools.get(name)

    def list_all(self) -> list[str]:
        self._ensure_loaded()
        return list(self._tools.keys())

    def list_for_capability(self, capability: str) -> list[MCPToolDefinition]:
        self._ensure_loaded()
        return [t for t in self._tools.values() if t.is_allowed_for(capability)]

    def list_by_category(self, category: str) -> list[MCPToolDefinition]:
        self._ensure_loaded()
        return [t for t in self._tools.values() if t.category == category]

    def resolve_fallback(self, tool_name: str) -> Optional[MCPToolDefinition]:
        """Geeft de fallback tool terug als de gevraagde tool faalt."""
        self._ensure_loaded()
        tool = self._tools.get(tool_name)
        if tool and tool.fallback_tool:
            return self._tools.get(tool.fallback_tool)
        return None

    def get_total_cost_estimate(self, tool_names: list[str], calls_each: int = 1) -> float:
        self._ensure_loaded()
        total = 0.0
        for name in tool_names:
            tool = self._tools.get(name)
            if tool:
                total += tool.estimated_cost_eur(calls_each)
        return round(total, 6)

    def register(self, tool: MCPToolDefinition) -> None:
        self._tools[tool.name] = tool
        self._loaded = True

    def reload(self) -> None:
        self._tools = {}
        self._loaded = False
        self._ensure_loaded()


def get_mcp_registry() -> MCPToolRegistry:
    global _registry
    if _registry is None:
        _registry = MCPToolRegistry()
    return _registry

_registry: Optional[MCPToolRegistry] = None
