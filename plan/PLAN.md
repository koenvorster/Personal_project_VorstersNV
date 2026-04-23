# VorstersNV — AI Platform Masterplan

## Status

| Fase | Omschrijving | Status |
|------|-------------|--------|
| F1 | Fundament: bugs, ParallelStep, schema validatie, tracing | ✅ Afgerond |
| F2 | Orchestratie: contracts, quality gates, YAML pipelines, skill chains | ✅ Afgerond |
| F3 | Multi-platform: capabilities, skill folders, Claude fleet, tool executor | ✅ Afgerond |
| F4 | Zelflerend: A/B testing, performance analyse, anomalie-detectie | ✅ Afgerond |
| F5 | Productie: API platform, webhooks, Control Plane, portfolio | ✅ Afgerond |

## Huidige architectuur

- **49 Claude agents** in `.claude/agents/` (alle geldig, 0 errors)
- **32 Ollama runtime agents** in `agents/` (YAML-configureerbaar)
- **29 GitHub Copilot agents** in `.github/agents/`
- **19 skills** in `.claude/skills/` (folder-structuur met SKILL.md)
- **5 workflow pipelines** in `ollama/workflows/` (YAML-geladen)
- **3 skill chains** in `ollama/workflows/chains/`
- **FastAPI backend** met 11 routers (incl. portal, feedback, streaming), JWT/Keycloak auth
- **Next.js frontend** met blog, portfolio, how-to's, portal klantpagina's
- **Quality Gate systeem** (QG-FRAUD-01..QG-CONTENT-01)
- **Event-driven orchestrator** (SkillChainOrchestrator)
- **47 ollama/ modules** (Control Plane, policy engine, A/B tester, deployment rings, RAG, KnowledgeGraph, compliance_engine, diagram_renderer, reasoning_logger, ...)
- **Consultancy tooling**: `scripts/analyse_project.py`, `code_analyse_agent`, `consultancy_orchestrator`

**AI Masterplan Revisie 5:** `documentatie/AI_OPTIMALISATIEPLAN_REVISIE5.TXT` (COMPLEET — alle gaps G-32..G-46 gesloten)
**AI Masterplan Revisie 6:** `documentatie/AI_OPTIMALISATIEPLAN_REVISIE6.TXT` (ACTIEF — W10 gepland)

---

## Revisie 5 — Waves Roadmap

> Volledige detailspec: `documentatie/AI_OPTIMALISATIEPLAN_REVISIE5.TXT`
> 15 nieuwe gaps (G-32..G-46) geïdentificeerd; 4 zijn BLOCKERS.

| Wave | Scope | Status | Key deliverables |
|------|-------|--------|-----------------|
| W1–W5 | F1–F5 fundament | ✅ COMPLEET | Zie Fase-tabel hierboven |
| **W6** | **Intelligence foundations** | ✅ COMPLEET | PII Scanner, ClientProjectSpace, AdaptiveChunker, SSE Streaming, EU AI Act, CostForecaster, AgentVersioning |
| **W7** | **RAG & Knowledge Graph** | ✅ COMPLEET | rag_engine.py, HashEmbedding fallback, KnowledgeGraph (Mermaid), MixtureOfAgents, 9 sector benchmarks |
| **W8** | **Self-improvement loop** | ✅ COMPLEET | SelfImprovementLoop, feedback API, recommendation_engine.py, platform_report.py, ab_tester chi-square |
| **W9** | **Portal, Compliance & Reasoning** | ✅ COMPLEET | DiagramRenderer (G-37), ComplianceEngine GDPR/NIS2/BTW (G-46), Portal API (6 endpoints), ReasoningLogger + DB migratie, auto_promoter FeedbackAnalyzer gate, 228 nieuwe tests (1649 totaal) |

### Revisie 5 — Volledig geïmplementeerde modules

