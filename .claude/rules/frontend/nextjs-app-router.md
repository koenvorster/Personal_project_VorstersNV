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
