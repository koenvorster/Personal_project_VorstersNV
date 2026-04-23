"""
VorstersNV PII Scanner — Detecteert gevoelige persoonsgegevens in broncode en documenten.

Scant bestanden op PII (Persoonlijk Identificeerbare Informatie) vóór ze naar een
AI-model worden gestuurd. Dit garandeert GDPR/AVG-compliance: klantdata verlaat
nooit de VorstersNV infrastructuur in ongemaskeerde vorm.

Gedetecteerde PII-types:
  - EMAIL:        e-mailadressen in code, configuratie of commentaar
  - PHONE:        Belgische telefoonnummers (+32 en nationaal formaat)
  - IBAN:         Belgische (BE) en Nederlandse (NL) IBAN-nummers
  - API_KEY:      API-sleutels, tokens en secrets in string literals
  - IP_ADDRESS:   IPv4-adressen (potentieel persoonsgegeven onder GDPR)

Risiconiveaus:
  - HIGH:   email, IBAN of API_KEY aanwezig → directe blootstelling van PII
  - MEDIUM: telefoonnummer of IP-adres aanwezig → indirecte identificatie
  - LOW:    geen PII gevonden of alleen laag-risico patronen

Gebruik:
    scanner = get_pii_scanner()
    resultaat = scanner.scan_bestand(Path("src/config.py"))
    print(resultaat.risiconiveau)   # "HIGH"
    print(resultaat.matches[0].waarde)  # "j***@***.com"

    alle_resultaten = scanner.scan_project(project)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ollama.client_project_space import ClientProjectSpace

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────

@dataclass
class PIIMatch:
    """
    Eén gevonden PII-treffer in een bestand.

    Attributes:
        type:     PII-categorie ("EMAIL" | "PHONE" | "IBAN" | "API_KEY" | "IP_ADDRESS").
        waarde:   Geanonimiseerde versie van de gevonden waarde.
        lijn:     Regelnummer in het bronbestand (1-gebaseerd).
        bestand:  Relatief of absoluut pad als string.
    """
    type:    str
    waarde:  str
    lijn:    int
    bestand: str


@dataclass
class PIIScanResult:
    """
    Volledig scanresultaat voor één bestand.

    Attributes:
        bestand:      Pad naar het gescande bestand.
        matches:      Lijst van gevonden PIIMatch-objecten.
        risiconiveau: Berekend risiconiveau ("LOW" | "MEDIUM" | "HIGH").
        aanbeveling:  Tekstuele aanbeveling voor de analist.
    """
    bestand:      str
    matches:      list[PIIMatch] = field(default_factory=list)
    risiconiveau: str = "LOW"
    aanbeveling:  str = ""


# ─────────────────────────────────────────────
# Regex Patronen
# ─────────────────────────────────────────────

# E-mailadressen — RFC 5321 vereenvoudigd
_RE_EMAIL = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)

# Belgische telefoonnummers:
#   +32 4xx xx xx xx  (mobiel)
#   +32 x xxx xx xx   (vast)
#   04xx/xx.xx.xx     (lokaal mobiel)
#   02/xxx.xx.xx      (vast Brussel)
_RE_PHONE = re.compile(
    r"""
    (?:
        \+32\s?(?:4\d{2}[\s\-]?\d{2}[\s\-]?\d{2}[\s\-]?\d{2}   # mobiel +32 4xx
        |\d[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})                 # vast +32 x xxx xx xx
    )
    |
    (?:
        0(?:4\d{2}|[1-9]\d)                                       # nationaal: 04xx of 0x
        [\s\/\-]?
        \d{2,3}
        [\s\.\-]?
        \d{2}
        [\s\.\-]?
        \d{2}
    )
    """,
    re.VERBOSE,
)

# IBAN — Belgisch (BE) en Nederlands (NL), 16 resp. 18 karakters
_RE_IBAN = re.compile(
    r"\b(?:BE\d{2}[\s]?\d{4}[\s]?\d{4}[\s]?\d{4}"      # BE XX XXXX XXXX XXXX
    r"|NL\d{2}[\s]?[A-Z]{4}[\s]?\d{10})\b",             # NL XX XXXX XXXXXXXXXX
    re.IGNORECASE,
)

# API-sleutels: lange hex/base64 strings in toewijzingen, env-vars of string literals
# Detecteert: API_KEY="...", token = "...", secret="...", password="...", Bearer TOKEN
# Optionele "Bearer " prefix wordt overgeslagen zodat de rauwe tokenwaarde wordt vastgelegd.
_RE_API_KEY = re.compile(
    r"""
    (?:
        (?:api[_\-]?key|token|secret|password|passwd|auth[_\-]?key|bearer)
        [\s]*[=:]+[\s]*
        ["\']?
        (?:Bearer\s+)?              # optionele "Bearer " prefix in waarde
        ([A-Za-z0-9\-_+/=]{20,})   # minstens 20 tekens — vermijd valse positieven
        ["\']?
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

# IPv4-adressen (niet 127.x.x.x of 0.x.x.x)
_RE_IP = re.compile(
    r"\b(?!127\.|0\.)(?:\d{1,3}\.){3}\d{1,3}\b"
)

# Mapping type → regex (volgorde bepaalt prioriteit bij overlap)
_PATRONEN: list[tuple[str, re.Pattern[str]]] = [
    ("EMAIL",      _RE_EMAIL),
    ("IBAN",       _RE_IBAN),
    ("API_KEY",    _RE_API_KEY),
    ("PHONE",      _RE_PHONE),
    ("IP_ADDRESS", _RE_IP),
]

# Hoog-risico types (→ risiconiveau HIGH)
_HOOG_RISICO_TYPES: frozenset[str] = frozenset({"EMAIL", "IBAN", "API_KEY"})

# Matig-risico types (→ risiconiveau MEDIUM als geen HIGH)
_MEDIUM_RISICO_TYPES: frozenset[str] = frozenset({"PHONE", "IP_ADDRESS"})

# Maximale bestandsgrootte voor scanning (5 MB) — grotere bestanden overslaan
_MAX_BESTAND_BYTES = 5 * 1024 * 1024

# Binaire bestandsextensies die niet gescand worden
_BINAIRE_EXTENSIES: frozenset[str] = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".pdf", ".zip", ".tar", ".gz", ".jar", ".war",
    ".class", ".pyc", ".pyo", ".so", ".dll", ".exe",
    ".db", ".sqlite", ".lock",
})


# ─────────────────────────────────────────────
# PII Scanner
# ─────────────────────────────────────────────

class PIIScanner:
    """
    Scant bronbestanden op persoonlijk identificeerbare informatie (PII).

    Gebruikt uitsluitend regex-patronen — geen externe afhankelijkheden
    (geen Presidio, geen ML-modellen). Geschikt voor offline/lokale analyse.

    Methodes:
        scan_bestand(pad)          → PIIScanResult voor één bestand
        scan_project(project)      → list[PIIScanResult] voor alle projectbestanden
        anonymiseer(waarde, type)  → gemaskeerde string
    """

    # ─── Publieke API ─────────────────────────────────────────────

    def scan_bestand(self, pad: Path) -> PIIScanResult:
        """
        Scan één bestand op PII-patronen.

        Leest het bestand regel voor regel. Grote of binaire bestanden worden
        overgeslagen om performance te garanderen.

        Args:
            pad: Path naar het te scannen bestand.

        Returns:
            PIIScanResult met gevonden matches, risiconiveau en aanbeveling.
        """
        bestand_str = str(pad)

        # Binaire bestanden overslaan
        if pad.suffix.lower() in _BINAIRE_EXTENSIES:
            logger.debug("Binair bestand overgeslagen: %s", bestand_str)
            return PIIScanResult(
                bestand=bestand_str,
                matches=[],
                risiconiveau="LOW",
                aanbeveling="Binair bestand — niet gescand.",
            )

        # Bestanden die niet bestaan
        if not pad.exists() or not pad.is_file():
            logger.warning("Bestand bestaat niet of is geen bestand: %s", bestand_str)
            return PIIScanResult(
                bestand=bestand_str,
                matches=[],
                risiconiveau="LOW",
                aanbeveling="Bestand niet gevonden.",
            )

        # Grote bestanden overslaan
        if pad.stat().st_size > _MAX_BESTAND_BYTES:
            logger.warning(
                "Bestand te groot voor PII-scan (%d bytes): %s",
                pad.stat().st_size, bestand_str,
            )
            return PIIScanResult(
                bestand=bestand_str,
                matches=[],
                risiconiveau="MEDIUM",
                aanbeveling="Bestand te groot voor volledige scan — handmatige review aanbevolen.",
            )

        matches: list[PIIMatch] = []

        try:
            inhoud = pad.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.error("Kon bestand niet lezen %s: %s", bestand_str, exc)
            return PIIScanResult(
                bestand=bestand_str,
                matches=[],
                risiconiveau="LOW",
                aanbeveling="Bestand kon niet worden geopend.",
            )

        regels = inhoud.splitlines()
        for lijnnummer, regel in enumerate(regels, start=1):
            for pii_type, patroon in _PATRONEN:
                for treffer in patroon.finditer(regel):
                    # Haal de ruwe waarde op (gebruik groep 1 bij API_KEY)
                    ruw = treffer.group(1) if pii_type == "API_KEY" and treffer.lastindex else treffer.group()
                    gemaskeerd = self.anonymiseer(ruw, pii_type)
                    matches.append(
                        PIIMatch(
                            type=pii_type,
                            waarde=gemaskeerd,
                            lijn=lijnnummer,
                            bestand=bestand_str,
                        )
                    )

        risiconiveau = self._bereken_risico(matches)
        aanbeveling = self._genereer_aanbeveling(risiconiveau, matches)

        logger.info(
            "PII-scan klaar: %s → %d matches, risico=%s",
            bestand_str, len(matches), risiconiveau,
        )
        return PIIScanResult(
            bestand=bestand_str,
            matches=matches,
            risiconiveau=risiconiveau,
            aanbeveling=aanbeveling,
        )

    def scan_project(self, project: "ClientProjectSpace") -> list[PIIScanResult]:
        """
        Scan alle bronbestanden van een project op PII.

        Gebruikt project.scan_bestanden() om de bestandslijst op te halen
        (al gefilterd op taal en gesorteerd op grootte).

        Args:
            project: ClientProjectSpace waarvan de bestanden gescand worden.

        Returns:
            Lijst van PIIScanResult, één per gescand bestand.
            Bestanden met HIGH-risico staan als eerste (gesorteerd).
        """
        bestanden = project.scan_bestanden()
        if not bestanden:
            logger.warning(
                "Geen bestanden gevonden voor PII-scan in project %s",
                project.project_id,
            )
            return []

        resultaten: list[PIIScanResult] = []
        for pad in bestanden:
            resultaat = self.scan_bestand(pad)
            resultaten.append(resultaat)

        # Sorteer: HIGH eerst, dan MEDIUM, dan LOW
        _risico_volgorde = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        resultaten.sort(key=lambda r: _risico_volgorde.get(r.risiconiveau, 3))

        hoog = sum(1 for r in resultaten if r.risiconiveau == "HIGH")
        medium = sum(1 for r in resultaten if r.risiconiveau == "MEDIUM")
        logger.info(
            "Project PII-scan klaar voor %s: %d bestanden, %d HIGH, %d MEDIUM",
            project.project_id, len(resultaten), hoog, medium,
        )
        return resultaten

    def anonymiseer(self, waarde: str, type: str) -> str:
        """
        Maskeer een gevoelige waarde zodat de structuur zichtbaar blijft
        maar de inhoud niet reconstrueerbaar is.

        Maskeringsregels per type:
          - EMAIL:      j***@***.com  (lokaal deel + domein gemaskeerd, TLD behouden)
          - PHONE:      +32 *** ** **  (enkel landcode behouden)
          - IBAN:       BE** **** **** ****  (enkel land + checksum behouden)
          - API_KEY:    sk-***...***  (eerste 3 + laatste 3 tekens)
          - IP_ADDRESS: ***.***.***.***  (volledig gemaskeerd)
          - overig:     ***  (volledig gemaskeerd)

        Args:
            waarde: Originele gevoelige string.
            type:   PII-type (bepaalt maskeringsstrategie).

        Returns:
            Gemaskeerde string.
        """
        waarde = waarde.strip()

        if type == "EMAIL":
            return self._maskeer_email(waarde)

        if type == "PHONE":
            # Behoud landcode als aanwezig, mask de rest
            if waarde.startswith("+32"):
                return "+32 *** ** **"
            return "0** *** ** **"

        if type == "IBAN":
            # Behoud land + checksum (4 tekens), mask rest
            schoon = waarde.replace(" ", "").upper()
            if len(schoon) >= 4:
                return f"{schoon[:4]} **** **** ****"
            return "** **** **** ****"

        if type == "API_KEY":
            if len(waarde) <= 6:
                return "***"
            return f"{waarde[:3]}***{waarde[-3:]}"

        if type == "IP_ADDRESS":
            return "***.***.***.***"

        # Fallback voor onbekende types
        return "***"

    # ─── Interne hulpfuncties ─────────────────────────────────────

    def _maskeer_email(self, email: str) -> str:
        """Maskeer e-mail naar j***@***.com formaat."""
        if "@" not in email:
            return "***@***.***"
        lokaal, rest = email.split("@", 1)
        # Maskeer lokaal deel: eerste letter behouden
        lokaal_gemaskeerd = (lokaal[0] + "***") if lokaal else "***"
        # Maskeer domein maar behoud TLD
        if "." in rest:
            _domein, tld = rest.rsplit(".", 1)
            return f"{lokaal_gemaskeerd}@***.{tld}"
        return f"{lokaal_gemaskeerd}@***"

    def _bereken_risico(self, matches: list[PIIMatch]) -> str:
        """
        Bereken risiconiveau op basis van gevonden PII-types.

        HIGH   → als minstens één EMAIL, IBAN of API_KEY gevonden
        MEDIUM → als minstens één PHONE of IP_ADDRESS gevonden (maar geen HIGH)
        LOW    → geen PII of onbekende lage-risico patronen
        """
        gevonden_types = {m.type for m in matches}
        if gevonden_types & _HOOG_RISICO_TYPES:
            return "HIGH"
        if gevonden_types & _MEDIUM_RISICO_TYPES:
            return "MEDIUM"
        return "LOW"

    def _genereer_aanbeveling(self, risiconiveau: str, matches: list[PIIMatch]) -> str:
        """Genereer een tekstuele aanbeveling op basis van risiconiveau en matches."""
        if not matches:
            return "Geen PII gevonden. Bestand is veilig voor AI-analyse."

        typen = sorted({m.type for m in matches})
        typen_str = ", ".join(typen)

        if risiconiveau == "HIGH":
            return (
                f"⚠️ HOOG RISICO: {typen_str} gevonden ({len(matches)} treffer(s)). "
                "Verwijder of anonimiseer PII vóór AI-analyse. "
                "GDPR Art. 25 (Privacy by Design) vereist actie."
            )
        if risiconiveau == "MEDIUM":
            return (
                f"⚡ GEMIDDELD RISICO: {typen_str} gevonden ({len(matches)} treffer(s)). "
                "Controleer of deze gegevens noodzakelijk zijn voor de analyse."
            )
        return (
            f"ℹ️ LAAG RISICO: {typen_str} gevonden ({len(matches)} treffer(s)). "
            "Beoordeel voor verzending naar AI-model."
        )


# ─────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────

_scanner: PIIScanner | None = None


def get_pii_scanner() -> PIIScanner:
    """
    Singleton accessor voor PIIScanner.

    Thread-safe voor read-only gebruik (patterns zijn gecompileerd bij import).
    Hergebruikt dezelfde instantie gedurende de levensduur van de applicatie.

    Returns:
        Gedeelde PIIScanner instantie.
    """
    global _scanner
    if _scanner is None:
        _scanner = PIIScanner()
        logger.debug("PIIScanner singleton aangemaakt")
    return _scanner