| Module | Gap | Status |
|--------|-----|--------|
| `ollama/client_project_space.py` | G-32 | ✅ |
| `ollama/pii_scanner.py` | G-39 | ✅ |
| `ollama/adaptive_chunker.py` | G-34 | ✅ |
| `ollama/ai_act_compliance.py` | G-43 | ✅ |
| `ollama/cost_forecaster.py` | G-41 | ✅ |
| `ollama/agent_versioning.py` | G-44 | ✅ |
| `ollama/rag_engine.py` | G-33 | ✅ |
| `ollama/knowledge_graph.py` | G-35 | ✅ |
| `ollama/mixture_of_agents.py` | W7 | ✅ |
| `ollama/sector_benchmarks.py` | W7 | ✅ |
| `ollama/self_improvement.py` | W8 | ✅ |
| `ollama/recommendation_engine.py` | W8 | ✅ |
| `ollama/platform_report.py` | W8 | ✅ |
| `api/routers/feedback.py` | W8 | ✅ |
| `api/routers/streaming.py` | G-40 | ✅ |
| `ollama/diagram_renderer.py` | G-37 | ✅ |
| `ollama/compliance_engine.py` | G-46 | ✅ |
| `api/routers/portal.py` | W9 | ✅ |
| `ollama/reasoning_logger.py` | W9 | ✅ |
| `ollama/auto_promoter.py` (FeedbackAnalyzer gate) | W9 | ✅ |
| `policies/nis2-policies.yaml` | W9 | ✅ |

### Alle gaps G-32..G-46 gesloten ✅

Revisie 5 is volledig geïmplementeerd. **1649 tests, 0 failures.**

### Future Items (post-Revisie 5 → Revisie 6)

- `CostForecaster v2 ML` (scikit-learn) — vereist ≥20 historische projecten data
- **GPU server integratie**: gaming desktop configureren als Ollama remote endpoint (`OLLAMA_GPU_URL=http://<desktop-ip>:11434`)
- `npm install mermaid` — volledige Mermaid.js rendering in frontend (nu: graceful fallback naar `<pre>`)
- Cypress E2E tests voor portal frontend (projectlijst, navigatie, detailpagina)

---

## Revisie 6 — Klantklaar Platform

> Volledige detailspec: `documentatie/AI_OPTIMALISATIEPLAN_REVISIE6.TXT`
> 12 nieuwe gaps (G-47..G-58) geïdentificeerd; 3 zijn BLOCKERS.

**Visie**: platform écht klantklaar maken — één betalende klant bedienen vóór einde Wave W11.

| Wave | Scope | Status | Key deliverables |
|------|-------|--------|-----------------|
| **W10** | **Production Foundation** | 🟡 GEPLAND | Portal auth middleware, multi-tenant isolatie, FastAPI Cloud Run deploy, GCP Secret Manager, Mermaid.js installatie |
| **W11** | **Client Experience** | ⬜ BACKLOG | Rapport-pagina portal, klant self-service onboarding, PDF-export, email notificaties (aiosmtplib) |
| **W12** | **Differentiatie** | ⬜ BACKLOG | GPU server integratie, CostForecaster v2 ML, geavanceerde portal analytics |

### Revisie 6 Gaps

| Gap | Naam | Klasse | Prioriteit |
|-----|------|--------|-----------|
| G-47 | Portal Authentication Gate | Auth/Security | BLOCKER |
| G-48 | Multi-tenant isolatie Portal | Data/Privacy | BLOCKER |
| G-49 | FastAPI niet gedeployd in CI/CD | Deployment | BLOCKER |
| G-50 | Mermaid.js niet geïnstalleerd | Frontend | HIGH |
| G-51 | Notificaties niet geïmplementeerd | Integratie | HIGH |
| G-52 | Klant self-service project aanmaken | Frontend/UX | HIGH |
| G-53 | Portal rapport-pagina ontbreekt | Frontend | HIGH |
| G-54 | Secrets management voor Cloud Run | Deployment | HIGH |
| G-55 | GPU server integratie | Performance | MEDIUM |
| G-56 | Rapport export / PDF download | Frontend/Value | MEDIUM |
| G-57 | Keycloak productie-setup | Auth | MEDIUM |
| G-58 | CostForecaster v2 ML | AI/Intelligence | LOW |

---

Zie `documentatie/AI_OPTIMALISATIEPLAN_REVISIE5.TXT` voor volledige Revisie 5 spec.
Zie `documentatie/AI_OPTIMALISATIEPLAN_REVISIE6.TXT` voor de Revisie 6 roadmap (W10-W12).
Gebruik `validate-agents.mjs` voor health checks van de Claude agent fleet.
