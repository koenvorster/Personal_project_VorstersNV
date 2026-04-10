"""
VorstersNV Prompt Iteratie Systeem
Beheert prompt-versies en feedback voor continue verbetering van agents.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
LOGS_DIR = Path(__file__).parent.parent / "logs"


class PromptIterator:
    """
    Beheert prompt-iteraties en feedback voor een agent.

    Gebruik dit systeem om prompts systematisch te verbeteren op basis
    van echte interacties en feedback.
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.iterations_file = PROMPTS_DIR / "prepromt" / f"{agent_name}_iterations.yml"
        self.log_dir = LOGS_DIR / agent_name
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def get_current_version(self) -> str:
        """Geef de huidige actieve prompt-versie terug."""
        if not self.iterations_file.exists():
            return "1.0"
        data = yaml.safe_load(self.iterations_file.read_text(encoding="utf-8"))
        iterations = data.get("iterations", [])
        for it in reversed(iterations):
            if it.get("status") == "actief":
                return it["version"]
        return "1.0"

    def log_interaction(
        self,
        user_input: str,
        agent_output: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Log een interactie voor latere analyse.

        Args:
            user_input: De invoer van de gebruiker
            agent_output: Het antwoord van de agent
            metadata: Extra metadata (context, timing, etc.)

        Returns:
            De ID van de opgeslagen interactie
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        interaction_id = f"{self.agent_name}_{timestamp.replace(':', '-')}"

        entry = {
            "id": interaction_id,
            "timestamp": timestamp,
            "prompt_version": self.get_current_version(),
            "user_input": user_input,
            "agent_output": agent_output,
            "metadata": metadata or {},
            "feedback": None,  # Wordt later ingevuld
        }

        log_file = self.log_dir / f"{interaction_id}.json"
        log_file.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")

        logger.debug("Interactie gelogd: %s", interaction_id)
        return interaction_id

    def add_feedback(
        self,
        interaction_id: str,
        rating: int,
        notes: str = "",
    ) -> bool:
        """
        Voeg feedback toe aan een gelogde interactie.

        Args:
            interaction_id: ID van de interactie
            rating: Beoordeling (1-5)
            notes: Optionele opmerkingen

        Returns:
            True als succesvol opgeslagen
        """
        log_file = self.log_dir / f"{interaction_id}.json"
        if not log_file.exists():
            logger.warning("Interactie niet gevonden: %s", interaction_id)
            return False

        entry = json.loads(log_file.read_text(encoding="utf-8"))
        entry["feedback"] = {
            "rating": rating,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        log_file.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
        return True

    def analyse_feedback(self) -> dict[str, Any]:
        """
        Analyseer alle feedback voor deze agent.

        Returns:
            Statistieken en inzichten voor prompt-verbetering
        """
        log_files = list(self.log_dir.glob("*.json"))
        ratings = []
        low_rated = []

        for log_file in log_files:
            entry = json.loads(log_file.read_text(encoding="utf-8"))
            feedback = entry.get("feedback")
            if feedback and feedback.get("rating") is not None:
                rating = feedback["rating"]
                ratings.append(rating)
                if rating <= 2:
                    low_rated.append(entry)

        if not ratings:
            return {"status": "geen_feedback", "totaal_interacties": len(log_files)}

        return {
            "agent": self.agent_name,
            "prompt_versie": self.get_current_version(),
            "totaal_interacties": len(log_files),
            "beoordeelde_interacties": len(ratings),
            "gemiddelde_score": round(sum(ratings) / len(ratings), 2),
            "lage_scores": len(low_rated),
            "verbeter_suggesties": self._generate_suggestions(low_rated),
        }

    def _generate_suggestions(self, low_rated: list[dict]) -> list[str]:
        """Genereer verbeter-suggesties op basis van laag beoordeelde interacties."""
        suggesties = []
        if len(low_rated) > 5:
            suggesties.append(
                f"Er zijn {len(low_rated)} laag beoordeelde interacties. "
                "Analyseer de patronen en pas de pre-prompt aan."
            )
        if low_rated:
            suggesties.append(
                "Bekijk de laag beoordeelde interacties in de logs map "
                "en identificeer gemeenschappelijke problemen."
            )
        return suggesties

    def create_new_version(
        self,
        new_prepromt: str,
        change_description: str,
        author: str = "handmatig",
    ) -> str:
        """
        Maak een nieuwe prompt-versie aan.

        Args:
            new_prepromt: De nieuwe pre-prompt tekst
            change_description: Beschrijving van de wijziging
            author: Wie de wijziging heeft gemaakt

        Returns:
            De nieuwe versienummer
        """
        current = self.get_current_version()
        major, minor = current.split(".")
        new_version = f"{major}.{int(minor) + 1}"

        # Sla nieuwe pre-prompt op
        prepromt_file = PROMPTS_DIR / "prepromt" / f"{self.agent_name}_v{new_version.replace('.', '_')}.txt"
        prepromt_file.write_text(new_prepromt, encoding="utf-8")

        # Update iterations log
        if self.iterations_file.exists():
            data = yaml.safe_load(self.iterations_file.read_text(encoding="utf-8"))
        else:
            data = {"agent": self.agent_name, "iterations": []}

        # Deactiveer huidige versie
        for it in data["iterations"]:
            if it.get("status") == "actief":
                it["status"] = "archief"

        # Voeg nieuwe versie toe
        data["iterations"].append({
            "version": new_version,
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "author": author,
            "change": change_description,
            "prepromt_file": str(prepromt_file.relative_to(PROMPTS_DIR.parent)),
            "status": "actief",
        })

        self.iterations_file.write_text(
            yaml.dump(data, allow_unicode=True, default_flow_style=False),
            encoding="utf-8",
        )

        logger.info(
            "Nieuwe versie %s aangemaakt voor agent '%s'",
            new_version,
            self.agent_name,
        )
        return new_version
