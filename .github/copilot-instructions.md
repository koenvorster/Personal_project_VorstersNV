# Copilot Instructions – VorstersNV

## Projectoverzicht

VorstersNV is een freelance **IT/AI-consultancy platform** voor Belgische KMOs, aangedreven door lokale AI-agents via Ollama.
Het project bestaat uit een **FastAPI backend**, **Next.js frontend**, een **YAML-gebaseerd agent-systeem** en **consultancy tooling**.

**Primaire focus (Fase 6)**: legacy code-analyse, bedrijfsproces automatisering, AI-agents bouwen voor klanten.
**Revisie 6 (W10–W12)**: klantklaar platform — portal auth, multi-tenant isolatie, Cloud Run FastAPI deploy, klantrapportage UI, PDF-export, email notificaties.
De webshop is lager geprioriteerd — consultancy tools zijn het actieve ontwikkeldomein.

---

## Taal & Communicatie

- **Code**: Engels (variabelenamen, functies, klassen, commentaar in code)
- **Documentatie & plannen**: Nederlands
- **Commit messages**: Nederlands
- **API responses / logs**: Engels

---

## Projectstructuur

```
Personal_project_VorstersNV/
├── .github/
│   ├── agents/               # 29 Copilot development agents (.agent.md)
│   └── copilot-instructions.md
├── agents/                   # Runtime Ollama agent YAML-definities (32 bestanden)
├── ollama/                   # Ollama Python module (47 modules)
│   ├── client.py             # OllamaClient – HTTP-communicatie met Ollama
│   ├── agent_runner.py       # Laadt agent YAML + voert agent uit
│   ├── prompt_iterator.py    # Prompt-versies vergelijken via feedback-scores
│   ├── control_plane.py      # Centrale routing, policy, HITL, ring-beslissing
│   ├── compliance_engine.py  # GDPR / NIS2 / BTW / EU AI Act validator (W9)
│   ├── diagram_renderer.py   # Mermaid/PlantUML architectuurdiagrammen (W9)
│   ├── reasoning_logger.py   # Chain-of-thought logging per sessie (W9)
│   ├── rag_engine.py         # RAG + HashEmbedding fallback (W7)
│   ├── knowledge_graph.py    # Knowledge graph + Mermaid export (W7)
│   ├── self_improvement.py   # FeedbackAnalyzer + SelfImprovementLoop (W8)
│   ├── recommendation_engine.py # Next-best-action via KnowledgeGraph (W8)
│   └── ... (35 meer modules: cost_governance, deployment_rings, skill_chain_orchestrator, ...)
├── backend/                  # Java Spring Boot 3.3.5 (Java 21) – aparte API-laag
│   └── src/main/java/dev/koenvorsters/
├── webhooks/                 # Python FastAPI webhook handlers
│   ├── app.py                # Hoofd FastAPI app + HMAC-verificatie
│   └── handlers/             # order_handler, payment_handler, inventory_handler
├── api/                      # FastAPI routers: products, orders, inventory
├── db/                       # SQLAlchemy modellen + Alembic migraties
├── frontend/                 # Next.js 16.2 (App Router, TypeScript)
├── prompts/
│   ├── system/               # System prompts per agent (.txt)
│   ├── preprompt/             # Preprompts per versie + iteratie-logs (.yml)
│   └── promptbooks/          # Uitgebreide prompt-documentatie (.md)
├── scripts/                  # Hulpscripts: set_mode.py, setup_ollama.py, test_agent.py
├── tests/                    # Pytest tests
├── plan/
│   ├── PLAN.md               # Projectplan met fases en checklists
│   └── mode.yml              # Actieve projectmode (plan / build / review)
├── docker-compose.yml        # Lokale services: Ollama, PostgreSQL, Redis, Webhooks
├── Dockerfile.webhooks       # Docker image voor de webhook service
├── requirements.txt          # Python dependencies
└── pyproject.toml            # Ruff + mypy + pytest configuratie
```

---

## DDD Bounded Contexts

