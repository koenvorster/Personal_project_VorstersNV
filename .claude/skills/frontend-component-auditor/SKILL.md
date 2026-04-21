---
name: frontend-component-auditor
description: >
  Use when: auditing Next.js 14 components in VorstersNV for data-testid attributes,
  Server vs Client component decisions, TypeScript strict compliance, Tailwind CSS usage,
  or reviewing component accessibility and performance.
  Triggers: "component auditen", "data-testid ontbreekt", "server component audit",
  "typescript strict", "use client", "client component", "next.js component review"
---

# SKILL: Frontend Component Auditor — VorstersNV

Audit-framework voor Next.js 14 App Router components in het VorstersNV platform.
Controleert correctheid op 4 dimensies: Server/Client split, TypeScript strict, data-testid en Tailwind.

## Audit Pipeline

```
Component Ontvangen
        │
        ▼
┌──────────────────────────────┐
│  Fase 1: Server/Client Split │  ← Heeft het "use client" nodig? Waarom?
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Fase 2: TypeScript Strict   │  ← Geen `any`, expliciete types, return types
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Fase 3: data-testid Audit   │  ← Elke interactieve element heeft een testid
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  Fase 4: Tailwind Audit      │  ← cn() helper, geen inline styles, responsive
└──────────────────────────────┘
```

## Fase 1: Server vs Client Component Beslisboom

```
Heeft het component:
  ├─ useState / useEffect / useContext?          → "use client" VERPLICHT
  ├─ onClick / onSubmit / andere event handlers? → "use client" VERPLICHT
  ├─ window / localStorage / document access?   → "use client" VERPLICHT
  ├─ react-query / useSWR?                      → "use client" VERPLICHT
  └─ Alleen data rendering + async props?       → Server Component (standaard)
```

### VorstersNV-specifieke voorbeelden

| Component | Type | Reden |
|-----------|------|-------|
| `ProductGrid` | Server | Leest data via `fetch()` of DB query |
| `AddToCartButton` | Client | `onClick`, `useState` voor winkelwagen |
| `ProductDetail` | Server | Statische rendering, geen interactie |
| `CheckoutForm` | Client | Formulier, validatie, betalingslogica |
| `ProductImages` | Client | Afbeelding-switcher met `useState` |
| `OrderSummary` | Server | Readonly order data tonen |
| `MollieRedirect` | Client | `window.location` redirect na betaling |
| `NavMenu` | Client | Mobile menu toggle met `useState` |

```tsx
// ✅ GOED — Server Component (geen "use client")
// app/producten/[slug]/page.tsx
export default async function ProductPage({ params }: { params: { slug: string } }) {
  const product = await getProduct(params.slug);  // Direct DB of API call
  return <ProductDetail product={product} />;
}

// ✅ GOED — Client Component (met "use client")
// components/AddToCartButton.tsx
"use client";

export function AddToCartButton({ productId }: { productId: string }) {
  const [added, setAdded] = useState(false);
  return (
    <button
      data-testid="add-to-cart-button"
      onClick={() => { addToCart(productId); setAdded(true); }}
    >
      {added ? "✓ Toegevoegd" : "Voeg toe aan winkelwagen"}
    </button>
  );
}
```

## Fase 2: TypeScript Strict Compliance

### Verboden patronen

```tsx
// ❌ VERBODEN — `any` type
const product: any = await getProduct(id);
const handleClick = (e: any) => {};
function processOrder(data: any): any {}

// ❌ VERBODEN — impliciete return type
export function ProductCard({ product }) {  // geen types!
  return <div>{product.naam}</div>;
}

// ❌ VERBODEN — type assertion zonder null check
const name = (product as Product).naam;  // kan null zijn!
```

```tsx
// ✅ CORRECT — expliciete types overal
interface ProductCardProps {
  product: Product;
  onAddToCart?: (id: string) => void;
}

export function ProductCard({ product, onAddToCart }: ProductCardProps): JSX.Element {
  return (
    <div data-testid={`product-card-${product.id}`}>
      <h2>{product.naam}</h2>
      <p>{product.prijs.toFixed(2)} EUR</p>
    </div>
  );
}

// ✅ CORRECT — null-safe access
const name = product?.naam ?? "Onbekend product";
```

### VorstersNV Type Definities

```typescript
// types/product.ts
export interface Product {
  id: string;
  naam: string;
  slug: string;
  prijs: number;
  voorraad: number;
  categorie: string;
  afbeeldingen: string[];
  actief: boolean;
}

export interface Order {
  id: string;
  klant_id: string;
  status: OrderStatus;
  regels: OrderLine[];
  totaal: number;
  aangemaakt_op: string;
}

export type OrderStatus =
  | "PENDING"
  | "PAYMENT_PENDING"
  | "PAID"
  | "PROCESSING"
  | "SHIPPED"
  | "DELIVERED"
  | "CANCELLED"
  | "PAYMENT_FAILED";
```

## Fase 3: data-testid Audit

**Alle interactieve elementen verplicht een `data-testid`.**

### Naamgevingsconventie

