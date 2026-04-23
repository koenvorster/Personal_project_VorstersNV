"""
VorstersNV Sector Benchmark Engine
Definieert typische kenmerken, technische schuld-patronen en aanbevelingen
per Belgisch KMO-sector voor gebruik in klantrapportage.

Gebruik:
    engine = get_benchmark_engine()

    # Automatisch sector detecteren
    sector = engine.detect_sector("transport van goederen via vrachtwagens")
    # → Sector.LOGISTIEK

    # Benchmark opvragen
    benchmark = engine.get_benchmark(Sector.RETAIL)

    # Vergelijking genereren
    vergelijking = engine.vergelijk_met_benchmark(
        project_id="PRJ-001",
        sector=Sector.RETAIL,
        gevonden_issues=["geen CI/CD", "directe DB-koppelingen"],
        gevonden_talen=["PHP", "JavaScript"],
    )

    # Leesbare samenvatting
    tekst = engine.genereer_samenvatting(vergelijking)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ─── Enums ────────────────────────────────────────────────────────────────────

class Sector(str, Enum):
    RETAIL = "retail"
    LOGISTIEK = "logistiek"
    PRODUCTIE = "productie"
    ZORG = "zorg"
    FINANCE = "finance"
    BOUW = "bouw"
    HORECA = "horeca"
    IT_DIENSTEN = "it_diensten"
    OVERHEID = "overheid"
    ONBEKEND = "onbekend"


# ─── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class TechnischeSchuldProfiel:
    """Technische schuld-kenmerken typisch voor een sector."""
    gemiddelde_score: float                    # 0.0 (geen schuld) – 10.0 (kritiek)
    meest_voorkomende_issues: list[str]
    typische_talen: list[str]
    typische_frameworks: list[str]
    gemiddelde_codebase_leeftijd_jaar: float


@dataclass
class SectorBenchmark:
    """Volledig benchmark-profiel voor één Belgische KMO-sector."""
    sector: Sector
    naam_nl: str
    beschrijving: str
    technische_schuld: TechnischeSchuldProfiel
    aanbevolen_modernisatie: list[str]
    typische_kpis: dict[str, str]
    compliance_vereisten: list[str]
    ai_kansen: list[str]
    roi_schatting: str


@dataclass
class BenchmarkVergelijking:
    """Vergelijking van een concreet project met de sector-norm."""
    project_id: str
    sector: Sector
    benchmark: SectorBenchmark
    afwijkingen: list[str]
    sterktes: list[str]
    verbeterpunten: list[str]
    prioriteit_score: float                    # 0.0–10.0 urgentie voor modernisatie


# ─── Ingebouwde benchmarks ────────────────────────────────────────────────────

_BENCHMARKS: dict[Sector, SectorBenchmark] = {

    # ── RETAIL ────────────────────────────────────────────────────────────────
    Sector.RETAIL: SectorBenchmark(
        sector=Sector.RETAIL,
        naam_nl="Retail & E-commerce",
        beschrijving=(
            "Belgische retailers met fysieke winkel en/of webshop, ERP-integraties, "
            "omnichannel strategie en seizoensgebonden pieken."
        ),
        technische_schuld=TechnischeSchuldProfiel(
            gemiddelde_score=6.5,
            meest_voorkomende_issues=[
                "verouderde PHP-webshop zonder API-laag",
                "directe database-koppelingen vanuit frontend",
                "monolithische architectuur moeilijk te schalen",
                "geen CI/CD pipeline — deployments manueel",
                "ERP-koppeling via CSV-export/import of screen scraping",
                "geen geautomatiseerde tests",
                "hard-coded productprijzen en BTW-logica",
            ],
            typische_talen=["PHP", "JavaScript", "Python"],
            typische_frameworks=["WooCommerce", "Magento", "Laravel", "Vue.js", "jQuery"],
            gemiddelde_codebase_leeftijd_jaar=7.5,
        ),
        aanbevolen_modernisatie=[
            "Migreer naar headless e-commerce architectuur (Next.js + API)",
            "Implementeer REST/GraphQL API-laag als ontkoppeling van ERP",
            "Containeriseer met Docker en Docker Compose",
            "Voeg CI/CD toe via GitHub Actions of GitLab CI",
            "Vervang CSV-integraties door event-driven koppeling (webhooks/messaging)",
            "Introduceer geautomatiseerde regressie- en integratietests",
            "Implementeer caching-laag (Redis) voor productcatalogus",
        ],
        typische_kpis={
            "conversieratio": "2–4%",
            "paginalaadtijd": "<3s",
            "beschikbaarheid": "99.9%",
            "gemiddelde orderwaarde": "€45–€120",
            "retourpercentage": "8–15%",
        },
        compliance_vereisten=["GDPR/AVG", "PCI-DSS (betalingen)", "Belgische consumentenwetgeving", "Herroepingsrecht 14 dagen", "NIS2 (voor grotere spelers)"],
        ai_kansen=[
            "Gepersonaliseerde productaanbevelingen op basis van browse-gedrag",
            "Dynamische prijsoptimalisatie (demand forecasting)",
            "Klantenservice chatbot voor FAQ en orderstatus",
            "Voorraadbeheer met AI-gestuurde inkoopadviezen",
            "Fraudedetectie op bestellingen",
            "Automatische productbeschrijvingen genereren",
            "Sentimentanalyse van klantreviews",
        ],
        roi_schatting="20–35% omzetstijging door personalisatie + 15% kostenbesparing klantenservice via AI-chatbot",
    ),

    # ── LOGISTIEK ─────────────────────────────────────────────────────────────
    Sector.LOGISTIEK: SectorBenchmark(
        sector=Sector.LOGISTIEK,
        naam_nl="Logistiek & Transport",
        beschrijving=(
            "Belgische transport- en logistiekbedrijven: wegvervoer, warehousing, "
            "last-mile delivery en supply chain management voor Belgische en Europese markt."
        ),
        technische_schuld=TechnischeSchuldProfiel(
            gemiddelde_score=7.0,
            meest_voorkomende_issues=[
                "TMS (Transport Management System) op legacy desktop-software (Delphi/VB6)",
                "Geen real-time track & trace voor klanten",
                "Planning nog deels manueel in Excel-sheets",
                "Integratie met klant-ERP via FTP-bestandsuitwisseling",
                "Geen digitale vrachtbrief — papieren documenten",
                "Chauffeurs-app ontbreekt of is verouderd",
                "Geen koppeling met telematica/boordcomputer data",
            ],
            typische_talen=["Delphi", "VB.NET", "C#", "PHP", "Java"],
            typische_frameworks=[".NET Framework (oud)", "WinForms", "ASP.NET WebForms"],
            gemiddelde_codebase_leeftijd_jaar=12.0,
        ),
        aanbevolen_modernisatie=[
            "Migreer naar cloud-based TMS met REST API",
            "Bouw chauffeurs-app (React Native / Flutter) met offline support",
            "Implementeer real-time GPS-integratie en track & trace portal voor klanten",
            "Vervang FTP-uitwisseling door EDI-standaarden (EDIFACT) of API-integratie",
            "Digitaliseer vrachtbrieven (e-CMR)",
            "Integreer boordcomputer-data (tachograaf, brandstof) in dashboards",
            "Zet over naar microservices voor planning, tracking en facturatie",
        ],
        typische_kpis={
            "on-time delivery": "94–98%",
            "voertuigbezetting": "82–90%",
            "brandstofkosten per km": "€0.28–€0.42",
            "documentatietijd per rit": "15–25 min",
            "klanttevredenheid": "7.5–8.5/10",
        },
        compliance_vereisten=["ADR (gevaarlijke stoffen)", "GDPR (chauffeurs + klantdata)", "Arbeidstijdenwet transport", "NIS2 (kritieke infrastructuur)", "CO2-rapportage (Scope 1 & 3)"],
        ai_kansen=[
            "Route-optimalisatie op basis van real-time verkeersdata",
            "Predictief onderhoud op basis van voertuigtelemetrie",
            "Automatische ritplanning met AI-solver",
            "Klant-communicatiebot voor leveringsupdates",
            "Anomaliedetectie in brandstofverbruik (diefstaldetectie)",
            "Automatische vrachtbriefverwerking via OCR",
            "Demand forecasting voor warehousing-capaciteitsplanning",
        ],
        roi_schatting="10–18% brandstofbesparing door route-optimalisatie + 25% minder planningsuren via AI-assisted planning",
    ),

    # ── PRODUCTIE ─────────────────────────────────────────────────────────────
    Sector.PRODUCTIE: SectorBenchmark(
        sector=Sector.PRODUCTIE,
        naam_nl="Productie & Maakindustrie",
        beschrijving=(
            "Belgische productiebedrijven: discrete productie, procesindustrie, "
            "food & beverage, metaalverwerking en hightech manufacturing (Industrie 4.0 context)."
        ),
        technische_schuld=TechnischeSchuldProfiel(
            gemiddelde_score=7.5,
            meest_voorkomende_issues=[
                "MES (Manufacturing Execution System) op verouderde client-server architectuur",
                "SCADA-systemen niet gekoppeld aan ERP (informatie-eilanden)",
                "Kwaliteitscontrole nog op papier of in Excel",
                "Onderhoudsbeheer zonder predictieve component",
                "Productieplanning in spreadsheets los van ERP",
                "Geen OEE (Overall Equipment Effectiveness) real-time monitoring",
                "PLC-software slecht gedocumenteerd, geen versiebeheer",
            ],
            typische_talen=["C", "C++", "Python", "VB.NET", "COBOL (legacy ERP)"],
            typische_frameworks=["WinCC", "iFIX", "SAP (oud)", "Infor", "Microsoft Dynamics NAV"],
            gemiddelde_codebase_leeftijd_jaar=14.0,
        ),
        aanbevolen_modernisatie=[
            "Implementeer IIoT-laag (MQTT/OPC-UA) voor machine-connectiviteit",
            "Koppel SCADA/PLC data aan cloud-platform (Azure IoT / AWS IoT) via edge computing",
            "Digitaliseer kwaliteitscontrole met tablet-apps en barcode/QR scanning",
            "Implementeer CMMS (Computerized Maintenance Management System)",
            "Bouw real-time OEE dashboard gekoppeld aan productieplanning",
            "Migreer van legacy ERP naar moderne cloud ERP (SAP S/4HANA, Odoo)",
            "Voer Git-versiebeheer in voor PLC-software en machine-configuraties",
        ],
        typische_kpis={
            "OEE": "65–80%",
            "planmatig onderhoud": "70–85%",
            "first-pass yield": "92–98%",
            "downtime niet-gepland": "<5%",
            "voorraadrotatie": "6–12x/jaar",
        },
        compliance_vereisten=["ISO 9001 (kwaliteit)", "ISO 14001 (milieu)", "GDPR (medewerkerdata)", "NIS2 (OT/ICS security)", "Seveso (chemie)", "CE-markering software"],
        ai_kansen=[
            "Predictief onderhoud op basis van sensor- en trillingsdata",
            "Computer vision voor kwaliteitsinspectie op productielijn",
            "AI-gestuurde productieplanning en schedulingoptimalisatie",
            "Energieverbruiksoptimalisatie via ML-modellen",
            "Procesintelligentie voor yield-verbetering",
            "Anomaliedetectie in SCADA-data",
            "Automatische receptuur-optimalisatie (food & beverage)",
        ],
        roi_schatting="12–20% downtime-reductie via predictief onderhoud + 8% energiebesparing door AI-optimalisatie",
    ),

    # ── ZORG ──────────────────────────────────────────────────────────────────
    Sector.ZORG: SectorBenchmark(
        sector=Sector.ZORG,
        naam_nl="Gezondheidszorg & Welzijn",
        beschrijving=(
            "Belgische zorginstellingen: ziekenhuizen, woonzorgcentra, thuiszorg, "
            "huisartsenpraktijken, paramedici en zorgnetwerken."
        ),
        technische_schuld=TechnischeSchuldProfiel(
            gemiddelde_score=6.0,
            meest_voorkomende_issues=[
                "Elektronisch patiëntendossier (EPD) in silo's per afdeling",
                "Geen interoperabiliteit tussen zorgverstrekkers (HL7/FHIR ontbreekt)",
                "Handmatige rapportage naar ziekenfondsen en overheid",
                "Roostersysteem losgekoppeld van EPD",
                "Verouderde medische apparatuur zonder digitale koppeling",
                "Papieren medicatieoverzichten op verpleegafdelingen",
                "IT-beveiliging ondermaats (geen MFA, verouderde systemen)",
            ],
            typische_talen=["Java", "C#", ".NET", "Python", "PHP"],
            typische_frameworks=["EPIC (internationaal)", "Nexuz Health", "Multimed", "ChipSoft"],
            gemiddelde_codebase_leeftijd_jaar=9.0,
        ),
        aanbevolen_modernisatie=[
            "Implementeer FHIR R4 API-standaard voor zorgdata-uitwisseling",
            "Bouw geïntegreerd zorgplatform met SSO (Single Sign-On)",
            "Digitaliseer medicatiebeheer met barcodescanning en closed-loop",
            "Koppel medische apparatuur via HL7/DICOM integratie",
            "Implementeer MFA en zero-trust security architectuur",
            "Migreer naar cloud-EHR met GDPR/gezondheidsrecht compliance",
            "Automatiseer rapportage via gestandaardiseerde data-exports",
        ],
        typische_kpis={
            "patiënttevredenheid": "8.0–9.0/10",
            "ziekenhuisheropname 30 dagen": "<8%",
            "medicatiefouten": "<0.5%",
            "registratietijd verpleging": "15–25% werktijd",
            "wachttijd spoedgevallen": "<4u",
        },
        compliance_vereisten=["GDPR + Gezondheidsgegevens (Art. 9)", "HIPAA-equivalent (Belgisch gezondheidsrecht)", "NIS2 (kritieke sector)", "e-Health standaarden (eHealth Box)", "Vlaams Patiëntenrechtenwet"],
        ai_kansen=[
            "Klinische beslissingsondersteuning (Clinical Decision Support)",
            "Automatische codering van diagnoses (ICD-10) via NLP",
            "Readmissie-risico-voorspelling",
            "AI-gestuurde roosterplanning voor verpleging",
            "Beeldanalyse voor radiologie (detectie anomalieën)",
            "Spraakherkenning voor verpleegkundige rapportage",
            "Chatbot voor patiëntenportaal (afspraken, medicatie-info)",
        ],
        roi_schatting="20–30% tijdsbesparing op administratie + 15% reductie vermijdbare heropnames via predictieve modellen",
    ),

    # ── FINANCE ───────────────────────────────────────────────────────────────
    Sector.FINANCE: SectorBenchmark(
        sector=Sector.FINANCE,
        naam_nl="Finance, Boekhouden & Accountancy",
        beschrijving=(
            "Belgische boekhoudkantoren, accountantskantoren, fiduciaires, "
            "kleine banken, kredietmakelaars en verzekeraars."
        ),
        technische_schuld=TechnischeSchuldProfiel(
            gemiddelde_score=5.5,
            meest_voorkomende_issues=[
                "Boekhoudpakket lokaal geïnstalleerd (geen cloud-sync)",
                "Documentuitwisseling met klanten via e-mail attachments",
                "Geen geautomatiseerde bank-reconciliatie",
                "Fiscale aangifte nog manueel ingegeven in Biztax/Intervat",
                "Klantdossiers in gedeelde schijven zonder versiebeheer",
                "Geen digitale handtekening workflow",
                "Rapportage in Excel gegenereerd uit boekhoudpakket",
            ],
            typische_talen=["VBA (Excel macros)", "C#", "PHP", "Python"],
            typische_frameworks=["Winbooks", "Exact Online", "Accountview", "Bob 50"],
            gemiddelde_codebase_leeftijd_jaar=8.0,
        ),
        aanbevolen_modernisatie=[
            "Migreer naar cloud-gebaseerd boekhoudpakket (Exact Online, Yuki, Billit)",
            "Implementeer digitale documentuitwisseling via klantportaal",
            "Automatiseer bankimport en -reconciliatie via PSD2 open banking API",
            "Digitaliseer factuurverwerking met OCR + AI (Basware, Zappix)",
            "Implementeer e-signing workflow (DocuSign, Connective)",
            "Bouw klantdashboard met real-time financieel overzicht",
            "Integreer met Biztax/Intervat API voor automatische aangifte",
        ],
        typische_kpis={
            "factuurverwerkingstijd": "2–8 min/factuur",
            "klanttevredenheid": "7.5–9.0/10",
            "tijdigheid aangiftes": ">99%",
            "klantretentie": "85–95%",
            "dossiers per medewerker": "40–80",
        },
        compliance_vereisten=["GDPR/AVG (financiële persoonsgegevens)", "ISAE 3402 (service organisation controls)", "Anti-witwassen (AMLD6)", "PSD2 (open banking)", "Belgische boekhoudwetgeving (CBN)", "DORA (2025, financiële sector)"],
        ai_kansen=[
            "Automatische factuurherkenning en boeking via AI-OCR",
            "Anomaliedetectie in boekhouding (fraude, fouten)",
            "AI-gestuurde belastingoptimalisatie en -advies",
            "Cashflow-prognoses via ML-modellen",
            "Automatische BTW-aangifte-voorbereiding",
            "Klantchatbot voor basisvragen (BTW-tarieven, deadlines)",
            "Credit scoring voor kredietmakelaars",
        ],
        roi_schatting="40–60% tijdsbesparing op factuurverwerking via AI-OCR + 25% minder correctietijd via anomaliedetectie",
    ),

    # ── BOUW ──────────────────────────────────────────────────────────────────
    Sector.BOUW: SectorBenchmark(
        sector=Sector.BOUW,
        naam_nl="Bouw & Vastgoed",
        beschrijving=(
            "Belgische aannemers, bouwpromotoren, installatiebedrijven (HVAC, elektriciteit), "
            "architectenbureaus en vastgoedontwikkelaars."
        ),
        technische_schuld=TechnischeSchuldProfiel(
            gemiddelde_score=7.0,
            meest_voorkomende_issues=[
                "Projectopvolging in Excel zonder gedeeld platform",
                "Werfrapportage op papier of via WhatsApp-foto's",
                "Geen digitale as-built plannen",
                "Facturatie en offertes in gescheiden systemen (Word + Excel)",
                "Geen koppeling tussen planning, budget en uitvoering",
                "Meerwerk-beheer via e-mail zonder formeel proces",
                "Uurregistratie manueel op papier",
            ],
            typische_talen=["VBA (Excel)", "PHP", "JavaScript"],
            typische_frameworks=["Bexio", "Exact", "Autodesk AutoCAD", "Microsoft Project"],
            gemiddelde_codebase_leeftijd_jaar=6.0,
        ),
        aanbevolen_modernisatie=[
            "Implementeer BIM (Building Information Modelling) voor plannen en coördinatie",
            "Voer een digitaal projectbeheerplatform in (Procore, PlanGrid, of maatwerk)",
            "Digitaliseer werfrapportage met mobiele app (foto's, tijdregistratie, issues)",
            "Integreer offerte, planning en facturatie in één systeem",
            "Implementeer digitale uurregistratie met GPS-verificatie",
            "Koppel facturatie aan vorderingsstaten via automatische berekening",
            "Voer digitale archivering in voor as-built plannen en attesten",
        ],
        typische_kpis={
            "projectbudgetafwijking": "<5%",
            "planningsafwijking": "<10%",
            "winstmarge": "4–8%",
            "offertesucces": "25–40%",
            "oplevering op tijd": "60–75%",
        },
        compliance_vereisten=["GDPR (klant- en werknemersdata)", "Belgische arbeidswetgeving (werfveiligheid)", "EPB (energieprestatie gebouwen)", "VCA certificering", "Asbestattest (2032 deadline)", "Omgevingsvergunning"],
        ai_kansen=[
            "AI-gestuurde offerte-calculatie op basis van historische projectdata",
            "Automatische meerwerkenherkenning via planvergelijking",
            "Bouwplaatsveiligheidsmonitoring via computer vision (helmen, vesten)",
            "Predictieve planning op basis van weer, leveringen en capaciteit",
            "OCR voor factuurverwerking van leveranciers",
            "Chatbot voor klanten over projectstatus",
            "Energieprestatie-optimalisatie via BIM + AI",
        ],
        roi_schatting="15% budgetafwijking-reductie via betere projectopvolging + 20% minder administratietijd via digitale rapportage",
    ),

    # ── HORECA ────────────────────────────────────────────────────────────────
    Sector.HORECA: SectorBenchmark(
        sector=Sector.HORECA,
        naam_nl="Horeca & Voeding",
        beschrijving=(
            "Belgische restaurants, hotels, catering, food trucks en cateringbedrijven. "
            "Kenmerkt zich door hoge operationele complexiteit, seizoenspieken en hoge personeelsrotatie."
        ),
        technische_schuld=TechnischeSchuldProfiel(
            gemiddelde_score=5.0,
            meest_voorkomende_issues=[
                "Kassasysteem (POS) niet gekoppeld aan boekhouding",
                "Voorraadbeheer manueel of in spreadsheet",
                "Reservatiesysteem losgekoppeld van planning en personeel",
                "Geen klantenkaart of loyaliteitsprogramma-data",
                "Personeelsplanning in WhatsApp-groepen",
                "Geen HACCP-digitalisering (temperatuur-logging op papier)",
                "Online bestellingen via meerdere niet-geïntegreerde platforms",
            ],
            typische_talen=["PHP", "JavaScript", "Python"],
            typische_frameworks=["Lightspeed", "Square", "Deliveroo API (extern)", "WordPress"],
            gemiddelde_codebase_leeftijd_jaar=4.5,
        ),
        aanbevolen_modernisatie=[
            "Koppel POS-systeem aan boekhouding en voorraad via API",
            "Implementeer geïntegreerd reservatie- en tafelbeheersysteem",
            "Centraliseer online bestelling (eigen platform + aggregator-koppeling)",
            "Digitaliseer HACCP-registratie via IoT-temperatuursensoren",
            "Voer personeelsplanning-app in (Shyfter, Easypay Planning)",
            "Bouw loyaliteitsprogramma met klantenapp",
            "Integreer leveranciersbestelproces met voorraadbeheer",
        ],
        typische_kpis={
            "tafelbezetting": "55–75%",
            "food cost ratio": "28–35%",
            "personeelskost/omzet": "30–40%",
            "online reviews score": "4.0–4.5/5",
            "no-show reservaties": "5–12%",
        },
        compliance_vereisten=["HACCP (voedselveiligheid)", "GDPR (klantendata, loyaliteitskaarten)", "Belgische horecawetgeving (zwarte kassa)", "Allergenenregistratie (EU 1169/2011)", "Alcohol- en tabakswetgeving"],
        ai_kansen=[
            "Menu-optimalisatie op basis van populariteit en marge (menu engineering AI)",
            "Voorraadbeheer en besteladvies via vraagvoorspelling",
            "Persoonlijke aanbevelingen voor stamgasten",
            "Chatbot voor reservaties en FAQ",
            "Sentimentanalyse van online reviews voor kwaliteitsopvolging",
            "Dynamische prijszetting op rustige periodes",
            "Automatische HACCP-rapportage via IoT-sensoren",
        ],
        roi_schatting="8–12% food cost-reductie via AI-gestuurde inkoop + 15% no-show reductie via AI-reminded reservatieflow",
    ),

    # ── IT_DIENSTEN ───────────────────────────────────────────────────────────
    Sector.IT_DIENSTEN: SectorBenchmark(
        sector=Sector.IT_DIENSTEN,
        naam_nl="IT-diensten & Consultancy",
        beschrijving=(
            "Belgische IT-bedrijven: software-ontwikkeling, managed services, "
            "cloud consultancy, IT-outsourcing en SaaS-aanbieders voor de KMO-markt."
        ),
        technische_schuld=TechnischeSchuldProfiel(
            gemiddelde_score=4.5,
            meest_voorkomende_issues=[
                "Monolithische SaaS-applicaties moeilijk te schalen",
                "Geen multi-tenancy architectuur (aparte DB per klant)",
                "Handmatige deployments zonder CI/CD",
                "Onvoldoende monitoring en alerting in productie",
                "Legacy code zonder tests, moeilijk te refactoren",
                "Geen feature flags of canary deployments",
                "Klantrapportage manueel samengesteld",
            ],
            typische_talen=["Java", "Python", "JavaScript/TypeScript", "PHP", "C#"],
            typische_frameworks=["Spring Boot", "Django", "React", "Angular", "Laravel", ".NET Core"],
            gemiddelde_codebase_leeftijd_jaar=5.5,
        ),
        aanbevolen_modernisatie=[
            "Migreer monoliet naar microservices of modulaire monoliet",
            "Implementeer multi-tenancy op database- of schema-niveau",
            "Bouw volledige CI/CD pipeline (build, test, deploy, rollback)",
            "Voer observability in (Prometheus, Grafana, distributed tracing)",
            "Introduceer feature flags (LaunchDarkly, Unleash) voor veilige releases",
            "Implementeer Infrastructure as Code (Terraform, Pulumi)",
            "Automatiseer klantrapportage via data pipeline",
        ],
        typische_kpis={
            "deployment frequency": "1–5x/week",
            "mean time to recovery": "<4u",
            "test coverage": "60–80%",
            "klanttevredenheid (NPS)": "30–50",
            "uptime SLA": "99.9%",
        },
        compliance_vereisten=["GDPR (verwerker-overeenkomsten)", "ISO 27001 (informatiebeveiliging)", "NIS2 (managed service providers verplicht)", "SOC 2 Type II (cloud providers)", "DORA (voor financiële klanten)"],
        ai_kansen=[
            "AI-gestuurde code review en bug detectie (GitHub Copilot, CodeClimate AI)",
            "Automatische testgeneratie op basis van code wijzigingen",
            "Incident-detectie en root cause analysis via ML",
            "AI-chatbot voor Tier-1 klantenondersteuning (ticketdeflectie)",
            "Intelligente resource-planning voor consultancy-projecten",
            "Automatische documentatiegeneratie vanuit code",
            "Anomaliedetectie in productie-logs",
        ],
        roi_schatting="30% snellere time-to-market via CI/CD + 40% reductie Tier-1 support tickets via AI-chatbot",
    ),

    # ── OVERHEID ──────────────────────────────────────────────────────────────
    Sector.OVERHEID: SectorBenchmark(
        sector=Sector.OVERHEID,
        naam_nl="Lokale Overheid & Semi-publieke Sector",
        beschrijving=(
            "Belgische gemeenten, OCMW's, intercommunales, havens, "
            "publieke nutsbedrijven en semi-publieke instellingen."
        ),
        technische_schuld=TechnischeSchuldProfiel(
            gemiddelde_score=7.8,
            meest_voorkomende_issues=[
                "Grote hoeveelheid legacy systemen (mainframe, AS/400, VB6)",
                "Silo-gebaseerde systemen per dienst zonder datadeling",
                "Papieren processen voor burgerzaken en vergunningen",
                "Geen geïntegreerd GIS (geografisch informatiesysteem)",
                "Verouderde webportalen niet mobiel-vriendelijk",
                "Handmatige rapportage naar hogere overheden",
                "E-mailgebaseerde interne workflows voor goedkeuringen",
            ],
            typische_talen=["COBOL", "RPG (AS/400)", "Java", "PHP", "C#"],
            typische_frameworks=["Cegeka", "Cipal Schaubroeck", "Remant", "e-government platforms"],
            gemiddelde_codebase_leeftijd_jaar=18.0,
        ),
        aanbevolen_modernisatie=[
            "Migreer legacy systemen stapsgewijs via strangler fig pattern",
            "Implementeer geïntegreerd burgerportaal (My Citizen) met SSO via itsme",
            "Digitaliseer vergunning- en aanvraagprocessen via low-code platform",
            "Koppel interne systemen via API-gateway en event bus",
            "Implementeer GIS-platform (ArcGIS, QGIS) voor ruimtelijke analyses",
            "Bouw data warehouse voor beleidsrapportage",
            "Introduceer BPM (Business Process Management) voor goedkeuringsworkflows",
        ],
        typische_kpis={
            "digitale dienstverlening": "40–70% online",
            "behandeltijd vergunningen": "30–90 dagen",
            "burgertevredenheid": "6.5–7.5/10",
            "IT-kostenratio": "3–6% van totaalbudget",
            "beschikbaarheid e-loket": "99.0%",
        },
        compliance_vereisten=["GDPR/AVG (verplicht voor publieke sector)", "Belgisch bestuursrecht", "Openbaarheid van bestuur", "NIS2 (overheid verplicht)", "Toegankelijkheid WCAG 2.1 AA (overheidswebsites)", "Archivenwetgeving"],
        ai_kansen=[
            "Chatbot voor burgervragen (openingsuren, procedures, formulieren)",
            "Automatische verwerking van aanvragen via NLP",
            "Fraudedetectie in sociale uitkeringen (OCMW)",
            "Predictief wegenonderhoud op basis van inspectiedata",
            "AI-gestuurde vergunningsbeoordeling voor routinedossiers",
            "Document-digitalisatie via AI-OCR voor historische archieven",
            "Sentimentanalyse van burgermeldingen voor prioritering",
        ],
        roi_schatting="25–35% reductie in behandeltijd via digitalisering + 20% minder inkomende telefoontjes via AI-chatbot voor burgervragen",
    ),
}

# Fallback voor onbekende sector
_ONBEKEND_BENCHMARK = SectorBenchmark(
    sector=Sector.ONBEKEND,
    naam_nl="Onbekende Sector",
    beschrijving="Sector kon niet worden bepaald op basis van de beschrijving.",
    technische_schuld=TechnischeSchuldProfiel(
        gemiddelde_score=6.0,
        meest_voorkomende_issues=["Technische schuld onbekend — sector-analyse vereist"],
        typische_talen=["Onbekend"],
        typische_frameworks=["Onbekend"],
        gemiddelde_codebase_leeftijd_jaar=8.0,
    ),
    aanbevolen_modernisatie=["Voer een diepgaande technische audit uit om prioriteiten te bepalen"],
    typische_kpis={},
    compliance_vereisten=["GDPR/AVG (van toepassing op alle sectoren)"],
    ai_kansen=["Procesautomatisering", "Data-analyse en rapportage"],
    roi_schatting="Afhankelijk van specifieke sector en projectomvang",
)

# ─── Sector-detectie keywords ─────────────────────────────────────────────────

_SECTOR_KEYWORDS: dict[Sector, list[str]] = {
    Sector.RETAIL: [
        "webshop", "e-commerce", "winkel", "retail", "kassa", "verkoop", "product",
        "woocommerce", "magento", "shopify", "handel", "supermarkt", "online shop",
        "bestelling", "omnichannel", "voorraadbeheer retail",
    ],
    Sector.LOGISTIEK: [
        "transport", "logistiek", "vrachtwagen", "chauffeur", "warehouse", "depot",
        "levering", "lading", "vrachtbrief", "tms", "last mile", "bezorging",
        "routeplanning", "track and trace", "expeditie", "goederenvervoer",
    ],
    Sector.PRODUCTIE: [
        "productie", "fabriek", "manufacturing", "machine", "mes", "scada", "plc",
        "assemblage", "maakindustrie", "food productie", "metaal", "industrie 4.0",
        "oee", "productielijn", "kwaliteitscontrole productie", "onderhoud machine",
    ],
    Sector.ZORG: [
        "ziekenhuis", "zorg", "patiënt", "verpleeg", "kliniek", "arts", "huisarts",
        "epd", "ehr", "medisch", "gezondheid", "apotheek", "thuiszorg", "woonzorgcentrum",
        "revalidatie", "spoedgevallen", "paramedici", "welzijn",
    ],
    Sector.FINANCE: [
        "boekhouding", "accountant", "finance", "bank", "verzekering", "fiscaal",
        "belasting", "factuur", "btw", "jaarrekening", "fintech", "krediet",
        "fiduciaire", "boekhoudkantoor", "audit", "accountancy",
    ],
    Sector.BOUW: [
        "bouw", "aannemer", "werf", "renovatie", "architect", "vastgoed", "project",
        "installatie", "hvac", "elektriciteit", "sanitair", "bim", "vergunning bouw",
        "meerwerk", "vorderingsstaat", "constructie",
    ],
    Sector.HORECA: [
        "restaurant", "hotel", "café", "catering", "keuken", "reservatie", "menu",
        "haccp", "horeca", "food", "beverage", "food truck", "bar", "terras",
        "tafels", "keukenteam", "chef", "food service",
    ],
    Sector.IT_DIENSTEN: [
        "software", "it diensten", "consultancy", "saas", "cloud", "managed service",
        "ontwikkeling", "deployment", "devops", "api", "platform", "it bedrijf",
        "software house", "outsourcing it", "it provider",
    ],
    Sector.OVERHEID: [
        "gemeente", "stad", "overheid", "ocmw", "publiek", "burger", "loket",
        "intercommunale", "haven", "nutsbedrijf", "vergunning overheid", "bestuur",
        "administratie", "ministerie", "agentschap",
    ],
}


# ─── Benchmark Engine ─────────────────────────────────────────────────────────

class SectorBenchmarkEngine:
    """
    Engine voor sector-benchmarks: detectie, opvraging en vergelijking.

    Biedt methoden om:
    - Een benchmark op te halen voor een gekende sector.
    - De sector te detecteren op basis van een tekstuele beschrijving.
    - Een project te vergelijken met de sectorgemiddelden.
    - Een leesbare samenvatting te genereren voor in een klantrapport.
    """

    def get_benchmark(self, sector: Sector) -> SectorBenchmark:
        """
        Geef de benchmark voor een specifieke sector.

        Args:
            sector: De sector waarvoor de benchmark gevraagd wordt.

        Returns:
            SectorBenchmark voor de gevraagde sector.
            Valt terug op de ONBEKEND-benchmark als de sector niet bestaat.
        """
        benchmark = _BENCHMARKS.get(sector)
        if benchmark is None:
            logger.warning("Geen benchmark gevonden voor sector '%s' — fallback naar ONBEKEND", sector)
            return _ONBEKEND_BENCHMARK
        return benchmark

    def detect_sector(self, beschrijving: str) -> Sector:
        """
        Detecteer de meest waarschijnlijke sector op basis van keyword-matching.

        De beschrijving wordt genormaliseerd (lowercase) en vergeleken met
        de sector-keywords. De sector met de meeste treffers wint.

        Args:
            beschrijving: Vrije tekst over het bedrijf of project.

        Returns:
            De gedetecteerde Sector, of Sector.ONBEKEND als geen match.
        """
        if not beschrijving or not beschrijving.strip():
            return Sector.ONBEKEND

        tekst = beschrijving.lower()
        scores: dict[Sector, int] = {}

        for sector, keywords in _SECTOR_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in tekst)
            if score > 0:
                scores[sector] = score

        if not scores:
            logger.info("Sector-detectie: geen treffers voor beschrijving '%s...'", beschrijving[:50])
            return Sector.ONBEKEND

        beste_sector = max(scores, key=lambda s: scores[s])
        logger.info(
            "Sector-detectie: '%s' gedetecteerd (score=%d) voor beschrijving '%s...'",
            beste_sector.value, scores[beste_sector], beschrijving[:50],
        )
        return beste_sector

    def vergelijk_met_benchmark(
        self,
        project_id: str,
        sector: Sector,
        gevonden_issues: list[str],
        gevonden_talen: list[str],
    ) -> BenchmarkVergelijking:
        """
        Vergelijk een project met de sector-norm en identificeer sterktes/zwaktes.

        Args:
            project_id:     Uniek identifier van het klantproject.
            sector:         De sector van het project.
            gevonden_issues: Lijst van technische problemen gevonden in het project.
            gevonden_talen:  Programmeertalen aangetroffen in het project.

        Returns:
            BenchmarkVergelijking met afwijkingen, sterktes en verbeterpunten.
        """
        benchmark = self.get_benchmark(sector)
        typische_issues = set(i.lower() for i in benchmark.technische_schuld.meest_voorkomende_issues)
        typische_talen = set(t.lower() for t in benchmark.technische_schuld.typische_talen)
        gevonden_lower = set(i.lower() for i in gevonden_issues)
        talen_lower = set(t.lower() for t in gevonden_talen)

        # Afwijkingen: issues die NIET typisch zijn voor de sector (project-specifiek)
        afwijkingen: list[str] = [
            issue for issue in gevonden_issues
            if issue.lower() not in typische_issues
        ]

        # Sterktes: typische sector-issues die het project NIET heeft
        sterktes: list[str] = [
            issue for issue in benchmark.technische_schuld.meest_voorkomende_issues
            if issue.lower() not in gevonden_lower
        ]

        # Verbeterpunten: typische sector-issues die het project WEL heeft
        verbeterpunten: list[str] = [
            issue for issue in benchmark.technische_schuld.meest_voorkomende_issues
            if issue.lower() in gevonden_lower
        ]

        # Prioriteit-score: gebaseerd op aantal gevonden issues t.o.v. benchmark-gemiddelde
        overlap_ratio = len(verbeterpunten) / max(len(benchmark.technische_schuld.meest_voorkomende_issues), 1)
        taal_mismatch = len(talen_lower - typische_talen) / max(len(talen_lower), 1) if talen_lower else 0.0
        prioriteit_score = round(
            min(
                benchmark.technische_schuld.gemiddelde_score * overlap_ratio
                + taal_mismatch * 2.0
                + (len(afwijkingen) * 0.3),
                10.0,
            ),
            1,
        )

        logger.info(
            "Benchmark vergelijking voor project '%s' (sector: %s): "
            "%d verbeterpunten, %d sterktes, prioriteit %.1f/10",
            project_id, sector.value, len(verbeterpunten), len(sterktes), prioriteit_score,
        )

        return BenchmarkVergelijking(
            project_id=project_id,
            sector=sector,
            benchmark=benchmark,
            afwijkingen=afwijkingen,
            sterktes=sterktes,
            verbeterpunten=verbeterpunten,
            prioriteit_score=prioriteit_score,
        )

    def genereer_samenvatting(self, vergelijking: BenchmarkVergelijking) -> str:
        """
        Genereer een leesbare Nederlandse samenvatting van de benchmark-vergelijking.

        Geschikt voor opname in een klantrapport of managementsamenvatting.

        Args:
            vergelijking: De BenchmarkVergelijking om samen te vatten.

        Returns:
            Geformatteerde tekst (markdown-compatibel).
        """
        b = vergelijking.benchmark
        v = vergelijking

        regels: list[str] = [
            f"## Sector Benchmark: {b.naam_nl}",
            "",
            f"**Project:** {v.project_id}  ",
            f"**Sector:** {b.naam_nl}  ",
            f"**Urgentie modernisatie:** {v.prioriteit_score:.1f}/10  ",
            "",
            "### Over deze sector",
            b.beschrijving,
            "",
            "### Technische Schuld Profiel",
            f"- Sectorgemiddelde technische schuld: **{b.technische_schuld.gemiddelde_score:.1f}/10**",
            f"- Gemiddelde leeftijd codebase in sector: **{b.technische_schuld.gemiddelde_codebase_leeftijd_jaar:.0f} jaar**",
            f"- Typische talen in sector: {', '.join(b.technische_schuld.typische_talen)}",
            "",
        ]

        if v.sterktes:
            regels.append("### ✅ Sterktes (beter dan sectorgemiddelde)")
            for sterkte in v.sterktes:
                regels.append(f"- {sterkte}")
            regels.append("")

        if v.verbeterpunten:
            regels.append("### ⚠️ Verbeterpunten (conform sector-patronen)")
            for punt in v.verbeterpunten:
                regels.append(f"- {punt}")
            regels.append("")

        if v.afwijkingen:
            regels.append("### 🔴 Project-specifieke issues (buiten sectornorm)")
            for afwijking in v.afwijkingen:
                regels.append(f"- {afwijking}")
            regels.append("")

        regels += [
            "### Aanbevolen Modernisatie",
        ]
        for aanbeveling in b.aanbevolen_modernisatie[:5]:
            regels.append(f"- {aanbeveling}")
        regels.append("")

        regels += [
            "### AI-kansen voor deze sector",
        ]
        for kans in b.ai_kansen[:4]:
            regels.append(f"- {kans}")
        regels.append("")

        regels += [
            "### Compliance vereisten",
            ", ".join(b.compliance_vereisten),
            "",
            "### Verwachte ROI",
            b.roi_schatting,
            "",
        ]

        if b.typische_kpis:
            regels.append("### Typische sector-KPIs")
            for kpi, waarde in b.typische_kpis.items():
                regels.append(f"- **{kpi}**: {waarde}")
            regels.append("")

        return "\n".join(regels)

    def alle_sectoren(self) -> list[Sector]:
        """Geef een lijst van alle beschikbare sectoren terug (exclusief ONBEKEND)."""
        return [s for s in Sector if s != Sector.ONBEKEND]

    def benchmark_overzicht(self) -> dict[str, Any]:
        """
        Geef een compacte overzichtstabel van alle benchmarks.

        Handig voor dashboard-weergave of rapportages.
        """
        return {
            sector.value: {
                "naam_nl": b.naam_nl,
                "gemiddelde_schuld_score": b.technische_schuld.gemiddelde_score,
                "codebase_leeftijd_jaar": b.technische_schuld.gemiddelde_codebase_leeftijd_jaar,
                "compliance_count": len(b.compliance_vereisten),
                "ai_kansen_count": len(b.ai_kansen),
                "roi_schatting": b.roi_schatting,
            }
            for sector, b in _BENCHMARKS.items()
        }


# ─── Module-level singleton ───────────────────────────────────────────────────

_benchmark_engine: SectorBenchmarkEngine | None = None


def get_benchmark_engine() -> SectorBenchmarkEngine:
    """Geef de singleton SectorBenchmarkEngine instantie terug."""
    global _benchmark_engine
    if _benchmark_engine is None:
        _benchmark_engine = SectorBenchmarkEngine()
    return _benchmark_engine
