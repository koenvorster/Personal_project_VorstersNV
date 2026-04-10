'use client'

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import { Clock, Calendar } from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'

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

const blogPosts = [
  {
    slug: 'ai-chatbots-voor-je-kmo',
    titel: 'Aan de slag met AI chatbots voor je KMO',
    excerpt: 'Ontdek hoe je met tools als OpenAI en LangChain een slimme chatbot bouwt die je klantenservice automatiseert. Stap voor stap, van API-key tot deployment.',
    datum: '12 juni 2025',
    leestijd: '8 min',
    categorie: 'AI',
    afbeelding: 'https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=800&q=80',
    categorieKleur: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
  },
  {
    slug: 'iot-sensoren-python-mqtt',
    titel: 'IoT sensoren uitlezen met Python en MQTT',
    excerpt: 'Een praktische tutorial over het opzetten van een IoT-sensornetwerk. Van ESP32 naar MQTT broker naar Python dashboard — alles wat je nodig hebt.',
    datum: '28 mei 2025',
    leestijd: '12 min',
    categorie: 'IoT',
    afbeelding: 'https://images.unsplash.com/photo-1558346490-a72e53ae2d4f?auto=format&fit=crop&w=800&q=80',
    categorieKleur: 'bg-green-500/20 text-green-400 border-green-500/30',
  },
  {
    slug: 'nextjs-fastapi-starter',
    titel: 'Next.js & FastAPI: een full-stack starter guide',
    excerpt: 'Bouw een moderne full-stack applicatie met Next.js als frontend en FastAPI als backend. Inclusief authentication, database setup en deployment tips.',
    datum: '3 mei 2025',
    leestijd: '15 min',
    categorie: 'Web Development',
    afbeelding: 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=800&q=80',
    categorieKleur: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  },
  {
    slug: 'docker-voor-beginners',
    titel: 'Docker voor beginners: je eerste container',
    excerpt: 'Wat is Docker eigenlijk en waarom zou je het als ontwikkelaar moeten gebruiken? In deze tutorial bouw je stap voor stap je eerste containerized applicatie.',
    datum: '14 april 2025',
    leestijd: '10 min',
    categorie: 'DevOps',
    afbeelding: 'https://images.unsplash.com/photo-1605745341112-85968b19335b?auto=format&fit=crop&w=800&q=80',
    categorieKleur: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  },
]

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
            <GlassCard className="overflow-hidden h-full flex flex-col group relative">
              {/* Image */}
              <div className="relative h-40 sm:h-48 md:h-52 overflow-hidden" role="img" aria-label={post.titel}>
                <div
                  className="absolute inset-0 bg-cover bg-center"
                  style={{ backgroundImage: `url('${post.afbeelding}')` }}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 to-transparent" />
                <div className="absolute top-4 left-4">
                  <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${post.categorieKleur}`}>
                    {post.categorie}
                  </span>
                </div>
                <div className="absolute top-4 right-4">
                  <span className="text-xs font-medium px-3 py-1 rounded-full bg-slate-900/80 text-slate-300 border border-white/10">
                    Binnenkort
                  </span>
                </div>
              </div>

              {/* Content */}
              <div className="p-4 sm:p-6 flex flex-col flex-1">
                <h2 className="text-lg sm:text-xl font-bold text-white mb-2">
                  {post.titel}
                </h2>
                <p className="text-slate-400 text-sm leading-relaxed mb-4 flex-1">
                  {post.excerpt}
                </p>

                {/* Meta */}
                <div className="flex items-center gap-4 text-xs text-slate-500 pt-4 border-t border-white/10">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />
                    {post.datum}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    {post.leestijd}
                  </span>
                </div>
              </div>
            </GlassCard>
          </AnimatedSection>
        ))}
      </div>

      {/* CTA */}
      <AnimatedSection delay={0.5}>
        <div className="mt-12 sm:mt-16 text-center">
          <GlassCard className="inline-block px-8 py-6 sm:px-12 sm:py-8">
            <p className="text-lg sm:text-xl font-semibold text-white mb-2">Binnenkort meer artikels</p>
            <p className="text-slate-400 text-sm sm:text-base">
              Ik schrijf regelmatig over mijn projecten, nieuwe technologieën en praktische tutorials.
            </p>
          </GlassCard>
        </div>
      </AnimatedSection>
    </div>
  )
}
