import { NextResponse } from 'next/server'

const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://localhost:8000'

export async function POST(
  request: Request,
  { params }: { params: Promise<{ betaling_id: string }> }
) {
  const { betaling_id } = await params
  try {
    const body = await request.json()
    const res = await fetch(
      `${FASTAPI_URL}/api/betalingen/${betaling_id}/simuleer`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }
    )
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch {
    return NextResponse.json({ detail: 'Backend niet bereikbaar.' }, { status: 503 })
  }
}
