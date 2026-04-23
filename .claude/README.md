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

### Voor AI-agent ontwerp
```
"Verbeter de system prompt van de developer agent"
"Maak een nieuw Ollama agent voor product-aanbevelingen"
"Welk agent moet ik gebruiken voor X?"
```
→ `ai-architect` agent (meta) of `ollama-agent-designer`

### Bij CI-problemen
```
"De GitHub Actions build is rood"
"pytest faalt in CI maar niet lokaal"
"TypeScript errors in de pipeline"
```
→ `ci-debugger` agent

### Als IT/AI consultant (freelance opdrachten) 🆕
```
"Analyseer deze Java codebase voor een klant"
"Breng dit bedrijfsproces in kaart"
"Schrijf een voorstel voor AI-automatisering"
"Genereer een klantrapport op basis van deze bevindingen"
```
→ `code-analyzer` / `business-process-advisor` / `it-consultant` agents

---

## Claude Rules (`.claude/rules/`)

Path-gebaseerde regels die automatisch laden op basis van welke bestanden open zijn in de editor.
Claude Code laadt de relevante rule-bestanden automatisch als context bij de corresponderende bestandstypen.

> **Setup vereist:** Draai eenmalig `.claude\scripts\setup-rules.ps1` om de directory-structuur
> en rule-bestanden aan te maken (PowerShell, vanuit project root).

| Rule | Locatie | Wanneer actief | Beschrijving |
|------|---------|----------------|-------------|
| `python-fastapi.md` | `rules/backend/` | Bij elk `*.py` bestand | Async/await, SQLAlchemy 2.x, Pydantic v2, logging, guard clauses, type hints |
| `alembic-migrations.md` | `rules/backend/` | Bij `db/migrations/**/*.py` en `alembic.ini` | Verplichte upgrade+downgrade, migration message, test-cyclus |
| `nextjs-app-router.md` | `rules/frontend/` | Bij `frontend/**/*.tsx` en `.ts` | Server Components, `"use client"`, data-testid, TypeScript strict, Tailwind |
| `git-commits.md` | `rules/general/` | Altijd actief | Nederlandstalig, imperativus, max 72 chars, type prefix |
| `project-context.md` | `rules/general/` | Altijd actief | VorstersNV architectuuroverzicht, bounded contexts, tech stack samenvatting |
| `docker.md` | `rules/tools/` | Bij `docker-compose.yml` en `Dockerfile*` | Vaste poorten, verplichte health checks, geen secrets in Dockerfile |

---

## Architecture Docs (`.claude/architecture/`) 🆕

Canonieke bronnen voor tech stack en domain model:

| Document | Inhoud |
|----------|--------|
| `architecture/TECH_STACK.md` | **Versienummers** (Next.js 16.2, Python 3.12, ...) |
| `architecture/BOUNDED_CONTEXTS.md` | **Domain model**, ubiquitous language, agent-routing per context |

> Bij versie-twijfel of domain vragen: raadpleeg eerst deze docs.

**Architectuurplan (actief):**
- 📄 [`documentatie/AI_OPTIMALISATIEPLAN_REVISIE5.TXT`](../documentatie/AI_OPTIMALISATIEPLAN_REVISIE5.TXT) — Revisie 5 (actief, Wave 6 roadmap)
- 📄 [`documentatie/AI_OPTIMALISATIEPLAN.TXT`](../documentatie/AI_OPTIMALISATIEPLAN.TXT) — Revisie 4 (archief)
- 📄 [`documentatie/architectuur/ARCHITECTURE.md`](../documentatie/architectuur/ARCHITECTURE.md) — technische architectuur v5.0

> **Fase 6 focus:** Wave 6 Intelligence Foundations — multi-tenant `ClientProjectSpace`,
> PII-scanner, EU AI Act compliance, SSE streaming, AdaptiveChunker.
> Zie Revisie 5 voor de volledige roadmap (Waves 6–8).

---

## Claude Agents (`.claude/agents/`)

> **49 agents** — volledig fleet, beschikbaar voor Claude-only gebruikers.

