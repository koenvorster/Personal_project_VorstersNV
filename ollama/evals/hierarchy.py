"""
4-Level Evaluation Hierarchy voor VorstersNV AI Platform.

Level 1 — UNIT:     Is de agent output schema-correct?
Level 2 — CAPABILITY: Kiest de agent de juiste output + tool?
Level 3 — CHAIN:    Volgt de chain de juiste flow + kan hij herstellen na fout?
Level 4 — BUSINESS: Neemt het systeem correcte beslissingen? Hoeveel false positives?
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum
import json


class EvalLevel(Enum):
    UNIT = 1
    CAPABILITY = 2
    CHAIN = 3
    BUSINESS = 4


@dataclass
class LevelResult:
    level: EvalLevel
    agent_name: str
    passed: bool
    score: float       # 0.0 - 1.0
    details: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        if self.score >= 0.85:
            return "PASS"
        elif self.score >= 0.65:
            return "NEEDS_REVIEW"
        return "FAIL"


@dataclass
class HierarchyResult:
    agent_name: str
    levels_run: list[EvalLevel]
    results: dict[str, LevelResult]   # level.name → result
    overall_score: float = 0.0
    overall_verdict: str = "UNKNOWN"
    blocking_level: Optional[str] = None  # eerste level dat faalt

    def __post_init__(self):
        if self.results:
            self.overall_score = sum(r.score for r in self.results.values()) / len(self.results)
        if self.overall_score >= 0.85:
            self.overall_verdict = "PASS"
        elif self.overall_score >= 0.65:
            self.overall_verdict = "NEEDS_REVIEW"
        else:
            self.overall_verdict = "FAIL"
        # Vind het eerste falende level
        for level in EvalLevel:
            name = level.name
            if name in self.results and not self.results[name].passed:
                self.blocking_level = name
                break


class EvalSuite:
    """Runs evaluation at a specific level for an agent."""

    # Level 1: Unit — schema validation
    def run_unit(self, agent_name: str, output: str, expected_schema: Optional[dict] = None) -> LevelResult:
        details = []
        errors = []
        score = 1.0

        if not output or not output.strip():
            errors.append("Output is leeg")
            score = 0.0
        else:
            details.append(f"Output aanwezig ({len(output)} chars)")

        if expected_schema:
            try:
                parsed = json.loads(output) if output.strip().startswith("{") else None
                if parsed is None:
                    errors.append("Output is geen geldige JSON")
                    score = max(0.0, score - 0.5)
                else:
                    for key in expected_schema.get("required", []):
                        if key not in parsed:
                            errors.append(f"Verplicht veld ontbreekt: {key}")
                            score = max(0.0, score - 0.2)
                        else:
                            details.append(f"Veld aanwezig: {key}")
            except Exception as e:
                errors.append(f"JSON schema validatie fout: {e}")
                score = max(0.0, score - 0.3)

        return LevelResult(
            level=EvalLevel.UNIT,
            agent_name=agent_name,
            passed=score >= 0.7,
            score=round(score, 2),
            details=details,
            errors=errors,
        )

    # Level 2: Capability — juiste output + tool gekozen?
    def run_capability(
        self,
        agent_name: str,
        output: str,
        expected_keywords: list[str],
        tool_used: Optional[str] = None,
        expected_tool: Optional[str] = None,
    ) -> LevelResult:
        details = []
        errors = []
        score = 1.0

        # Check keywords in output
        found = [kw for kw in expected_keywords if kw.lower() in output.lower()]
        missing = [kw for kw in expected_keywords if kw.lower() not in output.lower()]

        if expected_keywords:
            keyword_score = len(found) / len(expected_keywords)
            score = keyword_score
            details.append(f"Keywords gevonden: {found}")
            if missing:
                errors.append(f"Keywords ontbreken: {missing}")

        # Check tool
        if expected_tool and tool_used != expected_tool:
            errors.append(f"Verwachte tool '{expected_tool}', gebruikt '{tool_used}'")
            score = max(0.0, score - 0.3)
        elif expected_tool and tool_used == expected_tool:
            details.append(f"Correcte tool gebruikt: {tool_used}")

        return LevelResult(
            level=EvalLevel.CAPABILITY,
            agent_name=agent_name,
            passed=score >= 0.7,
            score=round(score, 2),
            details=details,
            errors=errors,
        )

    # Level 3: Chain — juiste flow + checkpoint recovery?
    def run_chain(
        self,
        agent_name: str,
        completed_steps: list[str],
        expected_steps: list[str],
        checkpoint_recovery_tested: bool = False,
    ) -> LevelResult:
        details = []
        errors = []

        if not expected_steps:
            return LevelResult(EvalLevel.CHAIN, agent_name, True, 1.0, ["Geen steps verwacht"])

        found = [s for s in expected_steps if s in completed_steps]
        missing = [s for s in expected_steps if s not in completed_steps]
        score = len(found) / len(expected_steps)

        details.append(f"Stappen voltooid: {found}")
        if missing:
            errors.append(f"Stappen ontbreken: {missing}")

        # Check volgorde
        indices = [completed_steps.index(s) for s in found if s in completed_steps]
        if indices != sorted(indices):
            errors.append("Stappen niet in verwachte volgorde uitgevoerd")
            score = max(0.0, score - 0.2)
        else:
            details.append("Volgorde correct")

        if checkpoint_recovery_tested:
            details.append("Checkpoint recovery getest ✓")
            score = min(1.0, score + 0.1)

        return LevelResult(
            level=EvalLevel.CHAIN,
            agent_name=agent_name,
            passed=score >= 0.7,
            score=round(score, 2),
            details=details,
            errors=errors,
        )

    # Level 4: Business — correcte beslissing + false positives?
    def run_business(
        self,
        agent_name: str,
        decisions: list[dict],  # {"predicted": "BLOCK", "actual": "BLOCK"}
    ) -> LevelResult:
        details = []
        errors = []

        if not decisions:
            return LevelResult(EvalLevel.BUSINESS, agent_name, False, 0.0, [], ["Geen beslissingen aangeleverd"])

        correct = sum(1 for d in decisions if d.get("predicted") == d.get("actual"))
        accuracy = correct / len(decisions)

        # False positive rate
        false_positives = sum(
            1 for d in decisions
            if d.get("predicted") == "BLOCK" and d.get("actual") == "ALLOW"
        )
        fp_rate = false_positives / len(decisions)

        details.append(f"Accuracy: {accuracy:.1%} ({correct}/{len(decisions)})")
        details.append(f"False positive rate: {fp_rate:.1%}")

        score = accuracy
        if fp_rate > 0.10:
            errors.append(f"False positive rate te hoog: {fp_rate:.1%} (max 10%)")
            score = max(0.0, score - 0.2)

        return LevelResult(
            level=EvalLevel.BUSINESS,
            agent_name=agent_name,
            passed=score >= 0.7,
            score=round(score, 2),
            details=details,
            errors=errors,
        )


class EvalHierarchy:
    """Runs multi-level evaluation for one or more agents."""

    def __init__(self):
        self._suite = EvalSuite()

    def run_eval_suite(
        self,
        agent_name: str,
        level: EvalLevel,
        **kwargs,
    ) -> LevelResult:
        """Runs a single level evaluation."""
        if level == EvalLevel.UNIT:
            return self._suite.run_unit(agent_name, **kwargs)
        elif level == EvalLevel.CAPABILITY:
            return self._suite.run_capability(agent_name, **kwargs)
        elif level == EvalLevel.CHAIN:
            return self._suite.run_chain(agent_name, **kwargs)
        elif level == EvalLevel.BUSINESS:
            return self._suite.run_business(agent_name, **kwargs)
        raise ValueError(f"Unknown level: {level}")

    def run_full_hierarchy(
        self,
        agent_name: str,
        unit_kwargs: Optional[dict] = None,
        capability_kwargs: Optional[dict] = None,
        chain_kwargs: Optional[dict] = None,
        business_kwargs: Optional[dict] = None,
        stop_on_fail: bool = True,
    ) -> HierarchyResult:
        """Runs all 4 levels, optionally stopping at first failure."""
        results = {}
        levels_run = []

        level_configs = [
            (EvalLevel.UNIT, unit_kwargs),
            (EvalLevel.CAPABILITY, capability_kwargs),
            (EvalLevel.CHAIN, chain_kwargs),
            (EvalLevel.BUSINESS, business_kwargs),
        ]

        for level, kwargs in level_configs:
            if kwargs is None:
                continue
            result = self.run_eval_suite(agent_name, level, **kwargs)
            results[level.name] = result
            levels_run.append(level)

            if stop_on_fail and not result.passed:
                break

        return HierarchyResult(
            agent_name=agent_name,
            levels_run=levels_run,
            results=results,
        )

    def get_ci_levels(self) -> list[EvalLevel]:
        """L1+L2 worden automatisch gerund in CI."""
        return [EvalLevel.UNIT, EvalLevel.CAPABILITY]

    def get_release_levels(self) -> list[EvalLevel]:
        """L3+L4 worden gerund bij release."""
        return [EvalLevel.CHAIN, EvalLevel.BUSINESS]


def get_eval_hierarchy() -> EvalHierarchy:
    global _hierarchy
    if _hierarchy is None:
        _hierarchy = EvalHierarchy()
    return _hierarchy

_hierarchy: Optional[EvalHierarchy] = None
