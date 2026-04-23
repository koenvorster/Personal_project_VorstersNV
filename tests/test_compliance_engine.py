"""
Tests voor ollama/compliance_engine.py (Wave 9).

Dekt:
- Singleton get_compliance_engine()
- valideer() met lege tekst
- GDPR: rijksregisternummer, bewaartermijn
- Belgian: BTW aanwezig/afwezig
- NIS2: incident-keywords
- ComplianceReport.to_dict() structuur
- Meerdere violations tegelijk
"""
import pytest

from ollama.compliance_engine import (
    ComplianceEngine,
    ComplianceLaag,
    ComplianceReport,
    ComplianceViolation,
    ViolationSeverity,
    get_compliance_engine,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def engine() -> ComplianceEngine:
    """Geeft een frisse ComplianceEngine per test."""
    return ComplianceEngine()


# ── Singleton ─────────────────────────────────────────────────────────────────

class TestSingleton:
    def test_get_compliance_engine_retourneert_instantie(self):
        eng = get_compliance_engine()
        assert isinstance(eng, ComplianceEngine)

    def test_get_compliance_engine_is_singleton(self):
        eng1 = get_compliance_engine()
        eng2 = get_compliance_engine()
        assert eng1 is eng2


# ── valideer() — lege invoer ──────────────────────────────────────────────────

class TestValideerLegeInvoer:
    def test_lege_string_retourneert_compliant_rapport(self, engine):
        rapport = engine.valideer("")
        assert isinstance(rapport, ComplianceReport)
        assert rapport.is_compliant is True
        assert rapport.violations == []

    def test_whitespace_only_retourneert_compliant_rapport(self, engine):
        rapport = engine.valideer("   \n\t  ")
        assert rapport.is_compliant is True
        assert len(rapport.violations) == 0

    def test_rapport_heeft_rapport_id(self, engine):
        rapport = engine.valideer("")
        assert rapport.rapport_id
        assert len(rapport.rapport_id) == 36  # UUID4 formaat

    def test_rapport_heeft_gecontroleerd_op_timestamp(self, engine):
        rapport = engine.valideer("")
        assert rapport.gecontroleerd_op
        assert "T" in rapport.gecontroleerd_op  # ISO 8601


# ── GDPR checks ───────────────────────────────────────────────────────────────

class TestGDPRViolations:
    def test_rijksregisternummer_geeft_gdpr_violation(self, engine):
        tekst = "De klant met rijksregisternummer 85.04.12-345.67 heeft betaald."
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.GDPR])
        regel_codes = [v.regel_code for v in rapport.violations]
        assert "GDPR-ART9-RR" in regel_codes

    def test_rijksregisternummer_violation_is_critical(self, engine):
        tekst = "Rijksregisternummer: 85.04.12-345.67"
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.GDPR])
        rr_violations = [v for v in rapport.violations if v.regel_code == "GDPR-ART9-RR"]
        assert len(rr_violations) == 1
        assert rr_violations[0].severity == ViolationSeverity.CRITICAL

    def test_rijksregisternummer_maakt_rapport_non_compliant(self, engine):
        tekst = "Rijksregisternummer aanwezig: 85.04.12-345.67"
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.GDPR])
        assert rapport.is_compliant is False

    def test_bewaartermijn_meer_dan_10_jaar_geeft_violation(self, engine):
        tekst = "Wij bewaren uw gegevens gedurende 15 jaar in onze archieven."
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.GDPR])
        regel_codes = [v.regel_code for v in rapport.violations]
        assert "GDPR-ART5-BEWAAR" in regel_codes

    def test_bewaartermijn_precies_10_jaar_geeft_geen_bewaar_violation(self, engine):
        tekst = "Wij bewaren uw gegevens gedurende 10 jaar in onze archieven."
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.GDPR])
        regel_codes = [v.regel_code for v in rapport.violations]
        assert "GDPR-ART5-BEWAAR" not in regel_codes

    def test_tekst_zonder_pii_geeft_geen_gdpr_violations(self, engine):
        tekst = "De orderbevestiging is succesvol verwerkt."
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.GDPR])
        gdpr_violations = [v for v in rapport.violations if v.laag == ComplianceLaag.GDPR]
        assert len(gdpr_violations) == 0


