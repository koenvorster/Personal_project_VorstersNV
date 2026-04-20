# SKILL: Next.js Frontend

Reference knowledge for the VorstersNV Next.js 14 App Router frontend.

## Project Structure

```
frontend/
├── app/                    ← App Router (all routes here)
│   ├── layout.tsx          ← Root layout (providers, fonts)
│   ├── page.tsx            ← Home page
│   ├── (shop)/             ← Route group
│   │   ├── products/
│   │   │   ├── page.tsx    ← /products listing
│   │   │   └── [id]/
│   │   │       └── page.tsx ← /products/:id
│   │   └── cart/
│   ├── (account)/
│   │   └── orders/
│   └── api/                ← API routes (server-side)
├── components/
│   ├── ui/                 ← Reusable UI components
│   └── features/           ← Feature-specific components
├── lib/                    ← Utilities, API clients
├── types/                  ← TypeScript type definitions
└── public/                 ← Static assets
```

## App Router Patterns

### Server Component (default)
```tsx
// app/products/page.tsx — no "use client" = Server Component
import { getProducts } from "@/lib/api/products"

export default async function ProductsPage() {
  const products = await getProducts()  // runs on server
  return (
    <main>
      <h1>Products</h1>
      <ProductGrid products={products} />
    </main>
  )
}
```

### Client Component (when needed)
```tsx
"use client"

import { useState } from "react"

export function AddToCartButton({ productId }: { productId: number }) {
  const [loading, setLoading] = useState(false)

  const handleClick = async () => {
    setLoading(true)
    await fetch("/api/cart", { method: "POST", body: JSON.stringify({ productId }) })
    setLoading(false)
  }

  return (
    <button
      data-testid="add-to-cart-button"
      onClick={handleClick}
      disabled={loading}
      className="bg-blue-600 text-white px-4 py-2 rounded"
    >
      {loading ? "Adding..." : "Add to Cart"}
    </button>
  )
}
```

### API Route (server action)
```typescript
// app/api/cart/route.ts
import { NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  const body = await request.json()
  // call FastAPI backend
  const res = await fetch(`${process.env.API_URL}/cart`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  return NextResponse.json(await res.json(), { status: res.status })
}
```

## TypeScript Conventions

```typescript
// Types in types/ directory
export interface Product {
  id: number
  name: string
  price: string   // Decimal as string from API
  stock: number
  categoryId: number
}

// Strict typing — NO `any`
const handleSubmit = (data: OrderFormData): void => {
  // ...
}

// Optional chaining
const city = user?.address?.city ?? "Unknown"
```

## Tailwind Patterns

```tsx
// Utility classes — no inline styles
<div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-4">
  <div className="rounded-lg shadow-md bg-white p-6 hover:shadow-lg transition-shadow">
    <h2 className="text-lg font-semibold text-gray-900">{product.name}</h2>
    <p className="text-blue-600 font-bold mt-2">€{product.price}</p>
  </div>
</div>

// Conditional classes
<button
  className={`px-4 py-2 rounded ${
    isActive ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-700"
  }`}
>
```

## data-testid Convention (REQUIRED)

Every interactive element needs `data-testid`:

```tsx
// Buttons
<button data-testid="submit-order-button">Bestelling plaatsen</button>

// Form inputs
<input data-testid="quantity-input" type="number" />

// Dropdowns
<select data-testid="category-select">

// Links that trigger actions
<a data-testid="view-order-link" href={`/orders/${id}`}>

// Pattern: kebab-case, descriptive, action-oriented
// ✅ "add-to-cart-button", "product-price", "order-status-badge"
// ❌ "btn1", "div-thing", "component"
```

## Fetching Data

```typescript
// lib/api/products.ts — server-side fetcher
export async function getProducts(): Promise<Product[]> {
  const res = await fetch(`${process.env.API_URL}/products`, {
    next: { revalidate: 60 },  // ISR: revalidate every 60s
  })
  if (!res.ok) throw new Error("Failed to fetch products")
  return res.json()
}

// Client-side with SWR or React Query
"use client"
import useSWR from "swr"
const fetcher = (url: string) => fetch(url).then(r => r.json())
const { data, isLoading } = useSWR("/api/products", fetcher)
```

## Metadata (SEO)

```typescript
// app/products/[id]/page.tsx
import { Metadata } from "next"

export async function generateMetadata({ params }): Promise<Metadata> {
  const product = await getProduct(params.id)
  return {
    title: `${product.name} | VorstersNV`,
    description: product.description,
    openGraph: { images: [product.imageUrl] },
  }
}
```

## Loading & Error States

```tsx
// app/products/loading.tsx — automatic Suspense boundary
export default function Loading() {
  return <div data-testid="products-loading" className="animate-pulse">Laden...</div>
}

// app/products/error.tsx
"use client"
export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div data-testid="products-error">
      <p>Er ging iets mis: {error.message}</p>
      <button onClick={reset}>Opnieuw proberen</button>
    </div>
  )
}
```

## Rules Summary

| ✅ DO | ❌ DON'T |
|-------|---------|
| Server Components by default | `"use client"` on everything |
| `data-testid` on interactive elements | Skip test attributes |
| TypeScript strict (no `any`) | Use `any` to escape type errors |
| Tailwind utility classes | Inline styles |
| Async/await in server components | `useEffect` for initial data fetch in server components |
| `next: { revalidate }` for caching | No caching strategy |
| Dutch UI text (`Bestelling plaatsen`) | English UI text |
