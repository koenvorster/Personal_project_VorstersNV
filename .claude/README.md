# .claude — VorstersNV AI Ecosystem Index

Complete overview of all Claude agents, skills and scripts for this project.

## Agents (`.claude/agents/`)

| Agent | Doel | Trigger |
|-------|------|---------|
| `fastapi-developer` | Implementeer FastAPI endpoints, services, DDD patterns | "add endpoint", "implement feature", "DDD" |
| `ollama-agent-designer` | Ontwerp en verbeter Ollama YAML agent definities | "improve agent", "new agent", "tune prompt" |

### GitHub Copilot Agents (`.github/agents/`)

21 specialized agents — aanroepen via `@agent-naam` in Copilot Chat:

| Category | Agents |
|----------|--------|
| Architecture | `@architect`, `@ddd-modeler`, `@domain-validator` |
| Development | `@developer`, `@frontend-specialist`, `@clean-code-reviewer`, `@security-permissions`, `@devops-engineer`, `@database-expert`, `@mollie-expert`, `@performance-optimizer` |
| Domain | `@klantenservice-expert`, `@product-content`, `@seo-specialist`, `@order-expert`, `@prompt-engineer` |
| Testing | `@automation-cypress`, `@playwright-mcp`, `@regression-selector`, `@test-data-designer`, `@test-orchestrator` |

## Skills (`.claude/skills/`)

| Skill | Content |
|-------|---------|
| `fastapi-ddd/` | FastAPI patterns, SQLAlchemy async, DDD aggregates/value objects/events, Pydantic v2, Alembic |
| `ollama-agents/` | YAML agent schema, prompt engineering, model tuning, agent_runner.py |
| `nextjs-frontend/` | App Router, Server Components, Tailwind, data-testid conventions, TypeScript strict |

## Scripts (`.claude/scripts/`)

| Script | Gebruik |
|--------|---------|
| `check-env.mjs` | Valideert `.env` vs `.env.example` — meldt ontbrekende variabelen |

**Run:**
```bash
node .claude/scripts/check-env.mjs
```

## Omgevingen

| Env | URL | Beschrijving |
|-----|-----|-------------|
| Local dev | `http://localhost:3000` (FE) / `http://localhost:8000` (API) | Docker Compose + Ollama |
| Production | TBD | Cloud Run / VPS |

## Tech Stack Snel Overzicht

| Laag | Tech |
|------|------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, App Router |
| Backend | FastAPI (Python 3.12), async SQLAlchemy |
| Database | PostgreSQL 16, Alembic migraties |
| Cache | Redis 7 |
| AI | Ollama (llama3, mistral) — volledig lokaal |
| Betalingen | Mollie API |
| Auth | Keycloak (dev), NextAuth |
| Container | Docker Compose |
| CI/CD | GitHub Actions |
