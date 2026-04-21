"""Tests voor de Ollama integratie en agent runner."""
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml


class TestAgentRunner:
    """Tests voor de AgentRunner klasse."""

    def test_agent_runner_loads_agents(self):
        """AgentRunner moet agents laden vanuit de agents map."""
        from ollama.agent_runner import AgentRunner

        agents_dir = Path(__file__).parent.parent / "agents"
        runner = AgentRunner(agents_dir=agents_dir)
        assert len(runner.list_agents()) > 0

    def test_agent_runner_lists_known_agents(self):
        """De bekende agents moeten worden gevonden."""
        from ollama.agent_runner import AgentRunner

        agents_dir = Path(__file__).parent.parent / "agents"
        runner = AgentRunner(agents_dir=agents_dir)
        agents = runner.list_agents()
        assert "klantenservice_agent" in agents
        assert "product_beschrijving_agent" in agents

    def test_get_nonexistent_agent_returns_none(self):
        """Niet-bestaande agent geeft None terug."""
        from ollama.agent_runner import AgentRunner

        agents_dir = Path(__file__).parent.parent / "agents"
        runner = AgentRunner(agents_dir=agents_dir)
        assert runner.get("onbestaande_agent") is None

    def test_agent_has_correct_model(self):
        """Agents moeten het juiste model hebben."""
        from ollama.agent_runner import AgentRunner

        agents_dir = Path(__file__).parent.parent / "agents"
        runner = AgentRunner(agents_dir=agents_dir)
        agent = runner.get("klantenservice_agent")
        assert agent is not None
        assert agent.model == "llama3"

    @pytest.mark.anyio
    async def test_run_agent_calls_ollama(self):
        """run_agent moet Ollama aanroepen."""
        from ollama.agent_runner import AgentRunner

        agents_dir = Path(__file__).parent.parent / "agents"
        runner = AgentRunner(agents_dir=agents_dir)

        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="Test antwoord van de agent")

        result, interaction_id, _ = await runner.run_agent(
            "klantenservice_agent",
            "Waar is mijn bestelling?",
            client=mock_client,  # Gebruik mock client
        )
        assert result == "Test antwoord van de agent"
        assert isinstance(interaction_id, str)

    @pytest.mark.anyio
    async def test_run_nonexistent_agent_raises(self):
        """Niet-bestaande agent gooit ValueError."""
        from ollama.agent_runner import AgentRunner

        agents_dir = Path(__file__).parent.parent / "agents"
        runner = AgentRunner(agents_dir=agents_dir)

        with pytest.raises(ValueError, match="niet gevonden"):
            await runner.run_agent("onbestaande_agent", "test")


class TestAgent:
    """Tests voor de Agent klasse."""

    def test_agent_loads_system_prompt(self):
        """Agent moet system prompt laden."""
        from ollama.agent_runner import Agent

        config = {
            "name": "test_agent",
            "model": "llama3",
            "description": "Test agent",
            "system_prompt_ref": "prompts/system/klantenservice.txt",
        }
        agent = Agent(config)
        assert len(agent.system_prompt) > 0

    def test_agent_handles_missing_prompt_ref(self):
        """Agent moet omgaan met ontbrekende prompt-bestanden."""
        from ollama.agent_runner import Agent

        config = {
            "name": "test_agent",
            "model": "llama3",
            "description": "Test agent",
            "system_prompt_ref": "prompts/system/niet_bestaand.txt",
        }
        agent = Agent(config)
        assert agent.system_prompt == ""

    @pytest.mark.anyio
    async def test_agent_run_with_context(self):
        """Agent run moet context-variabelen invullen."""
        from ollama.agent_runner import Agent

        config = {
            "name": "test_agent",
            "model": "llama3",
            "description": "Test",
            "preprompt_ref": "prompts/preprompt/klantenservice_v1.txt",
        }
        agent = Agent(config)

        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="Hallo klant!")

        context = {
            "klant_naam": "Jan Jansen",
            "klant_nummer": "KL-001",
            "klant_email": "jan@test.nl",
            "order_geschiedenis": "Geen orders",
            "vraag_categorie": "algemeen",
            "klant_vraag": "Wat zijn uw openingstijden?",
        }
        result, interaction_id, _ = await agent.run("test input", context=context, client=mock_client)
        assert result == "Hallo klant!"
        assert isinstance(interaction_id, str)
        mock_client.generate.assert_called_once()


