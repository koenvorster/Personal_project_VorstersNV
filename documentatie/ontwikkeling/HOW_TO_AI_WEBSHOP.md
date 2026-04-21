# How-To: Van nul naar AI-aangedreven webshop — het VorstersNV verhaal

> **Voor wie?** Ontwikkelaars, technische ondernemers en iedereen die nieuwsgierig is naar hoe je een echte webshop bouwt met lokale AI — zonder cloud-kosten of data die je bedrijf verlaat.

---

## Het begin: waarom dit project?

Alles begon met een simpele vraag: _"Kan ik een webshop bouwen die slim genoeg is om klanten te helpen, zonder dure abonnementen op ChatGPT of externe AI-diensten?"_

Het antwoord bleek: **ja, met Ollama, FastAPI en wat geduld**.

Dit is de stap-voor-stap handleiding van hoe ik VorstersNV heb opgebouwd — een volledig functioneel e-commerce platform met lokale AI-agents, een moderne webshop frontend, betalingen en een CI/CD pipeline.

---

## Wat heb je nodig?

### Hardware & OS
- Een PC of laptop met minstens **8 GB RAM** (16 GB aanbevolen voor Ollama)
- Windows 10/11, macOS of Linux (wij gebruikten Windows)
- Docker Desktop geïnstalleerd

### Software
- **Python 3.12** — de backend taal
- **Node.js 20+** — voor de Next.js frontend
- **Docker Compose** — voor PostgreSQL, Redis en Ollama lokaal
- **Git + GitHub** — versiebeheer en CI/CD
- **GitHub Copilot CLI** (optioneel maar *sterk* aanbevolen — dit is hoe we 90% van de code schreven)

### Kennis (basis volstaat)
- Basiskennis Python en JavaScript/TypeScript
- Begrip van REST APIs
- Docker-basis (images, containers, volumes)

---

## Stap 1: De AI lokaal draaien met Ollama

Ollama is een tool waarmee je grote taalmodellen (LLMs) lokaal op je eigen machine kunt draaien. Geen API-sleutels, geen kosten per request, geen data die je bedrijf verlaat.

```bash
# Installeer Ollama (zie ollama.ai)
# Start daarna modellen:
ollama pull llama3      # voor klantenservice en orderverwerking
ollama pull mistral     # voor SEO en productbeschrijvingen
```

### docker-compose.yml voor Ollama

```yaml
services:
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  database:
    image: postgres:16
    environment:
      POSTGRES_DB: vorstersNV
      POSTGRES_USER: vorstersNV
      POSTGRES_PASSWORD: dev-password-change-me
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

```bash
docker-compose up -d
```

---

## Stap 2: De backend opbouwen met FastAPI

FastAPI is een moderne Python web-framework dat perfect past bij async operaties — essentieel voor AI-aanroepen die even kunnen duren.

### Projectstructuur

```
backend/
├── api/
│   ├── routers/
│   │   ├── products.py      # Producten CRUD
│   │   ├── orders.py        # Bestellingen
│   │   ├── betalingen.py    # Checkout + betaalflow
│   │   └── agents.py        # AI agent endpoints
│   └── auth/
│       └── jwt.py           # Keycloak JWT validatie
├── db/
│   ├── base.py              # SQLAlchemy Base (apart!)
│   ├── database.py          # Engine + sessie
│   ├── models/              # ORM modellen
│   └── migrations/          # Alembic migraties
└── ollama/
    ├── client.py            # HTTP client voor Ollama
    ├── agent_runner.py      # Laadt agent YAML + voert uit
    └── orchestrator.py      # Multi-agent pipelines
```

### Kritieke les: db/base.py

**Grootste valkuil** bij Alembic + async SQLAlchemy:

```python
# ❌ FOUT: Base en engine in hetzelfde bestand
# Als Alembic models importeert, crasht het door asyncpg

# ✅ JUIST: db/base.py heeft ALLEEN Base
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

Alembic gebruikt sync psycopg2, maar FastAPI gebruikt async asyncpg. Door `Base` te isoleren vermijd je de "InvalidRequestError" die ons een uur kostte.

### Gast checkout zonder verplichte login

```python
# api/auth/jwt.py
async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> TokenData | None:
    """Geeft TokenData als ingelogd, None als gast. Nooit 401."""
    if credentials is None:
        return None
    try:
        return await _valideer_keycloak_token(credentials.credentials)
    except HTTPException:
        return None
```