# ── Belgische regelgeving ─────────────────────────────────────────────────────

class TestBelgischeRegelgeving:
    def test_btw_nummer_aanwezig_geeft_geen_btw_violation(self, engine):
        tekst = "Factuur totaal: €1.200,00 excl. BTW (21%). BTW-nummer BE0123.456.789."
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.BELGISCHE_REGELGEVING])
        btw_violations = [v for v in rapport.violations if v.regel_code == "BEL-BTW-001"]
        assert len(btw_violations) == 0

    def test_commercieel_contract_zonder_btw_geeft_violation(self, engine):
        tekst = "Factuur voor consultancydiensten. Totaal bedrag: €2.500,00."
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.BELGISCHE_REGELGEVING])
        regel_codes = [v.regel_code for v in rapport.violations]
        assert "BEL-BTW-001" in regel_codes

    def test_retour_zonder_14_dagen_termijn_geeft_violation(self, engine):
        tekst = "U kunt het product retourneren via ons retourformulier."
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.BELGISCHE_REGELGEVING])
        regel_codes = [v.regel_code for v in rapport.violations]
        assert "BEL-CONS-001" in regel_codes

    def test_retour_met_14_dagen_termijn_geen_violation(self, engine):
        tekst = "U heeft het recht om het product binnen 14 dagen te retourneren."
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.BELGISCHE_REGELGEVING])
        cons_violations = [v for v in rapport.violations if v.regel_code == "BEL-CONS-001"]
        assert len(cons_violations) == 0


# ── NIS2 checks ───────────────────────────────────────────────────────────────

class TestNIS2Violations:
    def test_cyberaanval_keyword_geeft_nis2_violation(self, engine):
        tekst = "Er heeft een cyberaanval plaatsgevonden op onze servers."
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.NIS2])
        regel_codes = [v.regel_code for v in rapport.violations]
        assert "NIS2-INC-001" in regel_codes

    def test_datalek_keyword_geeft_nis2_meldplicht_warning(self, engine):
        tekst = "Er is een datalek gedetecteerd waarbij klantgegevens zijn gelekt."
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.NIS2])
        nis2_violations = [v for v in rapport.violations if v.laag == ComplianceLaag.NIS2]
        assert len(nis2_violations) >= 1

    def test_incident_zonder_melding_is_critical(self, engine):
        tekst = "Er heeft een ernstig incident plaatsgevonden."
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.NIS2])
        inc_violations = [v for v in rapport.violations if v.regel_code == "NIS2-INC-001"]
        assert len(inc_violations) == 1
        assert inc_violations[0].severity == ViolationSeverity.CRITICAL

    def test_incident_met_melding_is_medium(self, engine):
        tekst = "Er was een incident. Melding gedaan bij CCN2.be conform procedure."
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.NIS2])
        inc_violations = [v for v in rapport.violations if v.regel_code == "NIS2-INC-001"]
        assert len(inc_violations) == 1
        assert inc_violations[0].severity == ViolationSeverity.MEDIUM

    def test_tekst_zonder_incident_geeft_geen_nis2_violation(self, engine):
        tekst = "Het systeem draait stabiel. Geen meldingen."
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.NIS2])
        nis2_violations = [v for v in rapport.violations if v.laag == ComplianceLaag.NIS2]
        assert len(nis2_violations) == 0


# ── ComplianceReport structuur ────────────────────────────────────────────────

