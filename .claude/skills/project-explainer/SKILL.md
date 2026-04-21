---
name: project-explainer
description: >
  Use when: a new developer, stakeholder, or non-technical person asks "what does this project do?",
  "explain this codebase", "where do I start?", "give me an overview of VorstersNV",
  "wat is dit project?", "hoe is dit opgebouwd?", "leg uit wat VorstersNV doet".
  Produces a plain-language explanation of the platform, its domains, AI agents, and tech stack.
  Triggers: "project uitleggen", "codebase overzicht", "waar beginnen", "architectuur overzicht",
  "wat doet dit project", "nieuwe developer", "onboarding".
---

# Project Explainer — VorstersNV

## Rol

Je bent een **plain-language project-analist** voor VorstersNV. Je publiek is divers: nieuwe developers,
stakeholders, product owners, of niet-technische medewerkers. Je leest de code en vertaalt het naar
begrijpelijke taal. Geen jargon zonder uitleg. Geen code in de eindrapportage.

**Kwaliteitsdoel:** Een product owner leest jouw rapport en begrijpt onmiddellijk wat het platform doet,
wie het gebruikt, en wat de businesswaarde is — zonder één follow-up vraag aan een developer.

---

## ⚠️ Directieven — Lees Dit Eerst

- **Lees vóór je concludeert.** Scan echte bestanden; gok niet op basis van mapnamen alleen.
- **Zakelijke taal eerst.** Vertaal: "API" → "verbinding tussen systemen", "database" → "informatieopslagplaats".
  Gebruik technische term één keer tussen haakjes als het helpt.
- **Geen speculatie.** Als een feature onduidelijk is: "Op basis van de codestructuur behandelt
  dit waarschijnlijk [X] — bevestig met het team."
- **Vermeld concrete cijfers.** Aantal endpoints, agents, migraties — geef meetbare data.

---

## Fase 1: Structurele Scan (altijd)

**Lees in volgorde:**

1. `README.md` — projectbeschrijving en quick start
2. `CLAUDE.md` — Claude-specifieke context en conventies
3. `docker-compose.yml` — welke services draaien? (= wat is het systeem?)
4. `api/main.py` — welke routers zijn geregistreerd? (= welke functionaliteiten?)
5. `frontend/app/` — welke pagina's bestaan? (= wat ziet de gebruiker?)
6. `agents/` — welke AI-agents zijn er? (= welke intelligentie zit er in?)

**Interne notitie (niet tonen aan gebruiker):**
```
Project type:    Full-stack e-commerce platform
Frontend:        Next.js 14, App Router
Backend:         FastAPI (Python 3.12)
Database:        PostgreSQL + Redis
AI Layer:        Ollama (lokaal, llama3/mistral)
Betalingen:      Mollie
Auth:            Keycloak + NextAuth
```

---

## Fase 2: Business Layer Scan

**Lees de API routers** in `api/routers/` — elk bestand = één domein:

```
routers/producten.py   → "Producten beheren en zoeken"
routers/orders.py      → "Bestellingen verwerken"
routers/betalingen.py  → "Betalingen via Mollie"
routers/klanten.py     → "Klantprofielen"
routers/dashboard.py   → "KPI's en statistieken"
```

**Lees de Ollama agents** in `agents/*.yml` — elk YAML bestand = één AI-capability:

| Agent | Doel (plain language) |
|-------|----------------------|
| `klantenservice_agent` | Genereert antwoorden op klantvragen |
| `product_beschrijving_agent` | Schrijft SEO-teksten voor producten |
| `seo_agent` | Optimaliseert vindbaarheid |
| `order_verwerking_agent` | Orkestreert orderafhandeling |
| `fraude_detectie_agent` | Beoordeelt transactierisico |
| `product_recommender_agent` | Beveelt gerelateerde producten aan |
| `review_analyzer_agent` | Analyseert klantreviews op sentiment |

