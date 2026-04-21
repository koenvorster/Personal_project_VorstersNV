# 📚 VorstersNV — Documentatie Index

> Centrale index van alle projectdocumentatie. Elke map heeft een specifiek doel.

---

## 📁 Mappenstructuur

```
documentatie/
├── architectuur/     ← Technische architectuur & AI-design
├── ontwikkeling/     ← Developer guides, how-to's & projectplan
├── analyse/          ← Externe analyses (loonschalen, etc.)
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
| `AI_OPTIMALISATIEPLAN.TXT` | AI Control Platform strategie — Revisie 4 (governance, evaluatie, schaalbaarheid) |

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
| `LOONSCHALEN_ANALYSE.txt` | Analyse van loonschalen (extern loonberekeningproject) |
| `LOONBEREKENING_ANALYSE.txt` | Technische analyse loonberekeningssysteem |

---

## 📣 marketing/

Externe communicatie en marketingmateriaal.

| Bestand | Beschrijving |
|---------|-------------|
| `LINKEDIN_POST.md` | LinkedIn post over het VorstersNV project |

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
| `../agents/README.md` | Ollama agents overzicht |
| `../frontend/README.md` | Next.js frontend documentatie |
| `../plan/PLAN.md` → zie `ontwikkeling/PLAN.md` | Projectplan (verplaatst) |

---

*Laatste update: reorganisatie documentatiestructuur — alle verouderde bestanden zijn gearchiveerd.*