class TestComplianceReportStructuur:
    def test_to_dict_bevat_alle_verwachte_velden(self, engine):
        rapport = engine.valideer("Gewone tekst zonder violations.")
        d = rapport.to_dict()
        verwachte_velden = {
            "rapport_id", "project_id", "agent_name",
            "gecontroleerde_tekst_hash", "violations",
            "is_compliant", "samenvatting", "gecontroleerd_op",
        }
        assert verwachte_velden.issubset(d.keys())

    def test_to_dict_violations_is_lijst(self, engine):
        rapport = engine.valideer("Rijksregisternummer: 85.04.12-345.67", lagen=[ComplianceLaag.GDPR])
        d = rapport.to_dict()
        assert isinstance(d["violations"], list)

    def test_violation_to_dict_structuur(self, engine):
        tekst = "Rijksregisternummer: 85.04.12-345.67"
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.GDPR])
        rr_violations = [v for v in rapport.violations if v.regel_code == "GDPR-ART9-RR"]
        assert len(rr_violations) >= 1
        vd = rr_violations[0].to_dict()
        verwachte_velden = {
            "violation_id", "laag", "severity", "regel_code",
            "beschrijving", "aanbeveling", "bewijs",
        }
        assert verwachte_velden.issubset(vd.keys())

    def test_gecontroleerde_tekst_hash_is_sha256(self, engine):
        rapport = engine.valideer("Testinput")
        # SHA-256 hex digest is 64 characters
        assert len(rapport.gecontroleerde_tekst_hash) == 64

    def test_rapport_samenvatting_niet_leeg(self, engine):
        rapport = engine.valideer("Een tekst voor compliance check.")
        assert rapport.samenvatting
        assert len(rapport.samenvatting) > 5

    def test_naar_markdown_retourneert_string_met_headers(self, engine):
        tekst = "Rijksregisternummer: 85.04.12-345.67"
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.GDPR])
        md = rapport.naar_markdown()
        assert isinstance(md, str)
        assert "# Compliance Rapport" in md
        assert "## Samenvatting" in md

    def test_naar_markdown_compliant_rapport_bevat_vinkje(self, engine):
        rapport = engine.valideer("Neutrale tekst zonder issues.", lagen=[ComplianceLaag.NIS2])
        md = rapport.naar_markdown()
        assert "COMPLIANT" in md

    def test_from_dict_rondreis(self, engine):
        rapport = engine.valideer("Rijksregisternummer: 85.04.12-345.67", lagen=[ComplianceLaag.GDPR])
        d = rapport.to_dict()
        hersteld = ComplianceReport.from_dict(d)
        assert hersteld.rapport_id == rapport.rapport_id
        assert hersteld.is_compliant == rapport.is_compliant
        assert len(hersteld.violations) == len(rapport.violations)


# ── Meerdere violations tegelijk ─────────────────────────────────────────────

class TestMeerdereViolations:
    def test_rijksregister_en_incident_tegelijk(self, engine):
        tekst = (
            "Klant 85.04.12-345.67 heeft een datalek gemeld. "
            "De factuur bedraagt €500."
        )
        rapport = engine.valideer(tekst)
        assert len(rapport.violations) >= 2
        lagen_geraakt = {v.laag for v in rapport.violations}
        assert ComplianceLaag.GDPR in lagen_geraakt
        assert ComplianceLaag.NIS2 in lagen_geraakt

    def test_heeft_critical_property(self, engine):
        tekst = "Rijksregisternummer: 85.04.12-345.67"
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.GDPR])
        assert rapport.heeft_critical is True

    def test_heeft_high_property(self, engine):
        tekst = "Rijksregisternummer aanwezig: 85.04.12-345.67 en er is een datalek."
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.GDPR])
        # GDPR-ART9-RR is CRITICAL, dus heeft_critical True
        assert rapport.heeft_critical is True

    def test_compliant_rapport_heeft_geen_critical_of_high(self, engine):
        rapport = engine.valideer("Neutrale orderbevestiging.", lagen=[ComplianceLaag.NIS2])
        assert rapport.heeft_critical is False
        assert rapport.heeft_high is False

    def test_check_gdpr_retourneert_lijst(self, engine):
        violations = engine.check_gdpr("Gewone zin.")
        assert isinstance(violations, list)

    def test_check_nis2_retourneert_lijst(self, engine):
        violations = engine.check_nis2("Gewone zin.")
        assert isinstance(violations, list)

    def test_check_belgische_regelgeving_retourneert_lijst(self, engine):
        violations = engine.check_belgische_regelgeving("Gewone zin.")
        assert isinstance(violations, list)

    def test_compliance_violation_from_dict(self, engine):
        tekst = "Rijksregisternummer: 85.04.12-345.67"
        rapport = engine.valideer(tekst, lagen=[ComplianceLaag.GDPR])
        rr = [v for v in rapport.violations if v.regel_code == "GDPR-ART9-RR"][0]
        d = rr.to_dict()
        hersteld = ComplianceViolation.from_dict(d)
        assert hersteld.regel_code == rr.regel_code
        assert hersteld.severity == rr.severity
        assert hersteld.laag == rr.laag
