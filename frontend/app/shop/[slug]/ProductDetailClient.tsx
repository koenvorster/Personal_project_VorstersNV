'use client'

import { useState } from 'react'
import { Minus, Plus, ShoppingCart } from 'lucide-react'
import { useCartStore } from '@/lib/cartStore'
import type { Product } from '../ProductGrid'

export default function ProductDetailClient({ product }: { product: Product }) {
  const [aantal, setAantal] = useState(1)
  const addItem = useCartStore((s) => s.addItem)
  const [added, setAdded] = useState(false)

  function handleAdd() {
    for (let i = 0; i < aantal; i++) {
      addItem({
        product_id: product.id,
        naam: product.naam,
        prijs: product.prijs,
        afbeelding_url: product.afbeelding_url,
      })
    }
    setAdded(true)
    setTimeout(() => setAdded(false), 2000)
  }

  const uitverkocht = product.voorraad <= 0

  return (
    <div className="space-y-4">
      {/* Quantity selector */}
      <div className="flex items-center gap-4">
        <span className="text-white/70 text-sm">Aantal:</span>
        <div className="flex items-center bg-white/5 border border-white/10 rounded-xl overflow-hidden">
          <button
            onClick={() => setAantal((n) => Math.max(1, n - 1))}
            className="px-3 py-2 text-white/70 hover:text-white hover:bg-white/10 transition-colors"
            disabled={uitverkocht}
          >
            <Minus className="w-4 h-4" />
          </button>
          <span className="px-4 py-2 text-white font-medium min-w-[2.5rem] text-center">
            {aantal}
          </span>
          <button
            onClick={() => setAantal((n) => Math.min(product.voorraad, n + 1))}
            className="px-3 py-2 text-white/70 hover:text-white hover:bg-white/10 transition-colors"
            disabled={uitverkocht}
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Add to cart */}
      <button
        onClick={handleAdd}
        disabled={uitverkocht}
        className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-3 rounded-xl font-medium transition-all"
      >
        <ShoppingCart className="w-5 h-5" />
        {uitverkocht ? 'Uitverkocht' : added ? 'Toegevoegd ✓' : 'Toevoegen aan winkelwagen'}
      </button>
    </div>
  )
}
