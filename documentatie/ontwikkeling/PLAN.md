# VorstersNV – Projectplan

## Overzicht

Dit document beschrijft het complete plan voor de VorstersNV applicatie: een zakelijk platform met webshop, aangedreven door lokale AI-agents (via Ollama) en geautomatiseerde webhooks en pipelines.

---

## Plan Modes

Het project werkt met drie **plan-modes** die bepalen in welke fase je werkt:

| Mode | Beschrijving |
|------|-------------|
| `plan` | Ontwerpen van nieuwe features, agent-configuraties en prompt-strategieën |
| `build` | Actieve ontwikkeling, integraties en pipeline-configuratie |
| `review` | Testen, evalueren van agent-output, prompt-iteraties en optimalisatie |

De huidige actieve mode wordt bijgehouden in [`mode.yml`](./mode.yml).

---

## Projectfasen

### Fase 1 – Fundament ✅
- [x] Projectstructuur aanmaken
- [x] Plan-document opstellen
- [x] Agent-definities (YAML) aanmaken
- [x] Prompt-boeken en pre-prompts structureren
- [x] Webhook-handlers (FastAPI) inrichten
- [x] GitHub Actions pipelines configureren
- [x] Ollama lokale AI-integratie opzetten
- [x] Docker Compose voor lokale ontwikkeling

### Fase 2 – Agents & Prompts ✅
- [x] Klantenservice-agent verbeteren met feedback-loop (v1.1 + sub-agents)
- [x] Product-beschrijving agent iteratief optimaliseren (v1.1 + USP + FAQ)
- [x] SEO-agent fine-tunen op webshop-producten (v1.1 + interne linking)
- [x] Order-verwerking agent bouwen (v1.1 + fraude pre-check + batch)
- [x] Sub-agents aanmaken: fraude_detectie, retour_verwerking, email_template, voorraad_advies
- [x] Multi-agent orkestratie implementeren (ParallelStep + 3 workflows)
- [x] Tuple-bug gerepareerd in agent_runner + orchestrator

### Fase 3 – Webshop & Business Logica 🔄 (in uitvoering)

**Voltooid:**
- [x] Orders router volledig verbonden met PostgreSQL (create, list, get, update_status, statistieken)
- [x] Inventory router volledig verbonden met PostgreSQL (overzicht, set, aanpassen, low-stock alerts)
- [x] Notifications router aangemaakt (email_template_agent integratie via AgentLog)
- [x] Dashboard router verbonden met echte DB (KPIs, voorraad alerts, agent scores)
- [x] Webhooks handler voor Mollie betalingsnotificaties
- [x] Fraude detectie sub-agent geïntegreerd in orderverwerking
- [x] Agent logging systeem (AgentLog tabel + rapportage)
- [x] Webshop frontend: `/shop`, `/shop/[slug]`, `/winkelwagen`, `/afrekenen` — volledig geïmplementeerd met SSR, SEO, Zustand cart store, voorraadvalidatie
- [x] Navbar uitgebreid met winkelwagen-icoon + item-badge (cartCount via useCartStore)
- [x] Betaling succes/mock pagina's: `/betaling/succes`, `/betaling/mock`

**Nog te doen — ON HOLD** ⏸

> **Strategische beslissing (2026-04):** Webshop-afwerking is deprioriteit. Huidig focuspunt is **AI-optimalisatie** en **freelance IT/AI-dienstverlening** (Fase 5). De onderstaande sprints blijven gedocumenteerd voor later gebruik.

#### 🔴 P1 — Sprint 1: Navbar & Webshop Afronden (~12u)

- [ ] **b1 – Navbar: `/shop` publieke link + WinkelwagenBadge**
  - [ ] `/shop` toevoegen aan publieke navigatielinks
  - [ ] `WinkelwagenBadge` component met artikelteller (Zustand)
  - [ ] Account-links conditioneel: ingelogd → `/account`, uitgelogd → `/login`

