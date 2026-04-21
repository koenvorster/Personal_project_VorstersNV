# Project Context — VorstersNV

## Wat is dit project?

**VorstersNV** is een Belgisch e-commerce platform (webshop) voor een KMO, aangedreven door
lokale AI-agents via Ollama. Het platform verwerkt bestellingen, betalingen (Mollie),
klantcommunicatie en productbeschrijvingen — volledig GDPR-compliant.

---

## Architectuuroverzicht

```
┌──────────────┐    ┌──────────────────┐    ┌───────────────────┐
│   Frontend   │    │   API / Backend  │    │   AI Agents Layer │
│  (Next.js)   │◄──►│   (FastAPI)      │◄──►│   (Ollama Local)  │
│  :3000       │    │   :8000          │    │   :11434          │
└──────────────┘    └──────────────────┘    └───────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         PostgreSQL        Redis         Keycloak
           :5432           :6379          :8080
```

---

## Primaire Backend: FastAPI (NIET Spring Boot)

De map `backend/` bevat een **legacy** Java/Spring Boot project — dit wordt NIET actief
ontwikkeld. De **primaire backend** is:

```
api/              ← FastAPI (Python 3.12) — dit is de actieve backend
  main.py         ← App entry point
  routers/        ← Endpoints per domein
  models/         ← SQLAlchemy 2.x ORM modellen
  schemas/        ← Pydantic v2 request/response
  dependencies.py ← FastAPI Depends()
```

---

## DDD Bounded Contexts

| Context | Beschrijving | Sleutelentiteiten |
|---------|-------------|-------------------|
| **Webshop** | Producten, categorieën, zoeken | Product, Categorie, Review |
| **Orders** | Bestellingen, orderlijnen, statussen | Order, OrderLine, Klant |
| **Betalingen** | Mollie integratie, webhooks | Betaling, Refund |
| **Voorraad** | Voorraadbeheer, low-stock alerts | Inventory, Alert |
| **Klanten** | Klantprofielen, adressen | Klant, Adres |
| **AI Agents** | Ollama agent uitvoering, logs | AgentLog, AgentRun |

---

## AI Agents (Ollama — volledig lokaal)

Agents staan in `agents/*.yml`. Ze worden aangeroepen via de FastAPI API of direct via scripts.

| Agent | Model | Doel |
|-------|-------|------|
| `klantenservice_agent_v2` | mistral | Klantreacties genereren |
| `product_beschrijving_agent` | llama3 | SEO-teksten schrijven |
| `seo_agent` | mistral | Zoekwoorden en metateksten |
| `order_verwerking_agent` | llama3 | Orderverwerking orkestreren |
| `fraude_detectie_agent` | mistral | Risicoscore berekenen |
| `product_recommender_agent` | llama3 | Productaanbevelingen |
| `review_analyzer_agent` | mistral | Klantreviews analyseren |

---

## Betalingen: Mollie

- API endpoint: `/api/betalingen/`
- Webhooks: `webhooks/` directory (aparte FastAPI app)
- Betaalmethoden: Bancontact, iDEAL, Visa/MC, SEPA
- Dev: `POST /api/betalingen/simuleer` voor test-betalingen
- Secret: `MOLLIE_API_KEY` in `.env`

---

## Database

- **PostgreSQL 16** — hoofddatabase
- **Alembic** voor migraties (`alembic.ini` + `alembic_analytics.ini`)
- **Redis 7** — caching (productlijsten), sessies
- In-memory SQLite voor unit tests (geen PostgreSQL vereist voor `pytest`)

---

## Poorten (Docker Compose)

| Service | Poort | Beschrijving |
|---------|-------|-------------|
| Next.js frontend | 3000 | Webshop UI |
| FastAPI backend | 8000 | REST API |
| PostgreSQL | 5432 | Hoofddatabase |
| Redis | 6379 | Cache |
| Keycloak | 8080 | Auth (dev) |
| Ollama | 11434 | AI model server |

---

## Tech Stack Samenvatting

| Laag | Technologie | Versie |
|------|-------------|--------|
| Frontend | Next.js, TypeScript, Tailwind CSS | 14, strict, 3.x |
| Backend | FastAPI, Python | 3.12 |
| ORM | SQLAlchemy async | 2.x |
| Validatie | Pydantic | v2 |
| Database | PostgreSQL | 16 |
| Cache | Redis | 7 |
| AI | Ollama (llama3, mistral) | lokaal |
| Betalingen | Mollie API | v2 |
| Auth | Keycloak, NextAuth | — |
| Container | Docker Compose | — |
| CI/CD | GitHub Actions | — |

---

## Belgische Compliance

- **BTW**: 21% standaard, 6% voeding/boeken, 0% export
- **Taalwetgeving**: NL voor Vlaamse klanten, FR voor Waalse klanten
- **GDPR**: bewaartermijnen, recht op vergetelheid, verwerkingsregister
- **Consumentenwet**: 14 dagen herroepingsrecht, retourbeleid

---

## Code Patronen — Snelreferentie

### Nieuwe API endpoint toevoegen

```python
# api/routers/producten.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.schemas.product import ProductCreate, ProductResponse
from api.services.product_service import ProductService
from db.database import get_db

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    """Maak een nieuw product aan. Business logica in ProductService."""
    return await ProductService(db).create(payload)
```

### Frontend pagina ophalen van API

```tsx
// frontend/app/(shop)/producten/page.tsx — Server Component
// Geen "use client" nodig — data fetch op server
export default async function ProductenPage() {
  const res = await fetch(`${process.env.API_URL}/api/products/`, {
    next: { revalidate: 60 },  // ISR cache: 60 seconden
  });
  const { items } = await res.json();
  return <ProductGrid producten={items} />;
}
```

### AI Agent aanroepen via FastAPI

```python
# api/services/ai_service.py
import httpx

async def genereer_productbeschrijving(product_naam: str, categorie: str) -> str:
    """Roept product_beschrijving_agent aan via Ollama."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": "llama3",
                "prompt": f"Schrijf een SEO-tekst voor: {product_naam} ({categorie})",
                "stream": False,
            },
            timeout=30.0,
        )
    return response.json()["response"]
```

### Mollie betaling aanmaken

```python
# api/services/payment_service.py
async def maak_betaling(order: Order) -> str:
    """Retourneert checkout URL voor Mollie Bancontact betaling."""
    payment = mollie_client.payments.create({
        "amount": {"currency": "EUR", "value": f"{order.totaal:.2f}"},
        "description": f"Order #{order.id} — VorstersNV",
        "redirectUrl": f"{settings.BASE_URL}/orders/{order.id}/bevestiging",
        "webhookUrl": f"{settings.BASE_URL}/webhook/mollie",
        "method": "bancontact",
        "metadata": {"order_id": str(order.id)},
    })
    return payment.checkout_url
```

### Database query met async SQLAlchemy

```python
# api/repositories/order_repository.py
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def get_order_met_regels(session: AsyncSession, order_id: int) -> Order | None:
    """Haal order op inclusief orderregels en producten (geen N+1)."""
    result = await session.execute(
        select(Order)
        .options(
            selectinload(Order.regels).selectinload(OrderRegel.product)
        )
        .where(Order.id == order_id)
    )
    return result.scalar_one_or_none()
```

---

## Lokale Ontwikkeling — Snel Starten

```bash
# Start alle services
docker compose up -d

# Check gezondheid
curl http://localhost:8000/health

# API documentatie
open http://localhost:8000/docs

# Frontend
open http://localhost:3000

# Test suite (geen PostgreSQL nodig — SQLite in-memory)
pytest tests/ -v --tb=short
```
