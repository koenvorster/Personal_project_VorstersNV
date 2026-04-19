---
mode: agent
description: Genereer een complete Next.js productpagina voor VorstersNV met Server Components, SEO metadata, structured data en Add-to-Cart knop.
---

# Productpagina Generator

Maak een complete, SEO-geoptimaliseerde Next.js 14 productpagina voor VorstersNV.

## Gevraagde informatie
- **Product type**: [bijv. elektronica, kleding, food]
- **Speciale vereisten**: [bijv. varianten, voorraadmelding, reviews]

## Wat te genereren

### 1. Pagina Component (`frontend/app/(shop)/shop/[slug]/page.tsx`)
- Server Component (geen `"use client"`)
- `generateMetadata()` voor SEO
- Structured Data (JSON-LD `Product` schema)
- Breadcrumb navigatie
- Foutafhandeling via `notFound()` bij ontbrekend product

### 2. Product Detail Component (`frontend/components/shop/ProductDetail.tsx`)
- Afbeeldingsgalerij met `next/image`
- Prijsweergave (met/zonder BTW)
- Voorraadstatus badge
- `AddToCartButton` (Client Component)
- Productbeschrijving (sanitized HTML of Markdown)

### 3. SEO Metadata
```tsx
export async function generateMetadata({ params }): Promise<Metadata> {
  const product = await getProduct(params.slug);
  return {
    title: `${product.naam} | VorstersNV`,
    description: product.meta_description,        // max 155 tekens
    openGraph: {
      title: product.naam,
      images: [{ url: product.afbeelding_url, width: 800, height: 800 }],
    },
    alternates: { canonical: `/shop/${product.slug}` },
  };
}
```

### 4. Structured Data (JSON-LD)
```tsx
const productSchema = {
  "@context": "https://schema.org",
  "@type": "Product",
  name: product.naam,
  description: product.beschrijving,
  image: product.afbeelding_url,
  offers: {
    "@type": "Offer",
    price: product.prijs,
    priceCurrency: "EUR",
    availability: product.stock > 0
      ? "https://schema.org/InStock"
      : "https://schema.org/OutOfStock",
  },
};
```

### 5. TypeScript Types (`frontend/lib/types.ts`)
```typescript
export interface Product {
  id: string;
  naam: string;
  slug: string;
  prijs: number;
  prijs_excl_btw: number;
  btw_percentage: number;
  beschrijving: string;
  meta_description: string;
  afbeelding_url: string;
  afbeeldingen: string[];
  stock: number;
  categorie: Category;
  actief: boolean;
}
```

### 6. API Fetch (`frontend/lib/api.ts`)
```typescript
export async function getProduct(slug: string): Promise<Product> {
  const res = await fetch(`${API_BASE}/api/v1/producten/${slug}`, {
    next: { revalidate: 60 },
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Product ophalen mislukt");
  return res.json();
}
```

## Kwaliteitsregels
- Afbeeldingen via `next/image` met `priority` op hoofdafbeelding
- `notFound()` bij null product — nooit een lege pagina
- Prijs altijd geformatteerd: `new Intl.NumberFormat("nl-BE", { style: "currency", currency: "EUR" })`
- BTW-informatie verplicht vermelden (Belgische wet)
