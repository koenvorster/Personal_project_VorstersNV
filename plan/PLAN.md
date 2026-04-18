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
- [x] Orders router volledig verbonden met PostgreSQL (create, list, get, update_status, statistieken)
- [x] Inventory router volledig verbonden met PostgreSQL (overzicht, set, aanpassen, low-stock alerts)
- [x] Notifications router aangemaakt (email_template_agent integratie via AgentLog)
- [x] Dashboard router verbonden met echte DB (KPIs, voorraad alerts, agent scores)
- [ ] Webshop frontend (Next.js): /shop, /shop/[slug], /winkelwagen, /afrekenen
- [ ] Navbar uitbreiden met /shop + winkelwagen-icoon
- [ ] Betalingsintegratie Mollie (echte API-aanroep, nu mock)
- [ ] CRM-koppeling

### Fase 4 – Cloud Deployment (Google Cloud Run)
- [ ] Google Cloud project aanmaken + APIs inschakelen
- [ ] Artifact Registry repository aanmaken (`europe-west1`)
- [ ] Cloud SQL instantie aanmaken (PostgreSQL 16, `db-f1-micro`)
- [ ] Service account aanmaken voor GitHub Actions (`github-deployer`)
- [ ] GitHub Secrets instellen: `GCP_SA_KEY`, `GCP_PROJECT_ID`, `DB_PASSWORD`
- [ ] Backend deployen naar Cloud Run (automatisch via `deploy.yml` bij push naar `main`)
- [ ] Frontend deployen naar Cloud Run (automatisch via `deploy.yml` bij push naar `main`)
- [ ] Custom domein koppelen (optioneel)

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
