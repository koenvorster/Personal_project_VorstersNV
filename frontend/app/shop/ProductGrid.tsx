'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { Search, ShoppingBag, Tag, X } from 'lucide-react'
import AddToCartButton from './AddToCartButton'
import SkeletonCards from './SkeletonCards'

export interface Product {
  id: number
  naam: string
  slug: string
  korte_beschrijving: string | null
  beschrijving: string | null
  prijs: number
  voorraad: number
  afbeelding_url?: string | null
  category_id?: number | null
  category_naam?: string | null
  kenmerken?: Record<string, unknown> | null
  tags?: string[] | null
  actief: boolean
  seo_titel?: string | null
  seo_omschrijving?: string | null
}

interface Category {
  id: number
  naam: string
  slug: string
}

interface ProductsResponse {
  items: Product[]
  totaal: number
  pagina: number
  per_pagina: number
}

function formatPrijs(prijs: number) {
  return new Intl.NumberFormat('nl-BE', { style: 'currency', currency: 'EUR' }).format(prijs)
}

function VoorraadBadge({ voorraad }: { voorraad: number }) {
  if (voorraad === 0)
    return <span className="text-xs text-red-400 bg-red-400/10 border border-red-400/20 rounded-full px-2 py-0.5">Uitverkocht</span>
  if (voorraad <= 5)
    return <span className="text-xs text-amber-400 bg-amber-400/10 border border-amber-400/20 rounded-full px-2 py-0.5">Nog {voorraad} stuks</span>
  return null
}

function ProductCard({ product }: { product: Product }) {
  return (
    <div className="group flex flex-col bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl overflow-hidden hover:border-purple-500/30 hover:bg-white/[0.08] transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-purple-500/10">
      {/* Image – klikbaar naar detailpagina */}
      <Link href={`/shop/${product.slug}`} className="block">
        <div className="relative h-48 bg-gradient-to-br from-purple-900/40 to-blue-900/40 flex items-center justify-center overflow-hidden">
          {product.afbeelding_url ? (
            <Image
              src={product.afbeelding_url}
              alt={product.naam}
              fill
              className="object-cover group-hover:scale-105 transition-transform duration-300"
              unoptimized
            />
          ) : (
            <ShoppingBag className="w-12 h-12 text-white/20 group-hover:text-white/30 transition-colors" />
          )}
          {product.tags?.includes('nieuw') && (
            <span className="absolute top-3 left-3 text-xs font-bold bg-purple-600 text-white px-2 py-0.5 rounded-full">Nieuw</span>
          )}
          {product.tags?.includes('populair') && (
            <span className="absolute top-3 left-3 text-xs font-bold bg-blue-600 text-white px-2 py-0.5 rounded-full">Populair</span>
          )}
        </div>
      </Link>

      {/* Content */}
      <div className="p-5 flex-1 flex flex-col">
        {product.category_naam && (
          <div className="flex items-center gap-1 mb-2">
            <Tag className="w-3 h-3 text-purple-400" />
            <span className="text-xs text-purple-400">{product.category_naam}</span>
          </div>
        )}
        <Link href={`/shop/${product.slug}`} className="group/title">
          <h3 className="text-white font-bold text-base mb-1 group-hover/title:text-purple-300 transition-colors line-clamp-2">
            {product.naam}
          </h3>
        </Link>
        <p className="text-white/60 text-sm leading-relaxed mb-3 flex-1 line-clamp-3">
          {product.korte_beschrijving}
        </p>

        <div className="flex items-center justify-between mb-3">
          <span className="text-xl font-extrabold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
            {formatPrijs(product.prijs)}
          </span>
          <VoorraadBadge voorraad={product.voorraad} />
        </div>

        <div className="flex items-center gap-2 pt-3 border-t border-white/5">
          <AddToCartButton product={product} />
          <Link
            href={`/shop/${product.slug}`}
            className="flex-1 text-center text-sm text-white/60 hover:text-purple-300 transition-colors py-2 rounded-xl hover:bg-white/5"
          >
            Meer info →
          </Link>
        </div>
      </div>
    </div>
  )
}

export default function ProductGrid() {
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [zoek, setZoek] = useState('')
  const [activeCat, setActiveCat] = useState<string | null>(null)
  const [debouncedZoek, setDebouncedZoek] = useState('')

  // Debounce zoekterm
  useEffect(() => {
    const t = setTimeout(() => setDebouncedZoek(zoek), 350)
    return () => clearTimeout(t)
  }, [zoek])

  // Categorieën ophalen
  useEffect(() => {
    fetch('/api/products/categorieen')
      .then(r => r.json())
      .then((data: Category[]) => setCategories(data))
      .catch(() => { /* silent */ })
  }, [])

  // Producten ophalen bij filter-/zoekwijziging
  const fetchProducts = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (debouncedZoek) params.set('zoek', debouncedZoek)
      if (activeCat) params.set('categorie_slug', activeCat)
      const res = await fetch(`/api/products?${params}`)
      const data: ProductsResponse = await res.json()
      setProducts(data.items ?? [])
    } catch {
      setProducts([])
    } finally {
      setLoading(false)
    }
  }, [debouncedZoek, activeCat])

  useEffect(() => { fetchProducts() }, [fetchProducts])

  return (
    <div>
      {/* Zoek + filter balk */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6 sm:mb-8">
        {/* Zoekbalk */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30 pointer-events-none" />
          <input
            type="search"
            value={zoek}
            onChange={e => setZoek(e.target.value)}
            placeholder="Zoek producten..."
            className="w-full bg-white/5 border border-white/10 rounded-xl pl-9 pr-9 py-2.5 text-sm text-white placeholder-white/30 focus:outline-none focus:border-purple-500/50 focus:bg-white/[0.07] transition-all"
          />
          {zoek && (
            <button
              onClick={() => setZoek('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/70 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Categorie-filter (horizontaal scrollbaar) */}
        {categories.length > 0 && (
          <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
            <button
              onClick={() => setActiveCat(null)}
              className={`shrink-0 text-xs px-3 py-2 rounded-xl transition-all ${
                activeCat === null
                  ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold'
                  : 'bg-white/5 border border-white/10 text-white/60 hover:text-white hover:border-white/20'
              }`}
            >
              Alles
            </button>
            {categories.map(cat => (
              <button
                key={cat.id}
                onClick={() => setActiveCat(activeCat === cat.slug ? null : cat.slug)}
                className={`shrink-0 text-xs px-3 py-2 rounded-xl transition-all ${
                  activeCat === cat.slug
                    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold'
                    : 'bg-white/5 border border-white/10 text-white/60 hover:text-white hover:border-white/20'
                }`}
              >
                {cat.naam}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Grid */}
      {loading ? (
        <SkeletonCards />
      ) : products.length === 0 ? (
        <div className="text-center py-24">
          <ShoppingBag className="w-14 h-14 text-white/20 mx-auto mb-4" />
          <p className="text-white/50 text-lg">Geen producten gevonden</p>
          {(zoek || activeCat) && (
            <button
              onClick={() => { setZoek(''); setActiveCat(null) }}
              className="mt-4 text-sm text-purple-400 hover:text-purple-300 transition-colors"
            >
              Filters wissen
            </button>
          )}
        </div>
      ) : (
        <>
          <p className="text-white/30 text-xs mb-4">{products.length} product{products.length !== 1 ? 'en' : ''} gevonden</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6">
            {products.map(product => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

