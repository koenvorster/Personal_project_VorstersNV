# .claude — VorstersNV AI Ecosystem Index

Complete overview van alle Claude agents, skills en scripts voor dit project.

## Quick start

### Als backend developer (FastAPI)
```
"Voeg een endpoint toe voor reviews"
"Fix deze async SQLAlchemy fout"
"Schrijf een Alembic migration voor de nieuwe kolom"
```
→ `fastapi-developer` agent + `fastapi-ddd` skill

### Als frontend developer (Next.js)
```
"Maak een productdetail component"
"Voeg data-testid toe aan de winkelwagen"
"Fix deze TypeScript error"
```
→ `nextjs-developer` agent + `nextjs-frontend` skill

### Als tester
```
"Schrijf tests voor het nieuwe reviews endpoint"
"Voeg test coverage toe voor het checkout flow"
"Mijn conftest fixture werkt niet"
```
→ `test-orchestrator` agent + `testing-patterns` skill

### Als reviewer
```
"Review mijn code voor de betaling fix"
"Is deze FastAPI endpoint correct?"
"Zijn er security-problemen?"
```
→ `mr-reviewer` agent

### Bij CI-problemen
```
"De GitHub Actions build is rood"
"pytest faalt in CI maar niet lokaal"
"TypeScript errors in de pipeline"
```
→ `ci-debugger` agent

### Voor AI-agent ontwerp
```
"Verbeter de system prompt van de developer agent"
"Maak een nieuw Ollama agent voor product-aanbevelingen"
"Welk agent moet ik gebruiken voor X?"
```
→ `ai-architect` agent (meta) of `ollama-agent-designer`

---

## Claude Agents (`.claude/agents/`)

| Agent | Model | Doel | permissionMode |
|-------|-------|------|----------------|
| `fastapi-developer` | sonnet | FastAPI endpoints, SQLAlchemy async, DDD, Alembic | auto |
| `ollama-agent-designer` | sonnet | Ollama YAML agents ontwerpen en verbeteren | auto |
| `nextjs-developer` | sonnet | Next.js 14 + App Router + TypeScript + Tailwind | auto |
| `test-orchestrator` | sonnet | pytest + httpx API-tests coördineren | auto |
| `mr-reviewer` | sonnet | Code review (FastAPI, Next.js, security) | plan |
| `ci-debugger` | haiku | GitHub Actions falen analyseren | plan |
| `ai-architect` | opus | Meta-agent: AI ecosystem beheer | plan |

---

## Claude Skills (`.claude/skills/`)

Skills worden automatisch getriggerd op basis van context-keywords.

| Skill | Directory | Triggers |
|-------|-----------|---------|
| `fastapi-ddd` | `skills/fastapi-ddd/` | "fastapi", "sqlalchemy", "async", "pydantic", "ddd" |
| `nextjs-frontend` | `skills/nextjs-frontend/` | "next.js", "app router", "tailwind", "data-testid" |
| `ollama-agents` | `skills/ollama-agents/` | "ollama", "agent yaml", "llama", "mistral", "system prompt" |
| `testing-patterns` | `skills/testing-patterns/` | "pytest", "conftest", "fixture", "test coverage" |
| `alembic-migrations` | `skills/alembic-migrations/` | "migration", "alembic", "schema", "kolom toevoegen" |

---

## GitHub Copilot Agents (`.github/agents/`)

21 gespecialiseerde agents — aanroepen via `@agent-naam` in GitHub Copilot Chat:

| Categorie | Agents |
|-----------|--------|
| Architecture | `@architect`, `@ddd-modeler`, `@domain-validator` |
| Development | `@developer`, `@frontend-specialist`, `@clean-code-reviewer`, `@security-permissions`, `@devops-engineer`, `@database-expert`, `@mollie-expert`, `@performance-optimizer` |
| Domain | `@klantenservice-expert`, `@product-content`, `@seo-specialist`, `@order-expert`, `@prompt-engineer` |
| Testing | `@automation-cypress`, `@playwright-mcp`, `@regression-selector`, `@test-data-designer`, `@test-orchestrator` |

---

## GitHub Copilot Prompts (`.github/prompts/`)

| Prompt | Gebruik |
|--------|---------|
| `nieuw-endpoint.prompt.md` | Template voor nieuw FastAPI endpoint |
| `mollie-checkout.prompt.md` | Mollie betaalflow implementeren |
| `db-migratie.prompt.md` | Alembic migration aanmaken |
| `agent-debug.prompt.md` | Ollama agent debuggen |
| `productpagina.prompt.md` | Next.js productpagina bouwen |
| `nieuwe-agent.prompt.md` | Nieuw Ollama YAML agent ontwerpen |
| `security-audit.prompt.md` | Security audit uitvoeren |

---

## Scripts (`.claude/scripts/`)

| Script | Gebruik |
|--------|---------|
| `check-env.mjs` | Valideert `.env` vs `.env.example` — meldt ontbrekende variabelen |

```bash
node .claude/scripts/check-env.mjs
```

---

## Tests

28 API-tests draaien met in-memory SQLite (geen PostgreSQL vereist):

```bash
pytest tests/ -v --tb=short
```

| Bestand | Tests |
|---------|-------|
| `tests/test_products_api.py` | 15 — product lijst, detail, categorieën, CRUD |
| `tests/test_betalingen_api.py` | 13 — bestelling, voorraad, simuleer betaling |
| `tests/test_webhooks.py` | Mollie webhook verwerking |

---

## Omgevingen

| Env | URL | Beschrijving |
|-----|-----|-------------|
| Local dev | `http://localhost:3000` (FE) / `http://localhost:8000` (API) | Docker Compose + Ollama |
| Production | TBD | Cloud Run / VPS |

---

## Tech Stack

| Laag | Tech |
|------|------|
| Frontend | Next.js 14, TypeScript strict, Tailwind CSS, App Router |
| Backend | FastAPI (Python 3.12), async SQLAlchemy 2.x |
| Database | PostgreSQL 16, Alembic migraties |
| Cache | Redis 7 |
| AI | Ollama (llama3, mistral) — volledig lokaal |
| Betalingen | Mollie API (+ simuleer-endpoint voor dev) |
| Auth | Keycloak (dev), NextAuth |
| Container | Docker Compose |
| CI/CD | GitHub Actions (4 jobs: python, yaml-validate, frontend, java) |
