"""
Tests voor ConsultancyOrchestratorRunner en helpers.

Gebruikt mock AgentRunner — geen echte Ollama-verbinding vereist.
"""
import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ollama.agent_runner import AgentRunner
from ollama.consultancy_runner import (
    ConsultancyOrchestratorRunner,
    ConsultancyResult,
    _eval_condition,
    _resolve_mapping,
    _resolve_path,
    get_consultancy_runner,
)

# ─────────────────────────────────────────────────────────
# Fixtures & helpers
# ─────────────────────────────────────────────────────────

SPEC_PATH = Path(__file__).parent.parent / "agents" / "consultancy_orchestrator.yml"

_INTAKE_OUTPUT_VALIDATED = {
    "code_analyse_vereist": True,
    "procesanalyse_vereist": False,
    "rapport_type": "code_analyse_rapport",
    "doelgroep": "it_team",
    "taal": "nl",
}

_CODE_ANALYSE_OUTPUT = "## Code-analyse resultaten\nBevindingen: N+1 queries gevonden."
_RAPPORT_OUTPUT = "## Klantrapport\nSamenvatting van bevindingen voor Acme NV."

_RAPPORT_VALIDATED = {
    "executive_summary": "Korte samenvatting.",
    "business_rules": ["Regel A", "Regel B"],
    "automatisering_score": 72.5,
    "aanbevelingen_top3": ["Aanbeveling 1", "Aanbeveling 2", "Aanbeveling 3"],
}


def _make_runner(responses: dict[str, tuple[str, dict | None]]) -> AgentRunner:
    """Maak een mock AgentRunner met voorgedefinieerde antwoorden per agent."""
    runner = MagicMock(spec=AgentRunner)

    async def _run(agent_name, user_input, context=None, client=None, retry_config=None):
        text, validated = responses.get(agent_name, (f"<output van {agent_name}>", None))
        return text, f"interaction-{agent_name}", validated

    runner.run_agent_with_retry = AsyncMock(side_effect=_run)
    return runner


def _full_runner() -> AgentRunner:
    """Runner met antwoorden voor alle drie de stages."""
    return _make_runner({
        "architect_agent": (json.dumps(_INTAKE_OUTPUT_VALIDATED), _INTAKE_OUTPUT_VALIDATED),
        "code_analyse_agent": (_CODE_ANALYSE_OUTPUT, None),
        "bedrijfsproces_agent": ("## Procesanalyse\nDetails.", None),
        "klant_rapport_agent": (_RAPPORT_OUTPUT, _RAPPORT_VALIDATED),
    })


_BASIC_OPDRACHT: dict[str, Any] = {
    "klant_naam": "Acme NV",
    "opdrachtbeschrijving": "Analyseer onze Java codebase.",
    "code_fragment": "public class Main {}",
    "programmeertaal": "java",
    "business_context": "ERP-systeem",
    "sector": "productie",
    "uren_per_week": 20,
}


# ─────────────────────────────────────────────────────────
# Unit tests: _resolve_path
# ─────────────────────────────────────────────────────────

class TestResolvePath:
    def test_simple_key(self):
        assert _resolve_path("a", {"a": 1}) == 1

    def test_nested_two_levels(self):
        ctx = {"intake": {"rapport_type": "code_analyse_rapport"}}
        assert _resolve_path("intake.rapport_type", ctx) == "code_analyse_rapport"

    def test_nested_three_levels(self):
        ctx = {"analyses": {"code_analyse": {"output": "resultaat"}}}
        assert _resolve_path("analyses.code_analyse.output", ctx) == "resultaat"

    def test_missing_key_returns_none(self):
        assert _resolve_path("x.y.z", {"a": 1}) is None

    def test_partial_path_missing(self):
        assert _resolve_path("a.b.c", {"a": {}}) is None

    def test_non_dict_intermediate(self):
        assert _resolve_path("a.b", {"a": "string"}) is None


# ─────────────────────────────────────────────────────────
# Unit tests: _resolve_mapping
# ─────────────────────────────────────────────────────────

