# VorstersNV – Fase 3: Technisch Ontwerp
> **Versie:** 1.0 | **Datum:** April 2026 | **Status:** Ontwerp (gereed voor implementatie)
> **Scope:** Webshop frontend, Mollie live, Zoekfunctie, Review-systeem, Klantaccounts

---

## Inhoudsopgave

1. [Overzicht & Afhankelijkheidsgraph](#1-overzicht--afhankelijkheidsgraph)
2. [Componentdiagram Webshop](#2-componentdiagram-webshop)
3. [A. Webshop Frontend Routes](#a-webshop-frontend-routes)
4. [B. Mollie Live Betalingsintegratie](#b-mollie-live-betalingsintegratie)
5. [C. Productzoekfunctie](#c-productzoekfunctie)
6. [D. Review-systeem](#d-review-systeem)
7. [E. Klantaccountpagina's](#e-klantaccountpaginaas)
8. [F. Navbar Uitbreiding](#f-navbar-uitbreiding)
9. [Database Schema Uitbreidingen](#database-schema-uitbreidingen)
10. [API Endpoint Overzicht — Nieuw in Fase 3](#api-endpoint-overzicht--nieuw-in-fase-3)
11. [Architectuurbeslissingen (ADRs)](#architectuurbeslissingen-adrs)
12. [Implementatieplan & Prioriteitsvolgorde](#implementatieplan--prioriteitsvolgorde)

---

## 1. Overzicht & Afhankelijkheidsgraph

De 7 openstaande items uit Fase 3 zijn niet onafhankelijk — er zijn duidelijke afhankelijkheden.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   FASE 3 — AFHANKELIJKHEIDSGRAPH                         │
│                                                                           │
│   F – Navbar            ──────────────────────────────────────────►      │
│   uitbreiding                                                    (alle   │
│                                                                   routes) │
│   A – Webshop routes    ──── vereist ────►  B – Mollie live               │
│   /shop, /[slug],                           (checkout → betaling)         │
│   /winkelwagen,                                                           │
│   /afrekenen                                                              │
│        │                                                                  │
│        └──── verbeterd door ────►  C – Zoekfunctie                       │
│                                      (/shop + zoekbalk)                  │
│        └──── verbeterd door ────►  D – Review-systeem                    │
│                                      (/shop/[slug] + reviews)            │
│                                                                           │
│   E – Klantaccounts     ──── vereist ────►  B – Mollie live               │
│   /account/bestellingen                     (orderhistorie = echte orders)│
│        └──── vereist ────►  A – Webshop routes                           │
│                              (klant moet kunnen winkelen)                 │
│                                                                           │
│   VOLGORDE: F → A → B → C → D → E                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

### Legenda prioriteiten

| Prio | Item | Rede |
|------|------|------|
| 🔴 P1 | F – Navbar uitbreiding | Vereist voor alle andere routes |
| 🔴 P1 | A – Webshop routes | Kern van de webshop — zonder dit geen e-commerce |
| 🟠 P2 | B – Mollie live | Echte inkomsten — vervangt huidige mock |
| 🟡 P3 | C – Productzoekfunctie | Conversie-booster: vindbaarheid verhogen |
| 🟡 P3 | D – Review-systeem | Social proof + SEO-waarde |
| 🟢 P4 | E – Klantaccountpagina's | Loyaliteitsfunctie — nice-to-have in early stage |

---

## 2. Componentdiagram Webshop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NEXT.JS 14 APP ROUTER                               │
│                                                                             │
│  ┌─────────────────┐  ┌──────────────────────┐  ┌───────────────────────┐  │
│  │   /shop          │  │   /shop/[slug]        │  │   /winkelwagen        │  │
│  │                  │  │                       │  │                       │  │
│  │  Server Component│  │  Server Component     │  │  Client Component     │  │
│  │  ─────────────   │  │  ─────────────────    │  │  ─────────────────    │  │
│  │  • ProductGrid   │  │  • ProductDetailPage  │  │  • WinkelwagenPage   │  │
│  │    (RSC, fetch)  │  │    (RSC, fetch/slug)  │  │  • useCartStore       │  │
│  │  • FilterBar     │  │  • ProductDetailClient│  │    (Zustand)          │  │
│  │    (Client)      │  │    (Client, AddToCart)│  │  • Hoeveelheid-ctrl  │  │
│  │  • SortDropdown  │  │  • ReviewList (RSC)   │  │  • OrderSamenvatting │  │
│  │    (Client)      │  │  • ReviewForm (Client)│  │                       │  │
│  │  • ZoekBalk      │  │  • StarRating         │  └───────────────────────┘  │
│  │    (Client)      │  │  • VoorraadBadge      │                             │
│  │  • Paginering    │  │                       │  ┌───────────────────────┐  │
│  └─────────────────┘  └──────────────────────┘  │   /afrekenen          │  │
│                                                   │                       │  │
│  ┌─────────────────────────────────────────────┐  │  Client Component     │  │
│  │            /account/*                        │  │  ─────────────────    │  │
│  │                                               │  │  • CheckoutForm      │  │
│  │  /account         → ProfielOverzicht (RSC)   │  │  • BestelSamenvatting│  │
│  │  /account/profiel → ProfielBewerken (Client) │  │  • MollieRedirect    │  │
│  │  /account/best.   → OrderGeschied. (RSC)     │  │    (betaal_url)      │  │
│  └─────────────────────────────────────────────┘  └───────────────────────┘  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    GEDEELDE STAAT & INFRASTRUCTUUR                   │   │
│  │                                                                       │   │
│  │  lib/cartStore.ts  (Zustand + localStorage persist)                  │   │
│  │  lib/auth.ts       (NextAuth session helpers)                        │   │
│  │  lib/api.ts        (typed fetch wrappers → FastAPI)                  │   │
│  │  components/Navbar.tsx  (winkelwagen badge, auth links)              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                        HTTP / Next.js API routes
                                     │
┌────────────────────────────────────▼────────────────────────────────────────┐
│                          FASTAPI BACKEND (poort 8000)                       │
│                                                                              │
│  /api/products/         GET lijst, GET /slug/:slug, GET /search?q=          │
│  /api/products/{id}/reviews   GET lijst, POST nieuw                         │
│  /api/bestellingen/     POST aanmaken (→ Mollie), GET status                │
│  /api/auth/             Keycloak JWT validatie                              │
│  /webhooks/mollie       POST Mollie statusupdates (HMAC-SHA256)            │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## A. Webshop Frontend Routes

### Huidige staat (al geïmplementeerd)

De volgende routes bestaan al en zijn functioneel:

| Route | Status | Componenten |
|-------|--------|-------------|
| `/shop` | ✅ Basis aanwezig | `ProductGrid`, `SkeletonCards`, `AddToCartButton` |
| `/shop/[slug]` | ✅ Basis aanwezig | `ProductDetailPage` (RSC), `ProductDetailClient` |
| `/winkelwagen` | ✅ Volledig | `WinkelwagenPage` (Client), `useCartStore` |
| `/afrekenen` | ✅ Volledig | `AfrekenPage` (Client), Mollie-redirect |

### Wat ontbreekt / uitgebreid moet worden

#### A1 — `/shop` — Filtering & Sortering

**Huidige staat:** Productgrid laadt alle actieve producten, geen filters zichtbaar voor de gebruiker.

**Ontbrekend:**
- `FilterBar` component (Client Component) — categoriefilter als horizontale scrollbare lijst
- `SortDropdown` (Client Component) — sorteren op: nieuwste, goedkoop→duur, duur→goedkoop
- `ZoekBalk` (Client Component) — debounced input, roept `/api/products/search?q=` aan
- URL-state synchronisatie via `useSearchParams` + `router.push` — zodat filters in URL staan (deelbaar, SEO-vriendelijk)

**Componentstructuur:**

```typescript
// /shop/page.tsx — Server Component (blijft RSC)
export default async function ShopPage({ searchParams }) {
  // Leest ?categorie=, ?sorteer=, ?pagina= uit URL
  // Fetcht server-side (Next.js cache)
  return (
    <>
      <FilterBar />          {/* Client Component */}
      <ZoekBalk />           {/* Client Component */}
      <Suspense fallback={<SkeletonCards />}>
        <ProductGrid params={searchParams} />   {/* RSC */}
      </Suspense>
    </>
  )
}
```

**Data fetching:**
- `ProductGrid` is een RSC → fetch rechtstreeks naar FastAPI met `cache: 'no-store'` (filters zijn dynamisch)
- URL parameters worden doorgegeven als props
- Paginering via `?pagina=` query param

#### A2 — `/shop/[slug]` — Reviews toevoegen

**Huidige staat:** Productdetail volledig, maar zonder reviews.

**Ontbrekend:**
- `ReviewList` (RSC) — toont bestaande reviews met gemiddelde sterren
- `ReviewForm` (Client Component) — formulier: rating (1-5 sterren), tekst, submit
- `StarRating` — herbruikbaar component voor weergave én invoer
- Review-sectie enkel zichtbaar voor ingelogde klanten (via NextAuth session check)

#### A3 — `/winkelwagen` & `/afrekenen`

**Huidige staat:** Volledig geïmplementeerd met Zustand + mock Mollie.

**Ontbrekend:**
- Koppeling met echte Mollie betaal-URL (zie sectie B)
- Betaalmethode iDEAL/Bancontact correct doorgeven aan Mollie API
- `/betaling/bevestiging?betaling_id=` pagina voor succesmelding na terugkeer van Mollie

**Nieuwe route: `/betaling/bevestiging`**

```
Server Component
├── Leest ?bestelling_id= en ?betaling_id= uit URL
├── Fetcht betalingstatus via GET /api/bestellingen/{id}
├── Toont: "Bedankt! Uw bestelling {BST-XXXX} is bevestigd."
└── Winkelwagen wordt gecleared via useCartStore (Client deelcomponent)
```

---

## B. Mollie Live Betalingsintegratie

### Huidige staat

De `/api/bestellingen` router maakt een echte DB-order aan maar retourneert een **mock** betaal-URL:
```
/betaling/mock?betaling_id=PAY-XXXX&bestelling_id=BST-XXXX
```

### Stap-voor-stap checkout data flow (na Mollie live)

```
1. KLANT
   Vult checkout formulier in, klikt "Betalen →"
   AfrekenPage.handleSubmit() → POST /api/bestellingen
   
2. FASTAPI /api/bestellingen (bestelling_aanmaken)
   ├── Valideert voorraad (DB-prijzen, niet client-prijzen)
   ├── Upsert Customer in DB
   ├── Maakt Order aan (status: pending)
   ├── Vermindert voorraad
   ├── [NIEUW] Roept Mollie API aan:
   │     mollie_client.payments.create({
   │       amount: { currency: "EUR", value: "XX.XX" },
   │       description: f"VorstersNV bestelling {order_nummer}",
   │       redirectUrl: f"{BASE_URL}/betaling/bevestiging?bestelling_id={order_nummer}",
   │       webhookUrl: f"{WEBHOOK_BASE_URL}/webhooks/mollie",
   │       method: betaalmethode,  # "ideal", "bancontact", etc.
   │       metadata: { order_nummer: order_nummer }
   │     })
   ├── Slaat Mollie payment_id op in Order.payment_id
   └── Retourneert: { betaal_url: checkout_url.href }

3. FRONTEND
   window.location.href = result.betaal_url
   → Klant wordt doorgestuurd naar Mollie checkout

4. MOLLIE CHECKOUT (extern)
   Klant kiest bank / betaalt

5. MOLLIE WEBHOOK → /webhooks/mollie
   ├── Verifieert HMAC-SHA256 handtekening (X-Mollie-Signature header)
   ├── Fetcht betalingstatus via Mollie API (payment_id)
   ├── Update Order.status:
   │     paid      → status = "paid"    (trigger: bestelbevestiging email)
   │     failed    → status = "pending" (voorraad terug vrij)
   │     cancelled → status = "cancelled"
   └── Publiceert DomainEvent naar EventBus (PaymentSucceededEvent)

6. REDIRECT
   Klant keert terug naar /betaling/bevestiging?bestelling_id=BST-XXXX
   → RSC fetcht order status, toont bevestiging of foutmelding
```

### Environment variabelen

```bash
# Dev (test-mode)
MOLLIE_API_KEY=test_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
MOLLIE_TEST_MODE=true
WEBHOOK_BASE_URL=https://abc123.ngrok.io   # ngrok tunnel in dev

# Productie (live-mode)
MOLLIE_API_KEY=live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
MOLLIE_TEST_MODE=false
WEBHOOK_BASE_URL=https://api.vorstersNV.be
```

> ⚠️ **Nooit** de `live_` API key hardcoden. Altijd via omgevingsvariabelen.

### HMAC verificatie (webhook security)

```python
# webhooks/mollie.py — bestaande code uitbreiden
import hmac, hashlib

def verify_mollie_signature(body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### Test-mode vs Live-mode strategie

| Omgeving | API Key | Webhook | Betaalmethoden |
|----------|---------|---------|----------------|
| `dev` (lokaal) | `test_xxx` | ngrok URL | Mollie test-betaalpagina |
| `staging` | `test_xxx` | staging URL | Mollie test-betaalpagina |
| `production` | `live_xxx` | `api.vorstersNV.be` | Echte iDEAL/Bancontact |

### Retry strategie

- Mollie webhooks kunnen meerdere keren worden verstuurd → **idempotency check** via `payment_id`
- Bij webhook-fout: Mollie herprobeert automatisch (15 min, 1 uur, 1 dag)
- Order status mag nooit achteruitgaan (paid → pending is verboden)

---

## C. Productzoekfunctie (PostgreSQL Full-Text Search)

### Aanpak: PostgreSQL tsvector

We kiezen voor **PostgreSQL ingebouwde full-text search** (geen Elasticsearch of Typesense).

**Reden:** Voor een KMO-webshop met <10.000 producten is PostgreSQL FTS meer dan voldoende. Geen extra infrastructuur, lagere kosten, minder complexiteit. Zie ADR-03.

### Database aanpassingen

**Alembic migration** — nieuwe kolom + index:

```sql
-- Voeg zoekkolom toe
ALTER TABLE products
ADD COLUMN zoek_vector tsvector
  GENERATED ALWAYS AS (
    to_tsvector('dutch',
      coalesce(naam, '') || ' ' ||
      coalesce(korte_beschrijving, '') || ' ' ||
      coalesce(beschrijving, '')
    )
  ) STORED;

-- GIN index voor performante zoekquery's
CREATE INDEX idx_products_zoek_vector
  ON products USING gin(zoek_vector);
```

> **Let op:** PostgreSQL ondersteunt `'dutch'` als full-text search dictionary.
> Tags en kenmerken (JSON) worden **niet** meegenomen in de gegenereerde kolom —
> die vereisen een trigger of applicatielaag update.

### FastAPI endpoint

**Nieuw:** `GET /api/products/search?q=&pagina=&per_pagina=`

```python
@router.get("/search", response_model=ProductListResponse)
async def zoek_producten(
    q: str = Query(..., min_length=2, max_length=100),
    pagina: int = Query(1, ge=1),
    per_pagina: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Full-text zoeken op productnaam, beschrijving en korte beschrijving."""
    zoek_query = func.plainto_tsquery("dutch", q)
    stmt = (
        select(Product)
        .options(selectinload(Product.category))
        .where(
            Product.actief == True,
            Product.zoek_vector.op("@@")(zoek_query)
        )
        .order_by(
            func.ts_rank(Product.zoek_vector, zoek_query).desc()
        )
        .offset((pagina - 1) * per_pagina)
        .limit(per_pagina)
    )
    # ... count + return
```

### Frontend ZoekBalk component

```typescript
// components/ZoekBalk.tsx — Client Component
'use client'
import { useCallback, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useDebouncedCallback } from 'use-debounce'

export default function ZoekBalk() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const handleZoek = useDebouncedCallback((waarde: string) => {
    const params = new URLSearchParams(searchParams)
    if (waarde) {
      params.set('q', waarde)
    } else {
      params.delete('q')
    }
    params.delete('pagina')  // Reset paginering bij nieuwe zoekopdracht
    router.push(`/shop?${params.toString()}`)
  }, 300)  // 300ms debounce

  return (
    <input
      type="search"
      placeholder="Zoek producten…"
      defaultValue={searchParams.get('q') ?? ''}
      onChange={(e) => handleZoek(e.target.value)}
      data-testid="zoek-input"
      className="..."
    />
  )
}
```

**Integratie `/shop/page.tsx`:**
- Als `?q=` aanwezig in URL → gebruik `/api/products/search?q=`
- Als geen `?q=` → gebruik `/api/products/` (bestaande lijst-endpoint)

---

## D. Review-systeem

### Database model

**Nieuw model: `Review`**

```python
class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    # Geanonimiseerde weergavenaam (GDPR: geen echte naam verplicht)
    auteur_naam: Mapped[str] = mapped_column(String(100), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)   # 1-5
    tekst: Mapped[str | None] = mapped_column(Text)
    goedgekeurd: Mapped[bool] = mapped_column(Boolean, default=False)  # Moderatie
    sentiment_score: Mapped[float | None] = mapped_column(Numeric(3, 2))  # AI-analyse
    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
    customer: Mapped["Customer | None"] = relationship("Customer")
```

**Invarianten:**
- `rating` tussen 1 en 5 (DB constraint: `CHECK (rating BETWEEN 1 AND 5)`)
- Klant kan maximaal 1 review per product achterlaten (unique constraint op `product_id + customer_id`)
- `goedgekeurd = False` standaard → review zichtbaar na moderatie (admin panel) **of** auto-goedkeuring bij positief sentiment

### Alembic migration

```sql
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    auteur_naam VARCHAR(100) NOT NULL,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    tekst TEXT,
    goedgekeurd BOOLEAN NOT NULL DEFAULT FALSE,
    sentiment_score NUMERIC(3, 2),
    aangemaakt_op TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_reviews_klant_product
  ON reviews (product_id, customer_id)
  WHERE customer_id IS NOT NULL;

CREATE INDEX idx_reviews_product_goedgekeurd
  ON reviews (product_id, goedgekeurd);
```

### API endpoints

**Nieuw:** Reviews router in `api/routers/reviews.py`

```
GET  /api/products/{id}/reviews
     → Geeft goedgekeurde reviews terug (gepagineerd)
     → Bevat: gemiddelde rating, aantal reviews, reviews[]

POST /api/products/{id}/reviews
     → Verplicht ingelogd (JWT)
     → Body: { auteur_naam, rating, tekst }
     → Triggert sentiment-analyse via review_analyzer_agent
     → Bij positief sentiment (score >= 0.7): auto-goedkeuring
     → Returns: { id, status: "wacht_op_moderatie" | "goedgekeurd" }
```

### Integratie met review_analyzer_agent

```
POST /api/products/{id}/reviews
     │
     ├── Review opslaan (goedgekeurd=False)
     │
     └── Async taak: AgentRunner.run("review_analyzer_agent", {
             tekst: review.tekst,
             rating: review.rating
         })
         │
         ├── output.sentiment_score >= 0.7 → goedgekeurd = True
         ├── output.sentiment_score <  0.3 → vlag voor handmatige review
         └── Slaat sentiment_score op in Review record
```

### Frontend componenten

**`ReviewList`** (RSC — rendert server-side):
```typescript
// Laadt goedgekeurde reviews via fetch (revalidate: 300s)
// Toont: gemiddelde ⭐⭐⭐⭐ (4.2/5 — 23 reviews)
// + lijst van individuele reviews
```

**`StarRating`** (Client Component, herbruikbaar):
```typescript
// Props: value (weergave) | onChange (invoer)
// Interactief voor ReviewForm, readonly voor ReviewList
```

**`ReviewForm`** (Client Component):
```typescript
// Alleen zichtbaar als session.user aanwezig (NextAuth)
// Formulier: naam (pre-filled uit session), sterren (1-5), tekst (optioneel)
// Submit → POST /api/products/{id}/reviews
// Succesmelding: "Uw review is ingediend en wordt bekeken."
```

---

## E. Klantaccountpagina's

### Auth flow: Keycloak / NextAuth

**Beslissing:** We gebruiken **NextAuth** als authenticatielaag (zie ADR-02).
- In development: NextAuth met credentials provider (email/wachtwoord naar FastAPI JWT)
- In productie: NextAuth met Keycloak OIDC provider
- JWT van Keycloak wordt doorgegeven aan FastAPI in `Authorization: Bearer` header

### Routes & componenten

#### `/account` — Profieloverzicht

```typescript
// Server Component (RSC)
// Vereist: session.user (middleware redirect als niet ingelogd)
// Fetcht: GET /api/auth/mij (klantprofiel op basis van JWT email)
// Toont: naam, email, lid sinds, snelkoppelingen naar /account/profiel en /account/bestellingen
```

#### `/account/bestellingen` — Ordergeschiedenis

```typescript
// Server Component (RSC)
// Vereist: session.user
// Fetcht: GET /api/bestellingen?klant_email={email} (JWT-beveiligd)
// Toont: tabel van orders met status, datum, totaal, link naar details
// Status-badges: pending 🟡 | paid 🟢 | shipped 📦 | cancelled 🔴
```

#### `/account/profiel` — Profiel bewerken

```typescript
// Client Component (formulier-interactie)
// Vereist: session.user
// Fetcht: GET /api/auth/mij (pre-fill formulier)
// Submit: PUT /api/klanten/{id} (naam, telefoon, adres bijwerken)
// Wachtwoord wijzigen: separaat formulier (delegeren naar Keycloak-flow)
```

### FastAPI aanpassingen

**Nieuw endpoint:** `GET /api/auth/mij`
```python
@router.get("/mij")
async def huidig_profiel(
    current_user: TokenData = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """Geeft klantprofiel terug op basis van JWT email."""
    customer = await db.execute(
        select(Customer).where(Customer.email == current_user.email)
    )
    return customer.scalar_one_or_none()
```

**Nieuw endpoint:** `PUT /api/klanten/{id}` (profiel bijwerken)

**Bestaand endpoint uitbreiden:** `GET /api/bestellingen` → voeg filter op `klant_email` toe (JWT-beveiligd, klant ziet alleen eigen orders)

### Middleware: Route protection

```typescript
// middleware.ts (Next.js root)
export const config = {
  matcher: ['/account/:path*'],
}

export default withAuth(
  function middleware(req) { /* ... */ },
  {
    callbacks: {
      authorized: ({ token }) => !!token,
    },
  }
)
```

---

## F. Navbar Uitbreiding

### Huidige staat

Navbar bestaat maar heeft geen `/shop` link en geen winkelwagen-badge.

### Gewenste toevoegingen

```typescript
// components/Navbar.tsx — uitbreiden

// 1. Navigatielinks
<Link href="/shop">Shop</Link>

// 2. Winkelwagen-icoon met badge
<WinkelwagenBadge />  // Client Component

// components/WinkelwagenBadge.tsx
'use client'
import { useCartStore } from '@/lib/cartStore'
import { ShoppingCart } from 'lucide-react'

export default function WinkelwagenBadge() {
  const aantalItems = useCartStore((s) => s.items.reduce((acc, i) => acc + i.aantal, 0))
  return (
    <Link href="/winkelwagen" className="relative" data-testid="cart-icon">
      <ShoppingCart className="w-5 h-5" />
      {aantalItems > 0 && (
        <span
          data-testid="cart-badge"
          className="absolute -top-2 -right-2 bg-purple-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center"
        >
          {aantalItems > 9 ? '9+' : aantalItems}
        </span>
      )}
    </Link>
  )
}

// 3. Account-links (conditie: session aanwezig)
{session?.user ? (
  <Link href="/account">Mijn account</Link>
) : (
  <Link href="/login">Inloggen</Link>
)}
```

> **Let op:** `WinkelwagenBadge` is een **Client Component** (leest Zustand state).
> De Navbar zelf mag een **Server Component** zijn als de badge als apart child wordt geïmporteerd.

---

## Database Schema Uitbreidingen

### Overzicht nieuwe tabellen & kolommen

```
BESTAAND                          NIEUW (Fase 3)
────────────────────────────────────────────────────────────────────
products                          products.zoek_vector (GENERATED)
  + idx_products_zoek_vector (GIN)

customers                         customers.geboorte_datum (optioneel, GDPR)
                                  customers.nieuwsbrief_opt_in (boolean)

orders                            orders.mollie_payment_id (vervangt payment_id mock)
                                  orders.mollie_checkout_url (cache, max 1 uur geldig)

NEW: reviews                      reviews (volledig nieuw, zie sectie D)
  + uq_reviews_klant_product
  + idx_reviews_product_goedgekeurd
```

### Alembic migraties volgorde

```
1. add_zoek_vector_to_products.py
   → ALTER TABLE products ADD COLUMN zoek_vector tsvector GENERATED ALWAYS AS ...
   → CREATE INDEX idx_products_zoek_vector ON products USING gin(zoek_vector)

2. add_mollie_fields_to_orders.py
   → ALTER TABLE orders ADD COLUMN mollie_payment_id VARCHAR(50)
   → ALTER TABLE orders ADD COLUMN mollie_checkout_url VARCHAR(500)
   → ALTER TABLE orders ADD COLUMN mollie_betaalmethode VARCHAR(30)

3. create_reviews_table.py
   → CREATE TABLE reviews (...)
   → Constraints + indexen zoals beschreven in sectie D

4. extend_customers_table.py
   → ALTER TABLE customers ADD COLUMN nieuwsbrief_opt_in BOOLEAN DEFAULT FALSE
   → ALTER TABLE customers ADD COLUMN geboorte_datum DATE  (optioneel, GDPR-bewust)
```

---

## API Endpoint Overzicht — Nieuw in Fase 3

| Methode | URL | Beschrijving | Auth | Prioriteit |
|---------|-----|-------------|------|-----------|
| `GET` | `/api/products/search?q=` | Full-text zoekresultaten | Publiek | P3 |
| `GET` | `/api/products/{id}/reviews` | Reviews van een product | Publiek | P3 |
| `POST` | `/api/products/{id}/reviews` | Review toevoegen | Klant JWT | P3 |
| `GET` | `/api/auth/mij` | Eigen klantprofiel | Klant JWT | P4 |
| `PUT` | `/api/klanten/{id}` | Profiel bijwerken | Klant JWT | P4 |
| `GET` | `/api/bestellingen?mijn=true` | Eigen ordergeschiedenis | Klant JWT | P4 |
| `POST` | `/webhooks/mollie` | Mollie betalingsstatus | HMAC-SHA256 | P2 |

**Reeds bestaand, uitbreiden:**

| Methode | URL | Uitbreiding |
|---------|-----|------------|
| `POST` | `/api/bestellingen` | Mollie API-aanroep i.p.v. mock URL |
| `GET` | `/api/products/` | `?q=` zoekparameter verbeterd (nu basic ILIKE → straks tsvector) |

---

## Architectuurbeslissingen (ADRs)

### ADR-01: Winkelwagen State — Zustand + localStorage

**Beslissing:** Winkelwagen staat wordt beheerd via **Zustand** met `persist` middleware naar `localStorage`.

**Alternatieven overwogen:**

| Optie | Voordelen | Nadelen | Beslissing |
|-------|-----------|---------|-----------|
| localStorage (direct) | Eenvoudig | Geen reactief state, geen SSR-veiligheid | ❌ |
| Server-side (DB) | Persistentie over apparaten | Vereist ingelogde gebruiker, extra API calls bij elke change | ❌ |
| **Zustand + localStorage** | Reactief, SSR-safe (lazy hydration), geen auth vereist | Niet gesynchroniseerd over apparaten | ✅ **Gekozen** |
| Redux Toolkit | Krachtig | Overkill voor winkelwagen | ❌ |

**Rationale:** Een KMO-webshop heeft geen behoefte aan cross-apparaat synchronisatie in de eerste versie. Zustand is al in gebruik (`lib/cartStore.ts`). Zustand `persist` zorgt voor hydration na page refresh zonder server roundtrip.

**Review punt voor Fase 5:** Als klantaccounts actief zijn, kan de winkelwagen optioneel server-side gesynchroniseerd worden voor ingelogde gebruikers (hybride aanpak).

---

### ADR-02: Auth — NextAuth (huidig) vs Keycloak JWT direct

**Beslissing:** **NextAuth** als authenticatielaag voor de frontend, met Keycloak als OIDC provider in productie.

**Alternatieven overwogen:**

| Optie | Voordelen | Nadelen | Beslissing |
|-------|-----------|---------|-----------|
| Keycloak JWT direct (frontend) | Geen extra laag | Complexe token-refresh logica, keycloak.js dependency | ❌ |
| **NextAuth** | Abstractielaag, eenvoudig providers wisselen, SSR-friendly sessions | Extra configuratie voor Keycloak OIDC | ✅ **Gekozen** |
| Auth.js v5 | Modernste versie | Beta in Next.js 14 context | 🔄 Evalueren voor Fase 5 |

**Rationale:** NextAuth zit al in de project dependencies. De `credentials` provider werkt nu tegen de FastAPI JWT. Bij migratie naar Keycloak OIDC is alleen de provider-config te wijzigen.

---

### ADR-03: Zoekfunctie — PostgreSQL FTS vs Elasticsearch vs Typesense

**Beslissing:** **PostgreSQL Full-Text Search** met `tsvector` GENERATED column.

**Alternatieven overwogen:**

| Optie | Voordelen | Nadelen | Beslissing |
|-------|-----------|---------|-----------|
| **PostgreSQL FTS** | Al aanwezig, geen infra, Dutch dictionary, GIN index snel | Minder geavanceerd (geen typo-tolerantie) | ✅ **Gekozen** |
| Elasticsearch | Krachtig, typo-tolerant, facet-filtering | Zware infrastructuur, €50+/maand cloud | ❌ (voor KMO niet proportioneel) |
| Typesense | Licht, typo-tolerant, goedkoper | Extra service, extra onderhoud | 🔄 Evalueren als FTS te beperkt blijkt |
| Meilisearch | Open source, snel | Extra service | 🔄 Evalueren als FTS te beperkt blijkt |

**Rationale:** VorstersNV heeft naar verwachting < 10.000 producten. PostgreSQL FTS met GIN-index handelt 10.000 records moeiteloos af (< 10ms). Upgrade naar Typesense is altijd mogelijk — het API-contract (`/search?q=`) blijft ongewijzigd.

---

## Implementatieplan & Prioriteitsvolgorde

### Sprint 1 — Basis webshop compleet (Week 1-2)

**Doel:** De webshop is volledig bruikbaar met filters, zoeken en werkende checkout.

| # | Taak | Bestand(en) | Uren |
|---|------|------------|------|
| 1.1 | Navbar: /shop link + WinkelwagenBadge | `components/Navbar.tsx`, `components/WinkelwagenBadge.tsx` | 2u |
| 1.2 | FilterBar component (categoriefilter) | `frontend/app/shop/FilterBar.tsx` | 3u |
| 1.3 | SortDropdown component | `frontend/app/shop/SortDropdown.tsx` | 2u |
| 1.4 | ProductGrid uitbreiden met categorie + sort params | `frontend/app/shop/ProductGrid.tsx` | 2u |
| 1.5 | `/betaling/bevestiging` pagina | `frontend/app/betaling/bevestiging/page.tsx` | 3u |

**Afhankelijkheden:** Geen — kan direct starten.

### Sprint 2 — Mollie Live (Week 2-3)

**Doel:** Echte betalingen verwerken via Mollie.

| # | Taak | Bestand(en) | Uren |
|---|------|------------|------|
| 2.1 | Alembic migration: mollie velden in orders | `db/migrations/add_mollie_fields.py` | 1u |
| 2.2 | Mollie Python SDK installeren + configureren | `requirements.txt`, `api/config.py` | 1u |
| 2.3 | `bestelling_aanmaken` endpoint: echte Mollie API call | `api/routers/betalingen.py` | 4u |
| 2.4 | HMAC verificatie in Mollie webhook | `webhooks/mollie.py` | 2u |
| 2.5 | Webhook: order status updaten + PaymentSucceededEvent | `webhooks/mollie.py` | 3u |
| 2.6 | Testen met Mollie test-mode (ngrok) | — | 2u |

**Afhankelijkheden:** Mollie API key (test), ngrok of andere tunnel voor lokale webhook testing.

### Sprint 3 — Zoekfunctie (Week 3)

**Doel:** Klanten kunnen producten zoeken.

| # | Taak | Bestand(en) | Uren |
|---|------|------------|------|
| 3.1 | Alembic migration: zoek_vector kolom + GIN index | `db/migrations/add_zoek_vector.py` | 2u |
| 3.2 | FastAPI: `/api/products/search` endpoint | `api/routers/products.py` | 2u |
| 3.3 | ZoekBalk component (debounced) | `frontend/components/ZoekBalk.tsx` | 2u |
| 3.4 | `/shop` routing: `?q=` param → search endpoint | `frontend/app/shop/page.tsx`, `ProductGrid.tsx` | 2u |

**Afhankelijkheden:** Sprint 1 (ProductGrid moet params ondersteunen).

### Sprint 4 — Review-systeem (Week 4)

**Doel:** Klanten kunnen reviews achterlaten, AI analyseert sentiment.

| # | Taak | Bestand(en) | Uren |
|---|------|------------|------|
| 4.1 | Alembic migration: reviews tabel | `db/migrations/create_reviews.py` | 1u |
| 4.2 | Review SQLAlchemy model | `db/models/models.py` | 1u |
| 4.3 | FastAPI reviews router | `api/routers/reviews.py` | 4u |
| 4.4 | StarRating component | `frontend/components/StarRating.tsx` | 2u |
| 4.5 | ReviewList RSC + ReviewForm Client Component | `frontend/app/shop/[slug]/` | 4u |
| 4.6 | Integratie review_analyzer_agent (async) | `api/routers/reviews.py` | 2u |

**Afhankelijkheden:** Sprint 1 (productdetail pagina), NextAuth (klant moet ingelogd zijn).

### Sprint 5 — Klantaccountpagina's (Week 5)

**Doel:** Ingelogde klanten kunnen hun profiel en bestellingen beheren.

| # | Taak | Bestand(en) | Uren |
|---|------|------------|------|
| 5.1 | Next.js middleware: /account/* beschermen | `frontend/middleware.ts` | 1u |
| 5.2 | Alembic migration: klanten velden uitbreiden | `db/migrations/extend_customers.py` | 1u |
| 5.3 | FastAPI: `GET /api/auth/mij` endpoint | `api/routers/auth.py` | 2u |
| 5.4 | FastAPI: `PUT /api/klanten/{id}` endpoint | `api/routers/klanten.py` | 2u |
| 5.5 | FastAPI: `GET /api/bestellingen?mijn=true` | `api/routers/betalingen.py` | 2u |
| 5.6 | `/account` profieloverzicht pagina | `frontend/app/account/page.tsx` | 2u |
| 5.7 | `/account/bestellingen` ordergeschiedenis | `frontend/app/account/bestellingen/page.tsx` | 3u |
| 5.8 | `/account/profiel` bewerkformulier | `frontend/app/account/profiel/page.tsx` | 3u |

**Afhankelijkheden:** Sprint 2 (Mollie live — bestellingen zijn echte orders), NextAuth configuratie.

---

### Totaaloverzicht

| Sprint | Item | Uren | Business waarde |
|--------|------|------|----------------|
| Sprint 1 | Navbar + Webshop voltooid | ~12u | 🔴 Hoog — klant kan navigeren |
| Sprint 2 | Mollie Live | ~13u | 🔴 Hoog — echte inkomsten |
| Sprint 3 | Zoekfunctie | ~8u | 🟠 Middel — conversie-booster |
| Sprint 4 | Review-systeem | ~14u | 🟡 Middel — social proof |
| Sprint 5 | Klantaccounts | ~16u | 🟢 Laag — loyaliteitsfunctie |
| **Totaal** | | **~63u** | |

> **Aanbeveling voor KMO:** Begin met Sprint 1 + Sprint 2. Na go-live met echte Mollie betalingen: evalueer of Sprint 3/4/5 direct nodig zijn of pas in Fase 4/5.