```
<pagina>-<element>-<type>

Voorbeelden:
  product-card-image
  checkout-submit-button
  cart-item-remove-button
  order-status-badge
  nav-menu-toggle
  search-input-field
  filter-categorie-select
```

### Volledige component check

```tsx
// ❌ ONTBREEKT — geen testids
export function ProductCard({ product }: ProductCardProps) {
  return (
    <div>
      <img src={product.afbeelding} alt={product.naam} />
      <h2>{product.naam}</h2>
      <button onClick={() => addToCart(product.id)}>
        Toevoegen
      </button>
    </div>
  );
}

// ✅ CORRECT — alle interactieve elementen hebben testid
export function ProductCard({ product }: ProductCardProps) {
  return (
    <div data-testid={`product-card-${product.id}`}>
      <img
        data-testid="product-card-image"
        src={product.afbeelding}
        alt={product.naam}
      />
      <h2 data-testid="product-card-title">{product.naam}</h2>
      <p data-testid="product-card-price">{product.prijs.toFixed(2)} EUR</p>
      <button
        data-testid="product-card-add-to-cart"
        onClick={() => addToCart(product.id)}
      >
        Toevoegen
      </button>
    </div>
  );
}
```

### Verplichte testids per pagina

| Pagina | Verplichte testids |
|--------|--------------------|
| Productlijst | `product-grid`, `product-card-{id}`, `filter-categorie-select`, `sort-select` |
| Productdetail | `product-detail-title`, `product-detail-price`, `add-to-cart-button`, `product-images` |
| Winkelwagen | `cart-container`, `cart-item-{id}`, `cart-item-remove-{id}`, `cart-total`, `checkout-button` |
| Checkout | `checkout-form`, `checkout-submit-button`, `payment-method-select`, `order-summary` |
| Order bevestiging | `order-confirmation`, `order-id`, `order-status-badge` |

## Fase 4: Tailwind CSS Audit

```tsx
// ❌ VERBODEN — inline styles
<div style={{ backgroundColor: '#ff0000', padding: '16px' }}>

// ❌ VERBODEN — hardcoded kleuren
<div className="bg-[#ff0000]">

// ❌ VERBODEN — klassen samenvoegen zonder cn()
<button className={`btn ${isActive ? 'active' : ''} ${disabled ? 'disabled' : ''}`}>

// ✅ CORRECT — cn() helper voor conditionele klassen
import { cn } from "@/lib/utils";

<button
  className={cn(
    "rounded-lg px-4 py-2 font-medium transition-colors",
    "bg-primary text-primary-foreground hover:bg-primary/90",
    isActive && "ring-2 ring-offset-2",
    disabled && "opacity-50 cursor-not-allowed",
  )}
>
```

### Responsive breakpoints (VorstersNV)

```tsx
// Productgrid — responsive van 1 tot 4 kolommen
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">

// Container — max-width met padding
<div className="container mx-auto px-4 sm:px-6 lg:px-8">
```

## Audit Rapport Template

```
🔍 Frontend Component Audit — VorstersNV
==========================================
Component: <ComponentNaam>
Bestand:   components/<pad/naar/component>.tsx

FASE 1: Server/Client Split
  ✅ Correct: Server Component (geen client-side state)
  — of —
  ⚠️  "use client" aanwezig maar useState/useEffect ontbreekt → kan Server Component zijn

FASE 2: TypeScript Strict
  ✅ Alle parameters getypeerd
  ❌ `any` gevonden op lijn 42: `const data: any = ...`
     Fix: vervang door expliciete interface

FASE 3: data-testid
  ✅ 3/4 interactieve elementen hebben testid
  ❌ <button onClick={...}> op lijn 28 mist data-testid
     Voorstel: data-testid="product-card-add-to-cart"

FASE 4: Tailwind
  ✅ cn() gebruikt voor conditionele klassen
  ⚠️  Hardcoded kleur gevonden: bg-[#2563eb]
     Vervang door: bg-primary (Tailwind config variable)

Score: 3/4 fases volledig
Kritieke issues: 1 (TypeScript any)
Waarschuwingen: 2
```

## Voorbeeld Gebruik

### Input
```
"Audit dit component op VorstersNV standaarden:

'use client'
export function ProductCard({ product }: any) {
  return <div>
    <img src={product.img} />
    <button onClick={() => add(product.id)}>Voeg toe</button>
  </div>
}"
```

### Output
```
🔍 Audit resultaat — ProductCard

FASE 1: Server/Client Split
  ⚠️  "use client" aanwezig — controleer of useState/useEffect echt nodig is.
     Heeft alleen onClick → kan blijven als Client Component.

FASE 2: TypeScript
  ❌ Props type is `any` — VERBODEN in strict mode
     Fix: interface ProductCardProps { product: Product; }

FASE 3: data-testid
  ❌ <button> mist data-testid
     Voorstel: data-testid="product-card-add-to-cart"
  ❌ <img> mist data-testid
     Voorstel: data-testid="product-card-image"

FASE 4: Tailwind
  ✅ Geen inline styles gevonden

Score: 1/4 volledig correct
Kritieke fixes vereist: 2 (TypeScript any, data-testid)
```

## Gerelateerde skills
- nextjs-frontend
- testing-patterns
- fastapi-ddd
