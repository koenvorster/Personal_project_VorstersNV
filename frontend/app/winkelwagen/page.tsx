'use client'

import Image from 'next/image'
import Link from 'next/link'
import { Minus, Plus, Trash2, ShoppingBag } from 'lucide-react'
import { useCartStore } from '@/lib/cartStore'

const VERZENDKOSTEN = 4.95
const BTW = 0.21

function formatPrijs(prijs: number) {
  return new Intl.NumberFormat('nl-BE', { style: 'currency', currency: 'EUR' }).format(prijs)
}

export default function WinkelwagenPage() {
  const { items, removeItem, updateAantal } = useCartStore()
  const subtotaal = useCartStore((s) => s.totaal())
  const verzendkosten = subtotaal >= 50 ? 0 : VERZENDKOSTEN
  const btw = subtotaal * BTW
  const totaal = subtotaal + btw + verzendkosten

  if (items.length === 0) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-4 text-center">
        <ShoppingBag className="w-16 h-16 text-white/20 mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">Uw winkelwagen is leeg</h2>
        <p className="text-white/60 mb-6">Voeg producten toe om verder te gaan.</p>
        <Link
          href="/shop"
          className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white px-6 py-3 rounded-xl font-medium transition-all"
        >
          Verder winkelen
        </Link>
      </div>
    )
  }

  return (
    <div className="min-h-screen px-4 sm:px-6 py-8 sm:py-12">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white mb-8">
          <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
            Winkelwagen
          </span>
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Items list */}
          <div className="lg:col-span-2 space-y-3">
            {items.map((item) => (
              <div
                key={item.product_id}
                className="flex items-center gap-4 bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-4"
              >
                {/* Image */}
                <div className="relative w-16 h-16 rounded-xl overflow-hidden bg-white/10 flex-shrink-0 flex items-center justify-center">
                  {item.afbeelding_url ? (
                    <Image src={item.afbeelding_url} alt={item.naam} fill className="object-cover" unoptimized />
                  ) : (
                    <ShoppingBag className="w-6 h-6 text-white/30" />
                  )}
                </div>

                {/* Name + price */}
                <div className="flex-1 min-w-0">
                  <p className="text-white font-medium text-sm truncate">{item.naam}</p>
                  <p className="text-white/50 text-xs">{formatPrijs(item.prijs)} / stuk</p>
                </div>

                {/* Quantity */}
                <div className="flex items-center bg-white/5 border border-white/10 rounded-xl overflow-hidden">
                  <button
                    data-testid={`quantity-minus-${item.product_id}`}
                    onClick={() => updateAantal(item.product_id, item.aantal - 1)}
                    className="px-2 py-1.5 text-white/60 hover:text-white hover:bg-white/10 transition-colors"
                  >
                    <Minus className="w-3.5 h-3.5" />
                  </button>
                  <span data-testid={`quantity-${item.product_id}`} className="px-3 py-1.5 text-white text-sm font-medium min-w-[2rem] text-center">
                    {item.aantal}
                  </span>
                  <button
                    data-testid={`quantity-plus-${item.product_id}`}
                    onClick={() => updateAantal(item.product_id, item.aantal + 1)}
                    className="px-2 py-1.5 text-white/60 hover:text-white hover:bg-white/10 transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Subtotaal */}
                <p className="text-white font-semibold text-sm w-16 text-right">
                  {formatPrijs(item.prijs * item.aantal)}
                </p>

                {/* Delete */}
                <button
                  data-testid={`remove-item-${item.product_id}`}
                  onClick={() => removeItem(item.product_id)}
                  className="text-white/30 hover:text-red-400 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>

          {/* Order summary */}
          <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6 h-fit">
            <h2 className="text-white font-bold text-lg mb-5">Overzicht</h2>

            <div className="space-y-3 text-sm mb-5">
              <div className="flex justify-between text-white/70">
                <span>Subtotaal</span>
                <span>{formatPrijs(subtotaal)}</span>
              </div>
              <div className="flex justify-between text-white/70">
                <span>BTW (21%)</span>
                <span>{formatPrijs(btw)}</span>
              </div>
              <div className="flex justify-between text-white/70">
                <span>Verzendkosten</span>
                <span>{verzendkosten === 0 ? 'Gratis' : formatPrijs(verzendkosten)}</span>
              </div>
              <div className="border-t border-white/10 pt-3 flex justify-between font-bold text-white text-base">
                <span>Totaal</span>
                <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                  {formatPrijs(totaal)}
                </span>
              </div>
            </div>

            <Link
              data-testid="checkout-link"
              href="/afrekenen"
              className="block w-full text-center bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white px-6 py-3 rounded-xl font-medium transition-all"
            >
              Afrekenen →
            </Link>

            <Link href="/shop" className="block text-center text-white/40 hover:text-white/70 text-sm mt-3 transition-colors">
              Verder winkelen
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
