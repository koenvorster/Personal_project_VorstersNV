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

### Fase 2 – Agents & Prompts
- [ ] Klantenservice-agent verbeteren met feedback-loop
- [ ] Product-beschrijving agent iteratief optimaliseren
- [ ] SEO-agent fine-tunen op webshop-producten
- [ ] Order-verwerking agent bouwen
- [ ] Multi-agent orkestratie implementeren

### Fase 3 – Webshop & Business Logica
- [ ] Webshop frontend (Next.js of Astro)
- [ ] Product- en voorraad-backend (FastAPI)
- [ ] Betalingsintegratie (Mollie / Stripe)
- [ ] CRM-koppeling
- [ ] Agent-gestuurde e-mail en notificaties

### Fase 4 – Optimalisatie & Productie
- [ ] Monitoring & logging dashboard
- [ ] A/B-testen van prompts
- [ ] Automatische prompt-verbetering via feedback
- [ ] Productie-deployment (Docker / Kubernetes)
- [ ] CI/CD volledig geautomatiseerd

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