### Architectuur & DDD
| Agent | Model | Doel | permissionMode |
|-------|-------|------|----------------|
| `architect` | claude-sonnet-4-5 | Systeemontwerp, ADRs, bounded contexts, integraties | default |
| `ddd-modeler` | claude-sonnet-4-5 | Domain model, aggregates, events, ubiquitous language | default |
| `domain-validator` | claude-sonnet-4-5 | Valideer code vs domeinregels | default |
| `ai-architect` | claude-opus-4-5 | Meta-agent: AI ecosystem beheer | default |

### Ontwikkeling
| Agent | Model | Doel | permissionMode |
|-------|-------|------|----------------|
| `developer` | claude-sonnet-4-5 | FastAPI + Next.js full-stack implementatie | allow |
| `fastapi-developer` | claude-sonnet-4-5 | FastAPI endpoints, SQLAlchemy async, DDD, Alembic | allow |
| `frontend-specialist` | claude-sonnet-4-5 | Next.js 16.2 + App Router + TypeScript + Tailwind | allow |
| `nextjs-developer` | claude-sonnet-4-5 | Next.js componenten en routes bouwen | allow |
| `devops-engineer` | claude-sonnet-4-5 | Docker, GitHub Actions CI/CD, Cloud Run | allow |
| `database-expert` | claude-sonnet-4-5 | SQLAlchemy async, Alembic migraties, PostgreSQL | allow |
| `clean-code-reviewer` | claude-sonnet-4-5 | SOLID, naming, code smells, refactoring | default |
| `security-permissions` | claude-sonnet-4-5 | RBAC, GDPR, JWT, HMAC, OWASP audit | default |
| `performance-optimizer` | claude-sonnet-4-5 | Core Web Vitals, Redis caching, N+1 queries | default |
| `mr-reviewer` | claude-sonnet-4-5 | Code review (FastAPI, Next.js, security) | default |
| `ci-debugger` | claude-haiku-4-5 | GitHub Actions falen analyseren | default |
| `feature-worker` | claude-sonnet-4-5 | Parallelle feature-ontwikkeling in git worktrees | allow |
| `ollama-agent-designer` | claude-sonnet-4-5 | Ollama YAML agents ontwerpen en verbeteren | allow |

### Domein Experts
| Agent | Model | Doel | permissionMode |
|-------|-------|------|----------------|
| `mollie-expert` | claude-sonnet-4-5 | Mollie Payments API, webhooks, terugbetalingen | allow |
| `klantenservice-expert` | claude-sonnet-4-5 | CS agent prompts, escalatieflows, sentimentanalyse | allow |
| `order-expert` | claude-sonnet-4-5 | Order lifecycle, fraudedetectie, pipeline | allow |
| `seo-specialist` | claude-sonnet-4-5 | SEO, metadata, structured data, sitemap | allow |
| `product-content` | claude-sonnet-4-5 | Productbeschrijvingen, USPs, prompt-iteratie | allow |
| `prompt-engineer` | claude-sonnet-4-5 | Ollama agent prompt optimalisatie | allow |

### Domein & Compliance
| Agent | Model | Doel | permissionMode |
|-------|-------|------|----------------|
| `gdpr-advisor` | claude-sonnet-4-5 | GDPR compliance: anonimisatie, bewaartermijnen, Art.17 | default |
| `db-explorer` | claude-sonnet-4-5 | Database-analyse: schema, queries, 3-mode safety | allow |
| `fraud-advisor` | claude-haiku-4-5 | Fraude assessment interpreteren, risicoscore advies | allow |
| `klantenservice-coach` | claude-sonnet-4-5 | Klantenservice antwoorden, klachten, retour, escalaties | allow |
| `audit-reporter` | claude-haiku-4-5 | Auditlogs genereren, GDPR decision-journal rapporten | allow |
| `order-analyst` | claude-haiku-4-5 | Order compliance Belgisch recht, BTW, Mollie validatie | allow |
| `product-writer` | claude-sonnet-4-5 | SEO productbeschrijvingen NL/FR, metateksten | allow |
| `lead-orchestrator` | claude-sonnet-4-5 | Multi-agent workflow orkestratie, agent routing | default |

