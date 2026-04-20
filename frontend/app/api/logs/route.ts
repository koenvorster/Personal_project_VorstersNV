import { NextResponse } from 'next/server'

const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://localhost:8000'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const limiet = searchParams.get('limiet') ?? '20'

  try {
    const res = await fetch(`${FASTAPI_URL}/api/logs/recent?limiet=${limiet}`, {
      next: { revalidate: 0 }, // altijd vers
    })
    if (!res.ok) {
      return NextResponse.json([], { status: res.status })
    }
    return NextResponse.json(await res.json())
  } catch {
    return NextResponse.json([], { status: 503 })
  }
}
