# CLAUDE.md — VorstersNV KMO Platform

Provides guidance to Claude Code when working in this repository.

## Project Overview

**VorstersNV** is a KMO (KMU) webshop + AI-agent platform. Full-stack monorepo:

| Layer | Tech | Path |
|-------|------|------|
| Frontend | Next.js 14, App Router, TypeScript, Tailwind CSS | `frontend/` |
| Backend API | FastAPI (Python 3.12), SQLAlchemy async, Alembic | `api/` |
| Backend Java | Spring Boot 3.3.5 (Java 21) | `backend/` |
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
python agent_runner.py --agent developer_agent --spec "..."  # run a YAML agent
```

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

Agent YAML files in `agents/` define runtime AI agents. Loaded by `agent_runner.py`:

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
```

## Atlassian

No Jira project configured yet for this repo. For future: cloudId = `4052e10c-2ea0-4f1d-a358-5597e539b140`

## Claude Agents & Skills

See `.claude/README.md` for the complete index.
