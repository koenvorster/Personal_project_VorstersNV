# 📚 VorstersNV — Documentatie Index

> Centrale index van alle projectdocumentatie. Elke map heeft een specifiek doel.
> **AI Masterplan:** `AI_OPTIMALISATIEPLAN_REVISIE5.TXT` (Revisie 5 — actief)

---

## 📁 Mappenstructuur

```
documentatie/
├── architectuur/     ← Technische architectuur & AI-design
├── ontwikkeling/     ← Developer guides, how-to's & projectplan
├── analyse/          ← Externe analyses (loonschalen, loonberekening, hardware)
├── diensten/         ← Dienstenaanbod & klantcommunicatie
├── marketing/        ← Externe communicatie & LinkedIn content
└── archief/          ← Verouderde documentatie (ter referentie)
```

---

## 🏗️ architectuur/

Technische architectuurdocumenten van het VorstersNV platform.

| Bestand | Beschrijving |
|---------|-------------|
| `ARCHITECTURE.md` | Volledige systeemarchitectuur — bounded contexts, tech stack, DDD-lagen |
| `AGENT_BASED_PLAN.md` | Agent-gebaseerd uitvoeringsplan Fase 3–5 — workflows per use case |
| `ORCHESTRATION_ARCHITECTURE.md` | Agent orchestratie architectuur — event flow, orchestrator patronen |
| `AGENT_COMMUNICATION.md` | Inter-agent communicatieprotocollen & datacontracten |
| `AGENT_PLAN_COMPLETE.md` | Compleet overzicht van alle agents, sub-agents en hun rollen |

---

## 🤖 AI Optimalisatieplannen

| Bestand | Revisie | Status | Beschrijving |
|---------|---------|--------|-------------|
| `AI_OPTIMALISATIEPLAN_REVISIE5.TXT` | **Revisie 5** | ✅ **Actief** | Enterprise Consultancy Intelligence Fabriek — 15 nieuwe gaps (G-32..G-46), Waves 6–8, EU AI Act |
| `AI_OPTIMALISATIEPLAN.TXT` | Revisie 4 | 📦 Archief | AI Control Platform strategie — 31 gaps (G-01..G-31), Waves 1–5 |

> **Gebruik Revisie 5** als primaire referentie. Revisie 4 blijft bewaard voor historische context.

---

## 🛠️ ontwikkeling/

Handleidingen en referentiedocumenten voor ontwikkelaars.

| Bestand | Beschrijving |
|---------|-------------|
| `PLAN.md` | Projectplan met fases, mode-beheer (plan/build/review) en voortgang |
| `HOW_TO_AI_WEBSHOP.md` | Stap-voor-stap gids: van nul naar AI-aangedreven webshop |
| `HOW_TO_AGENTS.md` | Hoe agents werken, aanroepen en uitbreiden |
| `MASTER_AGENT_PROMPTS_GUIDE.md` | Referentiegids voor agent-prompts en prompt-engineering |
| `ENV_VARIABELEN.txt` | Overzicht van omgevingsvariabelen en configuratie |

---

## 📊 analyse/

Externe analyses en onderzoeksmateriaal.

| Bestand | Beschrijving |
|---------|-------------|
| `AI_FLEET_KOSTEN_BATEN_ANALYSE.md` | Kosten/baten analyse van de AI agent fleet |
| `HARDWARE_ANALYSE_LLM.md` | Hardware-analyse voor lokale LLM inferentie (CPU vs GPU) |
| `LOKALE_SETUP_WCS_LIMA.md` | Lokale setup-analyse WCS Lima klantproject |
| `LOONBEREKENING_KRITISCHE_ANALYSE.md` | Kritische analyse loonberekeningssysteem |
| `LOONSCHALEN_ANALYSE.txt` | Analyse van loonschalen (extern loonberekeningproject) |
| `LOONBEREKENING_ANALYSE.txt` | Technische analyse loonberekeningssysteem |

---

## 🏢 diensten/

Dienstenaanbod en klantdocumentatie.

| Bestand | Beschrijving |
|---------|-------------|
| `DIENSTEN_AANBOD.md` | Overzicht van IT/AI consultancy diensten van VorstersNV |

---

## 📣 marketing/

Externe communicatie en marketingmateriaal.

| Bestand | Beschrijving |
|---------|-------------|
| `LINKEDIN_POST.md` | LinkedIn post over het VorstersNV project |

---

## 📋 Overige documenten (root van documentatie/)

| Bestand | Beschrijving |
|---------|-------------|
| `BACKEND_SECURITY_AUDIT.md` | Security audit van de FastAPI backend |
| `PRODUCTIE_GEREED_ANALYSE_PLAN.md` | Analyse en plan voor productie-gereedheid |

---

## 🗄️ archief/

Verouderde documenten die bewaard blijven ter historische referentie. **Niet gebruiken voor actieve ontwikkeling.**

Bevat onder andere:
- Oude FASE_4 documentatie (Smart Home, Cloud Run deployment)
- Vroege cloud platform plannen (SaaS, Kubernetes, $576K roadmap)
- Phase 1 execution checklists uit de opstartfase

---

## 🔗 Gerelateerde documentatie

| Locatie | Beschrijving |
|---------|-------------|
| `../CLAUDE.md` | Claude AI instructies voor dit project |
| `../README.md` | Project-introductie & quick start |
| `../agents/README.md` | Ollama agents overzicht (32 runtime agents) |
| `../frontend/README.md` | Next.js frontend documentatie |
| `../plan/PLAN.md` | Projectplan met Wave 6–8 roadmap |

---

*Laatste update: 2026-04-22 — Revisie 5 toegevoegd, duplicaat architectuur/AI_OPTIMALISATIEPLAN.TXT verwijderd, alle secties bijgewerkt.*
