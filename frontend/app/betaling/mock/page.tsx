'use client'

import { useSearchParams, useRouter } from 'next/navigation'
import { Suspense } from 'react'
import { CreditCard, CheckCircle, XCircle, ArrowLeft } from 'lucide-react'

function MockBetalingContent() {
  const params = useSearchParams()
  const router = useRouter()
  const betalingId = params.get('betaling_id') ?? '—'
  const bestellingId = params.get('bestelling_id') ?? '—'

  async function handleActie(actie: 'betaald' | 'geannuleerd') {
    try {
      await fetch(`/api/betalingen/${betalingId}/simuleer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: actie }),
      })
    } catch {
      // Simulatie best-effort
    }
    if (actie === 'betaald') {
      router.push(`/betaling/succes?bestelling_id=${bestellingId}`)
    } else {
      router.push('/winkelwagen?betaling=geannuleerd')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 text-center">
          <div className="flex justify-center mb-5">
            <div className="w-16 h-16 rounded-2xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center">
              <CreditCard className="w-8 h-8 text-purple-400" />
            </div>
          </div>

          <h1 className="text-2xl font-bold text-white mb-2">Testbetaling</h1>
          <p className="text-white/50 text-sm mb-6">
            Dit is de mock-betaalpagina. In productie wordt dit vervangen door Mollie.
          </p>

          <div className="bg-white/5 border border-white/10 rounded-xl p-4 mb-6 text-left space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-white/50">Bestelling</span>
              <span className="text-white font-mono">{bestellingId}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-white/50">Betaling ID</span>
              <span className="text-white font-mono">{betalingId}</span>
            </div>
          </div>

          <div className="space-y-3">
            <button
              onClick={() => handleActie('betaald')}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white px-6 py-3 rounded-xl font-medium transition-all"
            >
              <CheckCircle className="w-5 h-5" />
              Betaling bevestigen (succes)
            </button>
            <button
              onClick={() => handleActie('geannuleerd')}
              className="w-full flex items-center justify-center gap-2 bg-white/5 border border-white/10 hover:bg-white/10 text-white/70 hover:text-white px-6 py-3 rounded-xl font-medium transition-all"
            >
              <XCircle className="w-4 h-4" />
              Betaling annuleren
            </button>
          </div>

          <button
            onClick={() => router.push('/afrekenen')}
            className="mt-4 flex items-center justify-center gap-1 text-white/30 hover:text-white/60 text-sm mx-auto transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Terug naar checkout
          </button>
        </div>
      </div>
    </div>
  )
}

export default function MockBetalingPage() {
  return (
    <Suspense>
      <MockBetalingContent />
    </Suspense>
  )
}
