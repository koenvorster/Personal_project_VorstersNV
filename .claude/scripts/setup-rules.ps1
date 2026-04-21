#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup-script voor de .claude/rules/ directory structuur (VorstersNV AI Fleet).
    
.DESCRIPTION
    Maakt alle benodigde mappen aan voor het Claude rules-systeem en schrijft
    de volledige inhoud van elk rule-bestand.
    
    Draai dit eenmalig vanuit de project root:
        .\.claude\scripts\setup-rules.ps1

.NOTES
    Dit script moet eenmalig worden uitgevoerd nadat de repository is gekloond.
    Daarna laadt Claude Code de rules automatisch op basis van open bestanden.
#>

param(
    [switch]$WhatIf
)

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $ProjectRoot

Write-Host "`n🏗️  VorstersNV — Claude Rules Setup" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot`n" -ForegroundColor Gray

# ─── Directory structuur aanmaken ────────────────────────────────────────────

$Dirs = @(
    ".claude/rules"
    ".claude/rules/backend"
    ".claude/rules/frontend"
    ".claude/rules/general"
    ".claude/rules/tools"
    ".claude/skills/project-explainer"
    ".claude/skills/env-audit"
    ".claude/skills/agent-performance"
)

foreach ($dir in $Dirs) {
    $path = Join-Path $ProjectRoot $dir
    if (-not (Test-Path $path)) {
        if (-not $WhatIf) {
            New-Item -ItemType Directory -Force -Path $path | Out-Null
            Write-Host "  📁 Aangemaakt: $dir" -ForegroundColor Green
        } else {
            Write-Host "  [WhatIf] Zou aanmaken: $dir" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ✅ Bestaat al: $dir" -ForegroundColor Gray
    }
}

# ─── Hulpfunctie voor bestandsschrijven ──────────────────────────────────────

function Write-RuleFile {
    param(
        [string]$RelPath,
        [string]$Content
    )
    $fullPath = Join-Path $ProjectRoot $RelPath
    if (Test-Path $fullPath) {
        Write-Host "  ⚠️  Bestaat al (overgeslagen): $RelPath" -ForegroundColor Yellow
        return
    }
    if (-not $WhatIf) {
        Set-Content -Path $fullPath -Value $Content -Encoding UTF8
        Write-Host "  ✅ Aangemaakt: $RelPath" -ForegroundColor Green
    } else {
        Write-Host "  [WhatIf] Zou schrijven: $RelPath" -ForegroundColor Yellow
    }
}

Write-Host "`n📝 Rule-bestanden schrijven..." -ForegroundColor Cyan

# ─── .claude/rules/backend/python-fastapi.md ─────────────────────────────────

Write-RuleFile ".claude/rules/backend/python-fastapi.md" @'
---
paths:
  - "**/*.py"
---

# Backend Conventies — Python 3.12 + FastAPI

## Project Context

Dit is het VorstersNV platform. De **primaire backend is FastAPI** in `api/` — niet Spring Boot in `backend/`.
Bij elke `.py` bestand: check eerst of het in `api/`, `webhooks/`, `tests/`, of `scripts/` staat.

---

## Strictheidsgraden

- **VERPLICHT** — alle Python bestanden in dit project
- **STRICT** — nieuwe code; refactor bestaande code alleen op expliciet verzoek
- **AANBEVOLEN** — best practice; suggereer maar dwing niet af

---

## Async/Await — VERPLICHT

**Alle database-operaties zijn async.** Gebruik nooit synchrone SQLAlchemy calls.

```python
# GOED
async def get_product(product_id: int, db: AsyncSession) -> Product:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()

# SLECHT — synchrone sessie in async context
def get_product(product_id: int, db: Session) -> Product:
    return db.query(Product).filter(Product.id == product_id).first()
```

FastAPI route handlers zijn altijd `async def`.

---

## Type Hints — VERPLICHT

Type hints zijn verplicht op alle functie-parameters en return types.

```python
# GOED
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession,
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    ...

# SLECHT
async def create_order(order_data, db, current_user=None):
    ...
```

- Gebruik `from __future__ import annotations` bovenaan voor forward references
- `Optional[X]` schrijf je als `X | None` (Python 3.10+ stijl)
- `Union[X, Y]` schrijf je als `X | Y`

---

## SQLAlchemy 2.x Async — VERPLICHT

```python
# GOED — SQLAlchemy 2.x stijl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Selecteren met eager loading (voorkom N+1 queries)
orders = await db.execute(
    select(Order)
    .options(selectinload(Order.order_lines).selectinload(OrderLine.product))
    .where(Order.klant_id == klant_id)
)

# Aanmaken
db.add(new_product)
await db.commit()
await db.refresh(new_product)

# SLECHT — legacy query API
db.query(Product).filter(Product.actief == True).all()
```

---

## Pydantic v2 — VERPLICHT

```python
# GOED — Pydantic v2 stijl
from pydantic import BaseModel, ConfigDict, field_validator

class ProductCreate(BaseModel):
    naam: str
    prijs: Decimal
    voorraad: int = 0

    model_config = ConfigDict(from_attributes=True)

    @field_validator("prijs")
    @classmethod
    def prijs_positief(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Prijs moet positief zijn")
        return v

# SLECHT — Pydantic v1 syntax
class ProductCreate(BaseModel):
    class Config:
        orm_mode = True  # <-- VEROUDERD
```

