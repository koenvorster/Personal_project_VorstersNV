"""
Tests voor ollama/diagram_renderer.py (Wave 9).

Dekt:
- Singleton get_diagram_renderer()
- DiagramDefinition dataclass aanmaken
- render_diagram() → RenderedDiagram met render_success bool
- extract_mermaid_from_text()
- extract_plantuml_from_text()
- create_from_agent_output()
- RenderedDiagram.to_dict() structuur
- Fallback naar .md bestand als mmdc/plantuml niet beschikbaar
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ollama.diagram_renderer import (
    DiagramDefinition,
    DiagramRenderer,
    DiagramType,
    RenderedDiagram,
    get_diagram_renderer,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def renderer(tmp_path: Path) -> DiagramRenderer:
    """Frisse DiagramRenderer met tijdelijke output map per test."""
    return DiagramRenderer(output_dir=tmp_path / "diagrammen")


@pytest.fixture
def mermaid_definition(tmp_path: Path) -> DiagramDefinition:
    """Eenvoudige Mermaid DiagramDefinition voor rendering tests."""
    return DiagramDefinition(
        diagram_id=str(uuid.uuid4()),
        diagram_type=DiagramType.FLOWCHART,
        title="Test Flowchart",
        source_code="graph TD\n  A-->B\n  B-->C",
        created_at=datetime.now(timezone.utc).isoformat(),
        project_id="test-project",
        agent_name="test-agent",
    )


@pytest.fixture
def plantuml_definition() -> DiagramDefinition:
    """Eenvoudige PlantUML DiagramDefinition voor rendering tests."""
    return DiagramDefinition(
        diagram_id=str(uuid.uuid4()),
        diagram_type=DiagramType.PLANTUML,
        title="Test Sequence",
        source_code="Alice -> Bob : Hello\nBob --> Alice : Hi",
        created_at=datetime.now(timezone.utc).isoformat(),
        project_id="test-project",
        agent_name="test-agent",
    )


# ── Singleton ─────────────────────────────────────────────────────────────────

class TestSingleton:
    def test_get_diagram_renderer_retourneert_instantie(self):
        r = get_diagram_renderer()
        assert isinstance(r, DiagramRenderer)

    def test_get_diagram_renderer_is_singleton(self):
        r1 = get_diagram_renderer()
        r2 = get_diagram_renderer()
        assert r1 is r2


# ── DiagramDefinition ─────────────────────────────────────────────────────────

class TestDiagramDefinition:
    def test_aanmaken_met_minimale_velden(self):
        diagram_id = str(uuid.uuid4())
        d = DiagramDefinition(
            diagram_id=diagram_id,
            diagram_type=DiagramType.MERMAID,
            title="Mijn Diagram",
            source_code="graph LR\n  A-->B",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        assert d.diagram_id == diagram_id
        assert d.diagram_type == DiagramType.MERMAID
        assert d.title == "Mijn Diagram"
        assert d.project_id is None
        assert d.agent_name is None

    def test_to_dict_bevat_verwachte_velden(self):
        d = DiagramDefinition(
            diagram_id="abc-123",
            diagram_type=DiagramType.FLOWCHART,
            title="Flow",
            source_code="graph TD\nA-->B",
            created_at="2026-01-01T00:00:00+00:00",
            project_id="proj-1",
            agent_name="agent-x",
        )
        dd = d.to_dict()
        assert dd["diagram_id"] == "abc-123"
        assert dd["diagram_type"] == "flowchart"
        assert dd["title"] == "Flow"
        assert dd["source_code"] == "graph TD\nA-->B"
        assert dd["project_id"] == "proj-1"
        assert dd["agent_name"] == "agent-x"

    def test_from_dict_rondreis(self):
        d = DiagramDefinition(
            diagram_id="xyz-789",
            diagram_type=DiagramType.SEQUENCE,
            title="Sequence",
            source_code="sequenceDiagram\n  A->>B: msg",
            created_at="2026-06-01T12:00:00+00:00",
            project_id="p99",
        )
        hersteld = DiagramDefinition.from_dict(d.to_dict())
        assert hersteld.diagram_id == d.diagram_id
        assert hersteld.diagram_type == d.diagram_type
        assert hersteld.title == d.title


# ── render_mermaid() — fallback mode ──────────────────────────────────────────

class TestRenderMermaid:
    def test_render_geeft_rendered_diagram_terug(self, renderer, mermaid_definition):
        result = renderer.render_mermaid(mermaid_definition)
        assert isinstance(result, RenderedDiagram)

    def test_render_diagram_id_klopt(self, renderer, mermaid_definition):
        result = renderer.render_mermaid(mermaid_definition)
        assert result.diagram_id == mermaid_definition.diagram_id

    def test_render_title_klopt(self, renderer, mermaid_definition):
        result = renderer.render_mermaid(mermaid_definition)
        assert result.title == mermaid_definition.title

    def test_render_mermaid_source_aanwezig(self, renderer, mermaid_definition):
        result = renderer.render_mermaid(mermaid_definition)
        assert result.mermaid_source == mermaid_definition.source_code

    def test_render_fallback_zonder_mmdc_geeft_render_success_false(
        self, renderer, mermaid_definition, monkeypatch
    ):
        """Als mmdc niet beschikbaar is → render_success=False (fallback)."""
        import ollama.diagram_renderer as dr_module
        monkeypatch.setattr(dr_module, "_MMDC_AVAILABLE", False)
        result = renderer.render_mermaid(mermaid_definition)
        assert result.render_success is False

    def test_render_fallback_schrijft_md_bestand(
        self, renderer, mermaid_definition, monkeypatch
    ):
        import ollama.diagram_renderer as dr_module
        monkeypatch.setattr(dr_module, "_MMDC_AVAILABLE", False)
        renderer.render_mermaid(mermaid_definition)
        # .md bestand moet aangemaakt zijn
        project_dir = renderer._project_dir(mermaid_definition.project_id)
        md_bestanden = list(project_dir.glob("*.md"))
        assert len(md_bestanden) == 1

    def test_render_fallback_error_message_aanwezig(
        self, renderer, mermaid_definition, monkeypatch
    ):
        import ollama.diagram_renderer as dr_module
        monkeypatch.setattr(dr_module, "_MMDC_AVAILABLE", False)
        result = renderer.render_mermaid(mermaid_definition)
        assert result.error_message is not None
        assert len(result.error_message) > 0


# ── render_plantuml() — fallback mode ────────────────────────────────────────

class TestRenderPlantUML:
    def test_render_plantuml_geeft_rendered_diagram(self, renderer, plantuml_definition):
        result = renderer.render_plantuml(plantuml_definition)
        assert isinstance(result, RenderedDiagram)

    def test_render_plantuml_fallback_zonder_cli(
        self, renderer, plantuml_definition, monkeypatch
    ):
        import ollama.diagram_renderer as dr_module
        monkeypatch.setattr(dr_module, "_PLANTUML_AVAILABLE", False)
        result = renderer.render_plantuml(plantuml_definition)
        assert result.render_success is False

    def test_render_plantuml_fallback_schrijft_md(
        self, renderer, plantuml_definition, monkeypatch
    ):
        import ollama.diagram_renderer as dr_module
        monkeypatch.setattr(dr_module, "_PLANTUML_AVAILABLE", False)
        renderer.render_plantuml(plantuml_definition)
        project_dir = renderer._project_dir(plantuml_definition.project_id)
        md_bestanden = list(project_dir.glob("*.md"))
        assert len(md_bestanden) == 1


# ── extract_mermaid_from_text() ───────────────────────────────────────────────

class TestExtractMermaid:
    def test_extraheert_enkelvoudig_blok(self, renderer):
        tekst = "```mermaid\ngraph TD\n  A-->B\n```"
        sources = renderer.extract_mermaid_from_text(tekst)
        assert len(sources) == 1
        assert "graph TD" in sources[0]
        assert "A-->B" in sources[0]

    def test_extraheert_meerdere_blokken(self, renderer):
        tekst = (
            "Eerste diagram:\n```mermaid\ngraph LR\n  X-->Y\n```\n\n"
            "Tweede diagram:\n```mermaid\nsequenceDiagram\n  A->>B: Hallo\n```"
        )
        sources = renderer.extract_mermaid_from_text(tekst)
        assert len(sources) == 2

    def test_retourneert_lege_lijst_zonder_mermaid(self, renderer):
        tekst = "Gewone tekst zonder diagrammen."
        sources = renderer.extract_mermaid_from_text(tekst)
        assert sources == []

    def test_source_code_zonder_fences(self, renderer):
        """Extraheert alleen de inhoud, niet de ``` markers."""
        tekst = "```mermaid\ngraph TD\n  A-->B\n```"
        sources = renderer.extract_mermaid_from_text(tekst)
        assert "```" not in sources[0]


