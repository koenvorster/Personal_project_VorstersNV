"""Tests voor de AgentOrchestrator — workflows, retry en fraude-blocking."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ollama.agent_runner import AgentRunner, RetryConfig
from ollama.orchestrator import (
    AgentOrchestrator,
    OrchestratorStep,
    _classify_klantenservice_vraag,
    _parse_fraud_score,
)


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────

def _make_runner(responses: dict[str, str]) -> AgentRunner:
    """Maak een nep-runner die voorgedefinieerde antwoorden retourneert."""
    runner = MagicMock(spec=AgentRunner)

    async def _run(agent_name, user_input, context=None, client=None, retry_config=None):
        resp = responses.get(agent_name, f"<output van {agent_name}>")
        return resp, f"interaction-{agent_name}", None

    runner.run_agent_with_retry = AsyncMock(side_effect=_run)
    return runner


def _fraud_json(score: int) -> str:
    return json.dumps({
        "order_id": "TEST-001",
        "risicoscore": score,
        "risicosignalen": [],
        "aanbeveling": "verwerken" if score < 26 else "blokkeren",
        "motivatie": "testmotivatie",
        "gdpr_compliant": True,
    })


# ─────────────────────────────────────────────────────────
# Unit tests: hulpfuncties
# ─────────────────────────────────────────────────────────

class TestParseFraudScore:
    def test_parse_valid_json(self):
        output = _fraud_json(45)
        assert _parse_fraud_score(output) == 45

    def test_parse_json_embedded_in_text(self):
        output = f"Hier is de beoordeling:\n{_fraud_json(80)}\nDat was het."
        assert _parse_fraud_score(output) == 80

    def test_parse_score_zero(self):
        assert _parse_fraud_score(_fraud_json(0)) == 0

    def test_parse_score_max(self):
        assert _parse_fraud_score(_fraud_json(100)) == 100

    def test_returns_none_for_invalid_json(self):
        assert _parse_fraud_score("geen json hier") is None

    def test_returns_none_for_missing_score(self):
        assert _parse_fraud_score('{"order_id": "X"}') is None

    def test_handles_float_score(self):
        output = '{"risicoscore": 42.7}'
        assert _parse_fraud_score(output) == 42


class TestClassifyKlantenserviceVraag:
    def test_retour_keyword_in_vraag(self):
        assert _classify_klantenservice_vraag("Ik wil mijn product retourneren") == "retour"

    def test_defect_keyword(self):
        assert _classify_klantenservice_vraag("Het product is defect aangekomen") == "retour"

    def test_escalatie_keyword(self):
        assert _classify_klantenservice_vraag("Ik bel mijn advocaat") == "escalatie"

    def test_escalatie_prioriteit_boven_retour(self):
        # Escalatie moet prioriteit hebben boven retour
        vraag = "Dit is oplichterij, ik wil mijn geld terug anders ga ik naar de rechtbank"
        assert _classify_klantenservice_vraag(vraag) == "escalatie"

    def test_standaard_vraag(self):
        assert _classify_klantenservice_vraag("Wanneer wordt mijn pakket geleverd?") == "standaard"

    def test_retour_in_agent_output(self):
        assert _classify_klantenservice_vraag("", "U kunt het product retourneren via...") == "retour"

    def test_case_insensitive(self):
        assert _classify_klantenservice_vraag("RETOUR STUREN GRAAG") == "retour"


# ─────────────────────────────────────────────────────────
# Integratie tests: run_workflow met nep-runner
# ─────────────────────────────────────────────────────────

class TestRunWorkflow:
    @pytest.mark.asyncio
    async def test_basic_workflow_succeeds(self):
        runner = _make_runner({
            "agent_a": "output_a",
            "agent_b": "output_b",
        })
        orchestrator = AgentOrchestrator(runner=runner)
        steps = [
            OrchestratorStep(agent_name="agent_a", description="Stap A", context_key="a"),
            OrchestratorStep(agent_name="agent_b", description="Stap B", context_key="b"),
        ]
        result = await orchestrator.run_workflow("test", steps, "begin")
        assert result.success
        assert result.steps_completed == 2
        assert result.outputs["a"] == "output_a"
        assert result.outputs["b"] == "output_b"

    @pytest.mark.asyncio
    async def test_required_step_failure_stops_workflow(self):
        runner = MagicMock(spec=AgentRunner)
        runner.run_agent_with_retry = AsyncMock(side_effect=RuntimeError("Ollama down"))
        orchestrator = AgentOrchestrator(runner=runner)
        steps = [
            OrchestratorStep(agent_name="failing_agent", description="Mislukt", required=True),
            OrchestratorStep(agent_name="never_runs", description="Nooit"),
        ]
        result = await orchestrator.run_workflow("test", steps, "input")
        assert not result.success
        assert result.steps_completed == 0
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_optional_step_failure_continues_workflow(self):
        call_count = 0

        async def _run(agent_name, user_input, context=None, client=None, retry_config=None):
            nonlocal call_count
            call_count += 1
            if agent_name == "optional_fail":
                raise RuntimeError("tijdelijke fout")
            return f"output_{agent_name}", "id", None

        runner = MagicMock(spec=AgentRunner)
        runner.run_agent_with_retry = AsyncMock(side_effect=_run)
        orchestrator = AgentOrchestrator(runner=runner)
        steps = [
            OrchestratorStep(agent_name="ok_agent", description="OK", context_key="ok"),
            OrchestratorStep(agent_name="optional_fail", description="Optioneel", required=False),
            OrchestratorStep(agent_name="ok_agent2", description="Ook OK", context_key="ok2"),
        ]
        result = await orchestrator.run_workflow("test", steps, "input")
        assert result.success
        assert result.steps_completed == 2
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_condition_key_skips_step(self):
        runner = _make_runner({"agent_a": "output_a"})
        orchestrator = AgentOrchestrator(runner=runner)
        steps = [
            OrchestratorStep(agent_name="agent_a", description="A", context_key="a"),
            OrchestratorStep(
                agent_name="conditional_agent",
                description="Conditional",
                condition_key="non_existent_key",
            ),
        ]
        result = await orchestrator.run_workflow("test", steps, "begin")
        assert result.success
        assert result.steps_completed == 1


# ─────────────────────────────────────────────────────────
# Fraude-blocking tests
# ─────────────────────────────────────────────────────────

class TestFraudBlocking:
    @pytest.mark.asyncio
    async def test_high_fraud_score_blocks_pipeline(self):
        runner = _make_runner({
            "fraude_detectie_agent": _fraud_json(85),
            "order_verwerking_agent": "order verwerkt",
            "email_template_agent": "email verstuurd",
            "voorraad_advies_agent": "voorraad bijgewerkt",
        })
        orchestrator = AgentOrchestrator(runner=runner)
        result = await orchestrator.run_order_pipeline(
            order_id="ORD-001",
            klant_id="KL-001",
            klant_voornaam="Test",
            klant_email="test@test.be",
            orderwaarde=500.0,
            betaalmethode="creditcard",
            producten=[],
            bezorgadres="Teststraat 1",
        )
        assert result.fraud_blocked is True
        assert result.fraud_score == 85
        assert "fraude_beoordeling" in result.outputs
        assert "order_verwerking" not in result.outputs
        assert "bevestigings_email" not in result.outputs

    @pytest.mark.asyncio
    async def test_low_fraud_score_allows_processing(self):
        runner = _make_runner({
            "fraude_detectie_agent": _fraud_json(20),
            "order_verwerking_agent": "order verwerkt",
            "email_template_agent": "email verstuurd",
            "voorraad_advies_agent": "voorraad bijgewerkt",
        })
        orchestrator = AgentOrchestrator(runner=runner)
        result = await orchestrator.run_order_pipeline(
            order_id="ORD-002",
            klant_id="KL-002",
            klant_voornaam="Test",
            klant_email="test@test.be",
            orderwaarde=50.0,
            betaalmethode="ideal",
            producten=[],
            bezorgadres="Teststraat 1",
        )
        assert result.fraud_blocked is False
        assert result.fraud_score == 20
        assert "order_verwerking" in result.outputs

    @pytest.mark.asyncio
    async def test_fraud_score_exactly_at_threshold_blocks(self):
        runner = _make_runner({"fraude_detectie_agent": _fraud_json(75)})
        orchestrator = AgentOrchestrator(runner=runner)
        result = await orchestrator.run_order_pipeline(
            order_id="ORD-003",
            klant_id="KL-003",
            klant_voornaam="Test",
            klant_email="test@test.be",
            orderwaarde=100.0,
            betaalmethode="bancontact",
            producten=[],
            bezorgadres="Teststraat 1",
        )
        assert result.fraud_blocked is True

    @pytest.mark.asyncio
    async def test_fraud_score_one_below_threshold_allows(self):
        runner = _make_runner({
            "fraude_detectie_agent": _fraud_json(74),
            "order_verwerking_agent": "verwerkt",
            "email_template_agent": "email",
            "voorraad_advies_agent": "voorraad",
        })
        orchestrator = AgentOrchestrator(runner=runner)
        result = await orchestrator.run_order_pipeline(
            order_id="ORD-004",
            klant_id="KL-004",
            klant_voornaam="Test",
            klant_email="test@test.be",
            orderwaarde=100.0,
            betaalmethode="ideal",
            producten=[],
            bezorgadres="Teststraat 1",
        )
        assert result.fraud_blocked is False
        assert "order_verwerking" in result.outputs


# ─────────────────────────────────────────────────────────
# Klantenservice pipeline tests
# ─────────────────────────────────────────────────────────

class TestKlantenservicePipeline:
    @pytest.mark.asyncio
    async def test_standaard_vraag_geen_subrouting(self):
        runner = _make_runner({
            "klantenservice_agent": "Uw bestelling wordt morgen geleverd.",
        })
        orchestrator = AgentOrchestrator(runner=runner)
        result = await orchestrator.run_klantenservice_pipeline(
            klant_vraag="Wanneer wordt mijn pakket geleverd?",
            klant_naam="Jan Janssen",
            klant_email="jan@test.be",
        )
        assert result.success
        assert "klantenservice_antwoord" in result.outputs
        assert result.outputs["vraag_categorie"] == "standaard"
        assert not result.escalatie_vereist

    @pytest.mark.asyncio
    async def test_retour_vraag_triggert_subrouting(self):
        runner = _make_runner({
            "klantenservice_agent": "Wij helpen u met de retour.",
            "retour_verwerking_agent": '{"geldig": true, "retournummer": "RET-001"}',
            "email_template_agent": '{"onderwerpregel": "Retour bevestigd"}',
        })
        orchestrator = AgentOrchestrator(runner=runner)
        result = await orchestrator.run_klantenservice_pipeline(
            klant_vraag="Ik wil mijn product retourneren, het is defect.",
            klant_naam="Marie Dupont",
            klant_email="marie@test.be",
            order_id="ORD-100",
        )
        assert result.success
        assert result.outputs["vraag_categorie"] == "retour"
        assert "retour_beoordeling" in result.outputs

    @pytest.mark.asyncio
    async def test_escalatie_vraag_flagged(self):
        runner = _make_runner({
            "klantenservice_agent": "Wij begrijpen uw bezorgdheid.",
        })
        orchestrator = AgentOrchestrator(runner=runner)
        result = await orchestrator.run_klantenservice_pipeline(
            klant_vraag="Dit zijn oplichters, ik ga naar de rechtbank!",
            klant_naam="Boze Klant",
            klant_email="boos@test.be",
        )
        assert result.success
        assert result.escalatie_vereist is True
        assert "escalatie_reden" in result.outputs

    @pytest.mark.asyncio
    async def test_retour_zonder_order_id_geen_subrouting(self):
        """Als er geen order_id is, kan retour niet verwerkt worden — geen subrouting."""
        runner = _make_runner({
            "klantenservice_agent": "Kunt u uw ordernummer geven?",
        })
        orchestrator = AgentOrchestrator(runner=runner)
        result = await orchestrator.run_klantenservice_pipeline(
            klant_vraag="Ik wil iets retourneren",
            klant_naam="Test",
            klant_email="test@test.be",
            order_id="",  # geen order_id
        )
        assert result.success
        assert "retour_beoordeling" not in result.outputs


# ─────────────────────────────────────────────────────────
# Product pipeline tests
# ─────────────────────────────────────────────────────────

class TestProductPipeline:
    @pytest.mark.asyncio
    async def test_product_pipeline_alle_stappen(self):
        runner = _make_runner({
            "product_beschrijving_agent": '{"titel": "Test Product", "tags": ["test"]}',
            "seo_agent": '{"seo_score": 85, "meta_title": "Test Product | VorstersNV"}',
            "email_template_agent": '{"onderwerpregel": "Nieuw product toegevoegd"}',
        })
        orchestrator = AgentOrchestrator(runner=runner)
        result = await orchestrator.run_product_pipeline(
            product_naam="Ergonomische Stoel",
            categorie="Kantoor",
            kenmerken=["verstelbaar", "ergonomisch"],
            prijs=299.00,
        )
        assert result.success
        assert result.steps_completed == 3
        assert "productbeschrijving" in result.outputs
        assert "seo_output" in result.outputs
        assert "notificatie_email" in result.outputs


# ─────────────────────────────────────────────────────────
# Parallelle uitvoering tests
# ─────────────────────────────────────────────────────────

class TestParallelExecution:
    @pytest.mark.asyncio
    async def test_parallel_alle_agents_worden_uitgevoerd(self):
        """run_parallel voert alle stappen tegelijkertijd uit."""
        from ollama.orchestrator import ParallelStep

        runner = _make_runner({
            "seo_agent": "seo output",
            "product_beschrijving_agent": "beschrijving output",
        })
        orchestrator = AgentOrchestrator(runner=runner)

        parallel = ParallelStep(
            description="Parallelle content generatie",
            steps=[
                OrchestratorStep(
                    agent_name="seo_agent",
                    description="SEO",
                    context_key="seo",
                ),
                OrchestratorStep(
                    agent_name="product_beschrijving_agent",
                    description="Beschrijving",
                    context_key="beschrijving",
                ),
            ],
        )
        outputs = await orchestrator.run_parallel(parallel, shared_input="product info")
        assert outputs["seo"] == "seo output"
        assert outputs["beschrijving"] == "beschrijving output"

    @pytest.mark.asyncio
    async def test_parallel_optionele_stap_fout_gaat_door(self):
        """Optionele mislukte parallelle stap stopt niet de andere stappen."""
        from ollama.orchestrator import ParallelStep

        async def _run(agent_name, user_input, context=None, client=None, retry_config=None):
            if agent_name == "failing_agent":
                raise RuntimeError("Tijdelijke fout")
            return f"output_{agent_name}", "id", None

        runner = MagicMock(spec=AgentRunner)
        runner.run_agent_with_retry = AsyncMock(side_effect=_run)
        orchestrator = AgentOrchestrator(runner=runner)

        parallel = ParallelStep(
            description="Parallel met optionele fout",
            steps=[
                OrchestratorStep(
                    agent_name="seo_agent",
                    description="SEO",
                    context_key="seo",
                    required=False,
                ),
                OrchestratorStep(
                    agent_name="failing_agent",
                    description="Mislukt",
                    context_key="fail",
                    required=False,
                ),
            ],
        )
        # Optionele fout mag geen exception gooien
        outputs = await orchestrator.run_parallel(parallel, shared_input="test")
        assert "seo" in outputs
        assert "fail" not in outputs  # Mislukt, dus niet in outputs

    @pytest.mark.asyncio
    async def test_parallel_verplichte_stap_fout_gooit_exception(self):
        """Verplichte mislukte parallelle stap gooit exception."""
        from ollama.orchestrator import ParallelStep

        runner = MagicMock(spec=AgentRunner)
        runner.run_agent_with_retry = AsyncMock(side_effect=RuntimeError("Kritieke fout"))
        orchestrator = AgentOrchestrator(runner=runner)

        parallel = ParallelStep(
            description="Parallel met verplichte fout",
            steps=[
                OrchestratorStep(
                    agent_name="klantenservice_agent",
                    description="Verplicht",
                    context_key="output",
                    required=True,
                ),
            ],
        )
        with pytest.raises(RuntimeError, match="Kritieke fout"):
            await orchestrator.run_parallel(parallel, shared_input="test")


# ─────────────────────────────────────────────────────────
# OrchestratorResult velden
# ─────────────────────────────────────────────────────────

class TestOrchestratorResult:
    @pytest.mark.asyncio
    async def test_result_bevat_workflow_naam(self):
        runner = _make_runner({"agent_a": "output"})
        orchestrator = AgentOrchestrator(runner=runner)
        steps = [OrchestratorStep(agent_name="agent_a", description="Test", context_key="a")]
        result = await orchestrator.run_workflow("mijn_workflow", steps, "input")
        assert result.workflow_name == "mijn_workflow"

    @pytest.mark.asyncio
    async def test_steps_total_correct_met_overgeslagen_stap(self):
        """steps_total wordt verminderd bij overgeslagen stappen."""
        runner = _make_runner({"agent_a": "output"})
        orchestrator = AgentOrchestrator(runner=runner)
        steps = [
            OrchestratorStep(agent_name="agent_a", description="A", context_key="a"),
            OrchestratorStep(
                agent_name="conditional",
                description="Conditional",
                condition_key="bestaat_niet",
            ),
        ]
        result = await orchestrator.run_workflow("test", steps, "input")
        assert result.steps_completed == 1
        assert result.steps_total == 1  # Verminderd door overgeslagen stap

    @pytest.mark.asyncio
    async def test_fraud_blocked_false_by_default(self):
        runner = _make_runner({"agent_a": "output"})
        orchestrator = AgentOrchestrator(runner=runner)
        steps = [OrchestratorStep(agent_name="agent_a", description="A", context_key="a")]
        result = await orchestrator.run_workflow("test", steps, "input")
        assert result.fraud_blocked is False
        assert result.fraud_score is None
        assert result.escalatie_vereist is False
