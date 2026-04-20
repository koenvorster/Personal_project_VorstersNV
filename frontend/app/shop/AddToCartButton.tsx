'use client'

import { useCartStore } from '@/lib/cartStore'
import type { Product } from './ProductGrid'

export default function AddToCartButton({ product }: { product: Product }) {
  const addItem = useCartStore((s) => s.addItem)

  function handleAdd() {
    addItem({
      product_id: product.id,
      naam: product.naam,
      prijs: product.prijs,
      afbeelding_url: product.afbeelding_url ?? undefined,
    })
  }

  return (
    <button
      data-testid={`add-to-cart-${product.id}`}
      onClick={handleAdd}
      disabled={product.voorraad <= 0}
      className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm px-4 py-2 rounded-xl font-medium transition-all"
    >
      {product.voorraad <= 0 ? 'Uitverkocht' : 'In winkelwagen'}
    </button>
  )
}