- [ ] **b1b – `/shop` uitbreiden met filtering & sortering**
  - [ ] `FilterBar` component (categoriefilter — horizontale scrolllijst)
  - [ ] `SortDropdown` (nieuwste, prijs laag→hoog, prijs hoog→laag)
  - [ ] URL-state via `useSearchParams` + `router.push`
  - [ ] `ProductGrid` uitbreiden met `?categorie=` en `?sorteer=` params

- [ ] **b1c – `/betaling/bevestiging` pagina** (na Mollie-redirect)
  - [ ] Leest `?bestelling_id=` uit URL, toont bevestiging
  - [ ] Winkelwagen clearen na succesvolle betaling

#### 🟠 P2 — Sprint 2: Mollie Live Betalingsintegratie (~13u)

- [ ] **b2 – Betalingsintegratie Mollie LIVE**
  - [ ] Alembic migration: `mollie_payment_id`, `mollie_checkout_url`, `mollie_betaalmethode` in `orders`
  - [ ] `mollie-api-python` SDK installeren + `MOLLIE_API_KEY` env variable
  - [ ] `/api/bestellingen`: mock betaal-URL vervangen door echte Mollie `payments.create()` call
  - [ ] `webhookUrl` correct instellen (`WEBHOOK_BASE_URL` env variable)
  - [ ] Webhook HMAC-SHA256 verificatie (`X-Mollie-Signature` header)
  - [ ] Webhook: order status updaten + `PaymentSucceededEvent` publiceren
  - [ ] Idempotency check (payment_id al verwerkt → skip)
  - [ ] Test: iDEAL + Bancontact simuleren met Mollie test-mode + ngrok
  - _Vereist: `MOLLIE_API_KEY=test_xxx`, `WEBHOOK_BASE_URL` via ngrok_

#### 🟡 P3 — Sprint 3: Productzoekfunctie (~8u)

- [ ] **b3 – Productzoekfunctie** (full-text search via PostgreSQL)
  - [ ] Alembic migration: `zoek_vector tsvector GENERATED ALWAYS AS (...)` + GIN index
  - [ ] FastAPI: `GET /api/products/search?q=` endpoint (ts_rank sortering)
  - [ ] Frontend: `ZoekBalk` component (300ms debounce, URL-state)
  - [ ] `/shop` routing: `?q=` aanwezig → search endpoint, anders → lijst endpoint
  - _Vereist: Sprint 1 (ProductGrid URL-params)_

#### 🟡 P3 — Sprint 4: Review-systeem (~14u)

- [ ] **b4 – Review-systeem**
  - [ ] Alembic migration: `reviews` tabel (rating CHECK 1-5, unique per klant+product)
  - [ ] `Review` SQLAlchemy model (relaties naar Product + Customer)
  - [ ] FastAPI reviews router: `GET /api/products/{id}/reviews` + `POST`
  - [ ] Sentiment-analyse via `review_analyzer_agent` (async, auto-goedkeuring bij score ≥ 0.7)
  - [ ] Frontend: `StarRating`, `ReviewList` (RSC), `ReviewForm` (Client, alleen als ingelogd)
  - [ ] Integreren in `/shop/[slug]` pagina
  - _Vereist: Sprint 1 (productdetail), NextAuth sessie_

#### 🟢 P4 — Sprint 5: Klantaccountpagina's (~16u)

- [ ] **b5 – Klantaccountpagina's**
  - [ ] Next.js `middleware.ts`: `/account/*` beschermen (redirect naar login)
  - [ ] Alembic migration: `customers` uitbreiden (`nieuwsbrief_opt_in`, `geboorte_datum`)
  - [ ] FastAPI: `GET /api/auth/mij`, `PUT /api/klanten/{id}`, `GET /api/bestellingen?mijn=true`
  - [ ] Frontend: `/account` (profieloverzicht), `/account/profiel` (bewerken), `/account/bestellingen` (tabel)
  - _Vereist: Sprint 2 (echte orders), NextAuth sessie_

#### ⚪ Optioneel

