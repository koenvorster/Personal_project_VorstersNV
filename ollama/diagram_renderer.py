"""
VorstersNV DiagramRenderer — Wave 9

Rendert Mermaid- en PlantUML-diagrammen vanuit agent output naar SVG/PNG/Markdown.
Ondersteunt zowel CLI-rendering (mmdc, plantuml) als fallback-modus waarbij de
broncode als .md-bestand wordt bewaard voor client-side rendering in de frontend.

Use case:
    Na een code-analyseronde bevat de agent output Mermaid-blokken voor
    architectuurdiagrammen, ER-diagrammen of sequentiediagrammen. DiagramRenderer
    extraheert deze blokken, rendert ze indien mogelijk naar SVG/PNG en slaat ze
    op in documentatie/diagrammen/{project_id}/ voor gebruik in rapporten en de
    portal-frontend.

Fallback strategie:
    Als mmdc of plantuml niet beschikbaar zijn (geen CLI-installatie) wordt de
    Mermaid-broncode bewaard als .md-bestand. render_success=False maar GEEN
    exception — de frontend kan de source client-side renderen via Mermaid.js.

Gebruik::

    renderer = get_diagram_renderer()
    diagrams = renderer.create_from_agent_output(
        agent_output=output_text,
        agent_name="architectuur_agent",
        project_id="proj-uuid-hier",
    )
    for d in diagrams:
        print(d.title, d.render_success, d.svg_content[:80] if d.svg_content else d.mermaid_source[:80])
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Optionele CLI-beschikbaarheid ─────────────────────────────────────────────

try:
    _mmdc_check = subprocess.run(
        ["mmdc", "--version"],
        capture_output=True,
        timeout=5,
    )
    _MMDC_AVAILABLE = _mmdc_check.returncode == 0
except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
    _MMDC_AVAILABLE = False

try:
    _plantuml_check = subprocess.run(
        ["plantuml", "-version"],
        capture_output=True,
        timeout=5,
    )
    _PLANTUML_AVAILABLE = _plantuml_check.returncode == 0
except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
    _PLANTUML_AVAILABLE = False

logger.debug(
    "DiagramRenderer CLI-beschikbaarheid: mmdc=%s, plantuml=%s",
    _MMDC_AVAILABLE,
    _PLANTUML_AVAILABLE,
)


# ── Enums ─────────────────────────────────────────────────────────────────────


class DiagramType(Enum):
    MERMAID = "mermaid"
    PLANTUML = "plantuml"
    SEQUENCE = "sequence"
    FLOWCHART = "flowchart"
    CLASS_DIAGRAM = "class_diagram"
    ER_DIAGRAM = "er_diagram"


# ── Dataclasses ───────────────────────────────────────────────────────────────


@dataclass
class DiagramDefinition:
    """Beschrijft een te renderen diagram (vóór rendering)."""

    diagram_id: str
    diagram_type: DiagramType
    title: str
    source_code: str
    created_at: str
    project_id: str | None = None
    agent_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "diagram_id": self.diagram_id,
            "diagram_type": self.diagram_type.value,
            "title": self.title,
            "source_code": self.source_code,
            "created_at": self.created_at,
            "project_id": self.project_id,
            "agent_name": self.agent_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DiagramDefinition:
        return cls(
            diagram_id=data["diagram_id"],
            diagram_type=DiagramType(data["diagram_type"]),
            title=data["title"],
            source_code=data["source_code"],
            created_at=data["created_at"],
            project_id=data.get("project_id"),
            agent_name=data.get("agent_name"),
        )


@dataclass
class RenderedDiagram:
    """Resultaat na rendering — bevat altijd de originele Mermaid source."""

    diagram_id: str
    diagram_type: DiagramType
    title: str
    mermaid_source: str
    render_success: bool
    svg_content: str | None = None
    png_path: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "diagram_id": self.diagram_id,
            "diagram_type": self.diagram_type.value,
            "title": self.title,
            "mermaid_source": self.mermaid_source,
            "render_success": self.render_success,
            "svg_content": self.svg_content,
            "png_path": self.png_path,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RenderedDiagram:
        return cls(
            diagram_id=data["diagram_id"],
            diagram_type=DiagramType(data["diagram_type"]),
            title=data["title"],
            mermaid_source=data["mermaid_source"],
            render_success=data["render_success"],
            svg_content=data.get("svg_content"),
            png_path=data.get("png_path"),
            error_message=data.get("error_message"),
        )


# ── DiagramRenderer ───────────────────────────────────────────────────────────


class DiagramRenderer:
    """
    Extraheert en rendert Mermaid/PlantUML diagrammen vanuit agent output.

    Rendering-strategie:
    - mmdc beschikbaar  → render naar SVG (en optioneel PNG)
    - plantuml beschikbaar → render PlantUML naar PNG
    - fallback          → bewaar broncode als .md, render_success=False

    Output layout:
        documentatie/diagrammen/
        ├── global/          ← project_id=None
        │   ├── <id>.md      ← broncode fallback
        │   └── <id>.json    ← DiagramDefinition metadata
        └── <project_id>/
            ├── <id>.svg
            ├── <id>.png
            └── <id>.json
    """

    # Regex: ```mermaid\n...\n``` (ook zonder newline voor laatste ```)
    _MERMAID_RE = re.compile(
        r"```mermaid\s*\n(.*?)```",
        re.DOTALL | re.IGNORECASE,
    )

    # Regex: @startuml...@enduml (met of zonder label)
    _PLANTUML_RE = re.compile(
        r"@startuml(?:\s+\S+)?\s*\n(.*?)@enduml",
        re.DOTALL | re.IGNORECASE,
    )

    # Detecteer subtype van Mermaid broncode
    _MERMAID_SUBTYPE: list[tuple[re.Pattern[str], DiagramType]] = [
        (re.compile(r"^\s*sequenceDiagram", re.IGNORECASE | re.MULTILINE), DiagramType.SEQUENCE),
        (re.compile(r"^\s*classDiagram", re.IGNORECASE | re.MULTILINE), DiagramType.CLASS_DIAGRAM),
        (re.compile(r"^\s*erDiagram", re.IGNORECASE | re.MULTILINE), DiagramType.ER_DIAGRAM),
        (re.compile(r"^\s*(?:graph|flowchart)\s", re.IGNORECASE | re.MULTILINE), DiagramType.FLOWCHART),
    ]

    def __init__(self, output_dir: Path = Path("documentatie/diagrammen")) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            "DiagramRenderer geïnitialiseerd: output_dir=%s, mmdc=%s, plantuml=%s",
            self.output_dir,
            _MMDC_AVAILABLE,
            _PLANTUML_AVAILABLE,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _project_dir(self, project_id: str | None) -> Path:
        """Geeft de juiste submap terug op basis van project_id."""
        folder = project_id if project_id else "global"
        path = self.output_dir / folder
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _detect_mermaid_type(self, source: str) -> DiagramType:
        """Detecteert het subtype van een Mermaid diagram."""
        for pattern, dtype in self._MERMAID_SUBTYPE:
            if pattern.search(source):
                return dtype
        return DiagramType.MERMAID

    def _make_title(self, source: str, index: int) -> str:
        """Genereert een titel uit de eerste niet-lege regel van de broncode."""
        for line in source.strip().splitlines():
            clean = line.strip().lstrip("#").strip()
            if clean and not clean.startswith("%%"):
                return clean[:80]
        return f"Diagram {index + 1}"

    # ── Publieke API ──────────────────────────────────────────────────────────

    def extract_mermaid_from_text(self, text: str) -> list[str]:
        """
        Extraheert alle ```mermaid...``` blokken uit vrije tekst.

        Returns:
            Lijst van Mermaid-broncodes (zonder de fences).
        """
        return [m.group(1).strip() for m in self._MERMAID_RE.finditer(text)]

    def extract_plantuml_from_text(self, text: str) -> list[str]:
        """
        Extraheert alle @startuml...@enduml blokken uit vrije tekst.

        Returns:
            Lijst van PlantUML-broncodes (zonder de markers).
        """
        return [m.group(1).strip() for m in self._PLANTUML_RE.finditer(text)]

    def render_mermaid(self, definition: DiagramDefinition) -> RenderedDiagram:
        """
        Rendert een Mermaid DiagramDefinition naar SVG/PNG.

        - mmdc beschikbaar  → render naar .svg en .png
        - fallback          → sla broncode op als .md, render_success=False
        """
        project_dir = self._project_dir(definition.project_id)
        base_name = definition.diagram_id

        if not _MMDC_AVAILABLE:
            # Fallback: bewaar broncode als Markdown
            md_path = project_dir / f"{base_name}.md"
            md_path.write_text(
                f"# {definition.title}\n\n```mermaid\n{definition.source_code}\n```\n",
                encoding="utf-8",
            )
            logger.debug("mmdc niet beschikbaar — fallback naar %s", md_path)
            return RenderedDiagram(
                diagram_id=definition.diagram_id,
                diagram_type=definition.diagram_type,
                title=definition.title,
                mermaid_source=definition.source_code,
                render_success=False,
                error_message="mmdc CLI niet beschikbaar. Broncode opgeslagen als .md voor client-side rendering.",
                png_path=None,
                svg_content=None,
            )

        # Tijdelijk invoerbestand aanmaken voor mmdc
        input_file = project_dir / f"{base_name}_input.mmd"
        svg_file = project_dir / f"{base_name}.svg"
        png_file = project_dir / f"{base_name}.png"

        try:
            input_file.write_text(definition.source_code, encoding="utf-8")

            # SVG rendering
            result = subprocess.run(
                ["mmdc", "-i", str(input_file), "-o", str(svg_file), "--quiet"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise RuntimeError(f"mmdc fout: {result.stderr.strip()}")

            svg_content: str | None = None
            if svg_file.exists():
                svg_content = svg_file.read_text(encoding="utf-8")

            # PNG rendering (optioneel, geen harde fout als het mislukt)
            png_path_str: str | None = None
            try:
                png_result = subprocess.run(
                    ["mmdc", "-i", str(input_file), "-o", str(png_file), "--quiet"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if png_result.returncode == 0 and png_file.exists():
                    png_path_str = str(png_file)
            except Exception as png_exc:
                logger.debug("PNG rendering mislukt (niet kritiek): %s", png_exc)

            logger.info("Mermaid diagram gerenderd: %s → %s", definition.diagram_id, svg_file)
            return RenderedDiagram(
                diagram_id=definition.diagram_id,
                diagram_type=definition.diagram_type,
                title=definition.title,
                mermaid_source=definition.source_code,
                render_success=True,
                svg_content=svg_content,
                png_path=png_path_str,
            )

        except Exception as exc:
            logger.warning("Mermaid rendering mislukt voor %s: %s", definition.diagram_id, exc)
            # Fallback: bewaar broncode
            md_path = project_dir / f"{base_name}.md"
            md_path.write_text(
                f"# {definition.title}\n\n```mermaid\n{definition.source_code}\n```\n",
                encoding="utf-8",
            )
            return RenderedDiagram(
                diagram_id=definition.diagram_id,
                diagram_type=definition.diagram_type,
                title=definition.title,
                mermaid_source=definition.source_code,
                render_success=False,
                error_message=str(exc),
            )
        finally:
            # Verwijder tijdelijk invoerbestand
            if input_file.exists():
                input_file.unlink(missing_ok=True)

    def render_plantuml(self, definition: DiagramDefinition) -> RenderedDiagram:
        """
        Rendert een PlantUML DiagramDefinition naar PNG.

        - plantuml beschikbaar → render naar .png
        - fallback             → sla broncode op als .md, render_success=False
        """
        project_dir = self._project_dir(definition.project_id)
        base_name = definition.diagram_id

        # Converteer naar Mermaid-compatible source voor opslag (beste effort)
        mermaid_fallback = (
            f"sequenceDiagram\n    note over A,B: {definition.title}\n"
            f"    %% PlantUML source:\n"
            + "\n".join(f"    %% {line}" for line in definition.source_code.splitlines())
        )

        if not _PLANTUML_AVAILABLE:
            md_path = project_dir / f"{base_name}.md"
            md_path.write_text(
                f"# {definition.title}\n\n```\n@startuml\n{definition.source_code}\n@enduml\n```\n",
                encoding="utf-8",
            )
            logger.debug("plantuml CLI niet beschikbaar — fallback naar %s", md_path)
            return RenderedDiagram(
                diagram_id=definition.diagram_id,
                diagram_type=definition.diagram_type,
                title=definition.title,
                mermaid_source=mermaid_fallback,
                render_success=False,
                error_message="plantuml CLI niet beschikbaar. Broncode opgeslagen als .md.",
            )

        input_file = project_dir / f"{base_name}.puml"
        png_file = project_dir / f"{base_name}.png"

        try:
            puml_content = f"@startuml\n{definition.source_code}\n@enduml"
            input_file.write_text(puml_content, encoding="utf-8")

            result = subprocess.run(
                ["plantuml", "-tpng", str(input_file), "-o", str(project_dir)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise RuntimeError(f"plantuml fout: {result.stderr.strip()}")

            png_path_str = str(png_file) if png_file.exists() else None
            logger.info("PlantUML diagram gerenderd: %s → %s", definition.diagram_id, png_file)

            return RenderedDiagram(
                diagram_id=definition.diagram_id,
                diagram_type=definition.diagram_type,
                title=definition.title,
                mermaid_source=mermaid_fallback,
                render_success=True,
                png_path=png_path_str,
            )

        except Exception as exc:
            logger.warning("PlantUML rendering mislukt voor %s: %s", definition.diagram_id, exc)
            md_path = project_dir / f"{base_name}.md"
            md_path.write_text(
                f"# {definition.title}\n\n```\n@startuml\n{definition.source_code}\n@enduml\n```\n",
                encoding="utf-8",
            )
            return RenderedDiagram(
                diagram_id=definition.diagram_id,
                diagram_type=definition.diagram_type,
                title=definition.title,
                mermaid_source=mermaid_fallback,
                render_success=False,
                error_message=str(exc),
            )
        finally:
            if input_file.exists():
                input_file.unlink(missing_ok=True)

    def save_definition(self, definition: DiagramDefinition) -> Path:
        """
        Slaat een DiagramDefinition op als JSON in de project-map.

        Returns:
            Pad naar het opgeslagen JSON-bestand.
        """
        project_dir = self._project_dir(definition.project_id)
        json_path = project_dir / f"{definition.diagram_id}.json"
        json_path.write_text(
            json.dumps(definition.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.debug("DiagramDefinition opgeslagen: %s", json_path)
        return json_path

    def list_diagrams(self, project_id: str | None = None) -> list[DiagramDefinition]:
        """
        Laadt alle DiagramDefinitions voor een project (of globaal als project_id=None).

        Returns:
            Gesorteerde lijst van DiagramDefinition (nieuwste eerst).
        """
        project_dir = self._project_dir(project_id)
        definitions: list[DiagramDefinition] = []

        for json_file in project_dir.glob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                definitions.append(DiagramDefinition.from_dict(data))
            except Exception as exc:
                logger.warning("Fout bij laden van %s: %s", json_file, exc)

        definitions.sort(key=lambda d: d.created_at, reverse=True)
        return definitions

    def create_from_agent_output(
        self,
        agent_output: str,
        agent_name: str,
        project_id: str | None = None,
    ) -> list[RenderedDiagram]:
        """
        Alles-in-één: extraheer → definieer → render → sla op.

        Stappen:
        1. Extraheert Mermaid- en PlantUML-blokken uit agent_output
        2. Maakt een DiagramDefinition aan voor elk gevonden blok
        3. Rendert elk diagram (met fallback)
        4. Slaat DiagramDefinition op als JSON
        5. Geeft lijst van RenderedDiagram terug

        Args:
            agent_output:  Ruwe tekstuitvoer van een Ollama agent.
            agent_name:    Naam van de agent (voor traceerbaarheid).
            project_id:    Optioneel project UUID voor mapindeling.

        Returns:
            Lijst van RenderedDiagram (één per gevonden diagram-blok).
        """
        results: list[RenderedDiagram] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        # ── Mermaid blokken ───────────────────────────────────────────────────
        mermaid_sources = self.extract_mermaid_from_text(agent_output)
        logger.info(
            "create_from_agent_output: %d Mermaid blok(ken) gevonden (agent=%s, project=%s)",
            len(mermaid_sources),
            agent_name,
            project_id,
        )

        for idx, source in enumerate(mermaid_sources):
            diagram_id = str(uuid.uuid4())
            dtype = self._detect_mermaid_type(source)
            title = self._make_title(source, idx)

            definition = DiagramDefinition(
                diagram_id=diagram_id,
                diagram_type=dtype,
                title=title,
                source_code=source,
                created_at=now_iso,
                project_id=project_id,
                agent_name=agent_name,
            )

            self.save_definition(definition)
            rendered = self.render_mermaid(definition)
            results.append(rendered)

        # ── PlantUML blokken ──────────────────────────────────────────────────
        plantuml_sources = self.extract_plantuml_from_text(agent_output)
        logger.info(
            "create_from_agent_output: %d PlantUML blok(ken) gevonden (agent=%s, project=%s)",
            len(plantuml_sources),
            agent_name,
            project_id,
        )

        for idx, source in enumerate(plantuml_sources):
            diagram_id = str(uuid.uuid4())
            title = self._make_title(source, len(mermaid_sources) + idx)

            definition = DiagramDefinition(
                diagram_id=diagram_id,
                diagram_type=DiagramType.PLANTUML,
                title=title,
                source_code=source,
                created_at=now_iso,
                project_id=project_id,
                agent_name=agent_name,
            )

            self.save_definition(definition)
            rendered = self.render_plantuml(definition)
            results.append(rendered)

        if not results:
            logger.debug(
                "Geen diagrammen gevonden in output van agent '%s'.", agent_name
            )

        return results


# ── Singleton ─────────────────────────────────────────────────────────────────

_renderer_instance: DiagramRenderer | None = None


def get_diagram_renderer() -> DiagramRenderer:
    """
    Geeft de globale DiagramRenderer singleton terug.

    Thread-safe voor gebruik in asyncio-context (geen mutatie na eerste aanmaak).
    """
    global _renderer_instance
    if _renderer_instance is None:
        _renderer_instance = DiagramRenderer()
    return _renderer_instance