class TestResolveMapping:
    def test_plain_string_returned_as_is(self):
        assert _resolve_mapping("volledig", {}) == "volledig"

    def test_dotted_string_resolved(self):
        ctx = {"intake": {"doelgroep": "it_team"}}
        assert _resolve_mapping("intake.doelgroep", ctx) == "it_team"

    def test_dotted_string_missing_returned_as_is(self):
        assert _resolve_mapping("niet.aanwezig", {}) == "niet.aanwezig"

    def test_dict_resolved_recursively(self):
        ctx = {"intake": {"taal": "nl"}}
        mapping = {"taal": "intake.taal", "toon": "professioneel"}
        result = _resolve_mapping(mapping, ctx)
        assert result == {"taal": "nl", "toon": "professioneel"}

    def test_list_resolved_recursively(self):
        ctx = {"a": {"b": "waarde"}}
        assert _resolve_mapping(["a.b", "literal"], ctx) == ["waarde", "literal"]

    def test_nested_bevindingen(self):
        ctx = {
            "analyses": {
                "code_analyse": {"output": "Code bevindingen"},
                "procesanalyse": {"output": "Proces bevindingen"},
            }
        }
        mapping = {
            "bevindingen": {
                "code_analyse": "analyses.code_analyse.output",
                "procesanalyse": "analyses.procesanalyse.output",
            }
        }
        result = _resolve_mapping(mapping, ctx)
        assert result["bevindingen"]["code_analyse"] == "Code bevindingen"
        assert result["bevindingen"]["procesanalyse"] == "Proces bevindingen"


# ─────────────────────────────────────────────────────────
# Unit tests: _eval_condition
# ─────────────────────────────────────────────────────────

class TestEvalCondition:
    def test_true_condition(self):
        ctx = {"intake": {"code_analyse_vereist": True}}
        assert _eval_condition("intake.code_analyse_vereist == true", ctx) is True

    def test_false_condition(self):
        ctx = {"intake": {"code_analyse_vereist": False}}
        assert _eval_condition("intake.code_analyse_vereist == true", ctx) is False

    def test_not_equal_true(self):
        ctx = {"intake": {"taal": "fr"}}
        assert _eval_condition("intake.taal != nl", ctx) is True

    def test_not_equal_false(self):
        ctx = {"intake": {"taal": "nl"}}
        assert _eval_condition("intake.taal != nl", ctx) is False

    def test_string_comparison(self):
        ctx = {"intake": {"rapport_type": "code_analyse_rapport"}}
        assert _eval_condition("intake.rapport_type == code_analyse_rapport", ctx) is True

    def test_null_comparison_match(self):
        ctx = {"intake": {"score": None}}
        assert _eval_condition("intake.score == null", ctx) is True

    def test_no_operator_truthy(self):
        ctx = {"intake": {"code_analyse_vereist": True}}
        assert _eval_condition("intake.code_analyse_vereist", ctx) is True

    def test_no_operator_falsy(self):
        ctx = {"intake": {"code_analyse_vereist": False}}
        assert _eval_condition("intake.code_analyse_vereist", ctx) is False


# ─────────────────────────────────────────────────────────
# Integratie tests: ConsultancyOrchestratorRunner
# ─────────────────────────────────────────────────────────

