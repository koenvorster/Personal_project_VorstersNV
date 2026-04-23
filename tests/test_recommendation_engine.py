"""
Tests voor ollama/recommendation_engine.py (Wave 8/9).

Dekt:
- Singleton get_recommendation_engine()
- genereer_recommendations() → RecommendationReport
- Slechte metrics (hoge schuldscore, PHP 5) → kritieke aanbevelingen
- Goede metrics → geen kritieke aanbevelingen
- Output-velden: prioriteit, beschrijving, actie_stappen, etc.
- RecommendationReport.to_dict() en to_markdown()
- Recommendation.to_dict() / from_dict()
"""
import pytest

from ollama.recommendation_engine import (
    Recommendation,
    RecommendationEngine,
    RecommendationPriority,
    RecommendationReport,
    RecommendationType,
    get_recommendation_engine,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def engine() -> RecommendationEngine:
    """Frisse engine zonder externe afhankelijkheden."""
    return RecommendationEngine()


@pytest.fixture
def slechte_metrics_context() -> dict:
    """Context met hoge schuldscore en verouderde technologiestapel."""
    return {
        "sector": "RETAIL",
        "talen": ["php", "javascript"],
        "technologieen": ["PHP 5.6", "jQuery"],
        "bevindingen": ["geen CI/CD", "rest api aanwezig"],
        "schuldscore": 8.5,
    }


@pytest.fixture
def goede_metrics_context() -> dict:
    """Context met lage schuldscore en moderne stack."""
    return {
        "sector": "RETAIL",
        "talen": ["python", "typescript"],
        "technologieen": ["Python 3.12", "FastAPI", "React 18"],
        "bevindingen": ["CI/CD aanwezig", "unit tests aanwezig"],
        "schuldscore": 1.5,
    }


# ── Singleton ─────────────────────────────────────────────────────────────────

class TestSingleton:
    def test_get_recommendation_engine_retourneert_instantie(self):
        eng = get_recommendation_engine()
        assert isinstance(eng, RecommendationEngine)

    def test_get_recommendation_engine_is_singleton(self):
        eng1 = get_recommendation_engine()
        eng2 = get_recommendation_engine()
        assert eng1 is eng2


# ── genereer_recommendations() ───────────────────────────────────────────────

class TestGenereerRecommendations:
    def test_retourneert_recommendation_report(self, engine):
        rapport = engine.genereer_recommendations("TEST-001")
        assert isinstance(rapport, RecommendationReport)

    def test_rapport_bevat_project_id(self, engine):
        rapport = engine.genereer_recommendations("PROJ-XYZ")
        assert rapport.project_id == "PROJ-XYZ"

    def test_rapport_bevat_report_id(self, engine):
        rapport = engine.genereer_recommendations("TEST-002")
        assert rapport.report_id
        assert len(rapport.report_id) == 36  # UUID4

    def test_rapport_bevat_aangemaakt_op(self, engine):
        rapport = engine.genereer_recommendations("TEST-003")
        assert rapport.aangemaakt_op
        assert "T" in rapport.aangemaakt_op  # ISO 8601

    def test_lege_context_geeft_aanbevelingen(self, engine):
        """Dependency scanning aanbeveling wordt altijd gegenereerd."""
        rapport = engine.genereer_recommendations("LEEG-001")
        # Altijd tenminste dependency scanning
        assert rapport.totaal_aanbevelingen >= 1

    def test_totaal_aanbevelingen_klopt_met_lijst(self, engine):
        rapport = engine.genereer_recommendations("COUNT-001")
        assert rapport.totaal_aanbevelingen == len(rapport.alle_aanbevelingen)

    def test_aanbevelingen_gesorteerd_op_roi_desc(self, engine, slechte_metrics_context):
        rapport = engine.genereer_recommendations("SORT-001", slechte_metrics_context)
        if len(rapport.alle_aanbevelingen) >= 2:
            roi_scores = [r.roi_score for r in rapport.alle_aanbevelingen]
            assert roi_scores == sorted(roi_scores, reverse=True)

    def test_top_3_is_eerste_3_van_lijst(self, engine, slechte_metrics_context):
        rapport = engine.genereer_recommendations("TOP3-001", slechte_metrics_context)
        verwacht = rapport.alle_aanbevelingen[:3]
        assert len(rapport.top_3) <= 3
        for i, rec in enumerate(rapport.top_3):
            assert rec.recommendation_id == verwacht[i].recommendation_id

    def test_sector_wordt_opgeslagen(self, engine, slechte_metrics_context):
        rapport = engine.genereer_recommendations("SECTOR-001", slechte_metrics_context)
        assert rapport.sector == "RETAIL"


# ── Slechte metrics → kritieke aanbevelingen ─────────────────────────────────

class TestSlechteMetrics:
    def test_hoge_schuldscore_geeft_kritieke_aanbeveling(self, engine):
        context = {"schuldscore": 9.0}
        rapport = engine.genereer_recommendations("HOOG-001", context)
        kritiek = [r for r in rapport.alle_aanbevelingen
                   if r.prioriteit == RecommendationPriority.KRITIEK]
        assert len(kritiek) >= 1

    def test_php5_geeft_kritieke_aanbeveling(self, engine):
        context = {"technologieen": ["PHP 5.6"]}
        rapport = engine.genereer_recommendations("PHP5-001", context)
        kritiek = [r for r in rapport.alle_aanbevelingen
                   if r.prioriteit == RecommendationPriority.KRITIEK]
        assert len(kritiek) >= 1

    def test_php5_aanbeveling_is_modernize_type(self, engine):
        context = {"technologieen": ["PHP 5.6"]}
        rapport = engine.genereer_recommendations("PHP5-TYPE", context)
        modernize = [r for r in rapport.alle_aanbevelingen
                     if r.type == RecommendationType.MODERNIZE
                     and r.prioriteit == RecommendationPriority.KRITIEK]
        assert len(modernize) >= 1

    def test_kritieke_aanbevelingen_worden_geteld(self, engine, slechte_metrics_context):
        rapport = engine.genereer_recommendations("KRIT-COUNT", slechte_metrics_context)
        verwacht_kritiek = sum(
            1 for r in rapport.alle_aanbevelingen
            if r.prioriteit == RecommendationPriority.KRITIEK
        )
        assert rapport.kritieke_aanbevelingen == verwacht_kritiek

    def test_schuldscore_boven_7_is_refactor_kritiek(self, engine):
        context = {"schuldscore": 7.5}
        rapport = engine.genereer_recommendations("SD75-001", context)
        refactor_kritiek = [
            r for r in rapport.alle_aanbevelingen
            if r.type == RecommendationType.REFACTOR
            and r.prioriteit == RecommendationPriority.KRITIEK
        ]
        assert len(refactor_kritiek) >= 1


# ── Goede metrics → geen kritieke aanbevelingen ───────────────────────────────

class TestGoedeMetrics:
    def test_lage_schuldscore_geeft_geen_kritieke_refactor(self, engine, goede_metrics_context):
        rapport = engine.genereer_recommendations("GOED-001", goede_metrics_context)
        refactor_kritiek = [
            r for r in rapport.alle_aanbevelingen
            if r.type == RecommendationType.REFACTOR
            and r.prioriteit == RecommendationPriority.KRITIEK
        ]
        assert len(refactor_kritiek) == 0

    def test_moderne_stack_geen_php5_kritiek(self, engine, goede_metrics_context):
        rapport = engine.genereer_recommendations("GOED-002", goede_metrics_context)
        php5_kritiek = [
            r for r in rapport.alle_aanbevelingen
            if r.prioriteit == RecommendationPriority.KRITIEK
            and "php" in r.titel.lower()
        ]
        assert len(php5_kritiek) == 0


# ── Aanbeveling-velden ────────────────────────────────────────────────────────

class TestAanbevelingVelden:
    def test_elke_aanbeveling_heeft_titel(self, engine, slechte_metrics_context):
        rapport = engine.genereer_recommendations("VELD-001", slechte_metrics_context)
        for rec in rapport.alle_aanbevelingen:
            assert rec.titel
            assert len(rec.titel) > 3

    def test_elke_aanbeveling_heeft_beschrijving(self, engine, slechte_metrics_context):
        rapport = engine.genereer_recommendations("VELD-002", slechte_metrics_context)
        for rec in rapport.alle_aanbevelingen:
            assert rec.beschrijving
            assert len(rec.beschrijving) > 10

    def test_elke_aanbeveling_heeft_actie_stappen(self, engine, slechte_metrics_context):
        rapport = engine.genereer_recommendations("VELD-003", slechte_metrics_context)
        for rec in rapport.alle_aanbevelingen:
            assert isinstance(rec.actie_stappen, list)
            assert len(rec.actie_stappen) >= 1

    def test_elke_aanbeveling_heeft_impact_en_effort_score(self, engine, slechte_metrics_context):
        rapport = engine.genereer_recommendations("VELD-004", slechte_metrics_context)
        for rec in rapport.alle_aanbevelingen:
            assert 0.0 <= rec.impact_score <= 1.0
            assert 0.0 <= rec.effort_score <= 1.0

    def test_roi_score_berekend(self, engine):
        context = {"schuldscore": 8.0}
        rapport = engine.genereer_recommendations("ROI-001", context)
        for rec in rapport.alle_aanbevelingen:
            verwacht_roi = round(rec.impact_score / max(rec.effort_score, 0.01), 4)
            assert abs(rec.roi_score - verwacht_roi) < 0.01

    def test_prioriteit_is_geldig_enum(self, engine, slechte_metrics_context):
        rapport = engine.genereer_recommendations("PRIO-001", slechte_metrics_context)
        geldige_prioriteiten = {p.value for p in RecommendationPriority}
        for rec in rapport.alle_aanbevelingen:
            assert rec.prioriteit.value in geldige_prioriteiten

    def test_type_is_geldig_enum(self, engine, slechte_metrics_context):
        rapport = engine.genereer_recommendations("TYPE-001", slechte_metrics_context)
        geldige_types = {t.value for t in RecommendationType}
        for rec in rapport.alle_aanbevelingen:
            assert rec.type.value in geldige_types


# ── to_dict() / from_dict() ───────────────────────────────────────────────────

class TestSerializatie:
    def test_recommendation_to_dict_bevat_verwachte_velden(self, engine):
        context = {"schuldscore": 8.0}
        rapport = engine.genereer_recommendations("DICT-001", context)
        assert len(rapport.alle_aanbevelingen) > 0
        rec = rapport.alle_aanbevelingen[0]
        d = rec.to_dict()
        verwachte_velden = {
            "recommendation_id", "project_id", "type", "prioriteit",
            "titel", "beschrijving", "impact_score", "effort_score",
            "roi_score", "sector_benchmark_ref", "gerelateerde_nodes",
            "actie_stappen", "aangemaakt_op",
        }
        assert verwachte_velden.issubset(d.keys())

    def test_recommendation_from_dict_rondreis(self, engine):
        context = {"schuldscore": 8.0}
        rapport = engine.genereer_recommendations("RONDREIS-001", context)
        assert len(rapport.alle_aanbevelingen) > 0
        rec = rapport.alle_aanbevelingen[0]
        d = rec.to_dict()
        hersteld = Recommendation.from_dict(d)
        assert hersteld.recommendation_id == rec.recommendation_id
        assert hersteld.prioriteit == rec.prioriteit
        assert hersteld.type == rec.type
        assert hersteld.roi_score == rec.roi_score

    def test_rapport_to_dict_bevat_verwachte_velden(self, engine):
        rapport = engine.genereer_recommendations("RDIKT-001")
        d = rapport.to_dict()
        verwachte_velden = {
            "report_id", "project_id", "sector",
            "totaal_aanbevelingen", "kritieke_aanbevelingen",
            "top_3", "alle_aanbevelingen",
            "sector_vergelijking", "aangemaakt_op",
        }
        assert verwachte_velden.issubset(d.keys())

    def test_rapport_to_dict_alle_aanbevelingen_is_lijst(self, engine):
        rapport = engine.genereer_recommendations("LIJST-001")
        d = rapport.to_dict()
        assert isinstance(d["alle_aanbevelingen"], list)

    def test_rapport_to_markdown_retourneert_string(self, engine, slechte_metrics_context):
        rapport = engine.genereer_recommendations("MD-001", slechte_metrics_context)
        md = rapport.to_markdown()
        assert isinstance(md, str)
        assert len(md) > 50

    def test_rapport_to_markdown_bevat_samenvatting_header(self, engine, slechte_metrics_context):
        rapport = engine.genereer_recommendations("MD-002", slechte_metrics_context)
        md = rapport.to_markdown()
        assert "## 📊 Samenvatting" in md

    def test_rapport_to_markdown_bevat_project_id(self, engine):
        rapport = engine.genereer_recommendations("MD-003-PROJID")
        md = rapport.to_markdown()
        assert "MD-003-PROJID" in md