```python
# api/routers/betalingen.py
async def bestelling_aanmaken(
    body: BestellingAanmakenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[TokenData | None, Depends(get_optional_user)] = None,
):
    # Ingelogd? Gebruik JWT-email (spoof-safe)
    if current_user is not None:
        body = body.model_copy(update={
            "klant_email": current_user.email,
            "klant_naam": current_user.naam,
        })
```

---

## Stap 3: AI Agents bouwen

Elk AI-gedrag is gedefinieerd als een YAML-bestand. Zo houd je de configuratie gescheiden van de code.

### Agent YAML structuur

```yaml
# agents/klantenservice_agent.yml
name: klantenservice_agent
version: "2.1"
model: llama3
temperature: 0.3
max_tokens: 800
system_prompt_ref: prompts/system/klantenservice.txt
preprompt_ref: prompts/preprompt/klantenservice_v3.yml
capabilities:
  - klantvragen_beantwoorden
  - retour_verwerken
  - order_info_opzoeken
  - escalatie_detecteren
evaluation:
  feedback_loop: true
  metrics:
    - klant_tevredenheid
    - oplossings_percentage
```

### Agent Runner

```python
# ollama/agent_runner.py
class AgentRunner:
    def __init__(self, agent_name: str, config: RetryConfig):
        self.config = self._load_agent(agent_name)
        self.retry_config = config
        self.client = OllamaClient()

    def _load_agent(self, name: str) -> dict:
        path = Path(f"agents/{name}.yml")
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    async def run(self, user_input: str, context: dict = {}) -> AgentResult:
        system = self._load_system_prompt()
        preprompt = self._load_preprompt()
        full_prompt = f"{preprompt}\n\nKlant: {user_input}"

        for attempt in range(self.retry_config.max_attempts):
            try:
                response = await self.client.generate(
                    model=self.config["model"],
                    system=system,
                    prompt=full_prompt,
                )
                return AgentResult(success=True, content=response)
            except Exception as e:
                if attempt == self.retry_config.max_attempts - 1:
                    raise
                await asyncio.sleep(self.retry_config.backoff_seconds)
```

### Multi-agent Orchestrator

```python
# ollama/orchestrator.py
async def run_checkout_pipeline(klant_probleem: str, context: dict) -> dict:
    """
    Checkout fout → begeleiding → orderbevestiging email
    """
    checkout_runner = get_runner("checkout_begeleiding_agent")
    email_runner = get_runner("email_template_agent")

    begeleiding = await checkout_runner.run(klant_probleem, context)

    if begeleiding.success:
        email = await email_runner.run(
            f"Stuur orderbevestiging voor: {context.get('order_id')}",
            context
        )

    return {
        "begeleiding": begeleiding.content,
        "email_verstuurd": email.success if email else False,
    }
```

---

## Stap 4: De frontend met Next.js

```bash
cd frontend
npm install
npm run dev  # start op http://localhost:3000
```

### Architectuur keuzes

- **App Router** (niet Pages Router) — toekomstgericht
- **Server Components** voor productlijsten (SEO + snelheid)
- **Client Components** voor cart, filters, checkout form
- **Zustand** voor cart state management
- **Tailwind CSS** voor styling

### API proxy via Next.js

```typescript
// frontend/app/api/products/route.ts
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const backendUrl = process.env.FASTAPI_URL;

  const response = await fetch(
    `${backendUrl}/api/products?${searchParams}`,
    { next: { revalidate: 60 } }  // 60s cache
  );

  return Response.json(await response.json());
}
```

---

## Stap 5: Database met Alembic migraties

```bash
# Stel .env in:
DB_URL=postgresql+psycopg2://vorstersNV:dev-password@localhost:5432/vorstersNV

# Maak eerste migratie:
alembic revision --autogenerate -m "initial_webshop"

# Voer uit:
alembic upgrade head
```

### Seed data voor ontwikkeling

```python
# scripts/seed_dev.py
async def seed():
    async with AsyncSessionLocal() as db:
        categorieen = [
            Categorie(naam="Elektronica", slug="elektronica"),
            Categorie(naam="Kantoor", slug="kantoor"),
            Categorie(naam="Opslag", slug="opslag"),
        ]
        db.add_all(categorieen)
        await db.flush()

        producten = [
            Product(
                naam="USB-C Hub Pro",
                slug="usb-c-hub-pro",
                prijs=Decimal("49.99"),
                voorraad=25,
                laag_voorraad_drempel=5,  # NIET NULL — vergeet dit niet!
                categorie_id=categorieen[0].id,
                actief=True,
            ),
            # ... meer producten
        ]
        db.add_all(producten)
        await db.commit()
```

