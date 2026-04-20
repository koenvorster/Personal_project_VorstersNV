import { NextResponse } from 'next/server'

const FASTAPI_URL = process.env.FASTAPI_URL ?? 'http://localhost:8000'

interface ServiceCheck {
  naam: string
  poort: number
  host: string
  status: 'online' | 'offline'
  latency: string
}

const SERVICES = [
  { naam: 'FastAPI Backend', poort: 8000, host: 'localhost' },
  { naam: 'PostgreSQL', poort: 5432, host: 'localhost' },
  { naam: 'Redis Cache', poort: 6379, host: 'localhost' },
  { naam: 'Keycloak Auth', poort: 8080, host: 'localhost' },
  { naam: 'Ollama LLM', poort: 11434, host: 'localhost' },
  { naam: 'Webhook Engine', poort: 9000, host: 'localhost' },
]

async function checkPort(host: string, port: number, timeoutMs = 2000): Promise<{ ok: boolean; latency: number }> {
  const start = Date.now()
  try {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), timeoutMs)

    await fetch(`http://${host}:${port}/`, {
      signal: controller.signal,
      method: 'HEAD',
    }).catch(() => {
      // Even a connection refused means we tried — check if it was a timeout
    })

    clearTimeout(timeout)

    // Try a TCP-level check via fetch to any path
    const res = await fetch(`http://${host}:${port}/`, {
      signal: AbortSignal.timeout(timeoutMs),
    }).catch(() => null)

    const latency = Date.now() - start
    // If we got any response (even 404), the service is up
    return { ok: res !== null, latency }
  } catch {
    return { ok: false, latency: Date.now() - start }
  }
}

async function fetchFastapiUptime(): Promise<string | null> {
  try {
    const res = await fetch(`${FASTAPI_URL}/health`, {
      signal: AbortSignal.timeout(3000),
      next: { revalidate: 0 },
    })
    if (!res.ok) return null
    const data = await res.json()
    return data.started_at ?? null
  } catch {
    return null
  }
}

export async function GET() {
  const [serviceResults, startedAt] = await Promise.all([
    Promise.all(
      SERVICES.map(async (service) => {
        const { ok, latency } = await checkPort(service.host, service.poort)
        return {
          naam: service.naam,
          poort: service.poort,
          host: service.host,
          status: ok ? ('online' as const) : ('offline' as const),
          latency: ok ? `${latency}ms` : '—',
        } satisfies ServiceCheck
      })
    ),
    fetchFastapiUptime(),
  ])

  return NextResponse.json({
    services: serviceResults,
    timestamp: new Date().toISOString(),
    startedAt,
    onlineCount: serviceResults.filter((s) => s.status === 'online').length,
    totalCount: serviceResults.length,
  })
}