# ── extract_plantuml_from_text() ──────────────────────────────────────────────

class TestExtractPlantUML:
    def test_extraheert_enkelvoudig_blok(self, renderer):
        tekst = "@startuml\nAlice -> Bob : Hello\nBob --> Alice : Hi\n@enduml"
        sources = renderer.extract_plantuml_from_text(tekst)
        assert len(sources) == 1
        assert "Alice -> Bob" in sources[0]

    def test_extraheert_broncode_zonder_markers(self, renderer):
        tekst = "@startuml\nA -> B : test\n@enduml"
        sources = renderer.extract_plantuml_from_text(tekst)
        assert "@startuml" not in sources[0]
        assert "@enduml" not in sources[0]

    def test_retourneert_lege_lijst_zonder_plantuml(self, renderer):
        tekst = "Gewone tekst zonder PlantUML."
        sources = renderer.extract_plantuml_from_text(tekst)
        assert sources == []


# ── create_from_agent_output() ────────────────────────────────────────────────

class TestCreateFromAgentOutput:
    def test_geeft_lijst_terug(self, renderer, monkeypatch):
        import ollama.diagram_renderer as dr_module
        monkeypatch.setattr(dr_module, "_MMDC_AVAILABLE", False)
        results = renderer.create_from_agent_output(
            "Geen diagrammen hier.", agent_name="test-agent"
        )
        assert isinstance(results, list)

    def test_geen_diagrammen_geeft_lege_lijst(self, renderer, monkeypatch):
        import ollama.diagram_renderer as dr_module
        monkeypatch.setattr(dr_module, "_MMDC_AVAILABLE", False)
        results = renderer.create_from_agent_output(
            "Gewone output van een agent.", agent_name="analyse-agent"
        )
        assert results == []

    def test_mermaid_blok_geeft_rendered_diagram(self, renderer, monkeypatch):
        import ollama.diagram_renderer as dr_module
        monkeypatch.setattr(dr_module, "_MMDC_AVAILABLE", False)
        agent_output = (
            "Hier is de architectuur:\n```mermaid\ngraph TD\n  A-->B\n```"
        )
        results = renderer.create_from_agent_output(
            agent_output, agent_name="arch-agent", project_id="proj-test"
        )
        assert len(results) == 1
        assert isinstance(results[0], RenderedDiagram)

    def test_plantuml_blok_geeft_rendered_diagram(self, renderer, monkeypatch):
        import ollama.diagram_renderer as dr_module
        monkeypatch.setattr(dr_module, "_PLANTUML_AVAILABLE", False)
        agent_output = (
            "Sequentie:\n@startuml\nAlice -> Bob : Hi\n@enduml"
        )
        results = renderer.create_from_agent_output(
            agent_output, agent_name="seq-agent"
        )
        assert len(results) == 1
        assert isinstance(results[0], RenderedDiagram)

    def test_meerdere_blokken_worden_verwerkt(self, renderer, monkeypatch):
        import ollama.diagram_renderer as dr_module
        monkeypatch.setattr(dr_module, "_MMDC_AVAILABLE", False)
        agent_output = (
            "Diagram 1:\n```mermaid\ngraph TD\n  A-->B\n```\n\n"
            "Diagram 2:\n```mermaid\nsequenceDiagram\n  A->>B: msg\n```"
        )
        results = renderer.create_from_agent_output(
            agent_output, agent_name="multi-agent"
        )
        assert len(results) == 2

    def test_sla_json_op_na_rendering(self, renderer, monkeypatch):
        import ollama.diagram_renderer as dr_module
        monkeypatch.setattr(dr_module, "_MMDC_AVAILABLE", False)
        agent_output = "```mermaid\ngraph LR\n  X-->Y\n```"
        renderer.create_from_agent_output(
            agent_output, agent_name="save-agent", project_id="proj-save"
        )
        project_dir = renderer._project_dir("proj-save")
        json_bestanden = list(project_dir.glob("*.json"))
        assert len(json_bestanden) >= 1