Migratiecheatsheet:
- `orm_mode = True` → `model_config = ConfigDict(from_attributes=True)`
- `@validator` → `@field_validator` (met `@classmethod`)
- `.dict()` → `.model_dump()`
- `.parse_obj()` → `model_validate()`

---

## Logging — VERPLICHT

**Nooit `print()` in productiecode.**

```python
import logging
logger = logging.getLogger(__name__)

# GOED
async def process_order(order_id: int) -> None:
    logger.info("Order verwerking gestart", extra={"order_id": order_id})
    try:
        ...
    except Exception as e:
        logger.error("Order verwerking mislukt", extra={"order_id": order_id}, exc_info=True)
        raise

# SLECHT
print(f"Order {order_id} verwerking gestart")
```

Log levels:
- `debug` — ontwikkelingsdetails
- `info` — business events (order aangemaakt, betaling ontvangen)
- `warning` — onverwacht maar herstelbaar (retry, fallback)
- `error` — fout die actie vereist; altijd met `exc_info=True`
- `critical` — systeem kan niet verder

---

## Guard Clauses — VERPLICHT

Max 2 nesting levels. Gebruik early returns voor validatie.

```python
# GOED — guard clauses
async def update_product(product_id: int, data: ProductUpdate, db: AsyncSession) -> Product:
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product niet gevonden")
    if not product.actief:
        raise HTTPException(status_code=400, detail="Inactief product")
    product.naam = data.naam or product.naam
    await db.commit()
    return product

# SLECHT — diep genest
async def update_product(product_id: int, data: ProductUpdate, db: AsyncSession) -> Product:
    product = await db.get(Product, product_id)
    if product:
        if product.actief:
            ...  # te diep genest
```

---

## DDD-structuur — STRICT

```
api/
  routers/          # FastAPI routers (controller layer) — max ~5 regels per endpoint
  models/           # SQLAlchemy ORM modellen — alleen datahouders, geen business logica
  schemas/          # Pydantic request/response schemas
  services/         # Business logica — alle DB-aanroepen gaan hier
  dependencies.py   # FastAPI Depends()
```

---

## Beveiliging — VERPLICHT

- Nooit secrets in code — gebruik `os.getenv()` of Pydantic `BaseSettings`
- Nooit `f"SELECT ... {user_input}"` — gebruik altijd SQLAlchemy parametrisatie
- Valideer alle input via Pydantic schema vóór database-operaties
- CORS: nooit `allow_origins=["*"]` in productie
'@

# ─── .claude/rules/frontend/nextjs-app-router.md ─────────────────────────────

Write-RuleFile ".claude/rules/frontend/nextjs-app-router.md" @'
---
paths:
  - "frontend/**/*.tsx"
  - "frontend/**/*.ts"
---

# Frontend Conventies — Next.js 14 App Router

## Project Context

VorstersNV frontend gebruikt **Next.js 14 met App Router** (niet Pages Router).
Alle componenten staan in `frontend/app/`. TypeScript strict mode is ingeschakeld.

---

## Strictheidsgraden

- **VERPLICHT** — alle Next.js bestanden
- **STRICT** — nieuwe componenten
- **AANBEVOLEN** — suggestie voor bestaande code

---

## Server Components — VERPLICHT

**Standaard zijn alle componenten Server Components.** Voeg `"use client"` ALLEEN toe als:
- `useState` / `useEffect` / `useCallback` / `useRef` nodig is
- Event listeners (onClick, onChange, etc.) nodig zijn
- Browser-only APIs nodig zijn (localStorage, window, etc.)

```tsx
// GOED — Server Component (geen "use client")
// frontend/app/shop/page.tsx
import { getProducts } from "@/lib/api";

export default async function ShopPage() {
  const products = await getProducts();  // Direct fetch in server component
  return <ProductGrid products={products} />;
}

// GOED — Client Component alleen waar nodig
// frontend/app/shop/add-to-cart-button.tsx
"use client";
import { useState } from "react";

export function AddToCartButton({ productId }: { productId: string }) {
  const [loading, setLoading] = useState(false);
  ...
}
```

---

## data-testid — VERPLICHT

Elk interactief UI-element krijgt een `data-testid` attribuut voor Cypress/Playwright tests.

```tsx
// GOED
<button
  data-testid="add-to-cart-btn"
  onClick={handleAddToCart}
>
  In winkelwagen
</button>

<input
  data-testid="search-input"
  type="text"
  placeholder="Zoeken..."
/>

<a data-testid="product-link" href={`/shop/${product.slug}`}>
  {product.naam}
</a>

// SLECHT — geen data-testid
<button onClick={handleAddToCart}>In winkelwagen</button>
```

Naamconventie: `kebab-case`, beschrijvend, uniek per pagina.
Voorbeelden: `checkout-btn`, `product-card-{id}`, `cart-quantity-input`.

---

## TypeScript Strict — VERPLICHT

TypeScript strict mode is actief. Geen `any` types tenzij absoluut onvermijdelijk (met TODO-comment).

```tsx
// GOED
interface Product {
  id: string;
  naam: string;
  prijs: number;
  categorie: string;
  actief: boolean;
}

async function getProduct(id: string): Promise<Product | null> {
  const res = await fetch(`/api/products/${id}`);
  if (!res.ok) return null;
  return res.json() as Promise<Product>;
}

// SLECHT
async function getProduct(id: any): Promise<any> {
  ...
}
```

