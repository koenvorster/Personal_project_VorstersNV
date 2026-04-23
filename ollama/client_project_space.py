"""
VorstersNV Client Project Space — Multi-tenant projectbeheer voor consultancy analyses.

Elke klant krijgt een geïsoleerde ClientProjectSpace die:
  - een unieke project_id (UUID) als namespace heeft
  - via klant_id (tenant identifier) volledig gescheiden is van andere klanten
  - bronbestanden scant, filtert en sorteert voor AI-analyse
  - status bijhoudt gedurende de volledige analyse-pipeline

Multi-tenant isolatie wordt bereikt door:
  1. Elke project_id is een UUID — nooit herbruikbaar of gokbaar
  2. De _project_registry is gesegmenteerd per klant_id in list_projects()
  3. Geen gedeeld geheugen of pad-overlap tussen klanten mogelijk

Gebruik:
    config = ProjectConfig(model="codellama", taal_filter=[".py", ".ts"])
    project = create_project(
        klant_naam="Acme NV",
        klant_id="tenant-acme",
        bronpad=Path("/analyses/acme"),
        projecttype="code_analyse",
        config=config,
    )
    bestanden = project.scan_bestanden()
    get_project(project.project_id)       # ophalen via ID
    list_projects("tenant-acme")          # alle projecten voor tenant
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Enums & Config
# ─────────────────────────────────────────────

class ProjectStatus(str, Enum):
    """Lifecycle statussen van een consultancy project."""
    CREATED   = "CREATED"
    SCANNING  = "SCANNING"
    ANALYSING = "ANALYSING"
    RAPPORT   = "RAPPORT"
    DONE      = "DONE"
    FAILED    = "FAILED"


# Ondersteunde broncode-extensies per taal
_TAAL_EXTENSIES: dict[str, list[str]] = {
    "java":   [".java"],
    "python": [".py"],
    "php":    [".php"],
    "csharp": [".cs"],
    "js":     [".js"],
    "ts":     [".ts"],
}

# Alle ondersteunde extensies als platte set (gebruikt bij lege taal_filter)
_ALLE_EXTENSIES: set[str] = {
    ext
    for exts in _TAAL_EXTENSIES.values()
    for ext in exts
}


@dataclass
class ProjectConfig:
    """
    Configuratie voor een consultancy project.

    Attributes:
        model:        Ollama model naam voor de analyse (bijv. "codellama", "llama3").
        max_chunks:   Maximum aantal bestanden/chunks dat naar de AI gaat.
        taal_filter:  Lijst van bestandsextensies (bijv. [".py", ".ts"]).
                      Leeg betekent alle ondersteunde extensies.
        pii_scan:     Voer PII-scan uit op bronbestanden vóór analyse.
        rapport_taal: Taal van het eindrapport ("nl" of "fr").
    """
    model: str = "codellama"
    max_chunks: int = 50
    taal_filter: list[str] = field(default_factory=list)
    pii_scan: bool = True
    rapport_taal: str = "nl"

    def effectieve_extensies(self) -> set[str]:
        """
        Geef de effectieve bestandsextensies terug op basis van taal_filter.

        Returns:
            Set van extensie-strings (bijv. {".py", ".ts"}).
            Als taal_filter leeg is, worden alle ondersteunde extensies teruggegeven.
        """
        if not self.taal_filter:
            return _ALLE_EXTENSIES
        return set(self.taal_filter)


# ─────────────────────────────────────────────
# Client Project Space
# ─────────────────────────────────────────────

@dataclass
class ClientProjectSpace:
    """
    Geïsoleerde projectruimte per klant voor broncode- en procesanalyses.

    Elke instantie vertegenwoordigt één analyseproject en behoudt zijn eigen
    status, configuratie en metadata. Projecten van verschillende klanten
    zijn volledig geïsoleerd via klant_id.

    Attributes:
        project_id:    UUID string — unieke identifier van dit project.
        klant_naam:    Weergavenaam van de klant.
        klant_id:      Tenant identifier — gebruikt voor isolatie-checks.
        projecttype:   Type analyse: "code_analyse" | "bedrijfsproces" | "ai_roadmap".
        bronpad:       Absoluut pad naar de klant-codebase (lokale kopie).
        config:        ProjectConfig met model, taal_filter, pii_scan, etc.
        aangemaakt_op: UTC-timestamp van aanmaak.
        status:        Huidige fase in de analyse-pipeline.
        metadata:      Vrij woordenboek voor extra context (rapport_pad, scores, etc.).
    """
    project_id:    str
    klant_naam:    str
    klant_id:      str
    projecttype:   str
    bronpad:       Path
    config:        ProjectConfig
    aangemaakt_op: datetime
    status:        ProjectStatus
    metadata:      dict[str, Any] = field(default_factory=dict)

    # ─── Bestandsbeheer ───────────────────────────────────────────

    def scan_bestanden(self) -> list[Path]:
        """
        Scan bronpad op broncode-bestanden die voldoen aan taal_filter.

        Doorloopt recursief het bronpad, filtert op de effectieve extensies
        uit config.taal_filter, en sorteert op bestandsgrootte (groot → klein)
        zodat de grootste/meest relevante bestanden als eerste worden verwerkt.

        Returns:
            Lijst van Path-objecten gesorteerd op grootte (aflopend).
            Leeg als bronpad niet bestaat of geen bestanden bevat.
        """
        if not self.bronpad.exists():
            logger.warning(
                "Bronpad bestaat niet voor project %s: %s",
                self.project_id, self.bronpad,
            )
            return []

        if not self.bronpad.is_dir():
            logger.warning(
                "Bronpad is geen directory voor project %s: %s",
                self.project_id, self.bronpad,
            )
            return []

        extensies = self.config.effectieve_extensies()
        bestanden: list[Path] = []

        for pad in self.bronpad.rglob("*"):
            if pad.is_file() and pad.suffix.lower() in extensies:
                bestanden.append(pad)

        # Sorteer op grootte (groot naar klein) — grotere bestanden hebben meer logica
        bestanden.sort(key=lambda p: p.stat().st_size, reverse=True)

        logger.info(
            "Project %s: %d bestanden gevonden in %s (filter: %s)",
            self.project_id, len(bestanden), self.bronpad, sorted(extensies),
        )
        return bestanden

    # ─── Serialisatie ─────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """
        Serialiseer project naar een JSON-compatibel woordenboek.

        Path-objecten worden omgezet naar strings. Datetimes naar ISO 8601.
        ProjectStatus naar zijn string waarde.

        Returns:
            dict met alle project-velden in een serialiseerbaar formaat.
        """
        return {
            "project_id":    self.project_id,
            "klant_naam":    self.klant_naam,
            "klant_id":      self.klant_id,
            "projecttype":   self.projecttype,
            "bronpad":       str(self.bronpad),
            "config": {
                "model":        self.config.model,
                "max_chunks":   self.config.max_chunks,
                "taal_filter":  self.config.taal_filter,
                "pii_scan":     self.config.pii_scan,
                "rapport_taal": self.config.rapport_taal,
            },
            "aangemaakt_op": self.aangemaakt_op.isoformat(),
            "status":        self.status.value,
            "metadata":      self.metadata,
        }


# ─────────────────────────────────────────────
# Module-level Registry
# ─────────────────────────────────────────────

_project_registry: dict[str, ClientProjectSpace] = {}


def create_project(
    klant_naam:  str,
    klant_id:    str,
    bronpad:     Path,
    projecttype: str,
    config:      ProjectConfig | None = None,
) -> ClientProjectSpace:
    """
    Maak een nieuw ClientProjectSpace aan en registreer het.

    Args:
        klant_naam:  Weergavenaam van de klant (voor rapporten en logs).
        klant_id:    Tenant identifier — moet uniek zijn per klant.
        bronpad:     Pad naar de lokale klant-codebase (hoeft nog niet te bestaan).
        projecttype: Type analyse: "code_analyse" | "bedrijfsproces" | "ai_roadmap".
        config:      Optionele ProjectConfig. Standaard ProjectConfig() als None.

    Returns:
        Nieuw geregistreerde ClientProjectSpace met status CREATED.

    Raises:
        ValueError: Als projecttype niet één van de geldige waarden is.
    """
    geldige_types = {"code_analyse", "bedrijfsproces", "ai_roadmap"}
    if projecttype not in geldige_types:
        raise ValueError(
            f"Ongeldig projecttype '{projecttype}' — kies uit {geldige_types}"
        )

    project_id = str(uuid.uuid4())
    project = ClientProjectSpace(
        project_id=project_id,
        klant_naam=klant_naam,
        klant_id=klant_id,
        projecttype=projecttype,
        bronpad=Path(bronpad),
        config=config or ProjectConfig(),
        aangemaakt_op=datetime.now(timezone.utc),
        status=ProjectStatus.CREATED,
        metadata={},
    )
    _project_registry[project_id] = project
    logger.info(
        "Project aangemaakt: id=%s klant=%s type=%s bronpad=%s",
        project_id, klant_naam, projecttype, bronpad,
    )
    return project


def get_project(project_id: str) -> ClientProjectSpace | None:
    """
    Haal een project op via zijn UUID.

    Args:
        project_id: UUID string van het project.

    Returns:
        ClientProjectSpace als gevonden, anders None.
    """
    project = _project_registry.get(project_id)
    if project is None:
        logger.debug("Project niet gevonden in registry: %s", project_id)
    return project


def list_projects(klant_id: str) -> list[ClientProjectSpace]:
    """
    Geef alle projecten terug voor een specifieke tenant.

    Multi-tenant isolatie: enkel projecten met het opgegeven klant_id
    worden teruggegeven — andere tenants zijn niet zichtbaar.

    Args:
        klant_id: Tenant identifier om op te filteren.

    Returns:
        Lijst van ClientProjectSpace gesorteerd op aangemaakt_op (nieuwste eerst).
    """
    projecten = [
        p for p in _project_registry.values()
        if p.klant_id == klant_id
    ]
    projecten.sort(key=lambda p: p.aangemaakt_op, reverse=True)
    logger.debug(
        "list_projects voor klant_id=%s → %d projecten gevonden",
        klant_id, len(projecten),
    )
    return projecten