---

## Stap 6: CI/CD met GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: ruff check .
      - run: pytest tests/ -v

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: cd frontend && npm ci && npx tsc --noEmit
```

---

## Stap 7: GitHub Copilot CLI als AI-ontwikkelassistent

Dit is misschien wel de grootste productiviteitsboost van het hele project. Met GitHub Copilot CLI kun je in je terminal praten over je code:

```bash
# Installeer
npm install -g @github/copilot-cli

# Gebruik
gh copilot suggest "maak een async FastAPI endpoint voor bestellingen"
gh copilot explain "wat doet deze Alembic migratie?"
```

Maar nog krachtiger: de **interactieve CLI-modus** waarbij Copilot de code daadwerkelijk schrijft, tests uitvoert, linter-fouten oplost — allemaal in één gesprek.

**Wat we ermee deden:**
- Volledige backend rewrite van mock naar DB-backed in één sessie
- Alembic migratie-problemen debuggen
- 100 pytest tests schrijven
- GitHub Actions workflows opzetten
- AI agent YAML configuraties genereren

---

## Lessons learned

### 1. Begin met de databse, niet de UI
Alembic migraties en het datamodel zijn de fundering. Een goede `Base` in `db/base.py` scheelt uren debugging.

### 2. Prijzen altijd uit de DB halen
```python
# ❌ Nooit dit doen:
prijs = cart_item.prijs  # komt van de client → manipuleerbaar

# ✅ Altijd dit:
prijs = products_map[cart_item.product_id].prijs  # komt uit de DB
```

### 3. Async overal, maar pas op bij Alembic
FastAPI en asyncpg werken geweldig samen. Maar Alembic is sync. Zorg dat je twee aparte DB_URL configs hebt:
- `postgresql+asyncpg://` voor runtime (FastAPI)
- `postgresql+psycopg2://` voor migraties (Alembic)

### 4. JWT security in productie
```python
# ❌ Nooit in productie:
options={"verify_aud": False}

# ✅ Gebruik env-var:
_VERIFY_AUD = os.environ.get("KEYCLOAK_VERIFY_AUD", "false").lower() == "true"
```

### 5. AI agents = YAML + prompts + runner
Houd de AI-logica gescheiden van business-logica. Een agent is gewoon een YAML-bestand met een model, een system prompt en een preprompt. De runner doet de rest.

---

## Technologieoverzicht

| Laag | Technologie | Waarom |
|------|-------------|--------|
| Frontend | Next.js 14 (App Router) | SSR, TypeScript, groot ecosystem |
| Backend | FastAPI (Python 3.12) | Snel, async, automatische docs |
| Database | PostgreSQL 16 + SQLAlchemy async | Betrouwbaar, relaties, migrations |
| Cache | Redis 7 | Sessies, rate limiting |
| Lokale AI | Ollama (llama3, mistral) | Privacy, geen kosten, offline |
| Auth | Keycloak | Enterprise-grade, JWKS |
| Betalingen | Mollie | Belgische markt, ideal, bancontact |
| CI/CD | GitHub Actions | Gratis, geïntegreerd, 5 workflows |
| Containerisatie | Docker Compose | Reproduceerbare lokale omgeving |
| AI-assistent | GitHub Copilot CLI | Code schrijven, debuggen, reviewen |

---

## Wat komt er nog?

- **Mollie betalingen** — echte checkout met iDEAL, Bancontact, creditcard
- **Checkout pagina** — /checkout in Next.js met formulier + cart overzicht
- **E-mail notificaties** — orderbevestiging, verzending, factuur via email agent
- **Linux thuis-server** — portfolio en demo hosten voor vrienden en collega's
- **Cloud deployment** — Google Cloud Run voor productie

---

## Bronnen

- [FastAPI documentatie](https://fastapi.tiangolo.com)
- [Ollama](https://ollama.ai)
- [Next.js App Router](https://nextjs.org/docs/app)
- [SQLAlchemy async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Mollie API](https://docs.mollie.com)
- [GitHub Copilot CLI](https://githubnext.com/projects/copilot-cli)

---

*Geschreven door Koen Vorster — gebouwd met GitHub Copilot CLI*
