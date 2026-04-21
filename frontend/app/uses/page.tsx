'use client'

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import { Monitor, Laptop, Keyboard, Headphones, Code2, Brain, Cpu, Database, Terminal, BookOpen, Music, Zap } from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'

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

const hardware = [
  {
    icon: Laptop,
    naam: 'Dell XPS 15',
    categorie: 'Laptop',
    beschrijving: 'Krachtige i7 voor lokale AI modellen en zware builds',
    kleur: 'from-slate-500 to-slate-700',
  },
  {
    icon: Monitor,
    naam: '27" 4K IPS',
    categorie: 'Monitor',
    beschrijving: 'Breed werkoppervlak voor multi-window development',
    kleur: 'from-blue-500 to-blue-700',
  },
  {
    icon: Keyboard,
    naam: 'Mechanical TKL',
    categorie: 'Keyboard',
    beschrijving: 'Tactile switches voor comfortabel typen de hele dag door',
    kleur: 'from-emerald-500 to-emerald-700',
  },
  {
    icon: Headphones,
    naam: 'Sony WH-1000XM5',
    categorie: 'Headphones',
    beschrijving: 'Noise cancelling voor diepe focussessies zonder afleiding',
    kleur: 'from-amber-500 to-amber-700',
  },
]

const devTools = [
  {
    naam: 'VS Code / Cursor',
    beschrijving: 'Mijn primaire editors. Cursor voor AI-assisted coding dagelijks.',
    kleur: 'from-blue-500 to-blue-700',
    icon: Code2,
  },
  {
    naam: 'JetBrains IntelliJ',
    beschrijving: 'Voor zware Java/Spring projecten waar ik de kracht nodig heb.',
    kleur: 'from-orange-500 to-red-700',
    icon: Code2,
  },
  {
    naam: 'Docker Desktop',
    beschrijving: 'Alles in containers, altijd. Geen "works on my machine" meer.',
    kleur: 'from-blue-600 to-cyan-700',
    icon: Cpu,
  },
  {
    naam: 'TablePlus',
    beschrijving: 'Database GUI voor PostgreSQL en andere databases.',
    kleur: 'from-emerald-500 to-teal-700',
    icon: Database,
  },
  {
    naam: 'Insomnia',
    beschrijving: 'API testing & debugging. Overzichtelijker dan Postman vind ik.',
    kleur: 'from-violet-500 to-purple-700',
    icon: Terminal,
  },
  {
    naam: 'Git + GitHub',
    beschrijving: 'Versiebeheer, altijd en overal. Commit early, commit often.',
    kleur: 'from-slate-500 to-slate-700',
    icon: Code2,
  },
]

const aiTools = [
  {
    naam: 'Ollama',
    beschrijving: 'Lokale LLMs draaien zonder cloud kosten. Privacy by default.',
    kleur: 'from-green-500 to-emerald-700',
    icon: Brain,
  },
  {
    naam: 'GitHub Copilot / Cursor',
    beschrijving: 'AI pair programming dagelijks. Productiviteitsboost is reëel.',
    kleur: 'from-violet-500 to-purple-700',
    icon: Code2,
  },
  {
    naam: 'LangChain',
    beschrijving: 'Agent frameworks en RAG pipelines voor complexe AI flows.',
    kleur: 'from-yellow-500 to-orange-600',
    icon: Brain,
  },
  {
    naam: 'Claude (Anthropic)',
    beschrijving: 'Voor complexe analyse en architectuurbeslissingen.',
    kleur: 'from-amber-500 to-orange-700',
    icon: Brain,
  },
]

const productivity = [
  {
    naam: 'Notion',
    beschrijving: 'Projectplanning, notities en teamdocumentatie.',
    kleur: 'from-slate-500 to-slate-700',
    icon: BookOpen,
  },
  {
    naam: 'Obsidian',
    beschrijving: 'Persoonlijke kennisbank (second brain). Alles is Markdown.',
    kleur: 'from-violet-500 to-purple-700',
    icon: BookOpen,
  },
  {
    naam: 'PowerToys',
    beschrijving: 'Snelle launcher en tools voor Windows productiviteit.',
    kleur: 'from-blue-500 to-indigo-700',
    icon: Zap,
  },
  {
    naam: 'Spotify',
    beschrijving: 'Lofi en instrumentals tijdens het coderen. Essentieel.',
    kleur: 'from-green-500 to-emerald-700',
    icon: Music,
  },
]