# ── RenderedDiagram.to_dict() ─────────────────────────────────────────────────

class TestRenderedDiagramToDict:
    def test_to_dict_bevat_verwachte_velden(self, renderer, mermaid_definition, monkeypatch):
        import ollama.diagram_renderer as dr_module
        monkeypatch.setattr(dr_module, "_MMDC_AVAILABLE", False)
        result = renderer.render_mermaid(mermaid_definition)
        d = result.to_dict()
        verwachte_velden = {
            "diagram_id", "diagram_type", "title",
            "mermaid_source", "render_success",
            "svg_content", "png_path", "error_message",
        }
        assert verwachte_velden.issubset(d.keys())

    def test_to_dict_render_success_is_bool(self, renderer, mermaid_definition, monkeypatch):
        import ollama.diagram_renderer as dr_module
        monkeypatch.setattr(dr_module, "_MMDC_AVAILABLE", False)
        result = renderer.render_mermaid(mermaid_definition)
        d = result.to_dict()
        assert isinstance(d["render_success"], bool)

    def test_from_dict_rondreis(self, renderer, mermaid_definition, monkeypatch):
        import ollama.diagram_renderer as dr_module
        monkeypatch.setattr(dr_module, "_MMDC_AVAILABLE", False)
        result = renderer.render_mermaid(mermaid_definition)
        hersteld = RenderedDiagram.from_dict(result.to_dict())
        assert hersteld.diagram_id == result.diagram_id
        assert hersteld.render_success == result.render_success
        assert hersteld.mermaid_source == result.mermaid_source