class TestConsultancyOrchestratorRunner:
    def _make_runner_instance(self, responses: dict) -> ConsultancyOrchestratorRunner:
        mock_runner = _make_runner(responses)
        return ConsultancyOrchestratorRunner(runner=mock_runner, spec_path=SPEC_PATH)

    @pytest.mark.asyncio
    async def test_full_pipeline_success(self):
        runner = ConsultancyOrchestratorRunner(runner=_full_runner(), spec_path=SPEC_PATH)
        result = await runner.run(_BASIC_OPDRACHT)

        assert result.success is True
        assert result.klant_naam == "Acme NV"
        assert result.rapport_markdown == _RAPPORT_OUTPUT
        assert "intake" in result.stage_outputs
        assert "rapport" in result.stage_outputs

    @pytest.mark.asyncio
    async def test_rapport_validated_fields_mapped(self):
        runner = ConsultancyOrchestratorRunner(runner=_full_runner(), spec_path=SPEC_PATH)
        result = await runner.run(_BASIC_OPDRACHT)

        assert result.executive_summary == "Korte samenvatting."
        assert result.business_rules == ["Regel A", "Regel B"]
        assert result.automatisering_score == 72.5
        assert len(result.aanbevelingen_top3) == 3

    @pytest.mark.asyncio
    async def test_intake_failure_stops_pipeline(self):
        mock_runner = MagicMock(spec=AgentRunner)
        mock_runner.run_agent_with_retry = AsyncMock(side_effect=RuntimeError("Ollama offline"))
        runner = ConsultancyOrchestratorRunner(runner=mock_runner, spec_path=SPEC_PATH)

        result = await runner.run(_BASIC_OPDRACHT)

        assert result.success is False
        assert any("intake" in e for e in result.errors)
        assert result.rapport_markdown == ""

    @pytest.mark.asyncio
    async def test_condition_skips_procesanalyse_when_not_required(self):
        """Als procesanalyse_vereist=False, wordt bedrijfsproces_agent niet aangeroepen."""
        intake_no_process = {
            **_INTAKE_OUTPUT_VALIDATED,
            "code_analyse_vereist": True,
            "procesanalyse_vereist": False,
        }
        responses = {
            "architect_agent": (json.dumps(intake_no_process), intake_no_process),
            "code_analyse_agent": (_CODE_ANALYSE_OUTPUT, None),
            "klant_rapport_agent": (_RAPPORT_OUTPUT, _RAPPORT_VALIDATED),
        }
        mock_runner = _make_runner(responses)
        runner = ConsultancyOrchestratorRunner(runner=mock_runner, spec_path=SPEC_PATH)

        result = await runner.run(_BASIC_OPDRACHT)

        assert result.success is True
        # bedrijfsproces_agent mag NIET aangeroepen zijn
        calls = [c.kwargs["agent_name"] for c in mock_runner.run_agent_with_retry.call_args_list]
        assert "bedrijfsproces_agent" not in calls

    @pytest.mark.asyncio
    async def test_both_analyses_run_when_both_required(self):
        intake_both = {
            **_INTAKE_OUTPUT_VALIDATED,
            "code_analyse_vereist": True,
            "procesanalyse_vereist": True,
        }
        responses = {
            "architect_agent": (json.dumps(intake_both), intake_both),
            "code_analyse_agent": (_CODE_ANALYSE_OUTPUT, None),
            "bedrijfsproces_agent": ("## Procesanalyse", None),
            "klant_rapport_agent": (_RAPPORT_OUTPUT, _RAPPORT_VALIDATED),
        }
        mock_runner = _make_runner(responses)
        runner = ConsultancyOrchestratorRunner(runner=mock_runner, spec_path=SPEC_PATH)

        result = await runner.run(_BASIC_OPDRACHT)

        assert result.success is True
        calls = [c.kwargs["agent_name"] for c in mock_runner.run_agent_with_retry.call_args_list]
        assert "code_analyse_agent" in calls
        assert "bedrijfsproces_agent" in calls

    @pytest.mark.asyncio
    async def test_no_analyses_needed(self):
        """Als beide condities False zijn, worden analyses overgeslagen."""
        intake_none = {
            **_INTAKE_OUTPUT_VALIDATED,
            "code_analyse_vereist": False,
            "procesanalyse_vereist": False,
        }
        responses = {
            "architect_agent": (json.dumps(intake_none), intake_none),
            "klant_rapport_agent": (_RAPPORT_OUTPUT, _RAPPORT_VALIDATED),
        }
        mock_runner = _make_runner(responses)
        runner = ConsultancyOrchestratorRunner(runner=mock_runner, spec_path=SPEC_PATH)

        result = await runner.run(_BASIC_OPDRACHT)

        assert result.success is True
        calls = [c.kwargs["agent_name"] for c in mock_runner.run_agent_with_retry.call_args_list]
        assert "code_analyse_agent" not in calls
        assert "bedrijfsproces_agent" not in calls

    @pytest.mark.asyncio
    async def test_rapport_failure_marks_failure(self):
        intake_ok = _INTAKE_OUTPUT_VALIDATED

        async def _run_side_effect(agent_name, user_input, context=None, client=None, retry_config=None):
            if agent_name == "architect_agent":
                return json.dumps(intake_ok), "id-intake", intake_ok
            if agent_name == "code_analyse_agent":
                return _CODE_ANALYSE_OUTPUT, "id-code", None
            if agent_name == "klant_rapport_agent":
                raise RuntimeError("Rapport agent timeout")
            return "<fallback>", "id-?", None

        mock_runner = MagicMock(spec=AgentRunner)
        mock_runner.run_agent_with_retry = AsyncMock(side_effect=_run_side_effect)
        runner = ConsultancyOrchestratorRunner(runner=mock_runner, spec_path=SPEC_PATH)

        result = await runner.run(_BASIC_OPDRACHT)

        assert result.success is False
        assert any("rapport" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_result_dataclass_defaults(self):
        result = ConsultancyResult(klant_naam="Test")
        assert result.rapport_markdown == ""
        assert result.business_rules == []
        assert result.errors == []
        assert result.success is True
        assert result.automatisering_score is None


# ─────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────

class TestGetConsultancyRunner:
    def test_returns_instance(self):
        with patch("ollama.consultancy_runner.get_runner") as mock_get:
            mock_get.return_value = MagicMock(spec=AgentRunner)
            runner = get_consultancy_runner(spec_path=SPEC_PATH)
        assert isinstance(runner, ConsultancyOrchestratorRunner)

    def test_spec_loaded(self):
        with patch("ollama.consultancy_runner.get_runner") as mock_get:
            mock_get.return_value = MagicMock(spec=AgentRunner)
            runner = get_consultancy_runner(spec_path=SPEC_PATH)
        assert "intake" in runner._spec
        assert "analyses" in runner._spec
        assert "rapport" in runner._spec
