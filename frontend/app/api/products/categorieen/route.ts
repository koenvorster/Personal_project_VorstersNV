import { NextResponse } from 'next/server'

const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://localhost:8000'

const MOCK_CATEGORIES = [
  { id: 1, naam: 'Kleding', slug: 'kleding', omschrijving: null },
  { id: 2, naam: 'Accessoires', slug: 'accessoires', omschrijving: null },
  { id: 3, naam: 'Kantoor', slug: 'kantoor', omschrijving: null },
]

export async function GET() {
  try {
    const res = await fetch(`${FASTAPI_URL}/api/products/categorieen`, {
      next: { revalidate: 300 },
    })
    if (!res.ok) return NextResponse.json(MOCK_CATEGORIES)
    return NextResponse.json(await res.json())
  } catch {
    return NextResponse.json(MOCK_CATEGORIES)
  }
}
