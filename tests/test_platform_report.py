"""
Tests voor ollama/platform_report.py (Wave 8).

Dekt:
- Singleton get_weekly_report_generator()
- genereer_rapport() → PlatformWeekRapport
- Rapport bevat agents sectie, gaps sectie, waves sectie
- to_dict() heeft verwachte secties
- to_markdown() → string met Markdown headers
- sla_rapport_op() → schrijft JSON + MD bestanden
"""
from pathlib import Path

import pytest

from ollama.platform_report import (
    AgentVerbeteringRecord,
    KostEfficientieTrend,
    PlatformWeekRapport,
    WeeklyReportGenerator,
    get_weekly_report_generator,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def generator() -> WeeklyReportGenerator:
    """Frisse WeeklyReportGenerator zonder externe afhankelijkheden."""
    return WeeklyReportGenerator()


@pytest.fixture
def basis_rapport() -> PlatformWeekRapport:
    """Een handmatig samengesteld rapport voor serialisatie-tests."""
    import uuid
    from datetime import datetime, timezone

    return PlatformWeekRapport(
        rapport_id=str(uuid.uuid4()),
        week="2026-W20",
        gegenereerd_op=datetime.now(timezone.utc).isoformat(),
        agents_verbeterd=[
            AgentVerbeteringRecord(
                agent_name="analyse_agent",
                vorige_score=3.2,
                huidige_score=4.1,
                score_delta=0.9,
                versie_bumps=2,
                trend="stijgend",
            )
        ],
        agents_gedaald=[],
        agents_stabiel=3,
        gaps_gesloten=["G-32: Multi-tenant isolatie", "G-33: RAGEngine"],
        gaps_open=["G-45: Self-improvement loop"],
        kost_trend=KostEfficientieTrend(
            week="2026-W20",
            totaal_tokens_geschat=50_000,
            totaal_chunks_verwerkt=200,
            gemiddelde_chunk_tijd_sec=1.5,
            model_verdeling={"deepseek-r1:7b": 10},
            kostprijs_index=1.0,
        ),
        totaal_feedback_records=5,
        gemiddelde_klanttevredenheid=4.2,
        top_klacht="rapportage duurt lang",
        waves_status={
            "W1": "COMPLEET", "W2": "COMPLEET", "W3": "COMPLEET",
            "W4": "COMPLEET", "W5": "COMPLEET", "W6": "COMPLEET",
            "W7": "COMPLEET", "W8": "ACTIEF",
        },
    )


# ── Singleton ─────────────────────────────────────────────────────────────────

class TestSingleton:
    def test_get_weekly_report_generator_retourneert_instantie(self):
        gen = get_weekly_report_generator()
        assert isinstance(gen, WeeklyReportGenerator)

    def test_get_weekly_report_generator_is_singleton(self):
        gen1 = get_weekly_report_generator()
        gen2 = get_weekly_report_generator()
        assert gen1 is gen2


# ── genereer_rapport() ────────────────────────────────────────────────────────

class TestGenereerRapport:
    def test_retourneert_platform_weekrapport(self, generator):
        rapport = generator.genereer_rapport()
        assert isinstance(rapport, PlatformWeekRapport)

    def test_rapport_bevat_rapport_id(self, generator):
        rapport = generator.genereer_rapport()
        assert rapport.rapport_id
        assert len(rapport.rapport_id) == 36  # UUID4

    def test_rapport_bevat_week(self, generator):
        rapport = generator.genereer_rapport()
        assert rapport.week
        assert "W" in rapport.week  # formaat "YYYY-WNN"

    def test_rapport_bevat_gegenereerd_op(self, generator):
        rapport = generator.genereer_rapport()
        assert rapport.gegenereerd_op
        assert "T" in rapport.gegenereerd_op  # ISO 8601

    def test_rapport_met_expliciete_week(self, generator):
        rapport = generator.genereer_rapport(week="2026-W01")
        assert rapport.week == "2026-W01"

    def test_rapport_gaps_gesloten_is_lijst(self, generator):
        rapport = generator.genereer_rapport()
        assert isinstance(rapport.gaps_gesloten, list)

    def test_rapport_gaps_open_is_lijst(self, generator):
        rapport = generator.genereer_rapport()
        assert isinstance(rapport.gaps_open, list)

    def test_rapport_bevat_waves_status(self, generator):
        rapport = generator.genereer_rapport()
        assert isinstance(rapport.waves_status, dict)
        assert len(rapport.waves_status) > 0

    def test_rapport_agents_verbeterd_is_lijst(self, generator):
        rapport = generator.genereer_rapport()
        assert isinstance(rapport.agents_verbeterd, list)

    def test_rapport_agents_gedaald_is_lijst(self, generator):
        rapport = generator.genereer_rapport()
        assert isinstance(rapport.agents_gedaald, list)

    def test_rapport_totaal_feedback_records_is_int(self, generator):
        rapport = generator.genereer_rapport()
        assert isinstance(rapport.totaal_feedback_records, int)

    def test_rapport_hardcoded_gaps_aanwezig(self, generator):
        """Hardcoded gaps uit _GAPS_GESLOTEN moeten in het rapport staan."""
        rapport = generator.genereer_rapport()
        # Tenminste één gap gesloten verwacht (hardcoded in module)
        assert len(rapport.gaps_gesloten) > 0


# ── Rapport secties ───────────────────────────────────────────────────────────

class TestRapportSecties:
    def test_waves_status_bevat_w8(self, generator):
        rapport = generator.genereer_rapport()
        assert "W8" in rapport.waves_status

    def test_waves_status_waarden_zijn_strings(self, generator):
        rapport = generator.genereer_rapport()
        for wave, status in rapport.waves_status.items():
            assert isinstance(wave, str)
            assert isinstance(status, str)

    def test_agents_sectie_stabiel_is_int(self, generator):
        rapport = generator.genereer_rapport()
        assert isinstance(rapport.agents_stabiel, int)
        assert rapport.agents_stabiel >= 0


# ── to_dict() ─────────────────────────────────────────────────────────────────

class TestToDict:
    def test_to_dict_retourneert_dict(self, basis_rapport):
        d = basis_rapport.to_dict()
        assert isinstance(d, dict)

    def test_to_dict_bevat_rapport_id(self, basis_rapport):
        d = basis_rapport.to_dict()
        assert "rapport_id" in d
        assert d["rapport_id"] == basis_rapport.rapport_id

    def test_to_dict_bevat_agents_sectie(self, basis_rapport):
        d = basis_rapport.to_dict()
        assert "agents_verbeterd" in d
        assert "agents_gedaald" in d
        assert "agents_stabiel" in d

    def test_to_dict_bevat_gaps_sectie(self, basis_rapport):
        d = basis_rapport.to_dict()
        assert "gaps_gesloten" in d
        assert "gaps_open" in d

    def test_to_dict_bevat_waves_sectie(self, basis_rapport):
        d = basis_rapport.to_dict()
        assert "waves_status" in d

    def test_to_dict_bevat_kost_trend(self, basis_rapport):
        d = basis_rapport.to_dict()
        assert "kost_trend" in d
        assert d["kost_trend"] is not None

    def test_to_dict_bevat_feedback_velden(self, basis_rapport):
        d = basis_rapport.to_dict()
        assert "totaal_feedback_records" in d
        assert "gemiddelde_klanttevredenheid" in d
        assert "top_klacht" in d

    def test_to_dict_agents_verbeterd_is_lijst_van_dicts(self, basis_rapport):
        d = basis_rapport.to_dict()
        assert isinstance(d["agents_verbeterd"], list)
        assert len(d["agents_verbeterd"]) == 1
        assert isinstance(d["agents_verbeterd"][0], dict)

    def test_to_dict_gaps_gesloten_zijn_strings(self, basis_rapport):
        d = basis_rapport.to_dict()
        for gap in d["gaps_gesloten"]:
            assert isinstance(gap, str)

    def test_to_dict_kost_trend_bevat_velden(self, basis_rapport):
        d = basis_rapport.to_dict()
        kt = d["kost_trend"]
        verwachte_velden = {
            "week", "totaal_tokens_geschat", "totaal_chunks_verwerkt",
            "gemiddelde_chunk_tijd_sec", "model_verdeling", "kostprijs_index",
        }
        assert verwachte_velden.issubset(kt.keys())

    def test_to_dict_zonder_kost_trend(self, generator):
        import uuid
        from datetime import datetime, timezone
        rapport = PlatformWeekRapport(
            rapport_id=str(uuid.uuid4()),
            week="2026-W21",
            gegenereerd_op=datetime.now(timezone.utc).isoformat(),
            agents_verbeterd=[],
            agents_gedaald=[],
            agents_stabiel=0,
            gaps_gesloten=[],
            gaps_open=[],
            kost_trend=None,
            totaal_feedback_records=0,
            gemiddelde_klanttevredenheid=None,
            top_klacht=None,
            waves_status={"W8": "ACTIEF"},
        )
        d = rapport.to_dict()
        assert d["kost_trend"] is None


# ── to_markdown() ─────────────────────────────────────────────────────────────

class TestToMarkdown:
    def test_to_markdown_retourneert_string(self, basis_rapport):
        md = basis_rapport.to_markdown()
        assert isinstance(md, str)

    def test_to_markdown_bevat_hoofdtitel(self, basis_rapport):
        md = basis_rapport.to_markdown()
        assert "# 📊 VorstersNV Platform Weekrapport" in md

    def test_to_markdown_bevat_week(self, basis_rapport):
        md = basis_rapport.to_markdown()
        assert "2026-W20" in md

    def test_to_markdown_bevat_agent_performance_header(self, basis_rapport):
        md = basis_rapport.to_markdown()
        assert "## 🤖 Agent Performance" in md

    def test_to_markdown_bevat_gap_closure_header(self, basis_rapport):
        md = basis_rapport.to_markdown()
        assert "## 🔒 Gap Closure Status" in md

    def test_to_markdown_bevat_kostefficiëntie_header(self, basis_rapport):
        md = basis_rapport.to_markdown()
        assert "## 💰 Kostefficiëntie" in md

    def test_to_markdown_bevat_klantfeedback_header(self, basis_rapport):
        md = basis_rapport.to_markdown()
        assert "## ⭐ Klantfeedback" in md

    def test_to_markdown_bevat_waves_header(self, basis_rapport):
        md = basis_rapport.to_markdown()
        assert "## 🌊 Waves Status" in md

    def test_to_markdown_bevat_verbeterde_agent(self, basis_rapport):
        md = basis_rapport.to_markdown()
        assert "analyse_agent" in md

    def test_to_markdown_bevat_gesloten_gap(self, basis_rapport):
        md = basis_rapport.to_markdown()
        assert "G-32" in md

    def test_to_markdown_bevat_waves_status_tabel(self, basis_rapport):
        md = basis_rapport.to_markdown()
        assert "W8" in md

    def test_to_markdown_generator(self, generator):
        """Genereer via de generator en controleer markdown."""
        rapport = generator.genereer_rapport()
        md = rapport.to_markdown()
        assert isinstance(md, str)
        assert "## 🤖 Agent Performance" in md
        assert "## 🌊 Waves Status" in md


# ── sla_rapport_op() ─────────────────────────────────────────────────────────

class TestSlaRapportOp:
    def test_sla_op_retourneert_pad(self, generator, basis_rapport, tmp_path):
        md_pad = generator.sla_rapport_op(basis_rapport, output_dir=str(tmp_path))
        assert isinstance(md_pad, Path)

    def test_sla_op_schrijft_markdown_bestand(self, generator, basis_rapport, tmp_path):
        md_pad = generator.sla_rapport_op(basis_rapport, output_dir=str(tmp_path))
        assert md_pad.exists()
        assert md_pad.suffix == ".md"

    def test_sla_op_schrijft_json_bestand(self, generator, basis_rapport, tmp_path):
        generator.sla_rapport_op(basis_rapport, output_dir=str(tmp_path))
        json_bestanden = list(tmp_path.glob("*.json"))
        assert len(json_bestanden) == 1

    def test_sla_op_markdown_heeft_correcte_inhoud(self, generator, basis_rapport, tmp_path):
        md_pad = generator.sla_rapport_op(basis_rapport, output_dir=str(tmp_path))
        inhoud = md_pad.read_text(encoding="utf-8")
        assert "# 📊 VorstersNV Platform Weekrapport" in inhoud

    def test_sla_op_json_is_geldig(self, generator, basis_rapport, tmp_path):
        import json
        generator.sla_rapport_op(basis_rapport, output_dir=str(tmp_path))
        json_bestanden = list(tmp_path.glob("*.json"))
        data = json.loads(json_bestanden[0].read_text(encoding="utf-8"))
        assert "rapport_id" in data
        assert data["rapport_id"] == basis_rapport.rapport_id

    def test_bestandsnaam_bevat_week(self, generator, basis_rapport, tmp_path):
        md_pad = generator.sla_rapport_op(basis_rapport, output_dir=str(tmp_path))
        assert "2026-W20" in md_pad.name


# ── AgentVerbeteringRecord ────────────────────────────────────────────────────

class TestAgentVerbeteringRecord:
    def test_to_dict_bevat_verwachte_velden(self):
        record = AgentVerbeteringRecord(
            agent_name="test_agent",
            vorige_score=3.5,
            huidige_score=4.2,
            score_delta=0.7,
            versie_bumps=1,
            trend="stijgend",
        )
        d = record.to_dict()
        verwachte_velden = {
            "agent_name", "vorige_score", "huidige_score",
            "score_delta", "versie_bumps", "trend",
        }
        assert verwachte_velden.issubset(d.keys())

    def test_to_dict_agent_name_klopt(self):
        record = AgentVerbeteringRecord(
            agent_name="mijn_agent",
            vorige_score=None,
            huidige_score=3.0,
            score_delta=None,
            versie_bumps=0,
            trend="nieuw",
        )
        assert record.to_dict()["agent_name"] == "mijn_agent"
        assert record.to_dict()["trend"] == "nieuw"


# ── KostEfficientieTrend ──────────────────────────────────────────────────────

class TestKostEfficientieTrend:
    def test_to_dict_bevat_week(self):
        kt = KostEfficientieTrend(
            week="2026-W15",
            totaal_tokens_geschat=10_000,
            totaal_chunks_verwerkt=50,
            gemiddelde_chunk_tijd_sec=2.0,
            model_verdeling={"mistral:7b": 5},
            kostprijs_index=0.95,
        )
        d = kt.to_dict()
        assert d["week"] == "2026-W15"
        assert d["totaal_tokens_geschat"] == 10_000
        assert d["kostprijs_index"] == 0.95
