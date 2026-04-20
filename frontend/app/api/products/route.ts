import { NextResponse } from 'next/server'

const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://localhost:8000'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const params = new URLSearchParams()
  for (const [k, v] of searchParams.entries()) params.set(k, v)

  try {
    const res = await fetch(`${FASTAPI_URL}/api/products?${params}`, {
      next: { revalidate: 60 },
    })
    if (!res.ok) {
      return NextResponse.json(
        { error: 'Backend niet beschikbaar', detail: `Status: ${res.status}` },
        { status: res.status }
      )
    }
    return NextResponse.json(await res.json())
  } catch (err) {
    return NextResponse.json(
      { error: 'FastAPI backend niet bereikbaar', detail: String(err) },
      { status: 503 }
    )
  }
}

