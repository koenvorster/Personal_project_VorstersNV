"""
VorstersNV Review Loop
Voert een agent uit met iteratieve quality gate feedback totdat de output
goedgekeurd is of het maximum aantal iteraties bereikt is.

Gebruik:
    from ollama.review_loop import run_with_review

    output, verdict, results = await run_with_review(
        runner=runner,
        agent_name="fraud-agent",
        input_text="Analyseer order ORD-001",
        capability="fraud-detection",
        max_iterations=2,
    )
"""
from __future__ import annotations

import logging

from ..agents.agent_runner import AgentRunner
from ..observability.quality_gates import GateResult, QualityGateEngine, Verdict

logger = logging.getLogger(__name__)


async def run_with_review(
    runner: AgentRunner,
    agent_name: str,
    input_text: str,
    context: str = "",
    capability: str = "",
    max_iterations: int = 2,
    trace_id: str = "",
) -> tuple[str, Verdict, list[GateResult]]:
    """
    Voer een agent uit met iteratieve quality gate review.

    Stappen:
      1. Roep agent aan met input_text (en optionele context)
      2. Evalueer quality gates op de output
      3. Als APPROVED → return direct
      4. Als CHANGES_REQUESTED → bouw feedback prompt met de mislukte gates en
         herhaal (maximaal max_iterations keer)
      5. Als NEEDS_DISCUSSION → return direct zonder retry (BLOCKER mislukt)

    Args:
        runner:         AgentRunner instantie
        agent_name:     Naam van de te gebruiken agent
        input_text:     Originele invoer voor de agent
        context:        Optionele extra context (wordt prepended aan de prompt)
        capability:     Capability naam voor gate selectie (bijv. "fraud-detection")
        max_iterations: Maximum aantal hertries bij CHANGES_REQUESTED
        trace_id:       Optionele trace identifier

    Returns:
        Tuple van (finale output, verdict, gate resultaten van de laatste iteratie)
    """
    engine = QualityGateEngine()
    current_input = f"{context}\n\n{input_text}".strip() if context else input_text
    final_output = ""
    final_results: list[GateResult] = []
    final_verdict = Verdict.NEEDS_DISCUSSION

    for iteration in range(max_iterations + 1):
        logger.info(
            "Review loop iteratie %d/%d voor agent '%s' (trace=%s)",
            iteration + 1, max_iterations + 1, agent_name, trace_id,
        )

        output, _interaction_id, validated = await runner.run_agent(
            agent_name=agent_name,
            user_input=current_input,
        )

        gate_results = engine.run_gates(
            capability=capability,
            output=output,
            validated=validated,
            trace_id=trace_id,
        )
        verdict = engine.get_verdict(gate_results)

        final_output = output
        final_results = gate_results
        final_verdict = verdict

        logger.info(
            "Iteratie %d verdict: %s (trace=%s)",
            iteration + 1, verdict.value, trace_id,
        )

        if verdict == Verdict.APPROVED:
            return final_output, final_verdict, final_results

        if verdict == Verdict.NEEDS_DISCUSSION:
            # BLOCKER mislukt — geen retry zinvol
            logger.warning(
                "NEEDS_DISCUSSION na iteratie %d — geen retry (BLOCKER mislukt, trace=%s)",
                iteration + 1, trace_id,
            )
            return final_output, final_verdict, final_results

        # CHANGES_REQUESTED — bouw feedback prompt als er nog iteraties over zijn
        if iteration < max_iterations:
            failing = engine.get_failing_gates(gate_results)
            feedback_lines = [
                "De vorige output voldoet niet aan de kwaliteitseisen.",
                "Pas de output aan zodat de volgende punten worden opgelost:",
            ]
            for r in failing:
                feedback_lines.append(f"  - {r.message}")
            feedback_lines.append("")
            feedback_lines.append("Originele opdracht:")
            feedback_lines.append(input_text)
            current_input = "\n".join(feedback_lines)
        else:
            logger.info(
                "Maximum iteraties (%d) bereikt, return met verdict %s (trace=%s)",
                max_iterations, verdict.value, trace_id,
            )

    return final_output, final_verdict, final_results