| Context | Aggregates | Verantwoordelijkheid |
|---------|-----------|---------------------|
| **Catalog** | Product, Category | Producten, beschrijvingen, prijzen, stock-niveau |
| **Orders** | Order, OrderLine | Bestelflow, statussen, fraudecheck |
| **Inventory** | StockItem, Warehouse | Voorraadbeheer, herbesteldrempels |
| **Customer** | Customer, Address | Klantgegevens, adressen, voorkeuren |
| **Payments** | Payment, Refund | Mollie-integratie, terugbetalingen |
| **Notifications** | Notification | E-mails, SMS, push-berichten |

Ubiquitous language per context staat in de domein-agent YAML-bestanden in `agents/`.

---

## Technologiestack

| Laag | Technologie |
|------|-------------|
| Frontend | Next.js 16.2 (TypeScript, App Router, Tailwind CSS) |
| Backend API (Python) | FastAPI (Python 3.12) |
| Backend API (Java) | Spring Boot 3.3.5 (Java 21) in `backend/` |
| Lokale AI | Ollama – modellen: `llama3`, `mistral` |
| Agent Framework | YAML-definities geladen door `agent_runner.py` |
| Database | PostgreSQL 16 via SQLAlchemy (async) + Alembic migraties |
| Cache | Redis 7 |
| Betalingen | Mollie (primair) |
| Auth | Keycloak (dev) — productie-beslissing nog open |
| Containerisatie | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Code kwaliteit | Ruff (linter), mypy (type-check), pytest |

---

## Copilot Development Agent Fleet

Gebruik `@agent-naam` in Copilot Chat om een gespecialiseerde agent in te schakelen. Alle agents staan in `.github/agents/`.

### Architectuur & Design
| Agent | Aanroep | Doel |
|-------|---------|------|
| Architect | `@architect` | Systeemontwerp, ADRs, bounded contexts, integraties |
| DDD Modeler | `@ddd-modeler` | Domain model, aggregates, events, ubiquitous language |
| Domain Validator | `@domain-validator` | Valideer code vs domeinregels (Catalog, Orders, Inventory, Customer, Payments) |

### Ontwikkeling
| Agent | Aanroep | Doel |
|-------|---------|------|
| Developer | `@developer` | Python/FastAPI/Next.js/Java implementatie |
| Frontend Specialist | `@frontend-specialist` | Next.js 16.2, App Router, Tailwind, TypeScript |
| Clean Code Reviewer | `@clean-code-reviewer` | Code review: SOLID, clean code, refactoring |
| Security & Permissions | `@security-permissions` | HMAC, auth, input validatie, OWASP |
| DevOps Engineer | `@devops-engineer` | Docker, GitHub Actions CI/CD, Cloud Run |
| Database Expert | `@database-expert` | SQLAlchemy, Alembic migraties, PostgreSQL query-tuning |
| Mollie Expert | `@mollie-expert` | Betaalintegratie, webhooks, terugbetalingen |
| Performance Optimizer | `@performance-optimizer` | Core Web Vitals, Redis-caching, query-optimalisatie |

### Domein Experts
| Agent | Aanroep | Doel |
|-------|---------|------|
| Klantenservice Expert | `@klantenservice-expert` | Agent-prompts, escalatieflows, retourprocedures |
| Product Content | `@product-content` | Productbeschrijvingen, USPs, content kwaliteit |
| SEO Specialist | `@seo-specialist` | Meta tags, structured data, sitemap, robots.txt |
| Order Expert | `@order-expert` | Order lifecycle, fraudedetectie, Mollie-flow |
| Prompt Engineer | `@prompt-engineer` | AI prompt-iteratie, feedback-analyse, temperature-tuning |

