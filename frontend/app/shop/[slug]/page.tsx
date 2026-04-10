import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Image from 'next/image'
import { ShoppingBag } from 'lucide-react'
import type { Product } from '../ProductGrid'
import ProductDetailClient from './ProductDetailClient'

async function getProduct(slug: string): Promise<Product | null> {
  try {
    const res = await fetch(`http://localhost:8000/api/products/${slug}`, {
      next: { revalidate: 60 },
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Metadata> {
  const { slug } = await params
  const product = await getProduct(slug)
  return {
    title: product?.seo_titel ?? product?.naam ?? 'Product',
    description: product?.seo_omschrijving ?? product?.korte_beschrijving,
  }
}

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const product = await getProduct(slug)

  if (!product) notFound()

  const voorraadLabel =
    product.voorraad > 10
      ? { text: 'Op voorraad', cls: 'text-green-400 bg-green-400/10 border-green-400/20' }
      : product.voorraad > 0
      ? { text: `Nog ${product.voorraad} beschikbaar`, cls: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20' }
      : { text: 'Uitverkocht', cls: 'text-red-400 bg-red-400/10 border-red-400/20' }

  return (
    <div className="min-h-screen px-4 sm:px-6 py-8 sm:py-12">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
          {/* Left: image */}
          <div className="space-y-3">
            <div className="relative aspect-square bg-gradient-to-br from-purple-900/40 to-blue-900/40 rounded-2xl overflow-hidden border border-white/10 flex items-center justify-center">
              {product.afbeelding_url ? (
                <Image
                  src={product.afbeelding_url}
                  alt={product.naam}
                  fill
                  className="object-cover"
                  unoptimized
                />
              ) : (
                <ShoppingBag className="w-24 h-24 text-white/20" />
              )}
            </div>
          </div>

          {/* Right: details */}
          <div className="flex flex-col">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white mb-3">
              {product.naam}
            </h1>

            <div className="text-3xl font-extrabold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent mb-4">
              {new Intl.NumberFormat('nl-BE', { style: 'currency', currency: 'EUR' }).format(product.prijs)}
            </div>

            <span className={`inline-flex self-start text-xs font-medium px-3 py-1 rounded-full border mb-5 ${voorraadLabel.cls}`}>
              {voorraadLabel.text}
            </span>

            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-5 mb-6">
              <p className="text-white/70 text-sm leading-relaxed">
                {product.beschrijving || product.korte_beschrijving}
              </p>
            </div>

            <ProductDetailClient product={product} />
          </div>
        </div>
      </div>
    </div>
  )
}
