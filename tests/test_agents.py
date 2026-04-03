"""Tests voor agent-configuraties en YAML-validatie."""
import glob
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).parent.parent
AGENTS_DIR = REPO_ROOT / "agents"
PROMPTS_DIR = REPO_ROOT / "prompts"
PLAN_DIR = REPO_ROOT / "plan"


class TestAgentConfigs:
    """Valideer alle agent-YAML-configuraties."""

    def test_agents_dir_exists(self):
        assert AGENTS_DIR.exists(), "Agents map bestaat niet"

    def test_all_agent_yaml_are_valid(self):
        """Alle agent YAML-bestanden moeten geldig YAML zijn."""
        yaml_files = list(AGENTS_DIR.glob("*.yml"))
        assert yaml_files, "Geen agent YAML-bestanden gevonden"
        for f in yaml_files:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            assert data is not None, f"Leeg YAML-bestand: {f.name}"

    def test_agents_have_required_fields(self):
        """Elke agent moet verplichte velden hebben."""
        required = {"name", "model", "description"}
        for f in AGENTS_DIR.glob("*.yml"):
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            missing = required - set(data.keys())
            assert not missing, f"Agent {f.name} mist velden: {missing}"

    def test_known_agents_exist(self):
        """De verwachte agents moeten bestaan."""
        expected = [
            "klantenservice_agent",
            "product_beschrijving_agent",
            "seo_agent",
            "order_verwerking_agent",
        ]
        agent_names = [
            yaml.safe_load(f.read_text(encoding="utf-8"))["name"]
            for f in AGENTS_DIR.glob("*.yml")
        ]
        for name in expected:
            assert name in agent_names, f"Agent '{name}' niet gevonden"

    def test_agent_models_are_valid(self):
        """Agent-modellen moeten geldig Ollama-model-namen zijn."""
        valid_models = {"llama3", "mistral", "codellama", "llama2", "phi3"}
        for f in AGENTS_DIR.glob("*.yml"):
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            model = data.get("model", "")
            assert model in valid_models, (
                f"Agent {f.name} heeft ongeldig model '{model}'. "
                f"Geldig: {valid_models}"
            )

    def test_agent_system_prompts_exist(self):
        """Elke agent met een system_prompt_ref moet het bestand hebben."""
        for f in AGENTS_DIR.glob("*.yml"):
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            ref = data.get("system_prompt_ref", "")
            if ref:
                path = REPO_ROOT / ref
                assert path.exists(), (
                    f"Agent {f.name}: system_prompt_ref '{ref}' bestaat niet"
                )

    def test_agent_prepromts_exist(self):
        """Elke agent met een prepromt_ref moet het bestand hebben."""
        for f in AGENTS_DIR.glob("*.yml"):
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            ref = data.get("prepromt_ref", "")
            if ref:
                path = REPO_ROOT / ref
                assert path.exists(), (
                    f"Agent {f.name}: prepromt_ref '{ref}' bestaat niet"
                )


class TestPromptFiles:
    """Valideer prompt-bestanden."""

    def test_system_prompts_not_empty(self):
        """System-prompts mogen niet leeg zijn."""
        for f in (PROMPTS_DIR / "system").glob("*.txt"):
            content = f.read_text(encoding="utf-8").strip()
            assert content, f"System prompt is leeg: {f.name}"

    def test_prepromt_files_not_empty(self):
        """Pre-prompt bestanden mogen niet leeg zijn."""
        for f in (PROMPTS_DIR / "prepromt").glob("*.txt"):
            content = f.read_text(encoding="utf-8").strip()
            assert content, f"Pre-prompt is leeg: {f.name}"

    def test_iteration_files_are_valid_yaml(self):
        """Iteratie-logbestanden moeten geldig YAML zijn."""
        for f in (PROMPTS_DIR / "prepromt").glob("*_iterations.yml"):
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            assert data is not None, f"Leeg iteratie-bestand: {f.name}"
            assert "iterations" in data, f"Iteratie-bestand mist 'iterations' sleutel: {f.name}"

    def test_promptbooks_exist(self):
        """Promptboeken moeten aanwezig zijn."""
        books = list((PROMPTS_DIR / "promptbooks").glob("*.md"))
        assert books, "Geen promptboeken gevonden in prompts/promptbooks/"


class TestPlanMode:
    """Valideer het plan-mode systeem."""

    def test_plan_dir_exists(self):
        assert PLAN_DIR.exists(), "Plan map bestaat niet"

    def test_mode_file_exists(self):
        mode_file = PLAN_DIR / "mode.yml"
        assert mode_file.exists(), "plan/mode.yml bestaat niet"

    def test_mode_file_is_valid_yaml(self):
        mode_file = PLAN_DIR / "mode.yml"
        data = yaml.safe_load(mode_file.read_text(encoding="utf-8"))
        assert data is not None

    def test_mode_has_valid_value(self):
        mode_file = PLAN_DIR / "mode.yml"
        data = yaml.safe_load(mode_file.read_text(encoding="utf-8"))
        valid_modes = {"plan", "build", "review"}
        assert data.get("mode") in valid_modes, (
            f"Ongeldige mode '{data.get('mode')}'. Geldig: {valid_modes}"
        )

    def test_plan_document_exists(self):
        plan_doc = PLAN_DIR / "PLAN.md"
        assert plan_doc.exists(), "plan/PLAN.md bestaat niet"
