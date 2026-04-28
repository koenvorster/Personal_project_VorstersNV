"""
VorstersNV Consultancy Orchestrator Runner

YAML-gestuurde multi-stage pipeline voor IT/AI consultancy opdrachten.
Laadt consultancy_orchestrator.yml en voert uit:
  1. intake     — architect_agent bepaalt welke analyses nodig zijn
  2. analyses   — parallel code-analyse en/of procesanalyse (conditioneel)
  3. rapport    — klant_rapport_agent consolideert bevindingen

Gebruik:
    runner = get_consultancy_runner()
    result = await runner.run({
        "klant_naam": "Acme NV",
        "opdrachtbeschrijving": "...",
        "code_fragment": "...",
        "programmeertaal": "java",
    })
"""
import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .agent_runner import AgentRunner, RetryConfig, get_runner

logger = logging.getLogger(__name__)

CONSULTANCY_SPEC = Path(__file__).parent.parent.parent / "agents" / "consultancy_orchestrator.yml"


@dataclass
class ConsultancyResult:
    """Gestructureerd resultaat van de consultancy pipeline."""

    klant_naam: str
    rapport_markdown: str = ""
    executive_summary: str = ""
    business_rules: list[str] = field(default_factory=list)
    automatisering_score: float | None = None
    aanbevelingen_top3: list[str] = field(default_factory=list)
    stage_outputs: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    success: bool = True


# ─────────────────────────────────────────────
# Helper: dotted-path resolver
# ─────────────────────────────────────────────

def _resolve_path(path: str, context: dict[str, Any]) -> Any:
    """
    Los een dotted path op in de context.

    Voorbeeld: "intake.code_analyse_vereist" → context["intake"]["code_analyse_vereist"]
    Geeft None als het pad niet bestaat.
    """
    current: Any = context
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _resolve_mapping(mapping: Any, context: dict[str, Any]) -> Any:
    """
    Los een input_mapping op recursief.

    Strings met dotted-path notatie worden opgelost uit context.
    Overige strings, dicts en lijsten worden recursief verwerkt.
    """
    if isinstance(mapping, str):
        if "." in mapping:
            resolved = _resolve_path(mapping, context)
            if resolved is not None:
                return resolved
        return mapping
    if isinstance(mapping, dict):
        return {k: _resolve_mapping(v, context) for k, v in mapping.items()}
    if isinstance(mapping, list):
        return [_resolve_mapping(item, context) for item in mapping]
    return mapping


def _eval_condition(condition: str, context: dict[str, Any]) -> bool:
    """
    Evalueer een eenvoudige conditie: "path == value" of "path != value".

    Ondersteunt: true/false/null en stringvergelijkingen.
    Geeft True als de stap uitgevoerd moet worden.
    """
    condition = condition.strip()
    for op in ("==", "!="):
        if op in condition:
            left, right = (p.strip() for p in condition.split(op, 1))
            actual = _resolve_path(left, context)
            if right.lower() == "true":
                expected: Any = True
            elif right.lower() == "false":
                expected = False
            elif right.lower() == "null":
                expected = None
            else:
                expected = right.strip("\"'")
            return actual == expected if op == "==" else actual != expected
    # Geen operator: controleer of het pad truthy is
    return bool(_resolve_path(condition, context))


# ─────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────