- [ ] **b6 – CRM-koppeling** (afhankelijk van businessbeslissing — _on hold_)

---

### Fase 3b – AI Freelance Platform 🚀 (ACTIEVE FOCUS)

VorstersNV als freelance IT/AI-consultancy voor bedrijven. Drie pijlers:

| Pijler | Wat | Waarde voor klant |
|--------|-----|-------------------|
| **Code Analyse** | Bestaande systemen begrijpen & documenteren | Legacy code leesbaar maken |
| **AI Agents** | Chatbots, automatisering, rapportage | Processen versnellen |
| **Procesautomatisering** | Workflows mappen en optimaliseren | Kosten besparen |

#### 📁 P1 – Diensten Documentatie & Portfolio

- [ ] `documentatie/diensten/DIENSTEN_AANBOD.md` — volledige dienstenbeschrijving (aangemaakt)
- [ ] `/diensten` Next.js pagina uitbreiden met concrete use cases + demo-aanvraagformulier
- [ ] Portfolio case study: loonberekening-analyse als eerste voorbeeld (`documentatie/analyse/`)

#### 🤖 P1 – Claude Agents (Ontwikkelingstools voor consultancy)

- [ ] `code-analyzer.md` — codebase-analyse agent (Java, Python, C#, PHP) voor klantprojecten
- [ ] `business-process-advisor.md` — bedrijfsproces mapping + automatiseringsadvies
- [ ] `it-consultant.md` — IT/AI strategie + presentatiemateriaal genereren voor klanten

#### 🦙 P2 – Ollama Runtime Agents (Klant-gerichte capabilities)

- [ ] `code_analyse_agent.yml` — code analyse en documentatiegeneratie
- [ ] `bedrijfsproces_agent.yml` — BPMN-stijl procesanalyse vanuit beschrijving
- [ ] `klant_rapport_agent.yml` — professionele rapportgeneratie (PDF-klaar markdown)

#### ⚙️ P2 – FastAPI Platform Uitbreidingen

- [ ] `api/routers/analyse.py` — endpoints voor code/document analyse via Ollama
- [ ] `api/routers/rapporten.py` — rapportgeneratie endpoints (markdown → structuur)
- [ ] Rate limiting + API-keys voor klant-facing endpoints (stap naar productisering)

### Fase 4 – Deployment (KMO-realistische aanpak) 🔜

VorstersNV is een KMO. We kiezen eerst voor een **VPS** als eenvoudigere, goedkopere optie.
Google Cloud Run is beschikbaar als schaaloptie zodra het volume dit rechtvaardigt.

**Optie A: VPS Deployment (aanbevolen voor start)**
- [ ] VPS kiezen: Hetzner (€5/maand), DigitalOcean, of OVH
- [ ] Docker Compose in productie configureren (met `.env.production`)
- [ ] Nginx reverse proxy instellen (SSL via Let's Encrypt / Certbot)
- [ ] GitHub Actions deploy workflow aanmaken (`ssh` + `docker-compose pull && up`)
- [ ] PostgreSQL backup strategie (dagelijkse `pg_dump` naar S3/Backblaze)
- [ ] Monitoring instellen (Uptime Robot gratis tier)
- [ ] Custom domein koppelen + SSL certificaat
- [ ] Rollback procedure documenteren

**Optie B: Google Cloud Run (bij groeiend volume)**
- [ ] Google Cloud project aanmaken + APIs inschakelen
- [ ] Artifact Registry repository aanmaken (`europe-west1`)
- [ ] Cloud SQL instantie aanmaken (PostgreSQL 16, `db-f1-micro` — €7/maand)
- [ ] Service account aanmaken voor GitHub Actions (`github-deployer`)
- [ ] GitHub Secrets instellen: `GCP_SA_KEY`, `GCP_PROJECT_ID`, `DB_PASSWORD`
- [ ] Backend deployen naar Cloud Run (automatisch via `deploy.yml`)
- [ ] Frontend deployen naar Vercel (gratis tier) of Cloud Run
- [ ] Cloud Armor WAF configureren (optioneel)

### Fase 5 – AI Fleet & Intelligence 🤖 (ACTIEVE FOCUS)

Uitbreiding van het Ollama AI-ecosysteem voor IT/AI-consultancy en platform-optimalisatie.

#### 🔴 P0 – Ontbrekende Prompt Bestanden (agents werken niet zonder deze)

- [x] `prompts/system/code_analyse_v1.txt` — system prompt code analyse agent
- [x] `prompts/preprompt/code_analyse_v1.yml` — preprompt + context
- [x] `prompts/system/bedrijfsproces_v1.txt` — system prompt bedrijfsproces agent
- [x] `prompts/preprompt/bedrijfsproces_v1.yml` — preprompt + context
- [x] `prompts/system/klant_rapport_v1.txt` — system prompt klantrapport agent
- [x] `prompts/preprompt/klant_rapport_v1.yml` — preprompt + context

#### 🔴 P1 – Consultancy Agent Fleet

- [x] **Consultancy orchestrator** (`agents/consultancy_orchestrator.yml`)
  - Multi-step pipeline: code analyse → bedrijfsrapport → klantrapport
  - Parallel uitvoering van code analyse + procesanalyse
  - Gestructureerde handoff tussen agents via shared context
- [x] **Analyse script** (`scripts/analyse_project.py`)
  - CLI-tool om een externe codebase te analyseren
  - Leest klasse-bestanden, verdeelt in chunks, stuurt naar code_analyse_agent
  - Combineert resultaten tot een volledig rapport (markdown)
  - Getest op lpb_unified_master (loonberekening Java project)

#### 🟠 P2 – Agent Performance Monitoring

- [ ] **Agent monitoring dashboard** (via `/dashboard/agents`)
  - Live scores per agent (volledigheid, leesbaarheid, business-relevantie)
  - Prompt-versie vergelijking via `prompt_iterator.py`
  - Drempelwaarden-alerting (score < 0.6 → notificatie)
- [ ] **A/B testing framework voor prompts**
  - `scripts/prompt_iterator.py` uitbreiden met statistische significantietests
  - Resultaten opslaan in `agent_ab_tests` tabel
  - Dashboard-view voor A/B testresultaten

#### 🟡 P3 – Model Upgrades

- [ ] **codellama model integreren** voor code-specifieke taken
  - `ollama pull codellama` in Docker Compose setup
  - `code_analyse_agent.yml` model upgraden naar codellama
  - Vergelijkingstest: llama3 vs codellama op Java code (lpb_unified_master)
- [ ] **Multi-language support** (NL/FR) voor klantrapport agent
  - mistral ondersteunt FR goed
  - Automatische taaldetectie via preprompt parameter
- [ ] **Webshop agents on hold** ⏸
  - Product-recommender, review-analyzer, checkout-begeleiding
  - Wordt hernomen wanneer webshop (Fase 3) verder gaat

### Fase 6 – IT/AI Consultancy Platform 🚀 (VOLGENDE FOCUS)

VorstersNV als professioneel IT/AI-consultancy platform voor Belgische KMOs.
Webshop blijft on hold — focus op dienstverlening en freelance opdrachten.

#### 🔴 P0 – Analyse-tool productie-klaar maken

- [ ] **Claude API integratie voor code-analyse**
  - Lokale Ollama modellen zijn te traag voor productie (4+ min/chunk)
  - `analyse_project.py` uitbreiden met `--provider claude` optie
  - Claude Sonnet via Anthropic API: ~5s per chunk, veel betere output
  - Fallback: lokale Ollama als Claude API niet beschikbaar
- [ ] **Pre-processor voor grote Java-bestanden**
  - Java-bestanden automatisch reduceren tot signaturen + comments + constanten
  - Input verkleinen van 70KB → ~8KB zonder verlies van businesslogica
  - `scripts/java_extractor.py` bouwen (regex-based, geen AST nodig)

#### 🔴 P1 – Consultancy website

- [ ] **Diensten-pagina afwerken** (`frontend/app/diensten/page.tsx`)
  - Code-analyse als dienst presenteren met concrete voorbeelden
  - Procesanalyse en automatiseringsadvies als dienst
  - Prijsindicatie of "offerte aanvragen" CTA
- [ ] **Portfolio-pagina** met echte case studies
  - LPB loonberekening analyse als anoniem case study
  - Technologie-stack per project visueel maken
  - Resultaten en tijdswinst kwantificeren
- [ ] **Contact/offerte formulier**
  - Koppelen aan email_template_agent voor geautomatiseerde opvolging
  - Lead vastleggen in database (Customer bounded context)

#### 🟠 P2 – Freelance project pipeline

- [ ] **Project intake flow**
  - Klant vult intake-formulier in (tech stack, pijnpunten, doel)
  - `bedrijfsproces_agent` genereert automatisch een AS-IS analyse
  - Output: PDF-rapport klaar voor eerste gesprek
- [ ] **Offerte generator**
  - Op basis van project scope → automatisch offertebedrag berekenen
  - `klant_rapport_agent` maakt professioneel offertedocument
- [ ] **Tijdregistratie en facturatie**
  - Eenvoudige uren bijhouden per klant/project
  - Koppeling met klant-entiteiten in DB

#### 🟡 P3 – Model Upgrades & AI kwaliteit

- [ ] **codellama model downloaden** voor betere code-analyse
  - `ollama pull codellama:7b` (sneller dan llama3.2 voor code)
  - Vergelijkingstest op LPB Java code
- [ ] **Prompt kwaliteitsmonitoring activeren**
  - Agent dashboard scores live tonen
  - Drempelwaarden-alerting (score < 0.6)
- [ ] **Multi-language support** (NL/FR) voor klantrapport agent

---

## Architectuur

```
┌─────────────────────────────────────────────────────────┐
│                    VorstersNV Platform                   │
├──────────────┬──────────────────────┬───────────────────┤
│   Frontend   │      API / Webhooks  │   AI Agents Layer │
│  (Webshop)   │      (FastAPI)       │   (Ollama Local)  │
├──────────────┼──────────────────────┼───────────────────┤
│  - Webshop   │  - REST endpoints    │  - Customer svc   │
│  - Admin UI  │  - Webhook handlers  │  - Product desc   │
│  - Dashboard │  - Pipeline triggers │  - SEO agent      │
│              │  - Order processing  │  - Order agent    │
└──────────────┴──────────────────────┴───────────────────┘
                          │
                ┌─────────┴─────────┐
                │   Ollama (Local)  │
                │  llama3 / mistral │
                │  / codellama      │
                └───────────────────┘
```

---

## Technologiestack

| Laag | Technologie |
|------|-------------|
| Frontend | Next.js / Astro |
| Backend API | FastAPI (Python) |
| Lokale AI | Ollama + llama3 / mistral |
| Agent Framework | Eigen YAML-gebaseerd systeem |
| Webhooks | FastAPI + ngrok (dev) |
| Pipelines | GitHub Actions |
| Database | PostgreSQL + Redis |
| Containerisatie | Docker + Docker Compose |
| Cloud Platform | Google Cloud Run + Cloud SQL |

---

## Hoe te starten

```bash
# 1. Kloon het project
git clone https://github.com/koenvorster/Personal_project_VorstersNV

# 2. Installeer afhankelijkheden
pip install -r requirements.txt

# 3. Start Ollama lokaal
ollama pull llama3
ollama pull mistral

# 4. Start alle services via Docker Compose
docker-compose up -d

# 5. Wissel van plan-mode
python scripts/set_mode.py --mode build
```

---

## Plan-mode wijzigen

```bash
# Bekijk huidige mode
python scripts/set_mode.py --status

# Zet op plan-mode
python scripts/set_mode.py --mode plan

# Zet op build-mode
python scripts/set_mode.py --mode build

# Zet op review-mode
python scripts/set_mode.py --mode review
```
