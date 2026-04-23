"""
VorstersNV ComplianceEngine — Multi-laags compliance validatie voor AI-output
=============================================================================

Voert 4-laags compliance checks uit op tekst/output van AI-agents:
  1. EU AI Act (Verordening (EU) 2024/1689)
  2. GDPR/AVG (Verordening (EU) 2016/679)
  3. NIS2 (Richtlijn (EU) 2022/2555)
  4. Belgische regelgeving (BTW, consumentenwet, taalwetgeving)

Gebruik::

    engine = get_compliance_engine()
    rapport = engine.valideer(
        tekst="De betaling is goedgekeurd.",
        project_id="proj-123",
        agent_name="order_verwerking_agent",
    )
    if not rapport.is_compliant:
        print(rapport.naar_markdown())
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ─── Optionele integraties ────────────────────────────────────────────────────

try:
    from ollama.pii_scanner import (
        _HOOG_RISICO_TYPES as _PII_HOOG_RISICO,
    )
    from ollama.pii_scanner import (
        _PATRONEN as _PII_PATRONEN,
    )
    from ollama.pii_scanner import (
        get_pii_scanner as _get_pii_scanner,
    )
    _PII_SCANNER_AVAILABLE = True
except ImportError:
    _PII_SCANNER_AVAILABLE = False
    _get_pii_scanner = None  # type: ignore[assignment]
    _PII_PATRONEN = []       # type: ignore[assignment]
    _PII_HOOG_RISICO = frozenset()  # type: ignore[assignment]

try:
    from ollama.ai_act_compliance import get_compliance_engine as _get_ai_act_engine
    _AI_ACT_AVAILABLE = True
except ImportError:
    _AI_ACT_AVAILABLE = False
    _get_ai_act_engine = None  # type: ignore[assignment]

# ─── Constanten ───────────────────────────────────────────────────────────────

_LOGS_DIR = Path(__file__).parent.parent / "logs" / "compliance"

# EU AI Act — HIGH-RISK beslissingspatronen (zonder disclaimer → violation)
_HIGH_RISK_KEYWORDS: frozenset[str] = frozenset({
    "geblokkeerd", "geweigerd", "goedgekeurd", "risico", "afgewezen",
    "toegestaan", "fraudescore", "krediet", "kredietscore",
})

_HIGH_RISK_DISCLAIMER_PATTERNS: frozenset[str] = frozenset({
    "ai-beslissing", "geautomatiseerd besluit", "ai systeem",
    "automatische beslissing", "menselijk toezicht", "hitl",
    "human-in-the-loop", "ai-gegenereerd",
})

# GDPR regex patronen
_RE_RIJKSREGISTER = re.compile(
    r"\b\d{2}[.\-]\d{2}[.\-]\d{2}[.\-]\d{3}[.\-]\d{2}\b"
)
_RE_EMAIL_OUTPUT = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)
_RE_BEWAARTERMIJN = re.compile(
    r"\b(bewa[a-z]+|opslaan|archiveer[a-z]*)\b.{0,80}\b(\d+)\s*(jaar|jaren|year|years)\b",
    re.IGNORECASE | re.DOTALL,
)
_RE_NAAM_AANSPREKING = re.compile(
    r"\b(dhr\.|mevr\.|mr\.|mrs\.|de heer|mevrouw)\s+[A-Z][a-z]+\b"
)
_RE_STRAAT_ADRES = re.compile(
    r"\b\d{1,4}\s+[A-Za-z][a-z]+(?:straat|laan|weg|plein|avenue|boulevard|dreef|steenweg)\b",
    re.IGNORECASE,
)

# NIS2 keyword sets
_NIS2_INCIDENT_KEYWORDS: frozenset[str] = frozenset({
    "incident", "datalek", "breach", "data breach", "aanval",
    "gehackt", "gecompromitteerd", "inbreuk", "hack", "cyberaanval",
})
_NIS2_SUPPLY_CHAIN_KEYWORDS: frozenset[str] = frozenset({
    "derde partij", "leverancier", "api key", "credentials",
    "externe partij", "vendor", "third party", "supply chain",
})
_NIS2_VULN_KEYWORDS: frozenset[str] = frozenset({
    "vulnerability", "cve", "security fix", "patch",
    "kwetsbaarheid", "beveiligingslek", "exploit",
})
_NIS2_SECURITY_ACTIES: frozenset[str] = frozenset({
    "toegang verleend", "toegang geweigerd", "ingelogd", "uitgelogd",
    "wachtwoord gewijzigd", "rol toegewezen", "permissie gewijzigd",
    "authenticatie",
})

# Belgische regelgeving keyword sets
_BEL_FINANCIEEL_KEYWORDS: frozenset[str] = frozenset({
    "factuur", "rekening", "prijs", "bedrag", "totaal",
    "betaling", "invoice", "tarief", "offerte", "kostenraming",
})
_BEL_HERROEPING_TRIGGERS: frozenset[str] = frozenset({
    "annulering", "annuleer", "retour", "herroep",
    "terugsturen", "terugzenden", "herroeping",
})
_BEL_BETALING_TRIGGERS: frozenset[str] = frozenset({
    "checkout", "betaling", "bestelling plaatsen", "afrekenen",
    "winkelwagen", "betaal nu", "koop nu", "aankoop afronden",
})


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class ComplianceLaag(str, Enum):
    """De vier compliance lagen die de engine controleert."""
    EU_AI_ACT            = "eu_ai_act"
    GDPR                 = "gdpr"
    NIS2                 = "nis2"
    BELGISCHE_REGELGEVING = "belgische_regelgeving"


class ViolationSeverity(str, Enum):
    """Ernst van een compliance overtreding."""
    CRITICAL = "critical"   # Blokkeer output — onmiddellijke actie vereist
    HIGH     = "high"       # HITL vereist vóór verdere verwerking
    MEDIUM   = "medium"     # Waarschuwing + log — opvolging nodig
    LOW      = "low"        # Informatief — lage urgentie


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ComplianceViolation:
    """
    Eén compliance overtreding gedetecteerd door de ComplianceEngine.

    Attributes:
        violation_id:  UUID4 uniek identifier.
        laag:          Compliance laag (EU AI Act, GDPR, NIS2, Belgisch).
        severity:      Ernst van de overtreding.
        regel_code:    Regelcode (bijv. "GDPR-ART6", "NIS2-INC-001").
        beschrijving:  Mensleesbare beschrijving van de overtreding.
        aanbeveling:   Corrigerende actie aanbeveling.
        bewijs:        Tekstfragment dat de violation triggerde (optioneel, geanonimiseerd).
    """

    violation_id: str
    laag:         ComplianceLaag
    severity:     ViolationSeverity
    regel_code:   str
    beschrijving: str
    aanbeveling:  str
    bewijs:       str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialiseer naar JSON-compatibel dict."""
        return {
            "violation_id": self.violation_id,
            "laag":         self.laag.value,
            "severity":     self.severity.value,
            "regel_code":   self.regel_code,
            "beschrijving": self.beschrijving,
            "aanbeveling":  self.aanbeveling,
            "bewijs":       self.bewijs,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ComplianceViolation:
        """Deserialiseer vanuit dict."""
        return cls(
            violation_id=data["violation_id"],
            laag=ComplianceLaag(data["laag"]),
            severity=ViolationSeverity(data["severity"]),
            regel_code=data["regel_code"],
            beschrijving=data["beschrijving"],
            aanbeveling=data["aanbeveling"],
            bewijs=data.get("bewijs"),
        )


@dataclass
class ComplianceReport:
    """
    Volledig compliance rapport voor één validatierun.

    Attributes:
        rapport_id:                UUID4 identifier van dit rapport.
        project_id:                Optioneel project identifier.
        agent_name:                Optionele agent naam die de output genereerde.
        gecontroleerde_tekst_hash: SHA-256 hash van de gecontroleerde input.
        violations:                Lijst van gedetecteerde overtredingen.
        is_compliant:              True als er geen CRITICAL of HIGH violations zijn.
        samenvatting:              Beknopte mensleesbare samenvatting.
        gecontroleerd_op:          ISO 8601 timestamp van de controle.
    """

    rapport_id:                str
    project_id:                str | None
    agent_name:                str | None
    gecontroleerde_tekst_hash: str
    violations:                list[ComplianceViolation]
    is_compliant:              bool
    samenvatting:              str
    gecontroleerd_op:          str

    @property
    def heeft_critical(self) -> bool:
        """True als minstens één CRITICAL violation aanwezig is."""
        return any(v.severity == ViolationSeverity.CRITICAL for v in self.violations)

    @property
    def heeft_high(self) -> bool:
        """True als minstens één HIGH violation aanwezig is."""
        return any(v.severity == ViolationSeverity.HIGH for v in self.violations)

    def naar_markdown(self) -> str:
        """Genereer een Markdown-geformatteerd compliance rapport."""
        severity_icon = {
            "critical": "🔴",
            "high":     "🟠",
            "medium":   "🟡",
            "low":      "🔵",
        }

        lines: list[str] = [
            f"# Compliance Rapport `{self.rapport_id}`",
            "",
            f"**Status:** {'✅ COMPLIANT' if self.is_compliant else '❌ NIET COMPLIANT'}",
            f"**Agent:** {self.agent_name or '—'}",
            f"**Project:** {self.project_id or '—'}",
            f"**Gecontroleerd op:** {self.gecontroleerd_op}",
            f"**Tekst hash:** `{self.gecontroleerde_tekst_hash[:16]}...`",
            "",
            "## Samenvatting",
            "",
            self.samenvatting,
            "",
        ]

        if not self.violations:
            lines.append("_Geen violations gevonden._")
        else:
            lines.append(f"## Violations ({len(self.violations)})")
            lines.append("")
            for v in self.violations:
                icon = severity_icon.get(v.severity.value, "⚪")
                lines += [
                    f"### {icon} [{v.regel_code}] {v.beschrijving}",
                    "",
                    f"- **Laag:** `{v.laag.value}`",
                    f"- **Severity:** `{v.severity.value.upper()}`",
                    f"- **Aanbeveling:** {v.aanbeveling}",
                ]
                if v.bewijs:
                    lines.append(f"- **Bewijs:** `{v.bewijs[:100]}`")
                lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Serialiseer naar JSON-compatibel dict."""
        return {
            "rapport_id":                self.rapport_id,
            "project_id":                self.project_id,
            "agent_name":                self.agent_name,
            "gecontroleerde_tekst_hash": self.gecontroleerde_tekst_hash,
            "violations":                [v.to_dict() for v in self.violations],
            "is_compliant":              self.is_compliant,
            "samenvatting":              self.samenvatting,
            "gecontroleerd_op":          self.gecontroleerd_op,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ComplianceReport:
        """Deserialiseer vanuit dict."""
        return cls(
            rapport_id=data["rapport_id"],
            project_id=data.get("project_id"),
            agent_name=data.get("agent_name"),
            gecontroleerde_tekst_hash=data["gecontroleerde_tekst_hash"],
            violations=[ComplianceViolation.from_dict(v) for v in data.get("violations", [])],
            is_compliant=data["is_compliant"],
            samenvatting=data["samenvatting"],
            gecontroleerd_op=data["gecontroleerd_op"],
        )


# ─────────────────────────────────────────────────────────────────────────────
# Interne hulpfuncties
# ─────────────────────────────────────────────────────────────────────────────

def _nieuwe_violation(
    laag:         ComplianceLaag,
    severity:     ViolationSeverity,
    regel_code:   str,
    beschrijving: str,
    aanbeveling:  str,
    bewijs:       str | None = None,
) -> ComplianceViolation:
    """Maak een nieuwe ComplianceViolation aan met auto-gegenereerde UUID."""
    return ComplianceViolation(
        violation_id=str(uuid.uuid4()),
        laag=laag,
        severity=severity,
        regel_code=regel_code,
        beschrijving=beschrijving,
        aanbeveling=aanbeveling,
        bewijs=bewijs,
    )


def _bevat_keyword(tekst_lower: str, keywords: frozenset[str]) -> str | None:
    """
    Controleer of één van de keywords aanwezig is in de tekst (lowercase).

    Returns:
        Het gevonden keyword, of None als geen match.
    """
    for kw in keywords:
        if kw in tekst_lower:
            return kw
    return None


def _extract_bewijs(tekst: str, keyword: str, context_chars: int = 60) -> str:
    """
    Extraheer een tekstfragment rondom het gevonden keyword als bewijs.

    Returns:
        Geanonimiseerd fragment van max 120 tekens.
    """
    idx = tekst.lower().find(keyword.lower())
    if idx == -1:
        return keyword[:50]
    start = max(0, idx - context_chars // 2)
    end   = min(len(tekst), idx + len(keyword) + context_chars // 2)
    fragment = tekst[start:end].strip()
    if start > 0:
        fragment = "..." + fragment
    if end < len(tekst):
        fragment = fragment + "..."
    return fragment[:120]


# ─────────────────────────────────────────────────────────────────────────────
# ComplianceEngine
# ─────────────────────────────────────────────────────────────────────────────

class ComplianceEngine:
    """
    Multi-laags compliance validatie engine voor VorstersNV AI-output.

    Controleert tekst/AI-output op 4 compliance lagen in volgorde van prioriteit:
      1. EU AI Act (Verordening (EU) 2024/1689) — transparantie & HITL
      2. GDPR/AVG (Verordening (EU) 2016/679)  — PII & bewaartermijn
      3. NIS2 (Richtlijn (EU) 2022/2555)        — incidenten & supply chain
      4. Belgische regelgeving                  — BTW, consumentenwet, taalwet

    Violations met CRITICAL of HIGH severity maken het rapport non-compliant.
    Rapporten worden automatisch gelogd naar logs/compliance/{project_id}/.

    Gebruik::

        engine = get_compliance_engine()
        rapport = engine.valideer("output", project_id="proj-123")
        if not rapport.is_compliant:
            raise RuntimeError(rapport.samenvatting)
    """

    def __init__(self) -> None:
        self._logs_dir = _LOGS_DIR
        logger.debug("ComplianceEngine geïnitialiseerd (PII=%s, AI_ACT=%s)",
                     _PII_SCANNER_AVAILABLE, _AI_ACT_AVAILABLE)

    # ─── Laag 1: EU AI Act ────────────────────────────────────────────────────

    def check_eu_ai_act(
        self,
        tekst: str,
        capability_naam: str | None = None,
    ) -> list[ComplianceViolation]:
        """
        Controleert tekst op EU AI Act compliance (Verordening (EU) 2024/1689).

        Detecteert:
          - HIGH-RISK beslissingsoutput zonder transparantiedisclaimer (Art. 13)
          - HIGH-RISK agent output zonder HITL-bevestiging (Art. 14)
          - Verboden AI-praktijken: sociale scoring (Art. 5)

        Args:
            tekst:           Te controleren tekst.
            capability_naam: Optionele agent/capability naam voor risicoklasse-lookup
                             in ai_act_compliance.py.

        Returns:
            Lijst van ComplianceViolation, leeg als compliant.
        """
        violations: list[ComplianceViolation] = []
        tekst_lower = tekst.lower()

        # 1. Risicoklasse lookup via AI Act engine
        is_high_risk_agent = False
        if capability_naam and _AI_ACT_AVAILABLE and _get_ai_act_engine is not None:
            try:
                ai_engine = _get_ai_act_engine()
                profiel = getattr(ai_engine, "_agents", {}).get(capability_naam)
                if profiel and getattr(profiel.risicoklasse, "value", "") == "high_risk":
                    is_high_risk_agent = True
                    logger.debug("AI Act: '%s' geclassificeerd als HIGH-RISK", capability_naam)
            except Exception as exc:  # noqa: BLE001
                logger.warning("AI Act risicoklasse-lookup mislukt voor '%s': %s",
                               capability_naam, exc)

        # 2. HIGH-RISK beslissingspatroon zonder disclaimer (Art. 13 transparantie)
        gevonden_keyword   = _bevat_keyword(tekst_lower, _HIGH_RISK_KEYWORDS)
        heeft_disclaimer   = _bevat_keyword(tekst_lower, _HIGH_RISK_DISCLAIMER_PATTERNS)

        if gevonden_keyword and not heeft_disclaimer:
            severity = (
                ViolationSeverity.CRITICAL if is_high_risk_agent
                else ViolationSeverity.HIGH
            )
            violations.append(_nieuwe_violation(
                laag=ComplianceLaag.EU_AI_ACT,
                severity=severity,
                regel_code="EU-AI-ART13-DISC",
                beschrijving=(
                    f"Output bevat beslissingsterm '{gevonden_keyword}' zonder verplichte "
                    "AI-transparantiedisclaimer (EU AI Act Art. 13 & 50)"
                ),
                aanbeveling=(
                    "Voeg toe: 'Deze beslissing is gegenereerd door een geautomatiseerd "
                    "AI-systeem. Menselijk toezicht is van toepassing.' "
                    "Zie EU AI Act Art. 13 (transparantie) en Art. 50 (AI-identificatie)."
                ),
                bewijs=_extract_bewijs(tekst, gevonden_keyword),
            ))

        # 3. HIGH-RISK agent zonder HITL-vermelding (Art. 14)
        if is_high_risk_agent:
            hitl_keywords = frozenset({
                "hitl", "menselijk toezicht", "human-in-the-loop",
                "goedgekeurd door", "beoordeeld door operator",
            })
            if not _bevat_keyword(tekst_lower, hitl_keywords):
                violations.append(_nieuwe_violation(
                    laag=ComplianceLaag.EU_AI_ACT,
                    severity=ViolationSeverity.HIGH,
                    regel_code="EU-AI-ART14-HITL",
                    beschrijving=(
                        f"HIGH-RISK agent '{capability_naam}' output zonder HITL-bevestiging "
                        "(EU AI Act Art. 14 — menselijk toezicht)"
                    ),
                    aanbeveling=(
                        "Zorg dat HIGH-RISK beslissingen een HITL-goedkeuringsstap bevatten "
                        "vóór communicatie naar eindgebruikers. Activeer HITL-002 policy."
                    ),
                ))

        # 4. Verboden AI-praktijken: sociale scoring (Art. 5)
        sociale_scoring_patronen = [
            "sociale score", "burgerlijkescore", "gedragsscore",
            "vertrouwensscore burger", "sociale kredietscore",
            "sociaal krediet systeem",
        ]
        for patroon in sociale_scoring_patronen:
            if patroon in tekst_lower:
                violations.append(_nieuwe_violation(
                    laag=ComplianceLaag.EU_AI_ACT,
                    severity=ViolationSeverity.CRITICAL,
                    regel_code="EU-AI-ART5-VERBOD",
                    beschrijving=(
                        f"Verboden AI-praktijk gedetecteerd: '{patroon}' suggereert "
                        "een sociale-scoringsysteem (EU AI Act Art. 5(1)(c))"
                    ),
                    aanbeveling=(
                        "Sociale scoring van burgers is absoluut verboden onder Art. 5. "
                        "Verwijder onmiddellijk en escaleer naar de compliance officer."
                    ),
                    bewijs=_extract_bewijs(tekst, patroon),
                ))
                break  # Één CRITICAL per tekst volstaat

        logger.debug("EU AI Act: %d violation(s)", len(violations))
        return violations

    # ─── Laag 2: GDPR/AVG ────────────────────────────────────────────────────

    def check_gdpr(
        self,
        tekst: str,
        project_id: str | None = None,
    ) -> list[ComplianceViolation]:
        """
        Controleert tekst op GDPR/AVG compliance (Verordening (EU) 2016/679).

        Detecteert:
          - Rijksregisternummers (Art. 9 bijzondere categorieën)
          - Ongemaskeerde e-mailadressen (Art. 5 dataminimalisatie)
          - Naam + adres combinaties (Art. 6 rechtsgrond)
          - Overmatige bewaartermijnen > 10 jaar (Art. 5(1)(e))
          - Ontbrekende DPA voor projecten (Art. 28)
          - PII via geïntegreerde PIIScanner

        Args:
            tekst:      Te controleren tekst.
            project_id: Optioneel project ID voor DPA-aanwezigheidscheck.

        Returns:
            Lijst van ComplianceViolation.
        """
        violations: list[ComplianceViolation] = []

        # 1. PII scan via PIIScanner (indien beschikbaar) of eigen regex
        if _PII_SCANNER_AVAILABLE and _get_pii_scanner is not None:
            try:
                scanner      = _get_pii_scanner()
                pii_violations = self._check_pii_via_scanner(tekst, scanner)
                violations.extend(pii_violations)
            except Exception as exc:  # noqa: BLE001
                logger.warning("PIIScanner integratie mislukt, fallback regex: %s", exc)
                violations.extend(self._check_pii_regex(tekst))
        else:
            violations.extend(self._check_pii_regex(tekst))

        # 2. Rijksregisternummer (Belgisch nationaal nummer — Art. 9 bijzondere PII)
        rr_match = _RE_RIJKSREGISTER.search(tekst)
        if rr_match:
            violations.append(_nieuwe_violation(
                laag=ComplianceLaag.GDPR,
                severity=ViolationSeverity.CRITICAL,
                regel_code="GDPR-ART9-RR",
                beschrijving=(
                    "Rijksregisternummer gedetecteerd in output — bijzondere "
                    "categorie PII (GDPR Art. 9)"
                ),
                aanbeveling=(
                    "Rijksregisternummers vereisen een expliciete rechtsgrond (Art. 9(2)). "
                    "Maskeer onmiddellijk: XX.XX.XX-XXX.XX → **.**.**-***.**. "
                    "Controleer of verwerking conform privacywetgeving is gedocumenteerd."
                ),
                bewijs=rr_match.group()[:10] + "***",
            ))

        # 3. Ongemaskerde e-mailadressen (Art. 5 dataminimalisatie)
        email_matches = list(_RE_EMAIL_OUTPUT.finditer(tekst))
        for em in email_matches[:3]:  # Max 3 violations per scan
            val = em.group()
            if "***" not in val and not val.endswith(".example"):
                violations.append(_nieuwe_violation(
                    laag=ComplianceLaag.GDPR,
                    severity=ViolationSeverity.HIGH,
                    regel_code="GDPR-ART5-EMAIL",
                    beschrijving=(
                        "Ongemaskerd e-mailadres in AI-output "
                        "(GDPR Art. 5(1)(c) — dataminimalisatie)"
                    ),
                    aanbeveling=(
                        "Maskeer e-mailadressen: j***@***.com. "
                        "Controleer of de PII-scanner geconfigureerd is voor deze agent."
                    ),
                    bewijs=val[:5] + "***@***",
                ))

        # 4. Naam + adres combinatie (directe identificatie — Art. 6 rechtsgrond)
        heeft_naam  = _RE_NAAM_AANSPREKING.search(tekst)
        heeft_adres = _RE_STRAAT_ADRES.search(tekst)
        if heeft_naam and heeft_adres:
            violations.append(_nieuwe_violation(
                laag=ComplianceLaag.GDPR,
                severity=ViolationSeverity.HIGH,
                regel_code="GDPR-ART6-NAAM-ADRES",
                beschrijving=(
                    "Naam + adres combinatie gedetecteerd — directe identificatie "
                    "van betrokkene mogelijk (GDPR Art. 6 rechtsgrond)"
                ),
                aanbeveling=(
                    "Verwijder of anonimiseer de naam/adres combinatie vóór output. "
                    "GDPR Art. 6 vereist een geldige rechtsgrond voor verwerking van "
                    "identificerende persoonsgegevens."
                ),
                bewijs=f"{heeft_naam.group()[:25]}, adres aanwezig",
            ))

        # 5. Bewaartermijn > 10 jaar (Art. 5(1)(e) opslagbeperking)
        bewaar_match = _RE_BEWAARTERMIJN.search(tekst.lower())
        if bewaar_match:
            try:
                jaren = int(bewaar_match.group(2))
                if jaren > 10:
                    violations.append(_nieuwe_violation(
                        laag=ComplianceLaag.GDPR,
                        severity=ViolationSeverity.MEDIUM,
                        regel_code="GDPR-ART5-BEWAAR",
                        beschrijving=(
                            f"Bewaartermijn van {jaren} jaar gedetecteerd — "
                            "overschrijdt GDPR opslagbeperkingsbeginsel (Art. 5(1)(e))"
                        ),
                        aanbeveling=(
                            f"Beoordeel of {jaren} jaar bewaring noodzakelijk en "
                            "proportioneel is. Documenteer rechtsgrond (bijv. wettelijke "
                            "bewaarplicht). GDPR vereist minimale opslagduur."
                        ),
                        bewijs=bewaar_match.group()[:80],
                    ))
            except (ValueError, IndexError):
                pass

        # 6. DPA-aanwezigheidscheck voor projecten (Art. 28)
        if project_id:
            dpa_path = Path(__file__).parent.parent / "logs" / "dpa" / f"{project_id}-dpa.json"
            if not dpa_path.exists():
                violations.append(_nieuwe_violation(
                    laag=ComplianceLaag.GDPR,
                    severity=ViolationSeverity.LOW,
                    regel_code="GDPR-ART28-DPA",
                    beschrijving=(
                        f"Geen Data Processing Agreement gevonden voor project '{project_id}' "
                        "(GDPR Art. 28 — verwerkersovereenkomst)"
                    ),
                    aanbeveling=(
                        f"Maak een DPA aan: logs/dpa/{project_id}-dpa.json. "
                        "GDPR Art. 28 vereist een schriftelijke verwerkersovereenkomst "
                        "bij verwerking namens een verwerkingsverantwoordelijke."
                    ),
                ))

        logger.debug("GDPR: %d violation(s)", len(violations))
        return violations

    # ─── Laag 3: NIS2 ────────────────────────────────────────────────────────

    def check_nis2(
        self,
        tekst: str,
        event_type: str | None = None,
    ) -> list[ComplianceViolation]:
        """
        Controleert tekst op NIS2 compliance (Richtlijn (EU) 2022/2555).

        Detecteert:
          - Incidenten/datalekken zonder CCN2.be meldingsreferentie (Art. 23)
          - Supply chain risico's zonder risicobeoordeling (Art. 21(2)(d))
          - Security-acties zonder audit log referentie (Art. 21(2)(j))
          - Kwetsbaarheden zonder patch-tijdlijn (Art. 21(2)(e))

        Args:
            tekst:       Te controleren tekst.
            event_type:  Optioneel event type voor context-specifieke checks.

        Returns:
            Lijst van ComplianceViolation.
        """
        violations: list[ComplianceViolation] = []
        tekst_lower = tekst.lower()

        # 1. Incident/datalek — melding aan CCN2.be vereist (Art. 23)
        incident_kw = _bevat_keyword(tekst_lower, _NIS2_INCIDENT_KEYWORDS)
        if incident_kw:
            heeft_melding = any(
                kw in tekst_lower for kw in [
                    "ccn2", "ccb.belgium.be", "gemeld bij", "melding gedaan",
                    "incident report", "incident gemeld",
                ]
            )
            violations.append(_nieuwe_violation(
                laag=ComplianceLaag.NIS2,
                severity=ViolationSeverity.MEDIUM if heeft_melding else ViolationSeverity.CRITICAL,
                regel_code="NIS2-INC-001",
                beschrijving=(
                    f"Incident-keyword '{incident_kw}' gedetecteerd"
                    + (" — melding aan CCN2.be vereist binnen 24 uur" if not heeft_melding
                       else " — meldingsreferentie aanwezig")
                    + " (NIS2 Art. 23)"
                ),
                aanbeveling=(
                    "Meld significant incident INITIEEL binnen 24 uur bij CCN2.be: "
                    "https://ccb.belgium.be/nl/meld-een-incident. "
                    "Volledig rapport binnen 72 uur (NIS2 Art. 23(4))."
                    if not heeft_melding else
                    "Controleer dat de melding volledig is conform NIS2 Art. 23(4)."
                ),
                bewijs=_extract_bewijs(tekst, incident_kw),
            ))

        # 2. Supply chain risico zonder risicobeoordeling (Art. 21(2)(d))
        supply_kw = _bevat_keyword(tekst_lower, _NIS2_SUPPLY_CHAIN_KEYWORDS)
        if supply_kw:
            heeft_assessment = any(
                kw in tekst_lower for kw in [
                    "risicobeoordeling", "risk assessment",
                    "gecertificeerd", "iso 27001", "pci-dss", "soc2",
                ]
            )
            if not heeft_assessment:
                violations.append(_nieuwe_violation(
                    laag=ComplianceLaag.NIS2,
                    severity=ViolationSeverity.HIGH,
                    regel_code="NIS2-SC-002",
                    beschrijving=(
                        f"Supply chain verwijzing '{supply_kw}' zonder risicobeoordeling "
                        "(NIS2 Art. 21(2)(d) — supply chain beveiliging)"
                    ),
                    aanbeveling=(
                        "Documenteer risicobeoordeling voor externe componenten. "
                        "Controleer certificeringen (ISO 27001, SOC 2, PCI-DSS). "
                        "Zie policies/nis2-policies.yaml — NIS2-M04."
                    ),
                    bewijs=_extract_bewijs(tekst, supply_kw),
                ))

        # 3. Security-actie zonder audit log referentie (Art. 21(2)(j))
        security_actie = _bevat_keyword(tekst_lower, _NIS2_SECURITY_ACTIES)
        if security_actie:
            heeft_log_ref = any(
                kw in tekst_lower for kw in [
                    "audit log", "gelogd", "trace_id", "log entry",
                    "structured log", "journal",
                ]
            )
            if not heeft_log_ref:
                violations.append(_nieuwe_violation(
                    laag=ComplianceLaag.NIS2,
                    severity=ViolationSeverity.MEDIUM,
                    regel_code="NIS2-LOG-003",
                    beschrijving=(
                        f"Security-actie '{security_actie}' zonder audit log referentie "
                        "(NIS2 Art. 21(2)(j) — audit logging)"
                    ),
                    aanbeveling=(
                        "Log security-acties in structured JSON formaat met trace_id. "
                        "Gebruik decision_journal.py voor audittrails. "
                        "NIS2-M02 vereist gestructureerde incidentregistratie."
                    ),
                    bewijs=_extract_bewijs(tekst, security_actie),
                ))

        # 4. Kwetsbaarheid zonder patch-tijdlijn (Art. 21(2)(e))
        vuln_kw = _bevat_keyword(tekst_lower, _NIS2_VULN_KEYWORDS)
        if vuln_kw:
            heeft_patch_info = any(
                kw in tekst_lower for kw in [
                    "gepatchd", "opgelost", "fixed", "geüpdated",
                    "versie", "update beschikbaar", "patch beschikbaar",
                ]
            )
            violations.append(_nieuwe_violation(
                laag=ComplianceLaag.NIS2,
                severity=ViolationSeverity.HIGH if not heeft_patch_info else ViolationSeverity.MEDIUM,
                regel_code="NIS2-VULN-004",
                beschrijving=(
                    f"Kwetsbaarheid keyword '{vuln_kw}' gedetecteerd"
                    + (" — geen patch-tijdlijn aanwezig" if not heeft_patch_info
                       else " — patch-informatie aanwezig")
                    + " (NIS2 Art. 21(2)(e) — kwetsbaarheidsbeheer)"
                ),
                aanbeveling=(
                    "Documenteer: identificatiedatum, CVE-nummer, verwachte patchdatum, "
                    "verantwoordelijke en mitigatiemaatregelen. "
                    "NIS2 vereist proactief kwetsbaarheidsbeheer met aantoonbare tijdlijnen."
                ),
                bewijs=_extract_bewijs(tekst, vuln_kw),
            ))

        logger.debug("NIS2: %d violation(s)", len(violations))
        return violations

    # ─── Laag 4: Belgische regelgeving ───────────────────────────────────────

    def check_belgische_regelgeving(
        self,
        tekst: str,
        context: dict[str, Any] | None = None,
    ) -> list[ComplianceViolation]:
        """
        Controleert tekst op Belgische regelgeving compliance.

        Detecteert:
          - BTW-vermelding in financiële context (BTW-wetboek Art. 53)
          - Herroepingstermijn 14 dagen bij retour/annulering (WER Boek VI)
          - Taalwetgeving (NL+FR Brussel, NL Vlaanderen)
          - Verplichte ondernemingsvermeldingen bij e-commerce (WER Art. VI.45)

        Args:
            tekst:    Te controleren tekst.
            context:  Optioneel dict met sleutels:
                        - 'regio' (str): "brussel" | "vlaanderen" | "wallonie"
                        - 'type' (str): "factuur" | "checkout" | etc.

        Returns:
            Lijst van ComplianceViolation.
        """
        violations: list[ComplianceViolation] = []
        tekst_lower = tekst.lower()
        ctx         = context or {}

        # 1. BTW-vermelding in financiële output (BTW-wetboek Art. 53)
        financieel_kw = _bevat_keyword(tekst_lower, _BEL_FINANCIEEL_KEYWORDS)
        if financieel_kw:
            heeft_btw = any(
                kw in tekst_lower for kw in [
                    "btw", "tva", "belasting over toegevoegde waarde",
                    "excl. btw", "incl. btw", "21%", "12%", "6%", "0%",
                ]
            )
            if not heeft_btw:
                violations.append(_nieuwe_violation(
                    laag=ComplianceLaag.BELGISCHE_REGELGEVING,
                    severity=ViolationSeverity.MEDIUM,
                    regel_code="BEL-BTW-001",
                    beschrijving=(
                        f"Financieel document ('{financieel_kw}') zonder BTW-vermelding "
                        "(Belgisch BTW-wetboek Art. 53)"
                    ),
                    aanbeveling=(
                        "Vermeld: bedrag excl. BTW, BTW-tarief (21%/12%/6%/0%), "
                        "BTW-bedrag en totaal incl. BTW + BTW-nummer (BE0XXX.XXX.XXX). "
                        "Vereist voor alle B2B en B2C facturatie in België."
                    ),
                    bewijs=_extract_bewijs(tekst, financieel_kw),
                ))

        # 2. Herroepingstermijn 14 dagen bij retour/annulering (WER Boek VI Art. VI.47)
        herroeping_kw = _bevat_keyword(tekst_lower, _BEL_HERROEPING_TRIGGERS)
        if herroeping_kw:
            heeft_14_dagen = any(
                kw in tekst_lower for kw in [
                    "14 dagen", "14 calendar days", "veertien dagen",
                    "herroepingstermijn", "14 werkdagen",
                ]
            )
            if not heeft_14_dagen:
                violations.append(_nieuwe_violation(
                    laag=ComplianceLaag.BELGISCHE_REGELGEVING,
                    severity=ViolationSeverity.HIGH,
                    regel_code="BEL-CONS-001",
                    beschrijving=(
                        f"'{herroeping_kw}' vermeld zonder verplichte 14-dagentermijn "
                        "(Belgische Consumentenwet WER Boek VI Art. VI.47)"
                    ),
                    aanbeveling=(
                        "Voeg toe: 'U heeft het recht om binnen 14 kalenderdagen van dit "
                        "contract af te zien zonder opgave van reden.' "
                        "Vereist door WER Boek VI en EU Richtlijn 2011/83/EU."
                    ),
                    bewijs=_extract_bewijs(tekst, herroeping_kw),
                ))

        # 3. Taalwetgeving — Brussel: NL + FR verplicht
        regio = ctx.get("regio", "").lower()
        if regio in ("brussel", "brussels", "bruxelles"):
            nl_indicatoren = re.compile(r"\b(de|het|een|zijn|hebben|wordt|naar)\b")
            fr_indicatoren = re.compile(r"\b(le|la|les|est|sont|avoir|pour)\b")
            heeft_nl = bool(nl_indicatoren.search(tekst_lower))
            heeft_fr = bool(fr_indicatoren.search(tekst_lower))
            if not (heeft_nl and heeft_fr):
                violations.append(_nieuwe_violation(
                    laag=ComplianceLaag.BELGISCHE_REGELGEVING,
                    severity=ViolationSeverity.MEDIUM,
                    regel_code="BEL-TAAL-002",
                    beschrijving=(
                        "Brusselse regio context: output lijkt niet tweetalig (NL+FR) "
                        "(Brusselse taalwetgeving — Ordonnantie 2004)"
                    ),
                    aanbeveling=(
                        "Zorg voor NL én FR versie van alle communicatie in de Brusselse regio. "
                        "Vereist voor officiële en commerciële communicatie gericht op Brussel."
                    ),
                ))

        # 4. E-commerce — verplichte ondernemingsvermeldingen (WER Art. VI.45)
        betaling_kw = _bevat_keyword(tekst_lower, _BEL_BETALING_TRIGGERS)
        if betaling_kw:
            wettelijke_vermeldingen = [
                "ondernemingsnummer", "btw-nummer", "maatschappelijke zetel",
                "kvk", "enterprise number", "be0", "kbo",
            ]
            heeft_vermelding = any(kw in tekst_lower for kw in wettelijke_vermeldingen)
            if not heeft_vermelding:
                violations.append(_nieuwe_violation(
                    laag=ComplianceLaag.BELGISCHE_REGELGEVING,
                    severity=ViolationSeverity.MEDIUM,
                    regel_code="BEL-ECOM-003",
                    beschrijving=(
                        f"E-commerce context ('{betaling_kw}') zonder verplichte "
                        "ondernemingsvermeldingen (WER Boek VI Art. VI.45)"
                    ),
                    aanbeveling=(
                        "Voeg toe: ondernemingsnummer (BE0xxx.xxx.xxx), BTW-nummer, "
                        "maatschappelijke zetel en KBO-registratie. "
                        "Vereist voor alle Belgische e-commerce platforms."
                    ),
                    bewijs=_extract_bewijs(tekst, betaling_kw),
                ))

        logger.debug("Belgische regelgeving: %d violation(s)", len(violations))
        return violations

    # ─── Hoofd validatie methode ─────────────────────────────────────────────

    def valideer(
        self,
        tekst: str,
        project_id: str | None = None,
        agent_name: str | None = None,
        capability_naam: str | None = None,
        lagen: list[ComplianceLaag] | None = None,
    ) -> ComplianceReport:
        """
        Voer alle geselecteerde compliance lagen uit en retourneer een geaggregeerd rapport.

        Args:
            tekst:           Te valideren tekst (AI-output of document).
            project_id:      Optioneel project identifier (voor DPA-check en log-path).
            agent_name:      Optionele agent naam (voor logging en rapport).
            capability_naam: Optionele capability naam (voor EU AI Act risicoklasse-lookup).
            lagen:           Specifieke lagen om te controleren. None = alle 4 lagen.

        Returns:
            ComplianceReport met alle violations, compliance status en samenvatting.
            Rapport wordt automatisch gelogd naar logs/compliance/{project_id}/.
        """
        if not tekst or not tekst.strip():
            logger.debug("Lege input ontvangen — geen compliance checks")
            return self._leeg_rapport(project_id, agent_name, tekst)

        actieve_lagen  = lagen if lagen is not None else list(ComplianceLaag)
        alle_violations: list[ComplianceViolation] = []
        tekst_hash      = hashlib.sha256(tekst.encode("utf-8")).hexdigest()
        rapport_id      = str(uuid.uuid4())

        logger.info(
            "Compliance validatie gestart: id=%s agent=%s project=%s lagen=%s",
            rapport_id[:8], agent_name, project_id,
            [laag.value for laag in actieve_lagen],
        )

        # Voer actieve lagen uit — fouten per laag worden afgevangen
        _checks: list[tuple[ComplianceLaag, Any]] = [
            (ComplianceLaag.EU_AI_ACT,
             lambda: self.check_eu_ai_act(tekst, capability_naam=capability_naam or agent_name)),
            (ComplianceLaag.GDPR,
             lambda: self.check_gdpr(tekst, project_id=project_id)),
            (ComplianceLaag.NIS2,
             lambda: self.check_nis2(tekst)),
            (ComplianceLaag.BELGISCHE_REGELGEVING,
             lambda: self.check_belgische_regelgeving(tekst)),
        ]

        for laag, check_fn in _checks:
            if laag in actieve_lagen:
                try:
                    alle_violations.extend(check_fn())
                except Exception as exc:  # noqa: BLE001
                    logger.error("Compliance check mislukt voor laag '%s': %s", laag.value, exc)

        # Compliance status: CRITICAL of HIGH → non-compliant
        is_compliant = not any(
            v.severity in (ViolationSeverity.CRITICAL, ViolationSeverity.HIGH)
            for v in alle_violations
        )

        samenvatting = self._genereer_samenvatting(alle_violations, is_compliant, actieve_lagen)
        timestamp    = datetime.now(timezone.utc).isoformat()

        rapport = ComplianceReport(
            rapport_id=rapport_id,
            project_id=project_id,
            agent_name=agent_name,
            gecontroleerde_tekst_hash=tekst_hash,
            violations=alle_violations,
            is_compliant=is_compliant,
            samenvatting=samenvatting,
            gecontroleerd_op=timestamp,
        )

        self._log_rapport(rapport, project_id)

        logger.info(
            "Compliance validatie klaar: id=%s compliant=%s violations=%d",
            rapport_id[:8], is_compliant, len(alle_violations),
        )
        return rapport

    # ─── Interne helpers ─────────────────────────────────────────────────────

    def _check_pii_via_scanner(
        self,
        tekst: str,
        scanner: Any,
    ) -> list[ComplianceViolation]:
        """Gebruik PII Scanner regex-patronen voor directe tekst-scanning."""
        violations: list[ComplianceViolation] = []
        for pii_type, patroon in _PII_PATRONEN:
            if pii_type == "EMAIL":
                continue  # Wordt apart behandeld in check_gdpr
            match = patroon.search(tekst)
            if match:
                ruw      = match.group(1) if pii_type == "API_KEY" and match.lastindex else match.group()
                gemaskeerd = scanner.anonymiseer(ruw, pii_type)
                severity = (
                    ViolationSeverity.CRITICAL if pii_type == "API_KEY"
                    else ViolationSeverity.HIGH if pii_type in _PII_HOOG_RISICO
                    else ViolationSeverity.MEDIUM
                )
                violations.append(_nieuwe_violation(
                    laag=ComplianceLaag.GDPR,
                    severity=severity,
                    regel_code=f"GDPR-PII-{pii_type}",
                    beschrijving=(
                        f"PII type '{pii_type}' gedetecteerd via PII Scanner "
                        "(GDPR Art. 5 — dataminimalisatie)"
                    ),
                    aanbeveling=(
                        f"Maskeer of verwijder {pii_type} data vóór output. "
                        "Gebruik PIIScanner.anonymiseer() voor anonimisering."
                    ),
                    bewijs=gemaskeerd,
                ))
        return violations

    def _check_pii_regex(self, tekst: str) -> list[ComplianceViolation]:
        """Fallback PII check via eigen regex (zonder PIIScanner afhankelijkheid)."""
        violations: list[ComplianceViolation] = []

        # IBAN detectie (BE + NL)
        iban_re = re.compile(
            r"\b(?:BE\d{2}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}"
            r"|NL\d{2}[\s]?[A-Z]{4}[\s]?\d{10})\b",
            re.IGNORECASE,
        )
        if iban_re.search(tekst):
            violations.append(_nieuwe_violation(
                laag=ComplianceLaag.GDPR,
                severity=ViolationSeverity.HIGH,
                regel_code="GDPR-PII-IBAN",
                beschrijving="IBAN bankrekeningnummer gedetecteerd in output (GDPR Art. 5)",
                aanbeveling=(
                    "Maskeer IBAN: BE** **** **** ****. "
                    "Bankgegevens zijn gevoelige PII onder GDPR."
                ),
            ))

        # API key/credentials detectie
        api_re = re.compile(
            r"(?:api[_\-]?key|token|secret|password|passwd)\s*[=:]+\s*"
            r"[\"']?([A-Za-z0-9\-_+/=]{20,})[\"']?",
            re.IGNORECASE,
        )
        if api_re.search(tekst):
            violations.append(_nieuwe_violation(
                laag=ComplianceLaag.GDPR,
                severity=ViolationSeverity.CRITICAL,
                regel_code="GDPR-PII-APIKEY",
                beschrijving=(
                    "API key/credentials gedetecteerd in output "
                    "(GDPR Art. 32 — beveiliging van verwerking)"
                ),
                aanbeveling=(
                    "Verwijder credentials onmiddellijk. Gebruik .env en Pydantic Settings. "
                    "Roteer blootgestelde keys en log als security incident."
                ),
            ))

        return violations

    def _genereer_samenvatting(
        self,
        violations: list[ComplianceViolation],
        is_compliant: bool,
        lagen: list[ComplianceLaag],
    ) -> str:
        """Genereer een beknopte samenvatting voor het ComplianceReport."""
        lagen_str = ", ".join(laag.value for laag in lagen)

        if not violations:
            return (
                f"✅ Volledig compliant. {len(lagen)} laag/lagen gecontroleerd "
                f"({lagen_str}) — geen violations gevonden."
            )

        criticals = sum(1 for v in violations if v.severity == ViolationSeverity.CRITICAL)
        highs     = sum(1 for v in violations if v.severity == ViolationSeverity.HIGH)
        mediums   = sum(1 for v in violations if v.severity == ViolationSeverity.MEDIUM)
        lows      = sum(1 for v in violations if v.severity == ViolationSeverity.LOW)

        status = "❌ NIET COMPLIANT" if not is_compliant else "⚠️ COMPLIANT MET WAARSCHUWINGEN"
        delen: list[str] = [f"{status} — {len(violations)} violation(s)"]

        if criticals:
            delen.append(f"🔴 {criticals} CRITICAL")
        if highs:
            delen.append(f"🟠 {highs} HIGH")
        if mediums:
            delen.append(f"🟡 {mediums} MEDIUM")
        if lows:
            delen.append(f"🔵 {lows} LOW")

        delen.append(f"Gecontroleerde lagen: {lagen_str}")
        return " | ".join(delen)

    def _leeg_rapport(
        self,
        project_id: str | None,
        agent_name: str | None,
        tekst: str,
    ) -> ComplianceReport:
        """Retourneer een compliant rapport voor lege/None input."""
        return ComplianceReport(
            rapport_id=str(uuid.uuid4()),
            project_id=project_id,
            agent_name=agent_name,
            gecontroleerde_tekst_hash=hashlib.sha256(tekst.encode()).hexdigest(),
            violations=[],
            is_compliant=True,
            samenvatting="✅ Lege input — geen compliance checks uitgevoerd.",
            gecontroleerd_op=datetime.now(timezone.utc).isoformat(),
        )

    def _log_rapport(self, rapport: ComplianceReport, project_id: str | None) -> None:
        """Persisteer het compliance rapport als JSON naar logs/compliance/."""
        try:
            log_dir = (
                self._logs_dir / project_id
                if project_id
                else self._logs_dir / "_algemeen"
            )
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / f"{rapport.rapport_id}.json"
            with log_path.open("w", encoding="utf-8") as f:
                json.dump(rapport.to_dict(), f, ensure_ascii=False, indent=2)
            logger.debug("Compliance rapport opgeslagen: %s", log_path)
        except OSError as exc:
            logger.warning("Kon compliance rapport niet persisteren: %s", exc)


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_engine_instance: ComplianceEngine | None = None


def get_compliance_engine() -> ComplianceEngine:
    """
    Singleton accessor voor de ComplianceEngine.

    Thread-safe voor read-mostly gebruik (pattern matching is stateless).
    Hergebruikt dezelfde instantie gedurende de levensduur van de applicatie.

    Returns:
        Gedeelde ComplianceEngine instantie.
    """
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ComplianceEngine()
        logger.debug("ComplianceEngine singleton aangemaakt")
    return _engine_instance
