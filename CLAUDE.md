# CLAUDE.md — VorstersNV IT/AI Consultancy Platform

Provides guidance to Claude Code when working in this repository.

## Project Overview

**VorstersNV** is een freelance IT/AI-consultancy platform voor Belgische KMOs.
**Focus (Fase 6)**: legacy code-analyse, bedrijfsproces automatisering, AI-agents bouwen voor klanten.
**Revisie 6 doel (W10–W12)**: klantklaar platform — portal auth, multi-tenant isolatie, Cloud Run deploy (FastAPI), klantrapportage UI, PDF-export, email notificaties.
The webshop component is deprioritized — consultancy tooling is the primary development target.

Full-stack monorepo:

| Layer | Tech | Path |
|-------|------|------|
| Frontend | Next.js 16.2, App Router, TypeScript, Tailwind CSS | `frontend/` |
| Backend API | FastAPI (Python 3.12), SQLAlchemy async, Alembic | `api/` ← **ACTIEVE backend** |
| Backend Java | Spring Boot 3.3.5 (Java 21) — legacy/vestigieel | `backend/` |
| Local AI | Ollama — llama3, mistral | `ollama/` |
| AI Agents | YAML + `agent_runner.py` | `agents/` |
| Database | PostgreSQL 16 + Redis 7 | `docker-compose.yml` |
| Payments | Mollie (webhooks) | `api/routers/betalingen.py` |
| Auth | Keycloak (dev) | docker-based |
| CI/CD | GitHub Actions | `.github/workflows/` |

## Build & Dev Commands

### Backend Python (run from root)
```bash
pip install -r requirements.txt
uvicorn api.main:app --reload          # dev server :8000
pytest tests/                          # all tests
pytest tests/ -v --cov=api            # with coverage
ruff check api/                        # linting
mypy api/                             # type check
```

### Frontend (run from `frontend/`)
```bash
npm ci
npm run dev                            # Next.js dev :3000
npm run build                          # production build
npm run lint                           # ESLint
```

### Docker (run from root)
```bash
docker compose up -d                  # start PostgreSQL + Redis + Keycloak
docker compose down                   # stop all
docker compose logs -f api            # follow FastAPI logs
```

### Ollama agents
```bash
ollama serve                           # start Ollama daemon
python scripts/analyse_project.py --pad /path/to/client/project --dry-run  # codebase analyse
python agent_runner.py --agent code_analyse_agent --spec "..."  # directe agent run
```

## Consultancy Tooling (Fase 6 — Primaire Focus)

| Tool | Locatie | Doel |
|------|---------|------|
| `scripts/analyse_project.py` | `scripts/` | Codebase scannen + AI-analyse + rapport genereren |
| `agents/code_analyse_agent.yml` | `agents/` | Technische code-analyse per chunk |
| `agents/klant_rapport_agent.yml` | `agents/` | Klantgerichte samenvatting genereren |
| `agents/bedrijfsproces_agent.yml` | `agents/` | Bedrijfsproces AS-IS/TO-BE mapping |
| `agents/consultancy_orchestrator.yml` | `agents/` | End-to-end consultancy workflow |
| `ollama/compliance_engine.py` | `ollama/` | GDPR / NIS2 / BTW / EU AI Act validator (4-laags) |
| `ollama/diagram_renderer.py` | `ollama/` | Mermaid/PlantUML architectuurdiagrammen genereren |
| `ollama/reasoning_logger.py` | `ollama/` | Chain-of-thought stappen loggen per agent-sessie |
| `api/routers/portal.py` | `api/routers/` | Klantportal API (6 endpoints: projecten, status, rapport, diagrams, forecasts) |
| `documentatie/analyse/` | `documentatie/` | Gegenereerde klantanalyses opslaan |

### Analyse starten
```bash
# Dry run (geen AI, alleen bestandsscan)
python scripts/analyse_project.py --pad C:\pad\naar\klant-project --dry-run

# Volledige analyse (vereist werkende Ollama + GPU server)
python scripts/analyse_project.py --pad C:\pad\naar\klant-project
```

## Local AI / Ollama Status

> ⚠️ **Hardware beperking (laptop)**: Intel i7-1165G7, geen dedicated GPU (Intel Iris Xe 1GB).
> Alle modellen draaien op CPU — analyse duurt 2–5 minuten per chunk.

**Beschikbare modellen op dit apparaat:**
| Model | Status | Gebruik |
|-------|--------|---------|
| `mistral:latest` (7.2B Q4_K_M) | ✅ Werkt, traag (~290s/chunk) | Primaire analyse |
| `llama3.2:latest` (3.2B Q4_K_M) | ✅ Werkt, traag | Snellere fallback |
| `gpt-oss:20b` (MXFP4) | ❌ Broken (MXFP4 incompatibel CPU) | Niet gebruiken |
| `starcoder:3b` | ⚠️ Code completion only, geen instructies | Niet voor analyse |

