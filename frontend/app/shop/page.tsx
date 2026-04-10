import { Suspense } from 'react'
import type { Metadata } from 'next'
import ProductGrid from './ProductGrid'
import SkeletonCards from './SkeletonCards'

export const metadata: Metadata = {
  title: 'Shop — VorstersNV',
  description: 'Bekijk ons volledige productaanbod.',
}

export default function ShopPage() {
  return (
    <div className="min-h-screen px-4 sm:px-6 py-8 sm:py-12">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 sm:mb-10">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold mb-3">
            <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
              Onze Producten
            </span>
          </h1>
          <p className="text-white/60 text-sm sm:text-base max-w-xl">
            Ontdek ons aanbod van kwalitatieve producten en diensten.
          </p>
        </div>

        <Suspense fallback={<SkeletonCards />}>
          <ProductGrid />
        </Suspense>
      </div>
    </div>
  )
}
