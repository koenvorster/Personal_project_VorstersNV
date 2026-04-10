import Image from 'next/image'
import { ShoppingBag } from 'lucide-react'
import AddToCartButton from './AddToCartButton'

export interface Product {
  id: number
  naam: string
  slug: string
  korte_beschrijving: string
  beschrijving: string
  prijs: number
  voorraad: number
  afbeelding_url?: string
  category_id?: number
  actief: boolean
  seo_titel?: string
  seo_omschrijving?: string
}

interface ProductsResponse {
  items: Product[]
  totaal: number
  pagina: number
  per_pagina: number
}

async function getProducts(): Promise<Product[]> {
  try {
    const res = await fetch('http://localhost:8000/api/products', {
      next: { revalidate: 60 },
    })
    if (!res.ok) return []
    const data: ProductsResponse = await res.json()
    return data.items ?? []
  } catch {
    return []
  }
}

function formatPrijs(prijs: number) {
  return new Intl.NumberFormat('nl-BE', { style: 'currency', currency: 'EUR' }).format(prijs)
}

function ProductCard({ product }: { product: Product }) {
  return (
    <div className="group flex flex-col bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl overflow-hidden hover:border-purple-500/30 hover:bg-white/[0.08] transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-purple-500/10">
      {/* Image */}
      <div className="relative h-48 bg-gradient-to-br from-purple-900/40 to-blue-900/40 flex items-center justify-center overflow-hidden">
        {product.afbeelding_url ? (
          <Image
            src={product.afbeelding_url}
            alt={product.naam}
            fill
            className="object-cover"
            unoptimized
          />
        ) : (
          <ShoppingBag className="w-12 h-12 text-white/20" />
        )}
      </div>

      {/* Content */}
      <div className="p-5 flex-1 flex flex-col">
        <h3 className="text-white font-bold text-base mb-1 group-hover:text-purple-300 transition-colors line-clamp-2">
          {product.naam}
        </h3>
        <p className="text-white/60 text-sm leading-relaxed mb-4 flex-1 line-clamp-3">
          {product.korte_beschrijving}
        </p>

        <div className="flex items-center justify-between mt-auto pt-3 border-t border-white/5">
          <span className="text-xl font-extrabold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
            {formatPrijs(product.prijs)}
          </span>
          <AddToCartButton product={product} />
        </div>
      </div>
    </div>
  )
}

export default async function ProductGrid() {
  const products = await getProducts()

  if (products.length === 0) {
    return (
      <div className="text-center py-24">
        <ShoppingBag className="w-14 h-14 text-white/20 mx-auto mb-4" />
        <p className="text-white/50 text-lg">Geen producten gevonden</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  )
}