### Testing & Kwaliteit
| Agent | Model | Doel | permissionMode |
|-------|-------|------|----------------|
| `test-orchestrator` | claude-sonnet-4-5 | pytest + httpx API-tests coördineren | allow |
| `api-tester` | claude-sonnet-4-5 | FastAPI integratie tests, endpoint validatie | allow |
| `automation-cypress` | claude-sonnet-4-5 | Cypress E2E testsuites | allow |
| `playwright-mcp` | claude-sonnet-4-5 | Agentic browser automatisering | allow |
| `regression-selector` | claude-haiku-4-5 | Impact analyse, test selectie na wijziging | default |
| `test-data-designer` | claude-haiku-4-5 | Testdata sets, boundary values, fixtures | allow |
| `performance-tester` | claude-sonnet-4-5 | Load tests, stress tests, SLA validatie | allow |
| `security-tester` | claude-sonnet-4-5 | Security tests: IDOR, HMAC, injection, auth bypass | allow |
| `accessibility-tester` | claude-sonnet-4-5 | WCAG 2.1 AA tests, ARIA, toetsenbord navigatie | allow |

### Extra Specialisten
| Agent | Model | Doel | permissionMode |
|-------|-------|------|----------------|
| `technical-writer` | claude-sonnet-4-5 | API docs, ADRs, runbooks, onboarding guides | allow |
| `data-engineer` | claude-sonnet-4-5 | Data pipelines, analytics queries, dashboards | allow |
| `ux-reviewer` | claude-sonnet-4-5 | UX flows, usability, friction points | default |
| `jira-planner` | claude-sonnet-4-5 | Jira issues, sprint planning, story points via Atlassian MCP | allow |
| `confluence-writer` | claude-sonnet-4-5 | ADRs, runbooks, Confluence pagina's schrijven via Atlassian MCP | allow |
| `ollama-manager` | claude-sonnet-4-5 | Ollama model beheer, debugging, server configuratie | allow |

### Freelance IT/AI Consultancy
| Agent | Model | Doel | permissionMode |
|-------|-------|------|----------------|
| `code-analyzer` | claude-sonnet-4-5 | Bestaande codebases analyseren, business logic extraheren | allow |
| `business-process-advisor` | claude-sonnet-4-5 | Bedrijfsprocessen mappen, automatiseringskansen, ROI | allow |
| `it-consultant` | claude-sonnet-4-5 | IT/AI strategie, klantvoorstellen, rapporten | allow |

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
| `gdpr-privacy` | `skills/gdpr-privacy/` | "gdpr", "anonimisatie", "bewaartermijn", "recht op vergetelheid", "verwerkingsregister" |
| `database-explorer` | `skills/database-explorer/` | "schema analyseren", "query genereren", "db structuur", "tabel overzicht" |
| `ddd-patterns` | `skills/ddd-patterns/` | "aggregate", "bounded context", "domain event", "value object", "repository pattern" |
| `belgian-commerce` | `skills/belgian-commerce/` | "btw", "belgisch recht", "intracom", "taalwetgeving", "consumentenwet", "factuur" |
| `mollie-payments` | `skills/mollie-payments/` | "mollie", "betaling", "webhook", "refund", "bancontact", "payment status" |
| `order-lifecycle` | `skills/order-lifecycle/` | "order state", "lifecycle", "retour", "sla", "order timeout", "state machine" |
| `local-llm` | `skills/local-llm/` | "ollama timeout", "model traag", "gpu server", "cpu ollama", "gpt-oss leeg", "mistral slow" |
| `payroll-validation` | `skills/payroll-validation/` | "rsz", "loon", "bedrijfsvoorheffing", "vakantiegeld", "maaltijdcheques", "prc" |
| `fraud-patterns` | `skills/fraud-patterns/` | "fraud", "risicoscore", "velocity check", "fraude detectie", "device fingerprint" |
| `project-explainer` | `skills/project-explainer/` | "project uitleggen", "codebase overzicht", "waar beginnen", "nieuwe developer", "onboarding" |
| `env-audit` | `skills/env-audit/` | "env ontbreekt", "environment variabele", ".env controleren", "onboarding", "secrets controleren" |
| `agent-performance` | `skills/agent-performance/` | "agent presteert slecht", "prompt verbeteren", "agent score", "valideer agents", "lage score" |
| `mollie-checkout-validator` | `skills/mollie-checkout-validator/` | "mollie checkout", "hmac verificatie", "webhook signature", "checkout valideren", "mollie security" |
| `frontend-component-auditor` | `skills/frontend-component-auditor/` | "component auditen", "data-testid ontbreekt", "server component audit", "typescript strict", "use client" |

