"""
VorstersNV Agent Versioning — Semantisch versionsysteem voor Ollama runtime agents.

Beheert de volledige lifecycle van agent-versies van DRAFT tot ARCHIVED.
Versies worden in-memory bijgehouden en persistent opgeslagen als JSON in
``agents/versions/registry.json``.

Lifecycle-volgorde::

    DRAFT → SHADOW → CANARY → STABLE → DEPRECATED → ARCHIVED

- **SHADOW**: ontvangt productie-input maar de output wordt niet gebruikt.
- **CANARY**: ontvangt ~5 % van het productieverkeer.
- **STABLE**: volledige productie.

Gebruik::

    registry = get_agent_version_registry()
    versie = registry.register_version(
        agent_name="klantenservice_agent",
        yaml_path="agents/klantenservice_agent_v2.yml",
        notes="Nieuwe escalatie-logica toegevoegd",
        bump=VersionBump.MINOR,
    )
    registry.promote("klantenservice_agent", versie.version)
    registry.record_run("klantenservice_agent", versie.version, eval_score=0.87)
    registry.save()
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Constanten
# ─────────────────────────────────────────────

_START_VERSION = "1.0.0"
_MIN_RUNS_VOOR_PROMOTIE = 10  # minimaal vereiste runs voor SHADOW→CANARY/CANARY→STABLE


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class AgentLifecycle(str, Enum):
    """Lifecycle-fasen van een agent-versie."""

    DRAFT      = "draft"
    SHADOW     = "shadow"      # ontvangt productie-input maar output wordt niet gebruikt
    CANARY     = "canary"      # ~5 % van het productieverkeer
    STABLE     = "stable"      # 100 % productie
    DEPRECATED = "deprecated"
    ARCHIVED   = "archived"


class VersionBump(str, Enum):
    """Type versie-verhoging conform SemVer."""

    MAJOR = "major"   # fundamentele wijziging output-schema
    MINOR = "minor"   # wijziging reasoning-strategie
    PATCH = "patch"   # kleine prompt-verfijning


# ─────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────

@dataclass
class AgentVersion:
    """
    Één semantische versie van een Ollama agent.

    Attributes:
        agent_name:  Naam van de agent (bijv. ``"klantenservice_agent"``).
        version:     SemVer-string bijv. ``"2.1.3"``.
        sha256:      SHA-256 hex-digest van de agent YAML-content.
        lifecycle:   Huidige fase in de AgentLifecycle.
        created_at:  ISO 8601 UTC-tijdstempel van aanmaak.
        deployed_at: ISO 8601 UTC-tijdstempel van deployement, of ``None``.
        notes:       Korte omschrijving van de wijzigingen in deze versie.
        yaml_path:   Relatief pad naar de agent YAML (bijv. ``"agents/agent_v2.yml"``).
        eval_score:  Meest recente evaluatiescore (0.0–1.0) of ``None``.
        run_count:   Totaal aantal keren dat deze versie is uitgevoerd.
    """

    agent_name:  str
    version:     str
    sha256:      str
    lifecycle:   AgentLifecycle
    created_at:  str
    deployed_at: str | None
    notes:       str
    yaml_path:   str
    eval_score:  float | None
    run_count:   int

    # ─── Serialisatie ─────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """
        Serialiseer naar een JSON-compatibel woordenboek.

        Returns:
            dict met alle velden; lifecycle als string-waarde.
        """
        return {
            "agent_name":  self.agent_name,
            "version":     self.version,
            "sha256":      self.sha256,
            "lifecycle":   self.lifecycle.value,
            "created_at":  self.created_at,
            "deployed_at": self.deployed_at,
            "notes":       self.notes,
            "yaml_path":   self.yaml_path,
            "eval_score":  self.eval_score,
            "run_count":   self.run_count,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AgentVersion:
        """
        Deseraliseer vanuit een woordenboek (bijv. geladen JSON).

        Args:
            d: Dict met dezelfde sleutels als ``to_dict()``.

        Returns:
            Nieuwe AgentVersion instantie.
        """
        return cls(
            agent_name=  d["agent_name"],
            version=     d["version"],
            sha256=      d["sha256"],
            lifecycle=   AgentLifecycle(d["lifecycle"]),
            created_at=  d["created_at"],
            deployed_at= d.get("deployed_at"),
            notes=       d.get("notes", ""),
            yaml_path=   d["yaml_path"],
            eval_score=  d.get("eval_score"),
            run_count=   d.get("run_count", 0),
        )

    def is_promotable(self) -> bool:
        """
        True als deze versie promoveerbaar is naar de volgende fase.

        Een versie is promoveerbaar als ze in SHADOW of CANARY zit
        én al voldoende runs heeft om statistisch betrouwbaar te zijn.

        Returns:
            bool — True als promotie is toegestaan.
        """
        if self.lifecycle not in (AgentLifecycle.SHADOW, AgentLifecycle.CANARY):
            return False
        return self.run_count >= _MIN_RUNS_VOOR_PROMOTIE


# ─────────────────────────────────────────────
# Hulpfunctie — versie-berekening
# ─────────────────────────────────────────────

def _bump_version(current: str, bump: VersionBump) -> str:
    """
    Verhoog een SemVer-string op basis van het bump-type.

    Args:
        current: Huidige versie als ``"MAJOR.MINOR.PATCH"`` string.
        bump:    :class:`VersionBump` die aangeeft welk getal verhoogd wordt.

    Returns:
        Nieuwe versie-string na verhoging en reset van lagere getallen.

    Raises:
        ValueError: Als ``current`` niet het formaat ``"X.Y.Z"`` heeft.

    Examples:
        >>> _bump_version("1.2.3", VersionBump.MINOR)
        '1.3.0'
        >>> _bump_version("2.0.0", VersionBump.MAJOR)
        '3.0.0'
    """
    parts = current.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"Ongeldig versie-formaat: '{current}' — verwacht 'X.Y.Z'")

    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    if bump == VersionBump.MAJOR:
        return f"{major + 1}.0.0"
    if bump == VersionBump.MINOR:
        return f"{major}.{minor + 1}.0"
    # PATCH
    return f"{major}.{minor}.{patch + 1}"


def _sha256_van_bestand(yaml_path: Path) -> str:
    """
    Bereken de SHA-256 hex-digest van een YAML-bestand.

    Args:
        yaml_path: Absoluut of relatief pad naar het YAML-bestand.

    Returns:
        64-karakter hex-string.

    Raises:
        FileNotFoundError: Als het bestand niet bestaat.
    """
    inhoud = yaml_path.read_text(encoding="utf-8")
    return hashlib.sha256(inhoud.encode("utf-8")).hexdigest()


# ─────────────────────────────────────────────
# AgentVersionRegistry
# ─────────────────────────────────────────────

@dataclass
class AgentVersionRegistry:
    """
    In-memory registry van agent-versies met JSON-persistentie.

    Beheert versies per agent-naam en biedt methoden voor registratie,
    promotie, rollback en statistieken.  Wijzigingen worden pas op schijf
    geschreven na een expliciete aanroep van :meth:`save`.

    Attributes:
        _versions:      Dict van agent-naam naar gesorteerde lijst versies.
        _registry_path: Pad naar het persistente JSON-bestand.
    """

    _versions:      dict[str, list[AgentVersion]] = field(default_factory=dict)
    _registry_path: Path = field(default_factory=lambda: Path("agents/versions/registry.json"))

    # ─── Registratie ──────────────────────────────────────────────

    def register_version(
        self,
        agent_name: str,
        yaml_path:  str,
        notes:      str,
        bump:       VersionBump,
    ) -> AgentVersion:
        """
        Registreer een nieuwe agent-versie.

        Berekent de SHA-256 van de YAML-file, bepaalt het nieuwe versienummer
        op basis van de laatste geregistreerde versie en het ``bump``-type,
        en voegt de versie toe aan de registry met lifecycle DRAFT.

        Args:
            agent_name: Naam van de agent.
            yaml_path:  Relatief pad naar het agent YAML-bestand.
            notes:      Omschrijving van de wijzigingen.
            bump:       Hoe het versienummer verhoogd moet worden.

        Returns:
            Nieuw aangemaakte :class:`AgentVersion` met lifecycle DRAFT.

        Raises:
            FileNotFoundError: Als het YAML-bestand niet gevonden wordt.
        """
        pad = Path(yaml_path)
        sha = _sha256_van_bestand(pad)

        versies = self._versions.get(agent_name, [])
        if versies:
            huidig = versies[-1].version
            nieuw_versienummer = _bump_version(huidig, bump)
        else:
            nieuw_versienummer = _START_VERSION

        versie = AgentVersion(
            agent_name=  agent_name,
            version=     nieuw_versienummer,
            sha256=      sha,
            lifecycle=   AgentLifecycle.DRAFT,
            created_at=  datetime.now(timezone.utc).isoformat(),
            deployed_at= None,
            notes=       notes,
            yaml_path=   yaml_path,
            eval_score=  None,
            run_count=   0,
        )

        if agent_name not in self._versions:
            self._versions[agent_name] = []
        self._versions[agent_name].append(versie)

        logger.info(
            "Agent-versie geregistreerd: agent=%s versie=%s lifecycle=%s sha256=%.8s…",
            agent_name, nieuw_versienummer, versie.lifecycle.value, sha,
        )
        return versie

    # ─── Opvragen ─────────────────────────────────────────────────

    def get_active_version(self, agent_name: str) -> AgentVersion | None:
        """
        Geef de actieve versie terug: STABLE > CANARY > laatste versie.

        Args:
            agent_name: Naam van de agent.

        Returns:
            Meest productie-geschikte versie, of ``None`` als de agent onbekend is.
        """
        versies = self._versions.get(agent_name)
        if not versies:
            logger.debug("Geen versies gevonden voor agent: %s", agent_name)
            return None

        for lifecycle in (AgentLifecycle.STABLE, AgentLifecycle.CANARY):
            for v in reversed(versies):
                if v.lifecycle == lifecycle:
                    return v

        return versies[-1]

    def get_shadow_version(self, agent_name: str) -> AgentVersion | None:
        """
        Geef de SHADOW-versie terug als die bestaat.

        Args:
            agent_name: Naam van de agent.

        Returns:
            SHADOW-versie of ``None``.
        """
        versies = self._versions.get(agent_name, [])
        for v in reversed(versies):
            if v.lifecycle == AgentLifecycle.SHADOW:
                return v
        return None

    def _get_versie(self, agent_name: str, version: str) -> AgentVersion | None:
        """Intern: zoek een specifieke versie op naam + versienummer."""
        for v in self._versions.get(agent_name, []):
            if v.version == version:
                return v
        return None

    # ─── Promotie & rollback ───────────────────────────────────────

    def promote(self, agent_name: str, version: str) -> bool:
        """
        Promoveer een versie naar de volgende lifecycle-fase.

        Toegestane transities:

        - DRAFT  → SHADOW
        - SHADOW → CANARY  (vereist ``run_count >= _MIN_RUNS_VOOR_PROMOTIE``)
        - CANARY → STABLE  (vereist ``run_count >= _MIN_RUNS_VOOR_PROMOTIE``)

        Bij promotie naar STABLE wordt de vorige STABLE versie DEPRECATED.

        Args:
            agent_name: Naam van de agent.
            version:    Versienummer dat gepromoveerd moet worden.

        Returns:
            ``True`` als promotie geslaagd is, ``False`` bij ongeldig verzoek.
        """
        versie = self._get_versie(agent_name, version)
        if versie is None:
            logger.warning(
                "Promotie mislukt: versie niet gevonden agent=%s versie=%s",
                agent_name, version,
            )
            return False

        _promotie_pad: dict[AgentLifecycle, AgentLifecycle] = {
            AgentLifecycle.DRAFT:  AgentLifecycle.SHADOW,
            AgentLifecycle.SHADOW: AgentLifecycle.CANARY,
            AgentLifecycle.CANARY: AgentLifecycle.STABLE,
        }

        volgende = _promotie_pad.get(versie.lifecycle)
        if volgende is None:
            logger.warning(
                "Promotie niet toegestaan vanuit lifecycle %s (agent=%s versie=%s)",
                versie.lifecycle.value, agent_name, version,
            )
            return False

        # Controleer minimale runs voor SHADOW→CANARY en CANARY→STABLE
        if versie.lifecycle in (AgentLifecycle.SHADOW, AgentLifecycle.CANARY):
            if versie.run_count < _MIN_RUNS_VOOR_PROMOTIE:
                logger.warning(
                    "Promotie geblokkeerd: run_count=%d < %d vereist "
                    "(agent=%s versie=%s)",
                    versie.run_count, _MIN_RUNS_VOOR_PROMOTIE, agent_name, version,
                )
                return False

        # Bij promotie naar STABLE: vorige STABLE deprecaten
        if volgende == AgentLifecycle.STABLE:
            for v in self._versions.get(agent_name, []):
                if v.lifecycle == AgentLifecycle.STABLE and v.version != version:
                    v.lifecycle = AgentLifecycle.DEPRECATED
                    logger.info(
                        "Vorige STABLE gemarkeerd als DEPRECATED: agent=%s versie=%s",
                        agent_name, v.version,
                    )

            versie.deployed_at = datetime.now(timezone.utc).isoformat()

        vorige_lifecycle = versie.lifecycle
        versie.lifecycle = volgende
        logger.info(
            "Versie gepromoveerd: agent=%s versie=%s %s → %s",
            agent_name, version, vorige_lifecycle.value, volgende.value,
        )
        return True

    def rollback(self, agent_name: str) -> AgentVersion | None:
        """
        Rollback naar de vorige STABLE versie.

        Markeert de huidige STABLE als DEPRECATED en activeert de meest
        recente DEPRECATED versie als nieuwe STABLE.

        Args:
            agent_name: Naam van de agent.

        Returns:
            De herstelde :class:`AgentVersion` of ``None`` als rollback
            niet mogelijk was.
        """
        versies = self._versions.get(agent_name, [])
        huidige_stable: AgentVersion | None = None
        for v in reversed(versies):
            if v.lifecycle == AgentLifecycle.STABLE:
                huidige_stable = v
                break

        if huidige_stable is None:
            logger.warning(
                "Rollback niet mogelijk: geen STABLE versie voor agent=%s", agent_name,
            )
            return None

        # Zoek de meest recente DEPRECATED versie (vorige STABLE)
        vorige: AgentVersion | None = None
        for v in reversed(versies):
            if v.lifecycle == AgentLifecycle.DEPRECATED and v.version != huidige_stable.version:
                vorige = v
                break

        if vorige is None:
            logger.warning(
                "Rollback niet mogelijk: geen vorige DEPRECATED versie voor agent=%s",
                agent_name,
            )
            return None

        huidige_stable.lifecycle = AgentLifecycle.DEPRECATED
        vorige.lifecycle = AgentLifecycle.STABLE
        vorige.deployed_at = datetime.now(timezone.utc).isoformat()

        logger.info(
            "Rollback uitgevoerd: agent=%s huidig=%s → DEPRECATED, vorige=%s → STABLE",
            agent_name, huidige_stable.version, vorige.version,
        )
        return vorige

    # ─── Statistieken en evaluatie ─────────────────────────────────

    def record_run(
        self,
        agent_name:  str,
        version:     str,
        eval_score:  float | None = None,
    ) -> None:
        """
        Registreer één uitvoering van een agent-versie.

        Verhoogt ``run_count`` met 1.  Als ``eval_score`` meegegeven wordt,
        wordt de gemiddelde score bijgewerkt via een rolling average:
        ``(oude_score * (n-1) + nieuwe_score) / n``.

        Args:
            agent_name: Naam van de agent.
            version:    Versienummer dat is uitgevoerd.
            eval_score: Optionele evaluatiescore (0.0–1.0) voor deze run.
        """
        versie = self._get_versie(agent_name, version)
        if versie is None:
            logger.warning(
                "record_run: versie niet gevonden agent=%s versie=%s",
                agent_name, version,
            )
            return

        versie.run_count += 1

        if eval_score is not None:
            n = versie.run_count
            if versie.eval_score is None:
                versie.eval_score = eval_score
            else:
                versie.eval_score = (versie.eval_score * (n - 1) + eval_score) / n

        logger.debug(
            "Run geregistreerd: agent=%s versie=%s run_count=%d eval_score=%s",
            agent_name, version, versie.run_count,
            f"{versie.eval_score:.4f}" if versie.eval_score is not None else "n/a",
        )

    def detect_regression(self, agent_name: str, threshold: float = 0.10) -> bool:
        """
        Detecteer een regressie in eval_score ten opzichte van de vorige STABLE.

        Args:
            agent_name: Naam van de agent.
            threshold:  Relatieve drempel (standaard 10 %).  Als de huidige
                        STABLE/CANARY score meer dan ``threshold`` lager is dan
                        de vorige STABLE, wordt een regressie gerapporteerd.

        Returns:
            ``True`` als een regressie gedetecteerd is, anders ``False``.
        """
        versies = self._versions.get(agent_name, [])

        huidige = self.get_active_version(agent_name)
        if huidige is None or huidige.eval_score is None:
            return False

        # Zoek de vorige STABLE (niet de huidige)
        vorige_stable: AgentVersion | None = None
        for v in reversed(versies):
            if v.lifecycle == AgentLifecycle.DEPRECATED and v.eval_score is not None:
                vorige_stable = v
                break

        if vorige_stable is None or vorige_stable.eval_score is None:
            return False

        verschil = vorige_stable.eval_score - huidige.eval_score
        relatief = verschil / vorige_stable.eval_score if vorige_stable.eval_score > 0 else 0.0

        if relatief > threshold:
            logger.warning(
                "Regressie gedetecteerd: agent=%s huidig=%.4f vorig=%.4f verschil=%.2f%%",
                agent_name, huidige.eval_score, vorige_stable.eval_score, relatief * 100,
            )
            return True

        return False

    def get_changelog(self, agent_name: str) -> list[dict[str, Any]]:
        """
        Geef het versie-changelog terug gesorteerd op aanmaakdatum (nieuwste eerst).

        Args:
            agent_name: Naam van de agent.

        Returns:
            Lijst van dicts via :meth:`AgentVersion.to_dict`, nieuwste eerst.
        """
        versies = self._versions.get(agent_name, [])
        gesorteerd = sorted(versies, key=lambda v: v.created_at, reverse=True)
        return [v.to_dict() for v in gesorteerd]

    def get_statistieken(self) -> dict[str, Any]:
        """
        Geef globale statistieken over alle geregistreerde agents en versies.

        Returns:
            Dict met:
            - ``totaal_agents``:    Aantal unieke agent-namen.
            - ``totaal_versies``:   Totaal aantal versies over alle agents.
            - ``lifecycle_counts``: Dict van lifecycle-naam → aantal versies.
            - ``gem_eval_score``:   Gemiddelde eval_score van alle versies met score.
            - ``agents``:           Dict van agent-naam → stats (versies, active, lifecycle).
        """
        alle_versies: list[AgentVersion] = [
            v for vlijst in self._versions.values() for v in vlijst
        ]

        lifecycle_counts: dict[str, int] = {lc.value: 0 for lc in AgentLifecycle}
        for v in alle_versies:
            lifecycle_counts[v.lifecycle.value] += 1

        scores = [v.eval_score for v in alle_versies if v.eval_score is not None]
        gem_score = sum(scores) / len(scores) if scores else None

        agents_stats: dict[str, Any] = {}
        for agent_name, versies in self._versions.items():
            actief = self.get_active_version(agent_name)
            agents_stats[agent_name] = {
                "versies":       len(versies),
                "active":        actief.version if actief else None,
                "lifecycle":     actief.lifecycle.value if actief else None,
                "totaal_runs":   sum(v.run_count for v in versies),
            }

        return {
            "totaal_agents":    len(self._versions),
            "totaal_versies":   len(alle_versies),
            "lifecycle_counts": lifecycle_counts,
            "gem_eval_score":   gem_score,
            "agents":           agents_stats,
        }

    # ─── Persistentie ─────────────────────────────────────────────

    def save(self) -> None:
        """
        Sla de volledige registry op als JSON naar ``_registry_path``.

        Maakt de doeldirectory aan als die nog niet bestaat.
        """
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)

        payload: dict[str, list[dict[str, Any]]] = {
            agent_name: [v.to_dict() for v in versies]
            for agent_name, versies in self._versions.items()
        }

        self._registry_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(
            "Registry opgeslagen naar %s (%d agents, %d versies totaal)",
            self._registry_path,
            len(self._versions),
            sum(len(v) for v in self._versions.values()),
        )

    def load(self) -> None:
        """
        Laad de registry van JSON.

        Maakt de doeldirectory aan als die nog niet bestaat.
        Als het bestand niet bestaat, start de registry leeg (geen fout).
        """
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)

        if not self._registry_path.exists():
            logger.info(
                "Registry-bestand niet gevonden op %s — start leeg",
                self._registry_path,
            )
            self._versions = {}
            return

        try:
            raw = json.loads(self._registry_path.read_text(encoding="utf-8"))
            self._versions = {
                agent_name: [AgentVersion.from_dict(d) for d in versies]
                for agent_name, versies in raw.items()
            }
            logger.info(
                "Registry geladen van %s — %d agents, %d versies totaal",
                self._registry_path,
                len(self._versions),
                sum(len(v) for v in self._versions.values()),
            )
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.error(
                "Fout bij laden registry van %s: %s — start leeg",
                self._registry_path, exc,
            )
            self._versions = {}


# ─────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────

_registry: AgentVersionRegistry | None = None


def get_agent_version_registry() -> AgentVersionRegistry:
    """
    Geef de singleton :class:`AgentVersionRegistry` terug.

    Initialiseert de registry bij eerste aanroep en laadt de JSON van schijf.
    Opvolgende aanroepen geven altijd dezelfde instantie terug.

    Returns:
        Geïnitialiseerde :class:`AgentVersionRegistry`.
    """
    global _registry
    if _registry is None:
        _registry = AgentVersionRegistry(
            _versions={},
            _registry_path=Path("agents/versions/registry.json"),
        )
        _registry.load()
        logger.debug("AgentVersionRegistry singleton geïnitialiseerd")
    return _registry
