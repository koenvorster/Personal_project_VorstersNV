"""
Tests voor ollama/reasoning_logger.py (Wave 9).

Dekt:
- Singleton get_reasoning_logger()
- extraheer_reasoning() met <reasoning>, <thinking> en stap-patronen
- tel_chain_of_thought_stappen()
- log_reasoning() → schrijft JSON naar tmp_path
- laad_reasoning_geschiedenis() → lijst van ReasoningExtractie
- analyseer_redeneerpatronen() → dict met gem_stappen etc.
- ReasoningExtractie.to_dict() en from_dict()
"""
from pathlib import Path

import pytest

from ollama.reasoning_logger import (
    ReasoningExtractie,
    ReasoningLogger,
    get_reasoning_logger,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def logger_met_tmp(tmp_path: Path) -> ReasoningLogger:
    """ReasoningLogger met tijdelijke logs-map."""
    return ReasoningLogger(logs_dir=tmp_path / "reasoning")


# ── Singleton ─────────────────────────────────────────────────────────────────

class TestSingleton:
    def test_get_reasoning_logger_retourneert_instantie(self):
        rl = get_reasoning_logger()
        assert isinstance(rl, ReasoningLogger)

    def test_get_reasoning_logger_is_singleton(self):
        rl1 = get_reasoning_logger()
        rl2 = get_reasoning_logger()
        assert rl1 is rl2


# ── extraheer_reasoning() ─────────────────────────────────────────────────────

class TestExtraheerReasoning:
    def test_reasoning_tag_extraheert_inhoud(self, logger_met_tmp):
        tekst = "<reasoning>stap 1: analyseer</reasoning>rest van de output"
        result = logger_met_tmp.extraheer_reasoning(tekst, "test-agent")
        assert result is not None
        assert "stap 1" in result

    def test_reasoning_tag_retourneert_enkel_inhoud_zonder_tags(self, logger_met_tmp):
        tekst = "<reasoning>de redenering hier</reasoning>"
        result = logger_met_tmp.extraheer_reasoning(tekst, "agent-x")
        assert "<reasoning>" not in result
        assert "</reasoning>" not in result

    def test_thinking_tag_werkt(self, logger_met_tmp):
        tekst = "<thinking>denk na over de vraag</thinking>antwoord"
        result = logger_met_tmp.extraheer_reasoning(tekst, "agent-y")
        assert result is not None
        assert "denk na" in result

    def test_reasoning_tag_heeft_prioriteit_over_thinking(self, logger_met_tmp):
        tekst = "<reasoning>redenering</reasoning><thinking>denken</thinking>"
        result = logger_met_tmp.extraheer_reasoning(tekst, "agent-z")
        assert "redenering" in result

    def test_stap_patroon_nl_extraheert_stappen(self, logger_met_tmp):
        tekst = "Stap 1: analyseer de situatie\nStap 2: trek een conclusie"
        result = logger_met_tmp.extraheer_reasoning(tekst, "nl-agent")
        assert result is not None
        assert len(result) > 0

    def test_step_patroon_en_extraheert_stappen(self, logger_met_tmp):
        tekst = "Step 1: analyse the situation\nStep 2: draw conclusions"
        result = logger_met_tmp.extraheer_reasoning(tekst, "en-agent")
        assert result is not None

    def test_tekst_zonder_patroon_retourneert_none(self, logger_met_tmp):
        tekst = "Hier is gewoon een antwoord zonder reasoning-structuur."
        result = logger_met_tmp.extraheer_reasoning(tekst, "simple-agent")
        assert result is None

    def test_lege_tekst_retourneert_none(self, logger_met_tmp):
        result = logger_met_tmp.extraheer_reasoning("", "agent")
        assert result is None

    def test_multiline_reasoning_tag(self, logger_met_tmp):
        tekst = "<reasoning>\nRegel 1\nRegel 2\nRegel 3\n</reasoning>output"
        result = logger_met_tmp.extraheer_reasoning(tekst, "multi-agent")
        assert result is not None
        assert "Regel 1" in result
        assert "Regel 3" in result


# ── tel_chain_of_thought_stappen() ────────────────────────────────────────────

class TestTelChainOfThoughtStappen:
    def test_stap_patroon_telt_2_stappen(self, logger_met_tmp):
        tekst = "Stap 1: analyseer\nStap 2: conclusie"
        stappen = logger_met_tmp.tel_chain_of_thought_stappen(tekst)
        assert len(stappen) == 2

    def test_stap_patroon_telt_3_stappen(self, logger_met_tmp):
        tekst = "Stap 1: eerste\nStap 2: tweede\nStap 3: derde"
        stappen = logger_met_tmp.tel_chain_of_thought_stappen(tekst)
        assert len(stappen) == 3

    def test_numbered_patroon_werkt(self, logger_met_tmp):
        tekst = "1. Eerste stap\n2. Tweede stap\n3. Derde stap"
        stappen = logger_met_tmp.tel_chain_of_thought_stappen(tekst)
        assert len(stappen) >= 2

    def test_fallback_alineas_bij_geen_nummering(self, logger_met_tmp):
        tekst = "Eerste alinea met info.\n\nTweede alinea met meer info."
        stappen = logger_met_tmp.tel_chain_of_thought_stappen(tekst)
        assert len(stappen) >= 1

    def test_stappen_zijn_strings(self, logger_met_tmp):
        tekst = "Stap 1: analyseer\nStap 2: conclusie"
        stappen = logger_met_tmp.tel_chain_of_thought_stappen(tekst)
        assert all(isinstance(s, str) for s in stappen)

    def test_lege_stappen_worden_gefilterd(self, logger_met_tmp):
        tekst = "Stap 1: echte stap\nStap 2: nog een stap"
        stappen = logger_met_tmp.tel_chain_of_thought_stappen(tekst)
        assert all(len(s.strip()) > 0 for s in stappen)


# ── log_reasoning() ───────────────────────────────────────────────────────────

class TestLogReasoning:
    def test_log_reasoning_retourneert_extractie(self, logger_met_tmp):
        llm_output = "<reasoning>Stap 1: analyseer\nStap 2: conclusie</reasoning>Output"
        extractie = logger_met_tmp.log_reasoning(
            llm_output=llm_output,
            agent_name="test-agent",
        )
        assert extractie is not None
        assert isinstance(extractie, ReasoningExtractie)

    def test_log_reasoning_schrijft_json_bestand(self, logger_met_tmp, tmp_path):
        llm_output = "<reasoning>Stap 1: analyseer</reasoning>"
        extractie = logger_met_tmp.log_reasoning(
            llm_output=llm_output,
            agent_name="schrijf-agent",
        )
        assert extractie is not None
        agent_dir = logger_met_tmp._logs_dir / "schrijf-agent"
        json_bestanden = list(agent_dir.glob("*.json"))
        assert len(json_bestanden) == 1

    def test_log_reasoning_zonder_reasoning_retourneert_none(self, logger_met_tmp):
        llm_output = "Gewone output zonder structuur."
        extractie = logger_met_tmp.log_reasoning(
            llm_output=llm_output,
            agent_name="no-reason-agent",
        )
        assert extractie is None

    def test_log_reasoning_met_project_id(self, logger_met_tmp):
        llm_output = "<reasoning>analyse compleet</reasoning>"
        extractie = logger_met_tmp.log_reasoning(
            llm_output=llm_output,
            agent_name="proj-agent",
            project_id="project-123",
        )
        assert extractie is not None
        assert extractie.project_id == "project-123"

    def test_log_reasoning_met_model_name(self, logger_met_tmp):
        llm_output = "<reasoning>model test</reasoning>"
        extractie = logger_met_tmp.log_reasoning(
            llm_output=llm_output,
            agent_name="model-agent",
            model_name="deepseek-r1:7b",
        )
        assert extractie is not None
        assert extractie.model_name == "deepseek-r1:7b"

    def test_extractie_bevat_session_id(self, logger_met_tmp):
        llm_output = "<reasoning>sessie test</reasoning>"
        extractie = logger_met_tmp.log_reasoning(
            llm_output=llm_output, agent_name="sess-agent"
        )
        assert extractie is not None
        assert extractie.session_id
        assert len(extractie.session_id) == 36  # UUID4

    def test_extractie_bevat_gecreeerd_op(self, logger_met_tmp):
        llm_output = "<reasoning>tijdstip test</reasoning>"
        extractie = logger_met_tmp.log_reasoning(
            llm_output=llm_output, agent_name="time-agent"
        )
        assert extractie is not None
        assert "T" in extractie.gecreeerd_op  # ISO 8601


# ── laad_reasoning_geschiedenis() ────────────────────────────────────────────

class TestLaadReasoningGeschiedenis:
    def test_lege_map_retourneert_lege_lijst(self, logger_met_tmp):
        resultaten = logger_met_tmp.laad_reasoning_geschiedenis("onbekende-agent")
        assert resultaten == []

    def test_laad_gelogde_sessie(self, logger_met_tmp):
        llm_output = "<reasoning>gelogged</reasoning>"
        logger_met_tmp.log_reasoning(llm_output, agent_name="history-agent")
        resultaten = logger_met_tmp.laad_reasoning_geschiedenis("history-agent")
        assert len(resultaten) == 1
        assert isinstance(resultaten[0], ReasoningExtractie)

    def test_max_sessies_beperkt_resultaten(self, logger_met_tmp):
        for i in range(5):
            logger_met_tmp.log_reasoning(
                f"<reasoning>sessie {i}</reasoning>",
                agent_name="max-agent",
            )
        resultaten = logger_met_tmp.laad_reasoning_geschiedenis("max-agent", max_sessies=3)
        assert len(resultaten) <= 3

    def test_meerdere_sessies_worden_geladen(self, logger_met_tmp):
        for i in range(3):
            logger_met_tmp.log_reasoning(
                f"<reasoning>stap {i}</reasoning>",
                agent_name="multi-sess-agent",
            )
        resultaten = logger_met_tmp.laad_reasoning_geschiedenis("multi-sess-agent")
        assert len(resultaten) == 3


# ── analyseer_redeneerpatronen() ──────────────────────────────────────────────

class TestAnalyseerRedeneerpatronen:
    def test_retourneert_dict(self, logger_met_tmp):
        resultaat = logger_met_tmp.analyseer_redeneerpatronen("onbekend-agent-xyz")
        assert isinstance(resultaat, dict)

    def test_lege_agent_retourneert_nul_statistieken(self, logger_met_tmp):
        resultaat = logger_met_tmp.analyseer_redeneerpatronen("leeg-agent-abc")
        assert resultaat["totaal_sessies"] == 0
        assert resultaat["gem_stappen_per_sessie"] == 0.0

    def test_dict_bevat_verwachte_sleutels(self, logger_met_tmp):
        resultaat = logger_met_tmp.analyseer_redeneerpatronen("sleutels-agent")
        verwachte_sleutels = {
            "gem_stappen_per_sessie",
            "meest_voorkomende_keywords",
            "gem_reasoning_tokens",
            "sessies_met_reasoning",
            "totaal_sessies",
        }
        assert verwachte_sleutels.issubset(resultaat.keys())

    def test_statistieken_na_gelogde_sessies(self, logger_met_tmp):
        for i in range(3):
            logger_met_tmp.log_reasoning(
                f"<reasoning>Stap 1: analyseer {i}\nStap 2: conclusie {i}</reasoning>",
                agent_name="stat-agent",
            )
        resultaat = logger_met_tmp.analyseer_redeneerpatronen("stat-agent")
        assert resultaat["totaal_sessies"] == 3
        assert resultaat["gem_stappen_per_sessie"] > 0

    def test_sessies_met_reasoning_percentage(self, logger_met_tmp):
        logger_met_tmp.log_reasoning(
            "<reasoning>test reasoning</reasoning>",
            agent_name="pct-agent",
        )
        resultaat = logger_met_tmp.analyseer_redeneerpatronen("pct-agent")
        # Alle opgeslagen sessies hebben reasoning
        assert resultaat["sessies_met_reasoning"] == "100.0%"

    def test_meest_voorkomende_keywords_is_lijst(self, logger_met_tmp):
        logger_met_tmp.log_reasoning(
            "<reasoning>analyseer systeem architectuur klant project</reasoning>",
            agent_name="kw-agent",
        )
        resultaat = logger_met_tmp.analyseer_redeneerpatronen("kw-agent")
        assert isinstance(resultaat["meest_voorkomende_keywords"], list)


# ── ReasoningExtractie dataclass ──────────────────────────────────────────────

class TestReasoningExtractieDataclass:
    def test_to_dict_bevat_alle_velden(self, logger_met_tmp):
        llm_output = "<reasoning>test</reasoning>"
        extractie = logger_met_tmp.log_reasoning(llm_output, agent_name="dict-agent")
        assert extractie is not None
        d = extractie.to_dict()
        verwachte_sleutels = {
            "session_id", "agent_name", "project_id",
            "reasoning_text", "chain_of_thought_stappen",
            "input_tokens", "reasoning_tokens", "output_tokens",
            "model_name", "gecreeerd_op",
        }
        assert verwachte_sleutels.issubset(d.keys())

    def test_from_dict_rondreis(self, logger_met_tmp):
        llm_output = "<reasoning>rondreis test</reasoning>"
        extractie = logger_met_tmp.log_reasoning(llm_output, agent_name="rondreis-agent")
        assert extractie is not None
        d = extractie.to_dict()
        hersteld = ReasoningExtractie.from_dict(d)
        assert hersteld.session_id == extractie.session_id
        assert hersteld.agent_name == extractie.agent_name
        assert hersteld.reasoning_text == extractie.reasoning_text

    def test_token_schatting_op_basis_van_lengte(self, logger_met_tmp):
        tekst = "a" * 400  # 400 tekens → ~100 tokens
        llm_output = f"<reasoning>{tekst}</reasoning>"
        extractie = logger_met_tmp.log_reasoning(llm_output, agent_name="token-agent")
        assert extractie is not None
        # reasoning_tokens ≈ len(reasoning) // 4
        assert extractie.reasoning_tokens > 0

    def test_chain_of_thought_stappen_is_lijst(self, logger_met_tmp):
        llm_output = "<reasoning>Stap 1: analyseer\nStap 2: conclusie</reasoning>"
        extractie = logger_met_tmp.log_reasoning(llm_output, agent_name="stap-agent")
        assert extractie is not None
        assert isinstance(extractie.chain_of_thought_stappen, list)
        assert len(extractie.chain_of_thought_stappen) >= 1
