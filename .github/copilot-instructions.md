# Copilot Instructions – VorstersNV

## Projectoverzicht

VorstersNV is een zakelijk platform met webshop, aangedreven door lokale AI-agents via Ollama.
Het project bestaat uit een **FastAPI backend**, **Next.js frontend** en een **YAML-gebaseerd agent-systeem**.

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
├── agents/               # YAML-definities per AI-agent
├── ollama/               # Ollama client + agent runner + prompt iterator
│   ├── client.py         # OllamaClient – HTTP-communicatie met Ollama
│   ├── agent_runner.py   # Laadt agent YAML + voert agent uit
│   └── prompt_iterator.py# Prompt-versies vergelijken via feedback-scores
├── webhooks/             # FastAPI webhook handlers
│   ├── app.py            # Hoofd FastAPI app + HMAC-verificatie
│   └── handlers/         # order_handler, payment_handler, inventory_handler
├── db/                   # (te bouwen) SQLAlchemy modellen + Alembic
├── api/                  # (te bouwen) FastAPI routers: products, orders, inventory
├── frontend/             # (te bouwen) Next.js webshop
├── prompts/
│   ├── system/           # System prompts per agent (.txt)
│   ├── prepromt/         # Preprompts per versie + iteratie-logs (.yml)
│   └── promptbooks/      # Uitgebreide prompt-documentatie (.md)
├── scripts/              # Hulpscripts: set_mode.py, setup_ollama.py, test_agent.py
├── tests/                # Pytest tests
├── plan/
│   ├── PLAN.md           # Projectplan met fases en checklists
│   └── mode.yml          # Actieve projectmode (plan / build / review)
├── docker-compose.yml    # Lokale services: Ollama, PostgreSQL, Redis, Webhooks
├── Dockerfile.webhooks   # Docker image voor de webhook service
├── requirements.txt      # Python dependencies
└── pyproject.toml        # Ruff + mypy + pytest configuratie
```

---

## Technologiestack

| Laag | Technologie |
|------|-------------|
| Frontend | Next.js 14 (TypeScript, App Router, Tailwind CSS) |
| Backend API | FastAPI (Python 3.12) |
| Lokale AI | Ollama – modellen: `llama3`, `mistral` |
| Agent Framework | YAML-definities geladen door `agent_runner.py` |
| Database | PostgreSQL 16 via SQLAlchemy (async) + Alembic migraties |
| Cache | Redis 7 |
| Betalingen | Mollie (primair) |
| Containerisatie | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Code kwaliteit | Ruff (linter), mypy (type-check), pytest |

---

## AI-agents

Elke agent is gedefinieerd als een YAML-bestand in `agents/` en heeft:
- `model`: het Ollama-model (llama3 of mistral)
- `system_prompt_ref`: pad naar de system prompt
- `prepromt_ref`: pad naar de preprompt (versie-gebaseerd)
- `capabilities`: lijst van wat de agent kan
- `evaluation`: metrics + feedback_loop flag

| Agent | Model | Doel |
|-------|-------|------|
| `klantenservice_agent` | llama3 | Klantvragen, retouren, order-info |
| `product_beschrijving_agent` | mistral | Productbeschrijvingen + SEO-tekst genereren |
| `seo_agent` | mistral | SEO-optimalisatie van pagina's en producten |
| `order_verwerking_agent` | llama3 | Orderbevestiging, facturen, notificaties |

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

## Belangrijke Conventies

- Alle webhook payloads worden gevalideerd met HMAC-SHA256
- Agent-aanroepen worden gelogd in `logs/<agent_naam>/`
- Prompt-versies worden bijgehouden in `prompts/prepromt/*_iterations.yml`
- Database modellen komen in `db/models/`, migraties in `db/migrations/`
- Frontend API calls gaan altijd via `/api/` prefix (Next.js rewrites naar FastAPI)