class TestPromptIterator:
    """Tests voor het PromptIterator systeem."""

    def test_prompt_iterator_gets_current_version(self):
        """PromptIterator moet de huidige versie retourneren."""
        from ollama.prompt_iterator import PromptIterator

        iterator = PromptIterator("klantenservice_agent")
        version = iterator.get_current_version()
        assert version == "1.0"

    def test_log_interaction_creates_file(self):
        """log_interaction moet een bestand aanmaken."""
        import tempfile
        from ollama.prompt_iterator import PromptIterator

        with tempfile.TemporaryDirectory() as tmp:
            iterator = PromptIterator.__new__(PromptIterator)
            iterator.agent_name = "test_agent"
            iterator.log_dir = Path(tmp)
            iterator.iterations_file = Path(tmp) / "iterations.yml"

            interaction_id = iterator.log_interaction(
                "Vraag van klant",
                "Antwoord van agent",
                {"context": "test"},
            )
            assert interaction_id is not None
            log_file = Path(tmp) / f"{interaction_id}.json"
            assert log_file.exists()
            data = json.loads(log_file.read_text())
            assert data["user_input"] == "Vraag van klant"
            assert data["agent_output"] == "Antwoord van agent"

    def test_add_feedback_updates_file(self):
        """add_feedback moet de feedback opslaan."""
        from ollama.prompt_iterator import PromptIterator

        with tempfile.TemporaryDirectory() as tmp:
            iterator = PromptIterator.__new__(PromptIterator)
            iterator.agent_name = "test_agent"
            iterator.log_dir = Path(tmp)
            iterator.iterations_file = Path(tmp) / "iterations.yml"

            interaction_id = iterator.log_interaction("vraag", "antwoord")
            success = iterator.add_feedback(interaction_id, 5, "Uitstekend!")
            assert success

            log_file = Path(tmp) / f"{interaction_id}.json"
            data = json.loads(log_file.read_text())
            assert data["feedback"]["rating"] == 5
            assert data["feedback"]["notes"] == "Uitstekend!"

    def test_analyse_feedback_no_feedback(self):
        """analyse_feedback met lege logs geeft juist resultaat."""
        from ollama.prompt_iterator import PromptIterator

        with tempfile.TemporaryDirectory() as tmp:
            iterator = PromptIterator.__new__(PromptIterator)
            iterator.agent_name = "test_agent"
            iterator.log_dir = Path(tmp)
            iterator.iterations_file = Path(tmp) / "iterations.yml"

            result = iterator.analyse_feedback()
            assert result["status"] == "geen_feedback"

    def test_analyse_feedback_with_ratings(self):
        """analyse_feedback berekent gemiddelde score correct."""
        import time
        from ollama.prompt_iterator import PromptIterator

        with tempfile.TemporaryDirectory() as tmp:
            iterator = PromptIterator.__new__(PromptIterator)
            iterator.agent_name = "test_agent"
            iterator.log_dir = Path(tmp)
            iterator.iterations_file = Path(tmp) / "iterations.yml"

            # Log 3 interacties + voeg ratings toe (kleine pauze voor unieke timestamps)
            id1 = iterator.log_interaction("vraag1", "antwoord1")
            time.sleep(0.01)
            id2 = iterator.log_interaction("vraag2", "antwoord2")
            time.sleep(0.01)
            id3 = iterator.log_interaction("vraag3", "antwoord3")
            iterator.add_feedback(id1, 5, "Uitstekend")
            iterator.add_feedback(id2, 3, "Gemiddeld")
            iterator.add_feedback(id3, 1, "Slecht")

            result = iterator.analyse_feedback()
            assert result["beoordeelde_interacties"] == 3
            assert result["gemiddelde_score"] == pytest.approx(3.0)
            assert result["lage_scores"] == 1  # rating <=2

    def test_create_new_version_bumps_minor(self):
        """create_new_version verhoogt het minor versienummer."""
        from ollama.prompt_iterator import PromptIterator

        with tempfile.TemporaryDirectory() as tmp:
            iterator = PromptIterator.__new__(PromptIterator)
            iterator.agent_name = "test_agent"
            iterator.log_dir = Path(tmp)
            # Gebruik tijdelijke prompts map
            import yaml as _yaml
            iterations_file = Path(tmp) / "test_agent_iterations.yml"
            iterations_file.write_text(
                _yaml.dump({
                    "agent": "test_agent",
                    "iterations": [{"version": "1.0", "status": "actief", "date": "2025-01-01"}],
                }),
                encoding="utf-8",
            )
            iterator.iterations_file = iterations_file

            # Patch PROMPTS_DIR zodat we niet in de echte map schrijven
            import ollama.prompt_iterator as _pi
            original = _pi.PROMPTS_DIR
            _pi.PROMPTS_DIR = Path(tmp)
            try:
                (Path(tmp) / "preprompt").mkdir()
                new_ver = iterator.create_new_version("Nieuwe prompt tekst", "Testwijziging")
                assert new_ver == "1.1"
                # Iterations bestand bijgewerkt
                data = _yaml.safe_load(iterations_file.read_text(encoding="utf-8"))
                active = [it for it in data["iterations"] if it.get("status") == "actief"]
                assert len(active) == 1
                assert active[0]["version"] == "1.1"
            finally:
                _pi.PROMPTS_DIR = original