# ── DiagramType detectie ──────────────────────────────────────────────────────

class TestDiagramTypeDetectie:
    def test_sequence_diagram_gedetecteerd(self, renderer):
        source = "sequenceDiagram\n  A->>B: Hallo"
        dtype = renderer._detect_mermaid_type(source)
        assert dtype == DiagramType.SEQUENCE

    def test_class_diagram_gedetecteerd(self, renderer):
        source = "classDiagram\n  Animal <|-- Duck"
        dtype = renderer._detect_mermaid_type(source)
        assert dtype == DiagramType.CLASS_DIAGRAM

    def test_flowchart_gedetecteerd(self, renderer):
        source = "graph TD\n  A-->B"
        dtype = renderer._detect_mermaid_type(source)
        assert dtype == DiagramType.FLOWCHART

    def test_onbekend_type_retourneert_mermaid(self, renderer):
        source = "pie title Test\n  \"A\": 50\n  \"B\": 50"
        dtype = renderer._detect_mermaid_type(source)
        assert dtype == DiagramType.MERMAID


# ── list_diagrams() ───────────────────────────────────────────────────────────

class TestListDiagrams:
    def test_lege_map_retourneert_lege_lijst(self, renderer):
        diagrams = renderer.list_diagrams(project_id="leeg-project")
        assert diagrams == []

    def test_opgeslagen_diagram_verschijnt_in_lijst(self, renderer):
        d = DiagramDefinition(
            diagram_id=str(uuid.uuid4()),
            diagram_type=DiagramType.FLOWCHART,
            title="Opgeslagen Diagram",
            source_code="graph TD\n  A-->B",
            created_at=datetime.now(timezone.utc).isoformat(),
            project_id="list-project",
        )
        renderer.save_definition(d)
        diagrams = renderer.list_diagrams(project_id="list-project")
        assert len(diagrams) == 1
        assert diagrams[0].diagram_id == d.diagram_id