**Gaming desktop server (gepland):**
```
OLLAMA_BASE_URL=http://<desktop-ip>:11434   # in .env
```
Met RTX 3090/4070 Ti: mistral:7B in ~1-2s, modellen tot 34B parameters.

## Domain Model (DDD Bounded Contexts)

| Context | Aggregates | Routers |
|---------|-----------|---------|
| **Catalog** | Product, Category | `api/routers/products.py` |
| **Orders** | Order, OrderLine | `api/routers/orders.py` |
| **Inventory** | StockItem, Warehouse | `api/routers/inventory.py` |
| **Customer** | Customer, Address | `api/auth.py` |
| **Payments** | Payment, Refund | `api/routers/betalingen.py` |
| **Notifications** | Notification | `api/routers/notifications.py` |
| **Dashboard** | Metrics | `api/routers/dashboard.py` |
| **Portal** | ClientProject | `api/routers/portal.py` |
| **Feedback** | FeedbackRecord | `api/routers/feedback.py` |
| **Streaming** | SSE stream | `api/routers/streaming.py` |

## Architecture Decision: FastAPI is the primary backend

> **CRITICAL**: FastAPI (`api/`) is the single source of truth for backend logic.
> - Frontend calls `:8000` (FastAPI) — not `:8080` (Spring Boot)
> - All tests target FastAPI endpoints
> - All Ollama agents use FastAPI tool endpoints
> - `backend/` (Spring Boot) is vestigieel — do NOT add new features there
> - TODO: archiveer `backend/` naar `_archive/spring-boot-backend/` (zie backlog vn-imp-1-dual-api)

## Code Conventions (Python / FastAPI)

- **Python 3.12** — use `match/case`, `TypeAlias`, `Self`, PEP 695 syntax where appropriate
- **Async everywhere** — `async def` for all route handlers and service methods
- **SQLAlchemy async** — `async_sessionmaker`, `AsyncSession`, no `Session.query()` (deprecated)
- **Pydantic v2** — `model_config = ConfigDict(...)`, `model_validate()`, not `parse_obj()`
- **DTOs as Pydantic models** in `api/schemas/` — separate Request/Response schemas
- **Domain logic in services** — routers are thin; no business logic in handlers
- **Alembic for all schema changes** — never alter tables manually
- **DDD patterns**: aggregate roots, value objects (frozen dataclass), domain events
- **Guard clauses** — return early for invalid conditions, avoid deep nesting
- **No magic numbers** — extract as module-level constants or enums
- Tests in `tests/` — `pytest` + `httpx.AsyncClient` for FastAPI

## Code Conventions (Next.js / Frontend)

- **App Router** — no Pages Router; all routes under `app/`
- **Server Components by default** — add `"use client"` only when needed
- **TypeScript strict** — `strict: true` in tsconfig; no `any`
- **Tailwind CSS** — no inline styles, no hardcoded colors
- **`data-testid`** on every interactive element (required for Playwright/Cypress)
- **ShadCN/UI** or plain Tailwind — no MUI or Ant Design

## Ollama Agent System

**47 modules** in `ollama/` (Control Plane, Capability Plane, Execution Plane, Trust Plane, Consultancy Intelligence).
Key Wave 9 modules: `compliance_engine.py`, `diagram_renderer.py`, `reasoning_logger.py`.

Agent YAML files in `agents/` define runtime AI agents (32 YAML-bestanden). Loaded by `agent_runner.py`:

```yaml
name: my_agent
model: llama3          # or mistral
temperature: 0.4
system_prompt_ref: prompts/system/my_agent_system.txt
preprompt_ref: prompts/preprompt/my_agent_v1.yml
capabilities:
  - capability_name
input_schema: ...      # JSON Schema
output_schema: ...     # JSON Schema
```

All agent prompts live in `prompts/system/` and `prompts/preprompt/`.

## Environment Variables

Required in `.env` (see `.env.example`):
```
DB_PASSWORD=
NEXTAUTH_SECRET=
NEXTAUTH_URL=
MOLLIE_API_KEY=       # live/test key
KEYCLOAK_URL=
REDIS_URL=
# SMTP (W11 notificaties)
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
# Cloud Run (Revisie 6 / W10)
GCP_PROJECT_ID=
GCP_REGION=europe-west1
# GPU server (Revisie 6 / W12, optioneel)
OLLAMA_GPU_URL=       # http://<gaming-desktop-ip>:11434
```

## Atlassian

No Jira project configured yet for this repo. For future: cloudId = `4052e10c-2ea0-4f1d-a358-5597e539b140`

## Claude Agents & Skills

See `.claude/README.md` for the complete index.
