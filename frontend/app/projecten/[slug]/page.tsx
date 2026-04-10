'use client'

import { useParams } from 'next/navigation'
import { motion } from 'framer-motion'
import { ChevronLeft, Check, ExternalLink } from 'lucide-react'
import Link from 'next/link'
import { GithubIcon } from '@/components/icons/BrandIcons'
import GlassCard from '@/components/ui/GlassCard'
import { getProjectBySlug } from '@/data/projects'

export default function ProjectDetailPage() {
  const params = useParams()
  const slug = typeof params.slug === 'string' ? params.slug : ''
  const project = getProjectBySlug(slug)

  if (!project) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <GlassCard className="p-10 text-center max-w-md">
          <p className="text-4xl mb-4">🔍</p>
          <h2 className="text-white font-bold text-xl mb-2">Project niet gevonden</h2>
          <p className="text-slate-400 mb-6">Dit project bestaat niet of is verplaatst.</p>
          <Link href="/projecten" className="text-green-400 hover:text-green-300 transition-colors text-sm">
            ← Terug naar projecten
          </Link>
        </GlassCard>
      </div>
    )
  }

  const Icon = project.icon

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.4 }}>
        <Link href="/projecten" className="inline-flex items-center gap-2 text-slate-400 hover:text-white text-sm mb-8 transition-colors">
          <ChevronLeft className="w-4 h-4" />
          Terug naar projecten
        </Link>
      </motion.div>

      {/* Hero banner */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className={`relative h-48 sm:h-56 rounded-2xl bg-gradient-to-br ${project.gradient} flex items-center justify-center overflow-hidden mb-8`}
      >
        <Icon className="w-16 h-16 text-white/15" />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/60 to-transparent" />
        <div className="absolute bottom-4 left-5 sm:bottom-6 sm:left-8">
          <span className="text-xs font-medium text-white/70 uppercase tracking-wider">{project.categorie}</span>
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white">{project.naam}</h1>
        </div>
        <div className="absolute top-4 right-4">
          <span className={`text-xs font-medium px-3 py-1 rounded-full border ${
            project.status === 'Actief'
              ? 'bg-green-500/20 text-green-300 border-green-500/30'
              : 'bg-slate-500/20 text-slate-300 border-slate-500/30'
          }`}>
            {project.status}
          </span>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
        {/* Main content */}
        <motion.div
          className="lg:col-span-2 space-y-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <GlassCard className="p-5 sm:p-7">
            <h2 className="text-white font-semibold text-lg mb-3">Over dit project</h2>
            <p className="text-slate-400 leading-relaxed">{project.beschrijving}</p>
          </GlassCard>

          <GlassCard className="p-5 sm:p-7">
            <h2 className="text-white font-semibold text-lg mb-4">Belangrijkste features</h2>
            <ul className="space-y-3">
              {project.features.map((feature) => (
                <li key={feature} className="flex items-start gap-3 text-slate-300 text-sm">
                  <Check className="w-4 h-4 text-green-400 shrink-0 mt-0.5" />
                  {feature}
                </li>
              ))}
            </ul>
          </GlassCard>
        </motion.div>

        {/* Sidebar */}
        <motion.div
          className="space-y-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <GlassCard className="p-5 sm:p-7">
            <h3 className="text-white font-semibold text-sm uppercase tracking-wider mb-4">Tech Stack</h3>
            <div className="flex flex-wrap gap-2">
              {project.tags.map((tag) => (
                <span key={tag} className="text-xs px-3 py-1.5 rounded-lg bg-white/5 text-slate-300 border border-white/10 font-medium">
                  {tag}
                </span>
              ))}
            </div>
          </GlassCard>

          {(project.github || project.demo) && (
            <GlassCard className="p-5 sm:p-7">
              <h3 className="text-white font-semibold text-sm uppercase tracking-wider mb-4">Links</h3>
              <div className="space-y-3">
                {project.github && (
                  <a
                    href={project.github}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 text-slate-300 hover:text-white transition-colors text-sm group"
                  >
                    <GithubIcon className="w-5 h-5 text-slate-500 group-hover:text-white transition-colors" />
                    Broncode op GitHub
                    <ExternalLink className="w-3.5 h-3.5 ml-auto text-slate-600" />
                  </a>
                )}
                {project.demo && (
                  <a
                    href={project.demo}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 text-slate-300 hover:text-white transition-colors text-sm group"
                  >
                    <ExternalLink className="w-5 h-5 text-slate-500 group-hover:text-white transition-colors" />
                    Live demo bekijken
                  </a>
                )}
              </div>
            </GlassCard>
          )}

          <GlassCard className="p-5 sm:p-7 text-center">
            <p className="text-slate-400 text-sm mb-4">Interesse in dit project of een gelijkaardig idee?</p>
            <a
              href="mailto:koen@vorsters.dev"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-green-500 to-emerald-600 text-white hover:shadow-lg hover:shadow-green-500/25 transition-all duration-200 w-full justify-center"
            >
              Neem contact op
            </a>
          </GlassCard>
        </motion.div>
      </div>
    </div>
  )
}
