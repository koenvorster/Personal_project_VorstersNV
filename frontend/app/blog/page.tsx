'use client'

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import { Clock, Calendar, ArrowRight } from 'lucide-react'
import Link from 'next/link'
import GlassCard from '@/components/ui/GlassCard'
import { blogPosts } from '@/data/blog'

function AnimatedSection({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true })
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
      transition={{ duration: 0.6, delay }}
    >
      {children}
    </motion.div>
  )
}

export default function BlogPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="mb-8 sm:mb-12"
      >
        <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white mb-2 sm:mb-3">Blog</h1>
        <p className="text-slate-400 text-base sm:text-lg max-w-2xl">
          Technische tutorials, inzichten en tips over AI, IoT, web development en DevOps.
        </p>
      </motion.div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 md:gap-8">
        {blogPosts.map((post, i) => (
          <AnimatedSection key={post.slug} delay={i * 0.1}>
            <Link href={`/blog/${post.slug}`} className="block h-full">
              <GlassCard className="overflow-hidden h-full flex flex-col group relative hover:border-green-500/30 hover:bg-white/[0.08] transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-green-500/5">
                {/* Image */}
                <div className="relative h-40 sm:h-48 md:h-52 overflow-hidden" role="img" aria-label={post.titel}>
                  <div
                    className="absolute inset-0 bg-cover bg-center group-hover:scale-105 transition-transform duration-500"
                    style={{ backgroundImage: `url('${post.afbeelding}')` }}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 to-transparent" />
                  <div className="absolute top-4 left-4">
                    <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${post.categorieKleur}`}>
                      {post.categorie}
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="p-4 sm:p-6 flex flex-col flex-1">
                  <h2 className="text-lg sm:text-xl font-bold text-white mb-2 group-hover:text-green-400 transition-colors">
                    {post.titel}
                  </h2>
                  <p className="text-slate-400 text-sm leading-relaxed mb-4 flex-1">
                    {post.excerpt}
                  </p>

                  {/* Meta */}
                  <div className="flex items-center justify-between pt-4 border-t border-white/10">
                    <div className="flex items-center gap-4 text-xs text-slate-500">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5" />
                        {post.datum}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        {post.leestijd}
                      </span>
                    </div>
                    <span className="text-green-400 text-xs font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      Lees meer <ArrowRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              </GlassCard>
            </Link>
          </AnimatedSection>
        ))}
      </div>

      {/* CTA */}
      <AnimatedSection delay={0.5}>
        <div className="mt-12 sm:mt-16 text-center">
          <GlassCard className="inline-block px-8 py-6 sm:px-12 sm:py-8">
            <p className="text-lg sm:text-xl font-semibold text-white mb-2">Meer artikels onderweg</p>
            <p className="text-slate-400 text-sm sm:text-base">
              Ik schrijf regelmatig over mijn projecten, nieuwe technologieën en praktische tutorials.
            </p>
          </GlassCard>
        </div>
      </AnimatedSection>
    </div>
  )
}