---

## Tailwind — Geen Hardcoded Kleuren — VERPLICHT

Gebruik altijd Tailwind tokens of `brand-*` CSS variabelen. Nooit hardcoded hex/rgb waarden.

```tsx
// GOED
<div className="bg-brand-primary text-white rounded-lg p-4">
<div className="bg-blue-600 hover:bg-blue-700 text-white">
<div className="border border-gray-200 dark:border-gray-700">

// SLECHT
<div style={{ backgroundColor: "#1a73e8" }}>
<div className="bg-[#1a73e8]">
```

---

## Data Fetching — STRICT

```tsx
// GOED — Server Component: directe fetch met Next.js caching
async function ProductPage({ params }: { params: { slug: string } }) {
  const product = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/products/${params.slug}`,
    { next: { revalidate: 60 } }  // ISR: 60 seconden
  ).then(r => r.json());

  return <ProductDetail product={product} />;
}

// GOED — Productlijst: langere cache
fetch(url, { next: { revalidate: 300 } });

// GOED — Winkelwagen: altijd live
fetch(url, { cache: "no-store" });
```

---

## Loading States — VERPLICHT

Elke async data load toont een skeleton of loading state. Nooit lege ruimte tonen.

```tsx
// loading.tsx (Next.js App Router conventie)
export default function Loading() {
  return (
    <div className="grid grid-cols-3 gap-4" data-testid="products-skeleton">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="animate-pulse bg-gray-200 h-64 rounded-lg" />
      ))}
    </div>
  );
}
```

---

## Error Boundaries — STRICT

```tsx
// error.tsx naast elke page.tsx
"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div data-testid="error-boundary" className="text-center py-12">
      <h2>Er is iets misgegaan</h2>
      <button data-testid="retry-btn" onClick={reset}>
        Opnieuw proberen
      </button>
    </div>
  );
}
```

---

## Afbeeldingen — VERPLICHT

Altijd `next/image` gebruiken — nooit `<img>`.

```tsx
// GOED
import Image from "next/image";

<Image
  src={product.afbeelding_url}
  alt={product.naam}
  width={600}
  height={600}
  sizes="(max-width: 768px) 100vw, 600px"
  priority={isAboveFold}
/>

// SLECHT
<img src={product.afbeelding_url} alt={product.naam} />
```
'@

# ─── .claude/rules/backend/alembic-migrations.md ─────────────────────────────

Write-RuleFile ".claude/rules/backend/alembic-migrations.md" @'
---
paths:
  - "db/migrations/**/*.py"
  - "alembic.ini"
  - "alembic_analytics.ini"
---

# Alembic Migratie Conventies

## Project Context

VorstersNV heeft TWO alembic configuraties:
- `alembic.ini` — hoofddatabase (api schema)
- `alembic_analytics.ini` — analytics schema

Migraties staan in `db/migrations/versions/`.

---

## Verplichte Regels

### upgrade EN downgrade — VERPLICHT

Elke migratie heeft ALTIJD een functionele `upgrade()` EN `downgrade()` functie.
Nooit `pass` of `raise NotImplementedError()` in `downgrade()`.

```python
# GOED
def upgrade() -> None:
    op.add_column("products", sa.Column("slug", sa.String(255), nullable=True))
    op.create_index("ix_products_slug", "products", ["slug"], unique=True)

def downgrade() -> None:
    op.drop_index("ix_products_slug", table_name="products")
    op.drop_column("products", "slug")

# SLECHT
def downgrade() -> None:
    pass  # NOOIT — maak downgrade onmogelijk
```

### Nooit handmatig tabellen wijzigen — VERPLICHT

Alle schema-wijzigingen gaan via Alembic migraties. Nooit direct `ALTER TABLE`, `ADD COLUMN`
etc. uitvoeren op de database zonder bijbehorende migratie.

### Migration message is verplicht — VERPLICHT

```bash
# GOED — beschrijvende naam
alembic revision --autogenerate -m "add_slug_column_to_products"
alembic revision --autogenerate -m "add_klant_adres_table"
alembic revision -m "seed_initial_categories"

# SLECHT — vage naam
alembic revision -m "update"
alembic revision -m "changes"
alembic revision -m "fix"
```

### Test altijd na aanmaken — VERPLICHT

```bash
# Na het aanmaken van een migratie, test altijd:
alembic upgrade head      # migratie toepassen
alembic downgrade -1      # een stap terug
alembic upgrade head      # opnieuw toepassen (idempotentie check)
```

---

## Veelvoorkomende Patronen

### Kolom toevoegen (nullable eerst, dan not null)

```python
# Stap 1: voeg nullable kolom toe
def upgrade() -> None:
    op.add_column("orders", sa.Column("tracking_code", sa.String(100), nullable=True))

# Stap 2 (aparte migratie): vul data in + maak not null
def upgrade() -> None:
    op.execute("UPDATE orders SET tracking_code = 'ONBEKEND' WHERE tracking_code IS NULL")
    op.alter_column("orders", "tracking_code", nullable=False)
```

### Index aanmaken

```python
def upgrade() -> None:
    op.create_index(
        "ix_orders_klant_id_status",
        "orders",
        ["klant_id", "status"],
        unique=False
    )

def downgrade() -> None:
    op.drop_index("ix_orders_klant_id_status", table_name="orders")
