"""
VorstersNV Workflow Loader
Laadt YAML workflow definities uit ollama/workflows/ en biedt
topologische sortering, validatie en chain-lookup.

Gebruik:
    loader = WorkflowLoader()
    wf = loader.load("order-analysis-pipeline")
    steps = loader.get_steps_in_order(wf)
    ok, errors = loader.validate(wf)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False
    yaml = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

_WORKFLOWS_DIR = Path(__file__).parent / "workflows"


# ─────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────

@dataclass
class WorkflowStep:
    id: str
    skill: str
    required: bool = True
    depends_on: list[str] = field(default_factory=list)


@dataclass
class WorkflowDefinition:
    name: str
    version: str
    capability: str
    lane: str
    risk: str
    audience: str
    inputs: list[dict]
    outputs: list[dict]
    steps: list[WorkflowStep]
    chains: dict[str, list[str]] = field(default_factory=dict)

    def get_required_steps(self) -> list[WorkflowStep]:
        return [s for s in self.steps if s.required]

    def get_chain(self, trigger: str) -> list[str]:
        return self.chains.get(trigger, [])


# ─────────────────────────────────────────────
# Loader
# ─────────────────────────────────────────────

class WorkflowLoader:
    """
    Laadt YAML workflow definities en biedt sortering + validatie.

    Als PyYAML niet beschikbaar is, werkt de loader in fallback modus:
    list_workflows() geeft bestandsnamen terug, load() gooit ImportError.
    """

    def __init__(self, workflows_dir: Optional[Path] = None) -> None:
        self._dir = workflows_dir or _WORKFLOWS_DIR

    # ─── Public API ──────────────────────────────────────────────

    def load(self, name: str) -> WorkflowDefinition:
        """
        Laad een workflow op naam of bestandsnaam (zonder .yml).

        Args:
            name: workflow name (veld 'name' in YAML) of bestandsnaam zonder extensie.

        Returns:
            WorkflowDefinition

        Raises:
            ImportError: als PyYAML niet beschikbaar is
            FileNotFoundError: als workflow niet gevonden wordt
            ValueError: als YAML ongeldig is
        """
        if not _YAML_AVAILABLE:
            raise ImportError(
                "PyYAML is niet beschikbaar. Installeer met: pip install pyyaml"
            )

        # Zoek eerst op bestandsnaam, dan op 'name' veld
        candidate = self._dir / f"{name}.yml"
        if candidate.exists():
            return self._parse_file(candidate)

        # Scan alle bestanden op 'name' veld
        for path in self._dir.glob("*.yml"):
            try:
                wf = self._parse_file(path)
                if wf.name == name:
                    return wf
            except (ValueError, KeyError):
                continue

        raise FileNotFoundError(
            f"Workflow '{name}' niet gevonden in {self._dir}"
        )

    def list_workflows(self) -> list[str]:
        """
        Geef alle workflow namen terug.

        Als PyYAML niet beschikbaar is, worden bestandsnamen (zonder .yml) teruggegeven.

        Returns:
            Gesorteerde lijst van workflow namen.
        """
        if not self._dir.exists():
            return []

        yml_files = sorted(self._dir.glob("*.yml"))

        if not _YAML_AVAILABLE:
            logger.warning(
                "PyYAML niet beschikbaar — bestandsnamen worden teruggegeven"
            )
            return [p.stem for p in yml_files]

        names: list[str] = []
        for path in yml_files:
            try:
                with path.open(encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if isinstance(data, dict) and "name" in data:
                    names.append(data["name"])
                else:
                    names.append(path.stem)
            except Exception:
                names.append(path.stem)
        return names

    def get_steps_in_order(self, workflow: WorkflowDefinition) -> list[WorkflowStep]:
        """
        Geef stappen terug in topologische volgorde (Kahn's algoritme).

        Args:
            workflow: WorkflowDefinition

        Returns:
            Gesorteerde lijst van WorkflowStep

        Raises:
            ValueError: als er een circulaire afhankelijkheid bestaat
        """
        steps_by_id = {s.id: s for s in workflow.steps}
        in_degree: dict[str, int] = {s.id: 0 for s in workflow.steps}

        for step in workflow.steps:
            for dep in step.depends_on:
                if dep in in_degree:
                    in_degree[step.id] += 1

        queue = [sid for sid, deg in in_degree.items() if deg == 0]
        result: list[WorkflowStep] = []

        while queue:
            queue.sort()  # deterministisch
            current_id = queue.pop(0)
            result.append(steps_by_id[current_id])

            for step in workflow.steps:
                if current_id in step.depends_on:
                    in_degree[step.id] -= 1
                    if in_degree[step.id] == 0:
                        queue.append(step.id)

        if len(result) != len(workflow.steps):
            visited = {s.id for s in result}
            remaining = [s.id for s in workflow.steps if s.id not in visited]
            raise ValueError(
                f"Circulaire afhankelijkheid gedetecteerd in stappen: {remaining}"
            )

        return result

    def validate(self, workflow: WorkflowDefinition) -> tuple[bool, list[str]]:
        """
        Valideer een WorkflowDefinition.

        Controles:
        - Verplichte velden aanwezig
        - Elke depends_on verwijst naar een bestaande step id
        - Geen circulaire afhankelijkheden
        - Elke step heeft een niet-lege skill

        Returns:
            (is_valid, lijst_van_foutmeldingen)
        """
        errors: list[str] = []

        if not workflow.name:
            errors.append("workflow.name is verplicht")
        if not workflow.capability:
            errors.append("workflow.capability is verplicht")
        if not workflow.lane:
            errors.append("workflow.lane is verplicht")
        if not workflow.steps:
            errors.append("workflow moet minstens 1 stap hebben")

        step_ids = {s.id for s in workflow.steps}

        for step in workflow.steps:
            if not step.skill:
                errors.append(f"Stap '{step.id}' heeft geen skill gedefinieerd")
            for dep in step.depends_on:
                if dep not in step_ids:
                    errors.append(
                        f"Stap '{step.id}' verwijst naar onbekende depends_on: '{dep}'"
                    )

        # Circulaire afhankelijkheid check
        try:
            self.get_steps_in_order(workflow)
        except ValueError as exc:
            errors.append(str(exc))

        return len(errors) == 0, errors

    # ─── Interne helpers ─────────────────────────────────────────

    def _parse_file(self, path: Path) -> WorkflowDefinition:
        """Lees en parseer een YAML workflow bestand."""
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError(f"Ongeldig YAML formaat in {path}")

        steps: list[WorkflowStep] = []
        for raw_step in data.get("steps", []):
            steps.append(
                WorkflowStep(
                    id=raw_step["id"],
                    skill=raw_step["skill"],
                    required=raw_step.get("required", True),
                    depends_on=raw_step.get("depends_on", []),
                )
            )

        return WorkflowDefinition(
            name=data["name"],
            version=str(data.get("version", "1.0")),
            capability=data.get("capability", ""),
            lane=data.get("lane", ""),
            risk=data.get("risk", ""),
            audience=data.get("audience", ""),
            inputs=data.get("inputs", []),
            outputs=data.get("outputs", []),
            steps=steps,
            chains=data.get("chains", {}),
        )
