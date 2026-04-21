"""
Capability Registry — laadt en beheert capability YAML bestanden.
Koppelt capabilities aan agents, chains en contracts.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class CapabilityMaturity:
    level: str          # L1, L2, L3, L4
    label: str          # experimental, internal-beta, team-production, business-critical
    eval_required: bool = False
    human_approval_required: bool = False
    min_first_pass_score: float = 0.80


@dataclass
class CapabilityOperational:
    owner: str
    sla_tier: str        # bronze, silver, gold, platinum
    cost_budget_monthly_eur: float
    preferred_model: str = "llama3"
    escalation_model: str = "llama3.1"


@dataclass
class CapabilityRelease:
    rollout_ring: str    # ring-0 .. ring-4
    feature_flag: str


@dataclass
class CapabilityDefinition:
    name: str
    version: str
    description: str
    lane: str
    audience: str
    risk: str
    maturity: CapabilityMaturity
    operational: CapabilityOperational
    release: CapabilityRelease
    agents: list[str] = field(default_factory=list)
    contract: Optional[str] = None
    chain: Optional[str] = None

    def is_production_ready(self) -> bool:
        return self.maturity.level in ("L3", "L4")

    def requires_human_approval(self) -> bool:
        return self.maturity.human_approval_required is True

    def get_ring_number(self) -> int:
        return int(self.release.rollout_ring.split("-")[-1])


class CapabilityRegistry:
    """Loads and manages capability definitions from YAML files."""

    CAPABILITIES_DIR = Path(__file__).parent.parent / ".claude" / "capabilities"

    def __init__(self, capabilities_dir: Optional[Path] = None):
        self._dir = capabilities_dir or self.CAPABILITIES_DIR
        self._capabilities: dict[str, CapabilityDefinition] = {}
        self._loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            self._load_all()
            self._loaded = True

    def _load_all(self):
        if not self._dir.exists():
            return
        try:
            import yaml
            for yml_file in self._dir.glob("*.yaml"):
                if yml_file.name == "index.yaml":
                    continue
                try:
                    data = yaml.safe_load(yml_file.read_text(encoding="utf-8"))
                    if not isinstance(data, dict) or "name" not in data or "maturity" not in data:
                        continue
                    cap = self._parse(data)
                    self._capabilities[cap.name] = cap
                except Exception:
                    pass
        except ImportError:
            pass

    def _parse(self, data: dict) -> CapabilityDefinition:
        mat = data.get("maturity", {})
        op = data.get("operational", {})
        rel = data.get("release", {})
        return CapabilityDefinition(
            name=data["name"],
            version=data.get("version", "1.0"),
            description=data.get("description", ""),
            lane=data.get("lane", "deterministic"),
            audience=data.get("audience", "internal"),
            risk=data.get("risk", "low"),
            maturity=CapabilityMaturity(
                level=mat.get("level", "L1"),
                label=mat.get("label", "experimental"),
                eval_required=mat.get("eval_required", False),
                human_approval_required=mat.get("human_approval_required", False),
                min_first_pass_score=mat.get("min_first_pass_score", 0.80),
            ),
            operational=CapabilityOperational(
                owner=op.get("owner", "unknown"),
                sla_tier=op.get("sla_tier", "bronze"),
                cost_budget_monthly_eur=op.get("cost_budget_monthly_eur", 50.0),
                preferred_model=op.get("preferred_model", "llama3"),
                escalation_model=op.get("escalation_model", "llama3.1"),
            ),
            release=CapabilityRelease(
                rollout_ring=rel.get("rollout_ring", "ring-0"),
                feature_flag=rel.get("feature_flag", f"ai.capability.{data['name']}"),
            ),
            agents=data.get("agents", []),
            contract=data.get("contract"),
            chain=data.get("chain"),
        )

    def get(self, name: str) -> Optional[CapabilityDefinition]:
        self._ensure_loaded()
        return self._capabilities.get(name)

    def list_all(self) -> list[str]:
        self._ensure_loaded()
        return list(self._capabilities.keys())

    def list_by_lane(self, lane: str) -> list[CapabilityDefinition]:
        self._ensure_loaded()
        return [c for c in self._capabilities.values() if c.lane == lane]

    def list_production_ready(self) -> list[CapabilityDefinition]:
        self._ensure_loaded()
        return [c for c in self._capabilities.values() if c.is_production_ready()]

    def get_by_agent(self, agent_name: str) -> list[CapabilityDefinition]:
        self._ensure_loaded()
        return [c for c in self._capabilities.values() if agent_name in c.agents]

    def register(self, cap: CapabilityDefinition):
        self._capabilities[cap.name] = cap
        self._loaded = True

    def reload(self):
        self._capabilities = {}
        self._loaded = False
        self._ensure_loaded()


def get_capability_registry() -> CapabilityRegistry:
    global _registry
    if _registry is None:
        _registry = CapabilityRegistry()
    return _registry


_registry: Optional[CapabilityRegistry] = None