```

### Foreign key toevoegen

```python
def upgrade() -> None:
    op.add_column("orders", sa.Column("klant_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_orders_klant_id",
        "orders", "klanten",
        ["klant_id"], ["id"],
        ondelete="SET NULL"
    )

def downgrade() -> None:
    op.drop_constraint("fk_orders_klant_id", "orders", type_="foreignkey")
    op.drop_column("orders", "klant_id")
```

---

## Autogenerate Waarschuwingen

Autogenerate detecteert NIET altijd:
- Wijzigingen in `server_default`
- PostgreSQL ENUM wijzigingen
- Partial indexes
- Trigger wijzigingen

Controleer altijd de gegenereerde migratie vóór gebruik.

---

## Data Migraties

Gebruik `op.execute()` voor data-transformaties:

```python
def upgrade() -> None:
    # Schema wijziging
    op.add_column("products", sa.Column("prijs_excl_btw", sa.Numeric(10, 2)))
    
    # Data migratie
    op.execute("""
        UPDATE products 
        SET prijs_excl_btw = ROUND(prijs / 1.21, 2)
        WHERE prijs IS NOT NULL
    """)
```
'@

# ─── .claude/rules/general/git-commits.md ────────────────────────────────────

Write-RuleFile ".claude/rules/general/git-commits.md" @'
# Git Commit Conventies — VorstersNV

## Taal — VERPLICHT

**Commit messages zijn Nederlandstalig.** Alleen technische termen (SQL, API, etc.) mogen Engels blijven.

## Format — VERPLICHT

```
<type>(<scope>): <beschrijving>

[optionele body — max 72 tekens per regel]
```

- Max 72 tekens voor de onderwerpregel
- Imperativusvorm: "voeg toe" niet "toegevoegd"
- Geen punt aan het einde

## Types — VERPLICHT

| Type | Wanneer |
|------|---------|
| `feat` | Nieuwe functionaliteit |
| `fix` | Bug repareren |
| `docs` | Alleen documentatie |
| `refactor` | Code herstructureren (geen bugfix, geen feature) |
| `test` | Tests toevoegen of aanpassen |
| `perf` | Performance verbetering |
| `ci` | CI/CD pipeline aanpassen |
| `chore` | Afhankelijkheden bijwerken, build scripts |

## Scopes — AANBEVOLEN

| Scope | Beschrijving |
|-------|-------------|
| `api` | FastAPI backend |
| `frontend` | Next.js frontend |
| `db` | Database / Alembic |
| `agents` | Ollama agents / prompts |
| `mollie` | Betalingsintegratie |
| `auth` | Keycloak / NextAuth |
| `docker` | Containerisatie |
| `ci` | GitHub Actions |

## Voorbeelden

```bash
# GOED
feat(api): voeg productaanbevelingen endpoint toe
fix(frontend): herstel winkelwagen-teller bij pagina-refresh
docs(agents): beschrijf klantenservice agent werking
refactor(db): extraheer order queries naar apart service bestand
test(api): voeg integratietests toe voor betalingsflow
perf(api): cache productlijst in Redis voor 5 minuten
feat(agents): voeg review analyzer agent toe met sentiment scoring
fix(mollie): herstel webhook handtekening verificatie

# SLECHT
update code            # te vaag
Fixed bug              # Engelstalig en geen type
added new feature      # Engelstalig en geen type prefix
feat: product          # te kort, geen scope
```

## Beveiliging — VERPLICHT

- **Nooit secrets committen** — API sleutels, wachtwoorden, `.env` bestanden
- **Nooit `Co-Authored-By` AI-attributie** toevoegen — commit auteur is de developer
- **Nooit force-push** op beschermde branches (`main`, `develop`)
'@

# ─── .claude/rules/general/project-context.md ────────────────────────────────

Write-RuleFile ".claude/rules/general/project-context.md" @'
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
'@

# ─── .claude/rules/tools/docker.md ──────────────────────────────────────────

Write-RuleFile ".claude/rules/tools/docker.md" @'
---
paths:
  - "docker-compose.yml"
  - "Dockerfile*"
  - ".devcontainer/**"
---

# Docker Conventies — VorstersNV

## Vaste Poorten — VERPLICHT

Wijzig nooit de servicepoorten zonder overleg. Dit zijn de vastgestelde poorten:

| Service | Host-poort | Container-poort | Beschrijving |
|---------|-----------|-----------------|-------------|
| Next.js | 3000 | 3000 | Frontend webshop |
| FastAPI | 8000 | 8000 | REST API + webhooks |
| PostgreSQL | 5432 | 5432 | Hoofddatabase |
| Redis | 6379 | 6379 | Cache |
| Keycloak | 8080 | 8080 | Auth server (dev) |
| Ollama | 11434 | 11434 | AI model server |

---

## Health Checks — VERPLICHT

Elke service in `docker-compose.yml` heeft een `healthcheck`:

```yaml
# GOED
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

# SLECHT — geen health check
services:
  api:
    image: vorsternv-api:latest
    # ontbrekende healthcheck
```

---

## Geen Secrets in Dockerfile — VERPLICHT

```dockerfile
# GOED — secrets via omgevingsvariabelen op runtime
ENV DATABASE_URL=""
ENV MOLLIE_API_KEY=""

# SLECHT — hardcoded secret in image
ENV MOLLIE_API_KEY="live_abc123..."
RUN echo "password123" | ...
```

Gebruik altijd `.env` of Docker secrets voor gevoelige waarden. Het `.env` bestand staat
in `.gitignore` en mag NOOIT worden gecommit.

---

## Multi-stage Builds — AANBEVOLEN

```dockerfile
# Stap 1: Build stage
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stap 2: Runtime stage (kleinere image)
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## depends_on met condition — STRICT

```yaml
# GOED — wacht op echte health
services:
  api:
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

# SLECHT — wacht alleen op start, niet op beschikbaarheid
services:
  api:
    depends_on:
      - postgres
      - redis
```

---

## Volumes Naamgeving — VERPLICHT

Gebruik beschrijvende namen voor named volumes:

```yaml
volumes:
  vorsternv_postgres_data:
    driver: local
  vorsternv_redis_data:
    driver: local
  vorsternv_ollama_models:
    driver: local
```

---

## Niet wijzigen zonder overleg

- `docker-compose.yml` servicepoorten
- PostgreSQL volume configuratie (risico op dataverlies)
- Keycloak realm configuratie
- Ollama model directory
'@

Write-Host "`n📝 Skill-bestanden schrijven..." -ForegroundColor Cyan

# ─── .claude/skills/project-explainer/SKILL.md ───────────────────────────────

Write-RuleFile ".claude/skills/project-explainer/SKILL.md" @'
---
name: project-explainer
description: >
  Use when: a new developer, stakeholder, or non-technical person asks "what does this project do?",
  "explain this codebase", "where do I start?", "give me an overview of VorstersNV",
  "wat is dit project?", "hoe is dit opgebouwd?", "leg uit wat VorstersNV doet".
  Produces a plain-language explanation of the platform, its domains, AI agents, and tech stack.
  Triggers: "project uitleggen", "codebase overzicht", "waar beginnen", "architectuur overzicht",
  "wat doet dit project", "nieuwe developer", "onboarding".
---

# Project Explainer — VorstersNV

## Rol

Je bent een **plain-language project-analist** voor VorstersNV. Je publiek is divers: nieuwe developers,
stakeholders, product owners, of niet-technische medewerkers. Je leest de code en vertaalt het naar
begrijpelijke taal. Geen jargon zonder uitleg. Geen code in de eindrapportage.

**Kwaliteitsdoel:** Een product owner leest jouw rapport en begrijpt onmiddellijk wat het platform doet,
wie het gebruikt, en wat de businesswaarde is — zonder één follow-up vraag aan een developer.

---

## ⚠️ Directieven — Lees Dit Eerst

- **Lees vóór je concludeert.** Scan echte bestanden; gok niet op basis van mapnamen alleen.
- **Zakelijke taal eerst.** Vertaal: "API" → "verbinding tussen systemen", "database" → "informatieopslagplaats".
  Gebruik technische term één keer tussen haakjes als het helpt.
- **Geen speculatie.** Als een feature onduidelijk is: "Op basis van de codestructuur behandelt
  dit waarschijnlijk [X] — bevestig met het team."
- **Vermeld concrete cijfers.** Aantal endpoints, agents, migraties — geef meetbare data.

---

## Fase 1: Structurele Scan (altijd)

**Lees in volgorde:**

1. `README.md` — projectbeschrijving en quick start
2. `CLAUDE.md` — Claude-specifieke context en conventies
3. `docker-compose.yml` — welke services draaien? (= wat is het systeem?)
4. `api/main.py` — welke routers zijn geregistreerd? (= welke functionaliteiten?)
5. `frontend/app/` — welke pagina's bestaan? (= wat ziet de gebruiker?)
6. `agents/` — welke AI-agents zijn er? (= welke intelligentie zit er in?)

**Interne notitie (niet tonen aan gebruiker):**
```
Project type:    Full-stack e-commerce platform
Frontend:        Next.js 14, App Router
Backend:         FastAPI (Python 3.12)
Database:        PostgreSQL + Redis
AI Layer:        Ollama (lokaal, llama3/mistral)
Betalingen:      Mollie
Auth:            Keycloak + NextAuth
```

---

## Fase 2: Business Layer Scan

**Lees de API routers** in `api/routers/` — elk bestand = één domein:

```
routers/producten.py   → "Producten beheren en zoeken"
routers/orders.py      → "Bestellingen verwerken"
routers/betalingen.py  → "Betalingen via Mollie"
routers/klanten.py     → "Klantprofielen"
routers/dashboard.py   → "KPI's en statistieken"
```

**Lees de Ollama agents** in `agents/*.yml` — elk YAML bestand = één AI-capability:

| Agent | Doel (plain language) |
|-------|----------------------|
| `klantenservice_agent` | Genereert antwoorden op klantvragen |
| `product_beschrijving_agent` | Schrijft SEO-teksten voor producten |
| `seo_agent` | Optimaliseert vindbaarheid |
| `order_verwerking_agent` | Orkestreert orderafhandeling |
| `fraude_detectie_agent` | Beoordeelt transactierisico |
| `product_recommender_agent` | Beveelt gerelateerde producten aan |
| `review_analyzer_agent` | Analyseert klantreviews op sentiment |

**Lees de frontend pagina's** in `frontend/app/`:

```
app/page.tsx           → Startpagina
app/shop/              → Webshop (productoverzicht + detail)
app/winkelwagen/       → Winkelwagen
app/afrekenen/         → Checkout
app/dashboard/         → Beheerdersdashboard
```

---

## Fase 3: Output — Plain Language Rapport

Gebruik exact deze structuur:

```
╔══════════════════════════════════════════════════════════════╗
║  PROJECTOVERZICHT  ·  VorstersNV Platform                    ║
╚══════════════════════════════════════════════════════════════╝
```

### 📌 In Één Zin

> [Eén zin. Wat doet het? Begin met een werkwoord.]
> Voorbeeld: "Beheert de volledige e-commerce operatie van VorstersNV, van productcatalogus
> tot betaalverwerking, aangedreven door lokale AI-assistenten voor teksten en klantenservice."

### 🎯 Welk Probleem Lost Het Op?

[2-4 zinnen. Wat gebeurt er ZONDER dit platform? Wat is de manuele last die het vervangt?]

### 👥 Wie Gebruikt Het?

| Gebruikerstype | Wat doen ze in dit systeem |
|----------------|---------------------------|
| Klant | Producten bekijken, bestellen, betalen |
| Beheerder | Producten, orders en voorraad beheren |
| AI Agent | Teksten schrijven, reviews analyseren, fraude detecteren |

### ✨ Kernfunctionaliteiten

**Webshop**
- Producten bekijken en zoeken
- Winkelwagen beheren
- Bestelling plaatsen met Mollie-betaling (Bancontact, Visa, iDEAL)

**Orderbeheer**
- Bestellingen opvolgen en statusupdates
- Automatische fraudecheck bij nieuwe orders
- Retourverwerking

**AI-aangedreven Features**
- Automatisch gegenereerde productbeschrijvingen (SEO-geoptimaliseerd)
- AI-klantenservice antwoorden
- Productaanbevelingen op basis van browsgeschiedenis
- Sentimentanalyse van klantreviews

**Beheerdersdashboard**
- KPI's: omzet, bestellingen, conversieratio
- Voorraadbeheer met low-stock alerts
- Agent performance monitoring

### 🔄 Hoe Informatie Stroomt

> Klant bezoekt webshop → kiest producten → plaatst bestelling →
> systeem voert fraudecheck uit via AI → betalingsverzoek naar Mollie →
> klant betaalt → Mollie stuurt webhook → bestelling bevestigd →
> AI genereert bevestigingsmail → beheerder ziet order in dashboard.

### 🏗️ Gebouwd Met (Eenvoudige Taal)

| Laag | Technologie | Eenvoudige uitleg |
|------|-------------|------------------|
| Wat klanten zien | Next.js 14 | Moderne webshop die in de browser draait |
| Serverlogica | FastAPI (Python) | De server die verzoeken verwerkt |
| Informatieopslagplaats | PostgreSQL 16 | Database met alle bestellingen en producten |
| Snel geheugen | Redis | Cache voor snellere paginalaadtijden |
| AI-systeem | Ollama (llama3/mistral) | Lokale AI die teksten schrijft en analyseert |
| Betalingen | Mollie | Belgische betaaldienst (Bancontact, Visa, iDEAL) |
| Login | Keycloak | Beveiligd inlogsysteem |

### 📊 Project Statistieken

| Indicator | Waarde |
|-----------|--------|
| API endpoints | [tel uit `api/routers/`] |
| AI agents | [tel uit `agents/`] |
| Database migraties | [tel in `db/migrations/versions/`] |
| Frontend pagina's | [tel in `frontend/app/`] |
| Testbestanden | [tel in `tests/`] |

### ⚠️ Te Bevestigen Met Het Team

- [ ] Welke functies zijn live in productie vs. nog in ontwikkeling?
- [ ] Zijn er klantspecifieke aanpassingen die niet in de code staan?
'@

# ─── .claude/skills/env-audit/SKILL.md ───────────────────────────────────────

Write-RuleFile ".claude/skills/env-audit/SKILL.md" @'
---
name: env-audit
description: >
  Use when: checking if .env file is complete, comparing .env vs .env.example,
  debugging "missing environment variable" errors, onboarding a new developer,
  security audit of environment configuration.
  Triggers: "env ontbreekt", "environment variabele", ".env controleren", "onboarding",
  "missing env", "omgevingsvariabele", "secrets controleren", "env audit".
---

# Env Audit Skill — VorstersNV

## Doel

Valideer de volledigheid en correctheid van het `.env` bestand ten opzichte van `.env.example`.
Identificeer ontbrekende variabelen, geef uitleg wat ze doen, en check of secrets niet in code staan.

---

## Stap 1: Lees Referentie en Actueel .env

```python
# Lees altijd in deze volgorde:
1. .env.example    ← de referentie (wat MOET aanwezig zijn)
2. .env            ← de actuele configuratie (wat IS aanwezig)
```

Als `.env.example` ontbreekt: **stop en meld dit** — het project mist zijn configuratiereferentie.
Als `.env` ontbreekt: **genereer instructies** om het aan te maken op basis van `.env.example`.

---

## Stap 2: Vergelijk en Categoriseer

Vergelijk beide bestanden en categoriseer elke variabele:

| Status | Omschrijving |
|--------|-------------|
| ✅ Aanwezig | Variabele staat in `.env` met niet-lege waarde |
| ⚠️ Leeg | Variabele aanwezig maar zonder waarde (`KEY=`) |
| ❌ Ontbreekt | Variabele staat in `.env.example` maar niet in `.env` |
| 🔒 Extra | Variabele in `.env` maar NIET in `.env.example` (potentieel ongedocumenteerd) |

---

## Stap 3: Kritieke Variabelen Check

De volgende variabelen zijn **business-kritiek** — rapporteer ze altijd expliciet:

| Variabele | Beschrijving | Impact als ontbreekt |
|-----------|-------------|---------------------|
| `DATABASE_URL` | PostgreSQL verbindingsstring | API start niet op |
| `MOLLIE_API_KEY` | Mollie betaaldienst sleutel | Geen betalingen mogelijk |
| `WEBHOOK_SECRET` | Handtekening-verificatie Mollie webhooks | Webhooks worden genegeerd |
| `NEXTAUTH_SECRET` | Next.js sessie encryptie | Frontend auth werkt niet |
| `NEXTAUTH_URL` | Frontend base URL voor auth callbacks | Login-redirects falen |
| `REDIS_URL` | Redis cache verbinding | API degraded (geen caching) |
| `KEYCLOAK_CLIENT_SECRET` | Keycloak OAuth2 secret | Admin login werkt niet |
| `OLLAMA_BASE_URL` | Ollama AI server URL | Alle AI agents offline |
| `SECRET_KEY` | FastAPI JWT signing key | Auth tokens invalide |

---

## Stap 4: Security Check — Secrets in Code

Scan de codebase op hardcoded secrets:

```bash
# Zoek patronen die op secrets lijken
grep -r "MOLLIE_API_KEY\s*=" api/ --include="*.py"
grep -r "sk_live_\|sk_test_\|live_\|test_" . --include="*.py" --include="*.ts"
grep -r "password\s*=\s*[\"'][^$]" . --include="*.py"
grep -r "SECRET.*=.*[\"'][a-zA-Z0-9]{16,}" . --include="*.py"
```

**Rode vlag patronen:**
- Mollie keys: `live_...` of `test_...` hardcoded in code
- Database wachtwoord direct in connection string
- JWT secret als variabele in code (niet via `os.getenv()`)

---

## Stap 5: Rapport Genereren

### Format

```
╔══════════════════════════════════════════════════════╗
║  ENV AUDIT  ·  VorstersNV                            ║
╚══════════════════════════════════════════════════════╝

📊 Samenvatting
  Totaal in .env.example:  [N] variabelen
  ✅ Aanwezig:             [N] variabelen
  ⚠️  Leeg:               [N] variabelen
  ❌ Ontbreekt:            [N] variabelen

────────────────────────────────────────────────────────

🚨 KRITIEKE ONTBREKENDE VARIABELEN
  [Lijst met naam, beschrijving, en wat er misgaat]

⚠️  LEGE VARIABELEN
  [Lijst met naam en standaardwaarde uit .env.example]

🔒 NIET-GEDOCUMENTEERDE VARIABELEN
  [Variabelen in .env maar niet in .env.example]

────────────────────────────────────────────────────────

🔍 SECURITY CHECK
  [Bevindingen hardcoded secrets — of "Geen hardcoded secrets gevonden"]

────────────────────────────────────────────────────────

📋 ACTIES VEREIST
  [ ] [Actie 1]
  [ ] [Actie 2]
```

---

## Veelvoorkomende Issues en Oplossingen

### DATABASE_URL formaat

```bash
# PostgreSQL (productie/dev)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/vorsternv

# SQLite (tests)
DATABASE_URL=sqlite+aiosqlite:///./test.db
```

### MOLLIE_API_KEY

```bash
# Test (gratis, geen echte betalingen)
MOLLIE_API_KEY=test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Live (echte betalingen — NOOIT in .env.example committen!)
MOLLIE_API_KEY=live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### NEXTAUTH_SECRET genereren

```bash
# Genereer een veilig secret
openssl rand -base64 32
# Of via Node.js:
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```
'@

# ─── .claude/skills/agent-performance/SKILL.md ───────────────────────────────

Write-RuleFile ".claude/skills/agent-performance/SKILL.md" @'
---
name: agent-performance
description: >
  Use when: analyzing Ollama agent output quality, comparing prompt versions,
  running validate-agents.mjs, checking agent scores below threshold,
  improving agent prompts, debugging poor agent output.
  Triggers: "agent presteert slecht", "prompt verbeteren", "agent score", "valideer agents",
  "agent output kwaliteit", "prompt optimaliseren", "agent debug", "lage score".
---

# Agent Performance Skill — VorstersNV

## Doel

Analyseer de kwaliteit van Ollama runtime agents en Claude Code agents in het VorstersNV ecosysteem.
Identificeer agents met lage scores, analyseer oorzaken, en geef concrete verbeteringen.

---

## Stap 1: Claude Code Agents Valideren

```bash
# Valideer alle Claude Code agents op correcte YAML frontmatter
node .claude/scripts/validate-agents.mjs

# Met detail-output
node .claude/scripts/validate-agents.mjs --verbose

# Auto-fix eenvoudige fouten
node .claude/scripts/validate-agents.mjs --fix
```

**Wat wordt gevalideerd:**
- `name` aanwezig en kebab-case
- `description` begint met "Delegate to this agent when:"
- `model` is een geldige Claude versie
- `permissionMode` is `default`, `restricted`, of `allow`

---

## Stap 2: Ollama Agent Performance Analyseren

```bash
# Analyseer agent performance (output naar .claude/reports/)
node .claude/scripts/analyse-agent-performance.mjs

# Lees het rapport
cat .claude/reports/agent-performance.json
```

**Lees ook de agent YAML bestanden direct:**

```bash
# Controleer alle Ollama agents
ls agents/*.yml

# Bekijk een specifieke agent
cat agents/klantenservice_agent_v2.yml
```

---

## Stap 3: Scores Interpreteren

### Drempelwaarden

| Score | Status | Actie |
|-------|--------|-------|
| ≥ 0.8 | ✅ Goed | Geen actie nodig |
| 0.6 – 0.79 | ⚠️ Matig | Verbeteringen overwegen |
| < 0.6 | ❌ Slecht | **Prioriteit: direct verbeteren** |

### Score Dimensies

| Dimensie | Beschrijving | Oplossing bij laag |
|----------|-------------|-------------------|
| `bodyScore` | Kwaliteit van de system prompt inhoud | Herstructureer met duidelijkere instructies |
| `frontmatterScore` | Correctheid YAML frontmatter | Controleer verplichte velden |
| `templateScore` | Volledige preprompt template | Voeg ontbrekende variabelen toe |
| `outputScore` | Output format conformiteit | Specificeer output format in system prompt |

---

## Stap 4: Verbeteringen Per Agent

### Structuur van een goede system prompt

```
1. Rol-definitie (kort: "Je bent X voor Y")
2. Context (wat weet de agent over het project?)
3. Input-verwachtingen (welke variabelen krijgt de agent?)
4. Output-format (JSON? Markdown? Plain text?)
5. Specifieke regels (max 5-7 bullets)
6. Grenzen (wat doet de agent NIET?)
```

### Veelvoorkomende Problemen

**Probleem: Vage output**
```yaml
# SLECHT system prompt
system_prompt: "Help de klant met vragen."

# GOED — specifiek output format
system_prompt: |
  Je bent een klantenservice-medewerker voor VorstersNV.
  
  Antwoord ALTIJD in dit JSON-format:
  {
    "toon": "professioneel|vriendelijk|formeel",
    "antwoord": "Jouw antwoord hier",
    "vervolgactie": "geen|escalatie|retour|korting"
  }
  
  Regels:
  - Maximaal 150 woorden
  - Altijd in het Nederlands
  - Nooit korting beloven zonder goedkeuring
```

**Probleem: Ontbrekende template variabelen**
```yaml
# SLECHT — variabele {klant_naam} nooit gedefinieerd
prompt: "Beste {klant_naam}, ..."

# GOED — alle variabelen in input_schema
input_schema:
  properties:
    klant_naam: {type: string}
    order_id: {type: string}
    probleem: {type: string}
  required: [klant_naam, probleem]
```

---

## Stap 5: A/B Testing via prompt_iterator.py

```bash
# Vergelijk twee prompt-versies
python scripts/prompt_iterator.py \
  --agent klantenservice \
  --version v1 v2 \
  --test-cases prompts/preprompt/klantenservice_iterations.yml

# Bekijk resultaten
cat .claude/reports/prompt-comparison.json
```

**Iteratie-workflow:**

1. Maak `prompts/preprompt/{agent}_iterations.yml` aan met 2-3 varianten
2. Draai `prompt_iterator.py` met testcases
3. Vergelijk scores in rapport
4. Kies winnende versie → update `{agent}.yml` met nieuwe `preprompt_ref`
5. Archiveer verliezende versie (verwijder niet — historische referentie)

---

## Stap 6: Agent Performance Rapport

```
╔══════════════════════════════════════════════════════╗
║  AGENT PERFORMANCE RAPPORT  ·  VorstersNV            ║
╚══════════════════════════════════════════════════════╝

📊 Samenvatting
  Totaal agents:    [N] Claude Code + [N] Ollama
  ✅ Goed (≥0.8):  [N]
  ⚠️  Matig:        [N]
  ❌ Slecht (<0.6): [N]

────────────────────────────────────────────────────────

🚨 AGENTS DIE AANDACHT VEREISEN

Agent: [naam]
  Overall score:  [X.XX]
  bodyScore:      [X.XX]  ← [probleem beschrijving]
  frontmatterScore: [X.XX]
  
  Aanbevolen aanpak:
  1. [Concrete stap]
  2. [Concrete stap]

────────────────────────────────────────────────────────

✅ GOED PRESTERENDE AGENTS
  [lijst met naam en score]

────────────────────────────────────────────────────────

📋 AANBEVELINGEN
  [ ] [Actie met prioriteit]
```
'@

Write-Host "`n✅ Setup voltooid!" -ForegroundColor Green
Write-Host @"

Samenvatting aangemaakt:
  📁 .claude/rules/backend/python-fastapi.md
  📁 .claude/rules/backend/alembic-migrations.md
  📁 .claude/rules/frontend/nextjs-app-router.md
  📁 .claude/rules/general/git-commits.md
  📁 .claude/rules/general/project-context.md
  📁 .claude/rules/tools/docker.md
  📁 .claude/skills/project-explainer/SKILL.md
  📁 .claude/skills/env-audit/SKILL.md
  📁 .claude/skills/agent-performance/SKILL.md

Volgende stap: verifieer met 'node .claude/scripts/validate-agents.mjs'
"@ -ForegroundColor Cyan