class ConsultancyOrchestratorRunner:
    """
    YAML-gestuurde runner voor de consultancy pipeline.

    Voert de drie stages uit zoals gedefinieerd in consultancy_orchestrator.yml:
      1. intake    — bepaalt welke analyses nodig zijn
      2. analyses  — parallel code-analyse en/of procesanalyse (conditioneel)
      3. rapport   — consolideert bevindingen in klantrapport
    """

    def __init__(
        self,
        runner: AgentRunner | None = None,
        spec_path: Path = CONSULTANCY_SPEC,
    ):
        self._runner = runner or get_runner()
        self._spec: dict[str, Any] = yaml.safe_load(spec_path.read_text(encoding="utf-8"))

    async def run(
        self,
        opdracht: dict[str, Any],
        retry_config: RetryConfig | None = None,
    ) -> ConsultancyResult:
        """
        Voer de volledige consultancy pipeline uit.

        Args:
            opdracht: Input dict — vereist: klant_naam, opdrachtbeschrijving
            retry_config: Optionele retry-instellingen (standaard: 3 pogingen)

        Returns:
            ConsultancyResult met rapport_markdown, business_rules, etc.
        """
        klant_naam = opdracht.get("klant_naam", "onbekend")
        context: dict[str, Any] = {"opdracht": opdracht}
        result = ConsultancyResult(klant_naam=klant_naam)

        try:
            await self._run_intake(context, result, retry_config)
            if not result.success:
                return result

            await self._run_analyses(context, result, retry_config)
            if not result.success:
                return result

            await self._run_rapport(context, result, retry_config)

        except Exception as exc:
            logger.error("ConsultancyOrchestratorRunner fatale fout: %s", exc)
            result.errors.append(str(exc))
            result.success = False

        return result

    async def _run_intake(
        self,
        context: dict[str, Any],
        result: ConsultancyResult,
        retry_config: RetryConfig | None,
    ) -> None:
        """Stage 1: Intake — architect_agent bepaalt welke modules nodig zijn."""
        intake_spec = self._spec["intake"]
        agent_name: str = intake_spec["agent"]
        opdracht = context["opdracht"]

        user_input = (
            f"Analyseer deze opdracht voor {opdracht.get('klant_naam', 'de klant')}.\n"
            f"Opdracht: {opdracht.get('opdrachtbeschrijving', '')}\n"
            f"Bepaal welke analyse-modules nodig zijn."
        )

        logger.info("Consultancy intake — agent='%s'", agent_name)
        try:
            output, _, validated = await self._runner.run_agent_with_retry(
                agent_name=agent_name,
                user_input=user_input,
                context=opdracht,
                retry_config=retry_config,
            )
            context["intake"] = validated if validated is not None else {}
            result.stage_outputs["intake"] = output
            logger.info("Intake klaar — output velden: %s", list(context["intake"].keys()))
        except Exception as exc:
            logger.error("Intake mislukt: %s", exc)
            result.errors.append(f"intake: {exc}")
            result.success = False

    async def _run_analyses(
        self,
        context: dict[str, Any],
        result: ConsultancyResult,
        retry_config: RetryConfig | None,
    ) -> None:
        """Stage 2: Parallelle analyse-agents (conditioneel op intake output)."""
        analyses_spec = self._spec["analyses"]
        agents_spec: list[dict[str, Any]] = analyses_spec.get("agents", [])
        is_parallel: bool = analyses_spec.get("parallel", False)

        active = [
            spec for spec in agents_spec
            if not spec.get("condition") or _eval_condition(spec["condition"], context)
        ]

        if not active:
            logger.info("Geen analyse-agents actief voor deze opdracht")
            context["analyses"] = {}
            return

        logger.info(
            "Analyses starten: %d agent(s) %s",
            len(active), "parallel" if is_parallel else "sequentieel",
        )

        context["analyses"] = {}
        if is_parallel:
            tasks = [self._run_single_analysis(spec, context, retry_config) for spec in active]
            outputs = await asyncio.gather(*tasks, return_exceptions=True)
            for spec, output in zip(active, outputs):
                if isinstance(output, Exception):
                    logger.error("Analyse '%s' mislukt: %s", spec["id"], output)
                    result.errors.append(f"analyses.{spec['id']}: {output}")
                else:
                    context["analyses"][spec["id"]] = output
                    result.stage_outputs[f"analyses.{spec['id']}"] = output.get("output", "")
        else:
            for spec in active:
                try:
                    output = await self._run_single_analysis(spec, context, retry_config)
                    context["analyses"][spec["id"]] = output
                    result.stage_outputs[f"analyses.{spec['id']}"] = output.get("output", "")
                except Exception as exc:
                    logger.error("Analyse '%s' mislukt: %s", spec["id"], exc)
                    result.errors.append(f"analyses.{spec['id']}: {exc}")

    async def _run_single_analysis(
        self,
        agent_spec: dict[str, Any],
        context: dict[str, Any],
        retry_config: RetryConfig | None,
    ) -> dict[str, Any]:
        """Voer één analyse-agent uit en geef de output terug."""
        agent_name: str = agent_spec["agent"]
        input_mapping = agent_spec.get("input_mapping", {})
        resolved = _resolve_mapping(input_mapping, context)
        user_input = " | ".join(f"{k}: {v}" for k, v in resolved.items() if v)

        logger.info("Analyse agent='%s' gestart", agent_name)
        output, _, validated = await self._runner.run_agent_with_retry(
            agent_name=agent_name,
            user_input=user_input,
            context=resolved,
            retry_config=retry_config,
        )
        return {"output": output, "validated": validated}

    async def _run_rapport(
        self,
        context: dict[str, Any],
        result: ConsultancyResult,
        retry_config: RetryConfig | None,
    ) -> None:
        """Stage 3: Rapport consolidatie via klant_rapport_agent."""
        rapport_spec = self._spec["rapport"]
        agent_name: str = rapport_spec["agent"]
        resolved = _resolve_mapping(rapport_spec.get("input_mapping", {}), context)
        opdracht = context["opdracht"]

        user_input = (
            f"Genereer een {resolved.get('rapport_type', 'analyse_rapport')} voor "
            f"{resolved.get('klant_naam', opdracht.get('klant_naam', 'de klant'))}.\n"
            f"Doelgroep: {resolved.get('doelgroep', 'it_team')}.\n"
            f"Bevindingen: {resolved.get('bevindingen', {})}.\n"
            f"Taal: {resolved.get('taal', 'nl')}."
        )

        logger.info("Rapport generatie — agent='%s'", agent_name)
        try:
            output, _, validated = await self._runner.run_agent_with_retry(
                agent_name=agent_name,
                user_input=user_input,
                context=resolved,
                retry_config=retry_config,
            )
            result.rapport_markdown = output
            result.stage_outputs["rapport"] = output
            if validated:
                result.executive_summary = validated.get("executive_summary", "")
                result.business_rules = validated.get("business_rules", [])
                result.automatisering_score = validated.get("automatisering_score")
                result.aanbevelingen_top3 = validated.get("aanbevelingen_top3", [])
            logger.info("Rapport gegenereerd: %d tekens", len(output))
        except Exception as exc:
            logger.error("Rapport generatie mislukt: %s", exc)
            result.errors.append(f"rapport: {exc}")
            result.success = False


def get_consultancy_runner(
    spec_path: Path = CONSULTANCY_SPEC,
) -> ConsultancyOrchestratorRunner:
    """Geef een ConsultancyOrchestratorRunner terug met de singleton AgentRunner."""
    return ConsultancyOrchestratorRunner(runner=get_runner(), spec_path=spec_path)