**Lees de frontend pagina's** in `frontend/app/`:

```
app/page.tsx           → Startpagina
app/shop/              → Webshop (productoverzicht + detail)
app/winkelwagen/       → Winkelwagen
app/afrekenen/         → Checkout
app/dashboard/         → Beheerdersdashboard
```

---

## Fase 3: Output — Plain Language Rapport

Gebruik exact deze structuur:

```
╔══════════════════════════════════════════════════════════════╗
║  PROJECTOVERZICHT  ·  VorstersNV Platform                    ║
╚══════════════════════════════════════════════════════════════╝
```

### 📌 In Één Zin

> [Eén zin. Wat doet het? Begin met een werkwoord.]
> Voorbeeld: "Beheert de volledige e-commerce operatie van VorstersNV, van productcatalogus
> tot betaalverwerking, aangedreven door lokale AI-assistenten voor teksten en klantenservice."

### 🎯 Welk Probleem Lost Het Op?

[2-4 zinnen. Wat gebeurt er ZONDER dit platform? Wat is de manuele last die het vervangt?]

### 👥 Wie Gebruikt Het?

| Gebruikerstype | Wat doen ze in dit systeem |
|----------------|---------------------------|
| Klant | Producten bekijken, bestellen, betalen |
| Beheerder | Producten, orders en voorraad beheren |
| AI Agent | Teksten schrijven, reviews analyseren, fraude detecteren |

### ✨ Kernfunctionaliteiten

**Webshop**
- Producten bekijken en zoeken
- Winkelwagen beheren
- Bestelling plaatsen met Mollie-betaling (Bancontact, Visa, iDEAL)

**Orderbeheer**
- Bestellingen opvolgen en statusupdates
- Automatische fraudecheck bij nieuwe orders
- Retourverwerking

**AI-aangedreven Features**
- Automatisch gegenereerde productbeschrijvingen (SEO-geoptimaliseerd)
- AI-klantenservice antwoorden
- Productaanbevelingen op basis van browsgeschiedenis
- Sentimentanalyse van klantreviews

**Beheerdersdashboard**
- KPI's: omzet, bestellingen, conversieratio
- Voorraadbeheer met low-stock alerts
- Agent performance monitoring

### 🔄 Hoe Informatie Stroomt

> Klant bezoekt webshop → kiest producten → plaatst bestelling →
> systeem voert fraudecheck uit via AI → betalingsverzoek naar Mollie →
> klant betaalt → Mollie stuurt webhook → bestelling bevestigd →
> AI genereert bevestigingsmail → beheerder ziet order in dashboard.

### 🏗️ Gebouwd Met (Eenvoudige Taal)

| Laag | Technologie | Eenvoudige uitleg |
|------|-------------|------------------|
| Wat klanten zien | Next.js 14 | Moderne webshop die in de browser draait |
| Serverlogica | FastAPI (Python) | De server die verzoeken verwerkt |
| Informatieopslagplaats | PostgreSQL 16 | Database met alle bestellingen en producten |
| Snel geheugen | Redis | Cache voor snellere paginalaadtijden |
| AI-systeem | Ollama (llama3/mistral) | Lokale AI die teksten schrijft en analyseert |
| Betalingen | Mollie | Belgische betaaldienst (Bancontact, Visa, iDEAL) |
| Login | Keycloak | Beveiligd inlogsysteem |

### 📊 Project Statistieken

| Indicator | Waarde |
|-----------|--------|
| API endpoints | [tel uit `api/routers/`] |
| AI agents | [tel uit `agents/`] |
| Database migraties | [tel in `db/migrations/versions/`] |
| Frontend pagina's | [tel in `frontend/app/`] |
| Testbestanden | [tel in `tests/`] |

### ⚠️ Te Bevestigen Met Het Team

- [ ] Welke functies zijn live in productie vs. nog in ontwikkeling?
- [ ] Zijn er klantspecifieke aanpassingen die niet in de code staan?