---

## GitHub Copilot Agents (`.github/agents/`)

> **Let op: twee aparte agent-systemen!**
> - `.claude/agents/` → Claude Code delegates (subprocessen, volledige toolset)
> - `.github/agents/` → GitHub Copilot Chat (`@agent-naam` in VS Code / web)
>
> Ze overlappen qua domein maar zijn niet identiek — Claude agents zijn diepgaander,
> Copilot agents zijn breder. Kies op basis van je tool.

26 gespecialiseerde agents — aanroepen via `@agent-naam` in GitHub Copilot Chat:

| Categorie | Agents |
|-----------|--------|
| Architecture | `@architect`, `@ddd-modeler`, `@domain-validator` |
| Development | `@developer`, `@frontend-specialist`, `@clean-code-reviewer`, `@security-permissions`, `@devops-engineer`, `@database-expert`, `@mollie-expert`, `@performance-optimizer`, `@performance-profiler` |
| Domain | `@klantenservice-expert`, `@product-content`, `@seo-specialist`, `@order-expert`, `@prompt-engineer` |
| Testing | `@automation-cypress`, `@playwright-mcp`, `@regression-selector`, `@test-data-designer`, `@test-orchestrator` |
| Database | `@data-migrator` |
| **Consultancy** 🆕 | `@code-analyzer`, `@it-consultant`, `@business-process-advisor` |

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

## Capabilities (`.claude/capabilities/`)

Geregistreerde capabilities die Claude kan uitvoeren via `/capability run <naam>`:

| Capability | Beschrijving |
|------------|-------------|
| `feature-development` | Volledige feature bouwen: architectuur → code → tests → review |
| `code-review` | Code review met SOLID, security, performance checks |
| `test-generation` | pytest + Cypress E2E testsuites genereren |
| `gdpr-compliance` | GDPR audit: bewaartermijnen, anonimisatie, verwerkingsregister |
| `database-exploration` | DB schema analyseren en queries genereren |
| `ollama-agent-design` | Nieuwe Ollama runtime agent ontwerpen en testen |
| `ci-debugging` | GitHub Actions CI-fouten analyseren en fixen |

---

## Quick start — Nieuwe agents

### GDPR compliance check
```
"Controleer of onze klantdata GDPR-compliant bewaard wordt"
"Wat is de bewaartermijn voor besteldata?"
"Hoe implementeren we het recht op vergetelheid?"
```
→ `gdpr-advisor` agent + `gdpr-privacy` skill

### Database analyse
```
"Analyseer het schema van de orders tabel"
"Schrijf een query voor alle openstaande betalingen"
"Toon de database structuur"
```
→ `db-explorer` agent + `database-explorer` skill

### Parallelle feature-ontwikkeling
```
"Werk aan feature X en Y tegelijkertijd"
"Geef me een aparte worktree voor deze bugfix"
```
→ `feature-worker` agent (isolation: worktree)

---

## Scripts (`.claude/scripts/`)

| Script | Gebruik |
|--------|---------|
| `check-env.mjs` | Valideert `.env` vs `.env.example` — meldt ontbrekende variabelen |
| `validate-agents.mjs` | Valideert alle Claude agents op correcte YAML frontmatter |
| `analyse-agent-performance.mjs` | Scoort alle agents op 5 dimensies (0–1.0), genereert JSON rapport |

```bash
node .claude/scripts/check-env.mjs
node .claude/scripts/validate-agents.mjs
node .claude/scripts/analyse-agent-performance.mjs
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
| Frontend | Next.js 16.2, TypeScript strict, Tailwind CSS, App Router |
| Backend | FastAPI (Python 3.12), async SQLAlchemy 2.x |
| Database | PostgreSQL 16, Alembic migraties |
| Cache | Redis 7 |
| AI | Ollama (llama3, mistral) — volledig lokaal |
| Betalingen | Mollie API (+ simuleer-endpoint voor dev) |
| Auth | Keycloak (dev), NextAuth |
| Container | Docker Compose |
| CI/CD | GitHub Actions (4 jobs: python, yaml-validate, frontend, java) |