### Freelance IT/AI Consultancy 🆕
| Agent | Aanroep | Doel |
|-------|---------|------|
| Code Analyzer | `@code-analyzer` | Bestaande codebases analyseren (Java/Python/PHP/C#), business logic extraheren |
| IT Consultant | `@it-consultant` | Klantvoorstellen, IT/AI strategie, executive summaries, offertes |
| Business Process Advisor | `@business-process-advisor` | Processen in kaart brengen (AS-IS/TO-BE), automatiseringskansen, ROI |

---

## Copilot Prompt Skills

Herbruikbare prompt-templates in `.github/prompts/`. Gebruik via `#file:.github/prompts/<naam>.prompt.md` in Copilot Chat of via het `@` agent-systeem.

| Prompt File | Gebruik |
|-------------|---------|
| `nieuw-endpoint.prompt.md` | Genereer complete FastAPI endpoint + schema + test |
| `nieuwe-agent.prompt.md` | Maak nieuwe runtime Ollama agent (YAML + prompts) |
| `db-migratie.prompt.md` | SQLAlchemy model + Alembic migratie aanmaken |
| `security-audit.prompt.md` | OWASP security audit op code of module |
| `agent-debug.prompt.md` | Debug falende of underperformende Ollama agent |
| `mollie-checkout.prompt.md` | Volledige Mollie checkout flow implementeren |
| `productpagina.prompt.md` | Next.js productpagina met SEO + structured data |

### Testing & Kwaliteit
| Agent | Aanroep | Doel |
|-------|---------|------|
| Test Orchestrator | `@test-orchestrator` | Teststrategie, risicoanalyse, coverage |
| Test Data Designer | `@test-data-designer` | Testdata sets, boundary values, combinatorics |
| Playwright MCP | `@playwright-mcp` | E2E tests: shop, checkout, admin flows |
| Automation Cypress | `@automation-cypress` | Cypress component + API tests |
| Regression Selector | `@regression-selector` | Welke tests na een wijziging uitvoeren |

---

## Runtime AI-agents (Ollama)

Elke runtime-agent is gedefinieerd als een YAML-bestand in `agents/` en heeft:
- `model`: het Ollama-model (llama3 of mistral)
- `system_prompt_ref`: pad naar de system prompt
- `preprompt_ref`: pad naar de preprompt (versie-gebaseerd)
- `capabilities`: lijst van wat de agent kan
- `evaluation`: metrics + feedback_loop flag

### Kern Agents
| Agent YAML | Model | Doel |
|------------|-------|------|
| `klantenservice_agent_v2.yml` | llama3 | Klantvragen, escalatie, sentimentanalyse |
| `product_beschrijving_agent.yml` | llama3 | Productbeschrijvingen + SEO-tekst |
| `seo_agent.yml` | llama3 | SEO-optimalisatie pagina's en producten |
| `order_verwerking_agent.yml` | llama3 | Orderbevestiging, facturen, notificaties |
| `consultancy_orchestrator.yml` | llama3 | End-to-end IT/AI consultancy pipeline |
| `code_analyse_agent.yml` | llama3 | Legacy codebase analyse per chunk |
| `klant_rapport_agent.yml` | mistral | Klantgerichte samenvatting genereren |
| `bedrijfsproces_agent.yml` | llama3 | AS-IS/TO-BE procesanalyse + ROI |

### Sub-agents (selectie uit 32 totaal)
| Agent YAML | Model | Doel |
|------------|-------|------|
| `retour_verwerking_agent.yml` | llama3 | Retouraanvragen verwerken |
| `email_template_agent.yml` | llama3 | E-mailsjablonen genereren |
| `fraude_detectie_agent.yml` | llama3 | Fraudescores berekenen (0-100) |
| `voorraad_check_agent.yml` | llama3 | Voorraadbeheer + herbesteladvies |
| `java_chunk_analyse_agent.yml` | llama3 | Java-specifieke code-analyse |
| `architect_agent.yml` | llama3 | DDD-architectuur ontwerp + delegatie |

### Prompt Iteratie
- System prompts: `prompts/system/<agent>.txt`
- Preprompts per versie: `prompts/preprompt/<agent>_v1.txt`
- Iteratielogs: `prompts/preprompt/<agent>_iterations.yml`
- Feedback opslaan via `ollama/prompt_iterator.py`

---

## Coderichtlijnen

### Python
- Python 3.12, volledig async waar mogelijk
- Type hints overal verplicht
- Pydantic voor request/response validatie
- `async with` voor database sessies
- Fouten afhandelen met specifieke HTTPException statuscodes
- Logs via `logging.getLogger(__name__)` – geen `print()`

### FastAPI
- Routers in `api/routers/` per domein
- Dependency injection voor DB-sessie en auth
- `/health` endpoint altijd beschikbaar
- HMAC-verificatie voor alle webhook endpoints

### Next.js
- TypeScript strict mode
- App Router (niet Pages Router)
- Tailwind CSS voor styling
- Server Components standaard, Client Components alleen waar nodig
- API calls via `fetch` met typed responses

### Agent Runner
- Laad agent YAML via `pathlib.Path`
- Combineer system prompt + preprompt + user input
- Log elke aanroep met model, temperature en tokens
- Sla feedback op in iteratie-log YAML

---

## Lokale Ontwikkeling

```bash
# Start alle services
docker-compose up -d

# Installeer Python dependencies
pip install -r requirements.txt

# Draai tests
pytest tests/ -v

# Start webhook service lokaal (zonder Docker)
uvicorn webhooks.app:app --reload --port 8000

# Wissel projectmode
python scripts/set_mode.py --mode build
```

### Omgevingsvariabelen (.env)
```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3
WEBHOOK_SECRET=dev-secret-change-me
DB_URL=postgresql+asyncpg://vorstersNV:dev-password-change-me@localhost:5432/vorstersNV
REDIS_URL=redis://localhost:6379
```

---

## Projectmodes

| Mode | Wanneer |
|------|---------|
| `plan` | Nieuwe features ontwerpen, architectuur beslissingen |
| `build` | Actieve ontwikkeling en implementatie |
| `review` | Testen, prompt-iteraties, optimalisatie |

Huidige mode staat in `plan/mode.yml`.

---

## MCP Servers (Copilot CLI)

Configuratie in `mcp-config.json`. Actieve servers:

| Server | Gebruik |
|--------|---------|
| `ollama` | Lokale AI-modellen aanroepen via `agent_runner.py` |
| `github` | Issues, PRs, code zoeken (vereist `GITHUB_TOKEN`) |
| `playwright` | Browser automatisering, E2E tests, web scraping |
| `filesystem` | Lokale bestanden lezen/schrijven |
| `postgres` | Direct PostgreSQL queries (vereist `DB_URL`) |
| `fetch` | Externe URLs ophalen, API's aanroepen |
| `memory` | Feiten onthouden over sessies heen |
| **Atlassian** | **Ingebouwd in Copilot CLI** — Jira + Confluence zonder extra config |

### Atlassian MCP
De Atlassian integratie (Jira + Confluence) is beschikbaar via de ingebouwde Copilot CLI tools.
Geen extra setup nodig als je bent ingelogd via `gh auth login`.

Voor standalone gebruik (buiten Copilot CLI):
```bash
uvx mcp-atlassian --confluence-url https://jouw-site.atlassian.net
# Vereist: CONFLUENCE_API_TOKEN en JIRA_API_TOKEN environment variables
```

### Ollama op Remote Desktop Server
```bash
# .env op laptop — Ollama draait op gaming desktop
OLLAMA_HOST=http://192.168.1.XXX:11434
OLLAMA_DEFAULT_MODEL=llama3:70b
```

---

## Belangrijke Conventies

- Alle webhook payloads worden gevalideerd met HMAC-SHA256
- Agent-aanroepen worden gelogd in `logs/<agent_naam>/`
- Prompt-versies worden bijgehouden in `prompts/preprompt/*_iterations.yml`
- Database modellen komen in `db/models/`, migraties in `db/migrations/`
- Frontend API calls gaan altijd via `/api/` prefix (Next.js rewrites naar FastAPI)
- MCP server config staat in `mcp-config.json` — kopieer naar `~/.copilot/mcp.json` voor globaal gebruik
