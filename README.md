<div align="center">

# 🚀 VorstersNV Platform

**Full-stack AI-powered webshop & business platform — gebouwd door Koen Vorsters**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=nextdotjs)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![Ollama](https://img.shields.io/badge/Ollama-AI%20Local-black?logo=ollama)](https://ollama.ai)
[![Tests](https://img.shields.io/badge/Tests-42%20passing-brightgreen?logo=pytest)](tests/)
[![License](https://img.shields.io/badge/License-Privé-red)](LICENSE)

</div>

---

## 📋 Inhoudsopgave

- [Over het project](#-over-het-project)
- [Screenshots](#-screenshots)
- [Architectuur](#-architectuur)
- [Technologiestack](#-technologiestack)
- [AI-agents](#-ai-agents)
- [Hoe het werkt](#-hoe-het-werkt)
- [Snel starten](#-snel-starten)
- [API documentatie](#-api-documentatie)
- [Projectstructuur](#-projectstructuur)

---

## 🧭 Over het project

VorstersNV is een volledig zelfgebouwd bedrijfsplatform voor een KMO-webshop. Het combineert moderne web-development met lokale AI (via [Ollama](https://ollama.ai)) om bedrijfsprocessen zoals orderverwerking, klantenservice en productbeschrijvingen te automatiseren — **volledig zonder externe AI-API's**.

**Kernfunctionaliteit:**

| Functie | Beschrijving |
|---------|-------------|
| 🌐 **Portfolio & website** | Persoonlijke portfolio met projecten, blog en over-mij |
| 📊 **Live dashboard** | Real-time monitoring van alle services, AI-agents en logs |
| 🤖 **AI-agents** | 8 lokale AI-agents voor klantenservice, SEO, productbeschrijvingen en orderverwerking |
| 🛍️ **Webshop backend** | FastAPI REST API met producten, orders, voorraad en Mollie betalingen |
| 🔐 **SSO Authenticatie** | Keycloak single sign-on met JWT tokens |
| 📬 **Webhooks** | Real-time order- en betaalverwerking via HMAC-beveiligde webhooks |

---

## 📸 Screenshots

> **💡 Tip:** Voeg hier je eigen screenshots toe door ze te uploaden naar de `docs/screenshots/` map en de links hieronder te vervangen.

### 🏠 Homepage — Portfolio Landing

```
┌─────────────────────────────────────────────────────────────────┐
│  🔷 Koen Vorsters                    Home  Projecten  Dashboard │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│         Full-Stack Developer                                      │
│         AI Engineer & IoT Specialist                             │
│                                                                   │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│   │  4+      │  │  15+     │  │  9+      │  │  ∞       │       │
│   │  Jaar    │  │ Projecten│  │ Techno-  │  │ Passie   │       │
│   │ ervaring │  │          │  │ logieën  │  │ voor tech│       │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                   │
│   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│   │ 🧠 Full-Stack│ │ 🤖 AI / ML  │ │ 📡 IoT       │             │
│   │ Development │ │ Integration │ │ & Embedded   │             │
│   └─────────────┘ └─────────────┘ └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

> 📷 Vervang dit door: `![Homepage](docs/screenshots/homepage.png)`

---

### 📊 Live Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│  System Dashboard                              ↻ Refresh        │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│ Uptime       │ Services     │ AI Runs      │ Aktieve Agents     │
│ 14d 7h 23m   │ 5/6 online   │ 1,065        │ 3 / 4              │
├──────────────┴──────────────┴──────────────┴────────────────────┤
│ Services                          │ AI Agents                   │
│  ✅ FastAPI Backend   :8000  12ms │  🤖 Klantenservice  actief  │
│  ✅ PostgreSQL        :5432   3ms │  🤖 Product Beschr. actief  │
│  ✅ Redis Cache       :6379   1ms │  💤 SEO Agent       standby │
│  ✅ Keycloak Auth     :8080  45ms │  🤖 Order Verwerking actief │
│  ❌ Ollama LLM        :11434  —   │                             │
│  ✅ Webhook Engine    :9000   8ms │                             │
├───────────────────────────────────┴─────────────────────────────┤
│ 14:32:01  [INFO]  Webhook ontvangen: order.created              │
│ 14:31:45  [INFO]  Agent run voltooid: klantenservice (324ms)    │
│ 14:30:12  [WARN]  Redis cache miss ratio > 15%                  │
│ 14:28:33  [ERROR] Ollama LLM: connection refused op poort 11434 │
└─────────────────────────────────────────────────────────────────┘
```

> 📷 Vervang dit door: `![Dashboard](docs/screenshots/dashboard.png)`

---

### 🗂️ Projecten pagina

```
┌─────────────────────────────────────────────────────────────────┐
│  Mijn Projecten                                                  │
│  [ Alle ] [ Full-Stack ] [ AI/ML ] [ IoT ] [ DevOps ]           │
│  🔍 Zoek projecten...                                            │
├───────────────────┬─────────────────────┬───────────────────────┤
│ 🖥️ VorstersNV     │ 🧠 AI Orchestrator   │ 📡 IoT Pipeline       │
│ Platform          │                     │                       │
│ Full-stack + AI   │ Lokale LLM agents   │ MQTT + Cloud          │
│ [Python][Docker]  │ [Python][Ollama]    │ [IoT][Embedded]       │
│ ● Actief          │ ● Actief            │ ✓ Afgerond            │
├───────────────────┴─────────────────────┴───────────────────────┤
```

> 📷 Vervang dit door: `![Projecten](docs/screenshots/projecten.png)`

---

### 🔐 Login — Keycloak SSO

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                   │
│              🔷 VorstersNV                                        │
│                                                                   │
│         ┌─────────────────────────────────┐                      │
│         │  Welkom terug                   │                      │
│         │  Meld je aan bij je account     │                      │
│         │                                 │                      │
│         │  Email ________________________ │                      │
│         │  Wachtwoord ____________________ │                     │
│         │                                 │                      │
│         │  [ Aanmelden via Keycloak SSO ] │                      │
│         └─────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

> 📷 Vervang dit door: `![Login](docs/screenshots/login.png)`

---

### 📖 API Documentatie (Swagger UI)

```
┌─────────────────────────────────────────────────────────────────┐
│  VorstersNV API  v1.0.0            localhost:8000/docs           │
├─────────────────────────────────────────────────────────────────┤
│  🛍️ products                                             ▼      │
│     GET  /api/products           Lijst van producten            │
│     POST /api/products           Nieuw product aanmaken         │
│  📦 orders                                               ▼      │
│     GET  /api/orders/{id}        Order ophalen                  │
│     POST /api/orders             Order aanmaken                 │
│  📊 inventory                                            ▼      │
│     GET  /api/inventory/levels   Voorraadniveaus                │
│  🤖 dashboard                                            ▼      │
│     GET  /api/dashboard/agents   AI-agent statussen             │
└─────────────────────────────────────────────────────────────────┘
```

> 📷 Vervang dit door: `![Swagger](docs/screenshots/swagger.png)`

---

## 🏛️ Architectuur

```mermaid
graph TB
    subgraph Frontend["🌐 Frontend — Next.js 16"]
        UI[Portfolio / Webshop UI]
        DASH[Live Dashboard]
        LOGIN[Login — NextAuth + Keycloak]
    end

    subgraph Backend["⚙️ Backend — FastAPI"]
        API[REST API :8000]
        WH[Webhook Engine :9000]
    end

    subgraph AI["🤖 AI Laag — Ollama"]
        ORCH[Agent Orchestrator]
        KS[klantenservice_agent]
        OV[order_verwerking_agent]
        PB[product_beschrijving_agent]
        SEO[seo_agent]
        FD[fraude_detectie_agent]
        RV[retour_verwerking_agent]
        ET[email_template_agent]
        VA[voorraad_advies_agent]
    end

    subgraph Infra["🗄️ Infrastructuur — Docker Compose"]
        PG[(PostgreSQL 16)]
        RD[(Redis 7)]
        KC[Keycloak SSO]
        OL[Ollama LLM]
    end

    subgraph External["🔗 Externe Services"]
        MOLLIE[Mollie Betalingen]
        GH[GitHub]
    end

    UI --> API
    DASH --> API
    LOGIN --> KC
    API --> PG
    API --> RD
    API --> ORCH
    WH --> ORCH
    ORCH --> KS & OV & PB & SEO
    OV --> FD & ET & VA
    KS --> RV & ET & FD
    OL --> KS & OV & PB & SEO & FD & RV & ET & VA
    API --> MOLLIE
    WH --> |"HMAC-beveiligd"| MOLLIE
```

---

### Dataflow — Order verwerking

```mermaid
sequenceDiagram
    participant K as Klant
    participant FE as Next.js
    participant API as FastAPI
    participant WH as Webhook Engine
    participant ORCH as Orchestrator
    participant FD as fraude_detectie
    participant OV as order_verwerking
    participant ET as email_template
    participant DB as PostgreSQL

    K->>FE: Bestelling plaatsen
    FE->>API: POST /api/orders
    API->>DB: Order opslaan
    API->>WH: order.created event
    WH->>ORCH: run_order_with_fraud_check_workflow()
    ORCH->>FD: Fraude-risico beoordelen
    FD-->>ORCH: risicoscore + aanbeveling
    ORCH->>OV: Order valideren en verwerken
    OV-->>ORCH: Bevestiging
    ORCH->>ET: Orderbevestiging genereren
    ET-->>ORCH: E-mail inhoud
    ORCH-->>API: Workflow resultaat
    API-->>K: Bevestigingsmail + orderstatus
```

---

## 🛠️ Technologiestack

| Laag | Technologie | Doel |
|------|-------------|------|
| **Frontend** | Next.js 16, React 19, TypeScript | UI & portfolio |
| **Styling** | Tailwind CSS v4, Framer Motion | Animaties & glassmorphism design |
| **Auth (FE)** | NextAuth.js + Keycloak | SSO login |
| **Backend** | FastAPI, Python 3.12, async | REST API |
| **Database** | PostgreSQL 16, SQLAlchemy, Alembic | Data & migraties |
| **Cache** | Redis 7 | Performance caching |
| **Auth (BE)** | Keycloak + JWT | Toegangscontrole |
| **Betalingen** | Mollie | iDEAL, creditcard, Bancontact |
| **AI/LLM** | Ollama, LLaMA 3, Mistral | Lokale AI inference |
| **Containers** | Docker Compose | Lokale & productie-omgeving |
| **CI/CD** | GitHub Actions | Tests & linting |
| **Code kwaliteit** | Ruff, mypy, pytest | Linting & type checks |

---

## 🤖 AI-agents

Het platform bevat **8 AI-agents** die volledig lokaal draaien via Ollama.

### Parent agents

| Agent | Model | Temperatuur | Rol |
|-------|-------|-------------|-----|
| `klantenservice_agent` | llama3 | 0.4 | Klantvragen, orders, escalaties |
| `order_verwerking_agent` | llama3 | 0.1 | Ordervalidatie, facturen, notificaties |
| `product_beschrijving_agent` | mistral | 0.7 | SEO-teksten, USP's, FAQ |
| `seo_agent` | mistral | 0.5 | Keywords, meta-tags, schema markup |

### Sub-agents (nieuw)

| Sub-agent | Model | Triggered door | Doel |
|-----------|-------|----------------|------|
| `fraude_detectie_agent` | llama3 | order_verwerking, klantenservice | Risicoscore 0–100, fraude-signalen detecteren |
| `retour_verwerking_agent` | llama3 | klantenservice, order_verwerking | Retouren beoordelen + terugbetalingen |
| `email_template_agent` | mistral | klantenservice, order, retour | Klantgerichte e-mails schrijven |
| `voorraad_advies_agent` | mistral | order_verwerking | ABC-analyse, besteladvies, stockout alerts |

### Agent workflow — Fraude-check bij nieuwe order

```
order.created
     │
     ▼
┌─────────────────────┐
│ fraude_detectie     │  → risicoscore berekenen
│ (llama3, temp=0.1)  │  → signalen detecteren
└────────┬────────────┘
         │ score ≤ 60: doorgaan
         ▼
┌─────────────────────┐
│ order_verwerking    │  → order valideren
│ (llama3, temp=0.1)  │  → factuur genereren
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ email_template      │  → orderbevestiging schrijven
│ (mistral, temp=0.6) │  → verzenden via /api/notifications
└─────────────────────┘
```

### Prompt iteratie systeem

Alle agent-interacties worden gelogd in `logs/<agent_naam>/`. Feedback (rating 1–5) wordt bijgehouden zodat prompts systematisch verbeterd kunnen worden:

```python
from ollama.prompt_iterator import PromptIterator

iterator = PromptIterator("klantenservice_agent")

# Voeg feedback toe aan een interactie
iterator.add_feedback(interaction_id, rating=4, notes="Goed antwoord maar te lang")

# Analyseer alle feedback
stats = iterator.analyse_feedback()
# → {"gemiddelde_score": 3.8, "lage_scores": 2, "verbeter_suggesties": [...]}
```

---

## ⚙️ Hoe het werkt

### 1. Frontend — Next.js App Router

De frontend gebruikt Next.js 16 met App Router. Server Components voor statische pagina's, Client Components waar animaties of state nodig zijn.

```
frontend/app/
├── page.tsx              → Homepage (portfolio landing)
├── projecten/            → Projectenoverzicht + detail per slug
├── over-mij/             → CV, skills, tijdlijn
├── blog/                 → Blog artikelen
├── dashboard/            → Live system monitoring
└── login/                → Keycloak SSO login
```

**Glassmorphism design** via Tailwind CSS:
```tsx
// GlassCard component
<div className="backdrop-blur-md bg-white/5 border border-white/10 rounded-2xl p-6">
  {children}
</div>
```

---

### 2. Backend — FastAPI

De API heeft 6 routers, Swagger UI op `/docs` en CORS voor de Next.js frontend.

```
api/routers/
├── products.py    → GET/POST/PUT/DELETE /api/products
├── orders.py      → Order CRUD + status updates
├── inventory.py   → Voorraadniveaus + low-stock alerts
├── betalingen.py  → Mollie betaalintegratie
├── auth.py        → Token validatie + user info
└── dashboard.py   → Service health + agent statistieken
```

**Voorbeeld — product aanmaken met AI-beschrijving:**
```python
POST /api/products
{
  "naam": "Industriële sensor kit",
  "categorie": "elektronica",
  "kenmerken": ["IP67", "Bluetooth 5.0", "±0.1°C nauwkeurigheid"],
  "doelgroep": "industrieel",
  "tone_of_voice": "technisch"
}
# → AI genereert automatisch titel, beschrijving, SEO-tags, USP's en FAQ
```

---

### 3. Webhook Engine

Beveiligde webhook endpoints met HMAC-SHA256 verificatie. Triggered door Mollie en interne events.

```
/webhooks/
├── order-created    → fraude check + bevestigingsmail
├── order-paid       → factuur genereren + verzending starten
├── order-shipped    → track & trace notificatie
├── order-returned   → retour workflow starten
└── order-cancelled  → voorraad terugboeken
```

Elke webhook verifieert de handtekening:
```python
# HMAC-SHA256 verificatie
expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
assert hmac.compare_digest(f"sha256={expected}", signature)
```

---

### 4. Database — PostgreSQL + Alembic

Async SQLAlchemy met Alembic voor migraties.

```bash
# Nieuwe migratie aanmaken
alembic revision --autogenerate -m "add product table"

# Migraties uitvoeren
alembic upgrade head
```

---

## 🚀 Snel starten

### Vereisten

- Docker & Docker Compose
- Python 3.12+
- Node.js 20+
- [Ollama](https://ollama.ai) (voor lokale AI)

### 1. Repository klonen

```bash
git clone https://github.com/koenvorster/Personal_project_VorstersNV.git
cd Personal_project_VorstersNV
```

### 2. Omgevingsvariabelen instellen

```bash
cp .env.example .env
# Pas de waarden aan in .env
```

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3
WEBHOOK_SECRET=verander-dit-in-productie
DB_URL=postgresql+asyncpg://vorstersNV:wachtwoord@localhost:5432/vorstersNV
REDIS_URL=redis://localhost:6379
KEYCLOAK_URL=http://localhost:8080
```

### 3. Services starten met Docker

```bash
docker-compose up -d
```

Dit start:
| Service | Poort | Beschrijving |
|---------|-------|-------------|
| FastAPI backend | `:8000` | REST API + Swagger |
| Webhook engine | `:9000` | Event verwerking |
| PostgreSQL | `:5432` | Database |
| Redis | `:6379` | Cache |
| Keycloak | `:8080` | SSO authenticatie |

### 4. AI-modellen downloaden

```bash
ollama pull llama3
ollama pull mistral
```

### 5. Database migraties

```bash
pip install -r requirements.txt
alembic upgrade head
```

### 6. Frontend starten

```bash
cd frontend
npm install
npm run dev   # → http://localhost:3000
```

### 7. Agents testen

```bash
python scripts/test_agent.py --agent klantenservice_agent --input "Waar is mijn bestelling?"
```

---

## 📖 API documentatie

Na het starten van de backend:

| URL | Beschrijving |
|-----|-------------|
| `http://localhost:8000/docs` | Swagger UI — interactieve API docs |
| `http://localhost:8000/redoc` | ReDoc — leesbare API referentie |
| `http://localhost:8000/health` | Health check endpoint |
| `http://localhost:8000/openapi.json` | OpenAPI schema |

---

## 📁 Projectstructuur

```
Personal_project_VorstersNV/
├── agents/                  # YAML-configuraties per AI-agent (8 agents)
│   ├── klantenservice_agent.yml
│   ├── order_verwerking_agent.yml
│   ├── product_beschrijving_agent.yml
│   ├── seo_agent.yml
│   ├── fraude_detectie_agent.yml   # Sub-agent
│   ├── retour_verwerking_agent.yml # Sub-agent
│   ├── email_template_agent.yml    # Sub-agent
│   └── voorraad_advies_agent.yml   # Sub-agent
├── ollama/                  # Lokale AI-integratie
│   ├── client.py            # HTTP-client voor Ollama
│   ├── agent_runner.py      # Laadt YAML + voert agents uit
│   ├── orchestrator.py      # Multi-agent workflows
│   └── prompt_iterator.py   # Prompt-versies + feedback
├── api/                     # FastAPI backend
│   ├── main.py              # App + CORS + Swagger
│   └── routers/             # products, orders, inventory, auth, betalingen
├── webhooks/                # Webhook handlers
│   ├── app.py               # HMAC-verificatie + routing
│   └── handlers/            # order, payment, inventory handlers
├── db/                      # Database laag
│   ├── models/              # SQLAlchemy ORM modellen
│   └── migrations/          # Alembic migratie bestanden
├── frontend/                # Next.js 16 webshop & portfolio
│   ├── app/                 # App Router pages
│   └── components/          # Herbruikbare UI componenten
├── prompts/                 # AI-prompt bestanden
│   ├── system/              # System prompts per agent
│   └── prepromt/            # Pre-prompts + iteratie-logs
├── tests/                   # Pytest test suite (42 tests)
├── scripts/                 # Hulpscripts (setup, test, mode)
├── docker-compose.yml       # Alle services in één commando
└── pyproject.toml           # Ruff + mypy + pytest configuratie
```

---

## 🧪 Tests uitvoeren

```bash
# Alle tests
pytest tests/ -v

# Met coverage
pytest tests/ --cov=. --cov-report=html

# Specifieke module
pytest tests/test_agents.py -v
```

**Huidige testdekking:** 42 tests — webhooks, agent runner, prompt iteratie, YAML-validatie.

---

## 👤 Over de ontwikkelaar

**Koen Vorsters** — Full-Stack Developer, AI Engineer & IoT Specialist

- 🎓 Thomas More — Electronica ICT IoT (2019–2022)
- 💼 Product Engineer (2022–heden)
- 🚀 AI & IT Consulting voor KMO's

[![GitHub](https://img.shields.io/badge/GitHub-koenvorster-181717?logo=github)](https://github.com/koenvorsters)

---

<div align="center">

*Gebouwd met ❤️ en lokale AI door Koen Vorsters*

</div>
