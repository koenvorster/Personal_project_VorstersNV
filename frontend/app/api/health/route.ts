import { NextResponse } from 'next/server'

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

export async function GET() {
  const results: ServiceCheck[] = await Promise.all(
    SERVICES.map(async (service) => {
      const { ok, latency } = await checkPort(service.host, service.poort)
      return {
        naam: service.naam,
        poort: service.poort,
        host: service.host,
        status: ok ? ('online' as const) : ('offline' as const),
        latency: ok ? `${latency}ms` : '—',
      }
    })
  )

  return NextResponse.json({
    services: results,
    timestamp: new Date().toISOString(),
    onlineCount: results.filter((s) => s.status === 'online').length,
    totalCount: results.length,
  })
}
