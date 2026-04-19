'use client'

import { useSearchParams } from 'next/navigation'
import { Suspense } from 'react'
import Link from 'next/link'
import { CheckCircle, ShoppingBag, ArrowRight } from 'lucide-react'

function SuccesContent() {
  const params = useSearchParams()
  const bestellingId = params.get('bestelling_id') ?? '—'

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <div className="flex justify-center mb-6">
          <div className="w-20 h-20 rounded-full bg-green-500/20 border border-green-500/30 flex items-center justify-center">
            <CheckCircle className="w-10 h-10 text-green-400" />
          </div>
        </div>

        <h1 className="text-3xl font-extrabold text-white mb-3">
          <span className="bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">
            Bestelling bevestigd!
          </span>
        </h1>
        <p className="text-white/60 mb-2">
          Bedankt voor uw bestelling bij VorstersNV.
        </p>
        <p className="text-white/40 text-sm mb-8">
          U ontvangt een bevestigingsmail op het opgegeven e-mailadres.
        </p>

        <div className="bg-white/5 border border-white/10 rounded-2xl p-5 mb-8">
          <p className="text-white/50 text-xs mb-1">Bestelnummer</p>
          <p className="text-white font-mono text-lg font-bold">{bestellingId}</p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/shop"
            className="flex items-center justify-center gap-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white px-6 py-3 rounded-xl font-medium transition-all"
          >
            <ShoppingBag className="w-4 h-4" />
            Verder winkelen
          </Link>
          <Link
            href="/"
            className="flex items-center justify-center gap-2 bg-white/5 border border-white/10 hover:bg-white/10 text-white/70 hover:text-white px-6 py-3 rounded-xl font-medium transition-all"
          >
            Naar home
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  )
}

export default function BetalingSuccesPage() {
  return (
    <Suspense>
      <SuccesContent />
    </Suspense>
  )
}
