'use client'

import { useRef, useState } from 'react'
import { motion, useInView } from 'framer-motion'
import Link from 'next/link'
import { ExternalLink, Search, Tag } from 'lucide-react'
import { GithubIcon } from '@/components/icons/BrandIcons'
import GlassCard from '@/components/ui/GlassCard'
import { cn } from '@/lib/utils'
import { projecten, categories, type Category, type Project } from '@/data/projects'

function AnimatedSection({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: '-30px' })
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
      transition={{ duration: 0.5, delay }}
      style={{ willChange: 'opacity, transform' }}
    >
      {children}
    </motion.div>
  )
}

function ProjectCard({ project, index }: { project: Project; index: number }) {
  return (
    <AnimatedSection delay={index * 0.08}>
      <Link href={`/projecten/${project.slug}`}>
        <div className="group h-full backdrop-blur-md bg-white/5 border border-white/10 rounded-2xl overflow-hidden hover:border-green-500/30 hover:bg-white/[0.08] transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-green-500/5 flex flex-col">
          {/* Gradient header */}
          <div className={`relative h-32 sm:h-36 bg-gradient-to-br ${project.gradient} flex items-center justify-center overflow-hidden`}>
            <project.icon className="w-10 h-10 text-white/20 group-hover:text-white/30 group-hover:scale-110 transition-all duration-500" />
            <div className="absolute inset-0 bg-gradient-to-t from-slate-950/50 to-transparent" />
            <div className="absolute top-3 right-3">
              <span className={cn(
                'text-xs font-medium px-2.5 py-1 rounded-full border',
                project.status === 'Actief'
                  ? 'bg-green-500/20 text-green-300 border-green-500/30'
                  : 'bg-slate-500/20 text-slate-300 border-slate-500/30'
              )}>
                {project.status}
              </span>
            </div>
          </div>

          {/* Content */}
          <div className="p-5 sm:p-6 flex-1 flex flex-col">
            <span className="text-xs font-medium text-green-400 uppercase tracking-wider mb-1">{project.categorie}</span>
            <h3 className="text-white font-bold text-lg mb-2 group-hover:text-green-400 transition-colors">{project.naam}</h3>
            <p className="text-slate-400 text-sm leading-relaxed mb-4 flex-1">{project.korte}</p>

            <div className="flex flex-wrap gap-1.5 mb-4">
              {project.tags.slice(0, 4).map((tag) => (
                <span key={tag} className="text-xs px-2 py-0.5 rounded-md bg-white/5 text-slate-400 border border-white/10">
                  {tag}
                </span>
              ))}
              {project.tags.length > 4 && (
                <span className="text-xs px-2 py-0.5 rounded-md bg-white/5 text-slate-500 border border-white/10">
                  +{project.tags.length - 4}
                </span>
              )}
            </div>

            <div className="flex items-center gap-3 pt-2 border-t border-white/5">
              <span className="text-sm text-green-400 font-medium group-hover:underline flex items-center gap-1.5">
                Details bekijken <ExternalLink className="w-3.5 h-3.5" />
              </span>
              {project.github && (
                <span className="text-slate-500 hover:text-white transition-colors ml-auto">
                  <GithubIcon className="w-4 h-4" />
                </span>
              )}
            </div>
          </div>
        </div>
      </Link>
    </AnimatedSection>
  )
}

export default function ProjectenPage() {
  const [filter, setFilter] = useState<Category>('Alles')
  const [zoek, setZoek] = useState('')

  const filtered = projecten.filter((p) => {
    const matchCat = filter === 'Alles' || p.categorie === filter
    const matchZoek = zoek === '' ||
      p.naam.toLowerCase().includes(zoek.toLowerCase()) ||
      p.tags.some(t => t.toLowerCase().includes(zoek.toLowerCase()))
    return matchCat && matchZoek
  })

  return (
    <div className="min-h-screen px-4 sm:px-6 py-8 sm:py-12">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <AnimatedSection>
          <div className="mb-8 sm:mb-10">
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-white mb-2">
              Mijn <span className="text-green-400">Projecten</span>
            </h1>
            <p className="text-slate-400 text-sm sm:text-base max-w-xl">
              Een overzicht van projecten waar ik aan heb gewerkt — van full-stack platforms tot IoT-pipelines en AI-agents.
            </p>
          </div>
        </AnimatedSection>

        {/* Filters */}
        <AnimatedSection delay={0.1}>
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 mb-8">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                value={zoek}
                onChange={(e) => setZoek(e.target.value)}
                placeholder="Zoek op naam of technologie..."
                aria-label="Zoek projecten"
                className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:border-green-500/50 text-sm"
              />
            </div>
            <div className="flex gap-2 flex-wrap">
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setFilter(cat)}
                  className={cn(
                    'px-4 py-2 rounded-xl text-sm font-medium transition-all border',
                    filter === cat
                      ? 'bg-green-500/20 text-green-400 border-green-500/30'
                      : 'bg-white/5 text-slate-400 border-white/10 hover:bg-white/10 hover:text-white'
                  )}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>
        </AnimatedSection>

        {/* Project Grid */}
        {filtered.length === 0 ? (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-24">
            <Tag className="w-12 h-12 text-slate-700 mx-auto mb-4" />
            <p className="text-slate-500">Geen projecten gevonden voor deze zoekopdracht.</p>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6">
            {filtered.map((project, i) => (
              <ProjectCard key={project.slug} project={project} index={i} />
            ))}
          </div>
        )}

        {/* Tech overview */}
        <AnimatedSection delay={0.2}>
          <GlassCard className="mt-12 sm:mt-16 p-6 sm:p-8 text-center">
            <h3 className="text-white font-bold text-lg sm:text-xl mb-2">Geïnteresseerd in een samenwerking?</h3>
            <p className="text-slate-400 text-sm mb-5 max-w-md mx-auto">
              Ik sta open voor freelance opdrachten en samenwerkingen. Laat me weten wat uw project nodig heeft.
            </p>
            <a
              href="mailto:koen@vorsters.dev"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold bg-gradient-to-r from-green-500 to-emerald-600 text-white hover:shadow-lg hover:shadow-green-500/25 transition-all duration-200"
            >
              Neem contact op
            </a>
          </GlassCard>
        </AnimatedSection>
      </div>
    </div>
  )
}
