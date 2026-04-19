import { NextResponse } from 'next/server'

const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://localhost:8000'

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ slug: string }> },
) {
  const { slug } = await params
  try {
    const res = await fetch(`${FASTAPI_URL}/api/products/slug/${slug}`, {
      next: { revalidate: 60 },
    })
    if (res.status === 404) return NextResponse.json(null, { status: 404 })
    if (!res.ok) return NextResponse.json(null, { status: 404 })
    return NextResponse.json(await res.json())
  } catch {
    return NextResponse.json(null, { status: 404 })
  }
}
