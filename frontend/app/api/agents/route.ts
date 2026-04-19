import { NextResponse } from 'next/server'

const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://localhost:8000'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const agent = searchParams.get('agent')

  const url = agent
    ? `${FASTAPI_URL}/api/agents/analytics/${agent}`
    : `${FASTAPI_URL}/api/agents/analytics`

  try {
    const res = await fetch(url, {
      headers: { 'Authorization': request.headers.get('Authorization') ?? '' },
      next: { revalidate: 60 }, // cache 60s
    })

    if (!res.ok) {
      // FastAPI is offline of geen auth — stuur mock data terug
      return NextResponse.json(buildMockAnalytics())
    }

    const data = await res.json()
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(buildMockAnalytics())
  }
}

export async function POST(request: Request) {
  const { searchParams } = new URL(request.url)
  const agent = searchParams.get('agent')
  const interaction = searchParams.get('interaction')
  const action = searchParams.get('action') // "feedback" | "version"

  if (!agent || !action) {
    return NextResponse.json({ error: 'agent en action zijn verplicht' }, { status: 400 })
  }

  const body = await request.json()
  const url = action === 'feedback'
    ? `${FASTAPI_URL}/api/agents/${agent}/feedback/${interaction}`
    : `${FASTAPI_URL}/api/agents/${agent}/version`

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': request.headers.get('Authorization') ?? '',
      },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch {
    return NextResponse.json({ error: 'FastAPI niet beschikbaar' }, { status: 503 })
  }
}

function buildMockAnalytics() {
  const agents = [
    { naam: 'klantenservice_agent', versie: '1.2', interacties: 342, beoordeeld: 87, score: 4.1, laag: 5 },
    { naam: 'product_beschrijving_agent', versie: '1.1', interacties: 156, beoordeeld: 43, score: 4.4, laag: 2 },
    { naam: 'seo_agent', versie: '1.0', interacties: 89, beoordeeld: 12, score: 3.8, laag: 3 },
    { naam: 'order_verwerking_agent', versie: '1.3', interacties: 478, beoordeeld: 201, score: 4.6, laag: 1 },
    { naam: 'fraude_detectie_agent', versie: '1.0', interacties: 23, beoordeeld: 0, score: 0, laag: 0 },
    { naam: 'retour_verwerking_agent', versie: '1.0', interacties: 45, beoordeeld: 8, score: 3.5, laag: 4 },
    { naam: 'voorraad_advies_agent', versie: '1.0', interacties: 67, beoordeeld: 15, score: 4.2, laag: 1 },
  ]

  return agents.map(a => ({
    agent_naam: a.naam,
    prompt_versie: a.versie,
    totaal_interacties: a.interacties,
    beoordeelde_interacties: a.beoordeeld,
    gemiddelde_score: a.score,
    lage_scores: a.laag,
    verbeter_suggesties: a.laag > 3
      ? [`${a.laag} laag beoordeelde interacties — analyseer de pre-prompt.`]
      : [],
    status: a.beoordeeld > 0 ? 'actief' : 'geen_feedback',
  }))
}
