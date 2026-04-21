"""
VorstersNV Policy Engine
Laadt YAML policy bestanden uit /policies/ en evalueert regels tegen ExecutionContext.

Integreert met ControlPlane.enforce_policy() — vervangt de hardcoded checks
door YAML-gedreven policy evaluatie.

Gebruik:
    engine = PolicyEngine()
    violations = engine.evaluate("fraud-detection", context, tools_requested=["backoffice-write"])
    engine.enforce("fraud-detection", context)  # raises PolicyViolationError bij BLOCKER
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False
    yaml = None  # type: ignore[assignment]

from ollama.control_plane import ExecutionContext, PolicyViolationError, WorkflowLane

logger = logging.getLogger(__name__)

_POLICIES_DIR = Path(__file__).parent.parent / "policies"


# ─────────────────────────────────────────────
# Violation
# ─────────────────────────────────────────────

class Severity(str, Enum):
    BLOCKER = "BLOCKER"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class PolicyViolation:
    rule_id: str
    severity: Severity
    message: str
    capability: str
    audit: bool = True
    notify: bool = False


# ─────────────────────────────────────────────
# Policy Engine
# ─────────────────────────────────────────────

class PolicyEngine:
    """
    Laadt en evalueert alle YAML policy bestanden uit /policies/.

    Evaluatievolgorde:
      1. HITL policies
      2. Maturity policies
      3. Tool policies (bij tool_requested check)

    BLOCKER violations → PolicyViolationError
    WARNING/INFO violations → alleen logging
    """

    def __init__(self, policies_dir: Path | None = None) -> None:
        self._dir = policies_dir or _POLICIES_DIR
        self._hitl_rules: list[dict] = []
        self._tool_rules: list[dict] = []
        self._maturity_rules: list[dict] = []
        self._maturity_envs: dict[str, list[str]] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        if not _YAML_AVAILABLE:
            logger.warning("PyYAML niet beschikbaar — policy engine werkt in fallback modus")
            self._loaded = True
            return
        self._load_file("hitl-policies.yaml", "_hitl_rules")
        self._load_file("maturity-policies.yaml", "_maturity_rules", extras=["maturity_environments"])
        self._load_file("tool-policies.yaml", "_tool_rules")
        self._loaded = True

    def _load_file(self, filename: str, rules_attr: str, extras: list[str] | None = None) -> None:
        path = self._dir / filename
        if not path.exists():
            logger.warning("Policy bestand niet gevonden: %s", path)
            return
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        setattr(self, rules_attr, data.get("rules", []))
        for extra_key in (extras or []):
            snake = extra_key.replace("-", "_")
            if extra_key in data:
                setattr(self, f"_{snake}", data[extra_key])
        logger.debug("Policy geladen: %s (%d regels)", filename, len(getattr(self, rules_attr)))

    # ─── Evaluatie ──────────────────────────────────────────────

    def evaluate(
        self,
        capability: str,
        context: ExecutionContext,
        tools_requested: list[str] | None = None,
        lane: WorkflowLane | None = None,
    ) -> list[PolicyViolation]:
        """
        Evalueer alle policies en return lijst van violations.
        Gooit GEEN exception — gebruik enforce() voor harde blokkering.
        """
        self._ensure_loaded()
        violations: list[PolicyViolation] = []

        violations.extend(self._eval_hitl(capability, context, lane))
        violations.extend(self._eval_maturity(capability, context))
        if tools_requested:
            violations.extend(self._eval_tools(capability, tools_requested))

        for v in violations:
            if v.severity == Severity.BLOCKER:
                logger.error("POLICY BLOCKER [%s]: %s", v.rule_id, v.message)
            elif v.severity == Severity.WARNING:
                logger.warning("POLICY WARNING [%s]: %s", v.rule_id, v.message)
            else:
                logger.info("POLICY INFO [%s]: %s", v.rule_id, v.message)

        return violations

    def enforce(
        self,
        capability: str,
        context: ExecutionContext,
        tools_requested: list[str] | None = None,
        lane: WorkflowLane | None = None,
    ) -> list[PolicyViolation]:
        """
        Evalueer policies en gooi PolicyViolationError bij eerste BLOCKER.

        Returns:
            Lijst van WARNING/INFO violations (geen BLOCKERS).
        """
        violations = self.evaluate(capability, context, tools_requested, lane)
        blockers = [v for v in violations if v.severity == Severity.BLOCKER]
        if blockers:
            first = blockers[0]
            raise PolicyViolationError(first.rule_id, first.message)
        return [v for v in violations if v.severity != Severity.BLOCKER]

    def is_tool_allowed(self, capability: str, tool: str) -> bool:
        """
        Snel controleren of een specifieke tool toegestaan is voor een capability.
        """
        self._ensure_loaded()
        rule = self._find_tool_rule(capability)
        if not rule:
            return True  # geen tool policy → alles toegestaan

        deny_tools = rule.get("deny_tools", [])
        allow_tools = rule.get("allow_tools", [])

        if tool in deny_tools:
            return False
        if allow_tools and tool not in allow_tools:
            return False
        return True

    # ─── Interne evaluatoren ────────────────────────────────────

    def _eval_hitl(
        self,
        capability: str,
        context: ExecutionContext,
        lane: WorkflowLane | None,
    ) -> list[PolicyViolation]:
        violations = []
        hitl_approved = context.metadata.get("hitl_approved", False)

        for rule in self._hitl_rules:
            when = rule.get("when", {})
            matched = True

            if "lane" in when:
                if lane is None or lane.value != when["lane"]:
                    matched = False

            if "environment" in when:
                if context.environment.value != when["environment"]:
                    matched = False

            if "hitl_approved" in when:
                if hitl_approved != when["hitl_approved"]:
                    matched = False

            if "risk_score_gte" in when:
                if context.risk_score < when["risk_score_gte"]:
                    matched = False

            if "maturity_level" in when:
                if context.maturity_level.value != when["maturity_level"]:
                    matched = False

            if matched:
                msg = rule.get("message", "Policy violation").format(
                    capability=capability,
                    risk_score=context.risk_score,
                    tenant_id=context.tenant_id,
                )
                violations.append(PolicyViolation(
                    rule_id=rule["id"],
                    severity=Severity(rule.get("severity", "BLOCKER")),
                    message=msg,
                    capability=capability,
                    audit=rule.get("audit", True),
                    notify=rule.get("notify", False),
                ))

        return violations

    def _eval_maturity(
        self,
        capability: str,
        context: ExecutionContext,
    ) -> list[PolicyViolation]:
        violations = []

        for rule in self._maturity_rules:
            when = rule.get("when", {})
            matched = True

            if "maturity_level" in when:
                if context.maturity_level.value != when["maturity_level"]:
                    matched = False

            if "environment" in when:
                if context.environment.value != when["environment"]:
                    matched = False

            if matched:
                msg = rule.get("message", "Maturity policy violation").format(
                    capability=capability,
                )
                violations.append(PolicyViolation(
                    rule_id=rule["id"],
                    severity=Severity(rule.get("severity", "BLOCKER")),
                    message=msg,
                    capability=capability,
                    audit=rule.get("audit", True),
                ))

        return violations

    def _eval_tools(
        self,
        capability: str,
        tools_requested: list[str],
    ) -> list[PolicyViolation]:
        violations = []
        rule = self._find_tool_rule(capability)
        if not rule:
            return violations

        deny_tools = set(rule.get("deny_tools", []))
        allow_tools = set(rule.get("allow_tools", []))

        for tool in tools_requested:
            blocked = False
            if tool in deny_tools:
                blocked = True
            elif allow_tools and tool not in allow_tools:
                blocked = True

            if blocked:
                msg = rule.get("message", "Tool not allowed").format(
                    tool=tool, capability=capability,
                )
                violations.append(PolicyViolation(
                    rule_id=rule["id"],
                    severity=Severity(rule.get("severity", "BLOCKER")),
                    message=msg,
                    capability=capability,
                    audit=rule.get("audit", True),
                ))

        return violations

    def _find_tool_rule(self, capability: str) -> dict[str, Any] | None:
        for rule in self._tool_rules:
            if rule.get("capability") == capability:
                return rule
        return None

    def get_allowed_tools(self, capability: str) -> list[str] | None:
        """Geef de whitelist terug voor een capability, of None als geen rule."""
        self._ensure_loaded()
        rule = self._find_tool_rule(capability)
        return rule.get("allow_tools") if rule else None

    def get_denied_tools(self, capability: str) -> list[str]:
        """Geef de blacklist terug voor een capability."""
        self._ensure_loaded()
        rule = self._find_tool_rule(capability)
        return rule.get("deny_tools", []) if rule else []


# Singleton
_engine: PolicyEngine | None = None


def get_policy_engine() -> PolicyEngine:
    """Geef de singleton PolicyEngine terug."""
    global _engine
    if _engine is None:
        _engine = PolicyEngine()
    return _engine