function ToolGrid({ items }: { items: { naam: string; beschrijving: string; kleur: string; icon: React.ComponentType<{ className?: string }> }[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
      {items.map((item, i) => (
        <AnimatedSection key={item.naam} delay={i * 0.07}>
          <GlassCard hover className="p-4 sm:p-5 h-full flex gap-3 sm:gap-4">
            <div className={`p-2.5 rounded-xl bg-gradient-to-br ${item.kleur} shrink-0 self-start`}>
              <item.icon className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
            </div>
            <div className="min-w-0">
              <h3 className="text-white font-semibold text-sm mb-1 leading-tight">{item.naam}</h3>
              <p className="text-slate-400 text-xs leading-relaxed">{item.beschrijving}</p>
            </div>
          </GlassCard>
        </AnimatedSection>
      ))}
    </div>
  )
}

export default function UsesPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      {/* Hero */}
      <section className="mb-14 sm:mb-16 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
        >
          <span className="inline-flex items-center px-3 sm:px-4 py-1.5 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-xs sm:text-sm font-medium mb-4 sm:mb-6">
            Setup & Toolbox
          </span>
          <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-extrabold text-white mb-4 sm:mb-6 leading-tight">
            Mijn Setup &{' '}
            <span className="bg-gradient-to-r from-green-400 via-emerald-400 to-emerald-500 bg-clip-text text-transparent">
              Tools
            </span>
          </h1>
          <p className="text-slate-400 text-base sm:text-lg md:text-xl max-w-2xl mx-auto leading-relaxed">
            Alles wat ik gebruik om te bouwen, te leren en productief te blijven —
            eerlijk en zonder reclame.
          </p>
        </motion.div>
      </section>

      {/* Hardware */}
      <section className="mb-14 sm:mb-16">
        <AnimatedSection>
          <div className="mb-6 sm:mb-8">
            <h2 className="text-xl sm:text-2xl md:text-3xl font-bold text-white mb-2">Hardware</h2>
            <p className="text-slate-400 text-sm sm:text-base">De fysieke setup waar ik dagelijks op werk</p>
          </div>
        </AnimatedSection>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          {hardware.map((item, i) => (
            <AnimatedSection key={item.naam} delay={i * 0.08}>
              <GlassCard hover className="p-5 sm:p-6 h-full flex flex-col">
                <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${item.kleur} mb-4 self-start`}>
                  <item.icon className="w-5 h-5 text-white" />
                </div>
                <span className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1">{item.categorie}</span>
                <h3 className="text-white font-bold text-base mb-2">{item.naam}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{item.beschrijving}</p>
              </GlassCard>
            </AnimatedSection>
          ))}
        </div>
      </section>

      {/* Development Tools */}
      <section className="mb-14 sm:mb-16">
        <AnimatedSection>
          <div className="mb-6 sm:mb-8">
            <h2 className="text-xl sm:text-2xl md:text-3xl font-bold text-white mb-2">Development Tools</h2>
            <p className="text-slate-400 text-sm sm:text-base">Editors, databases en dev workflow</p>
          </div>
        </AnimatedSection>
        <ToolGrid items={devTools} />
      </section>

      {/* AI Tools */}
      <section className="mb-14 sm:mb-16">
        <AnimatedSection>
          <div className="mb-6 sm:mb-8">
            <h2 className="text-xl sm:text-2xl md:text-3xl font-bold text-white mb-2">
              AI Tools{' '}
              <span className="text-sm font-normal text-green-400 ml-2">mijn favorieten</span>
            </h2>
            <p className="text-slate-400 text-sm sm:text-base">De AI-tools die ik dagelijks inzet in mijn workflow</p>
          </div>
        </AnimatedSection>
        <ToolGrid items={aiTools} />
      </section>

      {/* Productivity */}
      <section className="mb-14 sm:mb-16">
        <AnimatedSection>
          <div className="mb-6 sm:mb-8">
            <h2 className="text-xl sm:text-2xl md:text-3xl font-bold text-white mb-2">Productiviteit</h2>
            <p className="text-slate-400 text-sm sm:text-base">Apps om gefocust en georganiseerd te blijven</p>
          </div>
        </AnimatedSection>
        <ToolGrid items={productivity} />
      </section>

      {/* Quote */}
      <AnimatedSection>
        <GlassCard className="p-8 sm:p-12 text-center max-w-2xl mx-auto">
          <div className="text-4xl mb-4">💡</div>
          <blockquote className="text-lg sm:text-xl md:text-2xl font-bold text-white mb-3 leading-relaxed">
            &ldquo;De beste tool is de tool die je niet in de weg staat.&rdquo;
          </blockquote>
          <p className="text-slate-500 text-sm">— Koen Vorsters</p>
        </GlassCard>
      </AnimatedSection>
    </div>
  )
}
