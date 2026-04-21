'use client'

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import {
  Code2, Brain, Wifi, CheckCircle2, Mail, ArrowRight, Search
} from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'
import GradientButton from '@/components/ui/GradientButton'
import Link from 'next/link'

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

const diensten = [
  {
    icon: Brain,
    titel: 'AI Consulting & Integratie',
    ondertitel: 'Help bedrijven AI implementeren die écht werkt',
    gradient: 'from-violet-600 to-purple-800',
    prijs: 'Op maat',
    features: [
      'AI strategie & roadmap',
      'Multi-agent systemen bouwen',
      'LLM integratie (Ollama, OpenAI)',
      'Policy & governance inrichten',
      'Training & workshops',
    ],
  },
  {
    icon: Code2,
    titel: 'Full-Stack Development',
    ondertitel: 'Van concept tot productie — snel, schaalbaar en onderhoudbaar',
    gradient: 'from-blue-600 to-cyan-800',
    prijs: '€75/u',
    features: [
      'React / Next.js frontends',
      'FastAPI / Python backends',
      'PostgreSQL & database design',
      'REST API & WebSocket',
      'Docker & cloud deployment',
    ],
  },
  {
    icon: Wifi,
    titel: 'IoT & Embedded Systems',
    ondertitel: 'Hardware en software naadloos laten samenwerken',
    gradient: 'from-emerald-600 to-green-800',
    prijs: 'Op maat',
    features: [
      'Sensornetwerken & data-acquisitie',
      'MQTT & real-time data',
      'Embedded programming',
      'Cloud dashboards & alerts',
      'Prototyping & MVPs',
    ],
  },
  {
    icon: Search,
    titel: 'Legacy Code Analyse',
    ondertitel: 'Maak uw ongedocumenteerde systemen begrijpelijk',
    gradient: 'from-amber-600 to-orange-800',
    prijs: 'Vanaf €500',
    features: [
      'Java, Python, C#, PHP, VBA',
      'Business logic extraheren',
      'Leesbare documentatie voor niet-technici',
      'AI-assisted analyse van grote codebases',
      'Modernisatieadvies & roadmap',
    ],
  },
]

const stappen = [
  { nummer: '01', titel: 'Kennismaking', beschrijving: 'Gratis intakegesprek om jouw uitdaging te begrijpen' },
  { nummer: '02', titel: 'Analyse & Voorstel', beschrijving: 'Gedetailleerde aanpak en transparante offerte' },
  { nummer: '03', titel: 'Bouw & Itereer', beschrijving: 'Agile werken met regelmatige check-ins en demos' },
  { nummer: '04', titel: 'Oplevering & Support', beschrijving: 'Zorgvuldige overdracht en nazorg na go-live' },
]

export default function DienstenPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      {/* Hero */}
      <section className="mb-16 sm:mb-20 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
        >
          <span className="inline-flex items-center px-3 sm:px-4 py-1.5 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-xs sm:text-sm font-medium mb-4 sm:mb-6">
            Beschikbaar voor projecten
          </span>
          <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-extrabold text-white mb-4 sm:mb-6 leading-tight">
            Mijn{' '}
            <span className="bg-gradient-to-r from-green-400 via-emerald-400 to-emerald-500 bg-clip-text text-transparent">
              diensten
            </span>
          </h1>
          <p className="text-slate-400 text-base sm:text-lg md:text-xl max-w-2xl mx-auto leading-relaxed">
            Ik help bedrijven groeien door slimme technologie in te zetten — van AI-strategie tot
            werkende software en verbonden hardware.
          </p>
        </motion.div>
      </section>

      {/* Service Cards */}
      <section className="mb-16 sm:mb-20">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 sm:gap-8">
          {diensten.map((dienst, i) => (
            <AnimatedSection key={dienst.titel} delay={i * 0.15}>
              <GlassCard hover className="overflow-hidden h-full flex flex-col">
                {/* Card header with gradient */}
                <div className={`bg-gradient-to-br ${dienst.gradient} p-6 sm:p-8 relative`}>
                  <div className="flex items-start justify-between mb-4">
                    <div className="p-3 rounded-xl bg-white/20 backdrop-blur-sm">
                      <dienst.icon className="w-6 h-6 text-white" />
                    </div>
                    <span className="text-white/90 font-bold text-lg sm:text-xl">{dienst.prijs}</span>
                  </div>
                  <h2 className="text-xl sm:text-2xl font-bold text-white mb-2">{dienst.titel}</h2>
                  <p className="text-white/70 text-sm leading-relaxed">{dienst.ondertitel}</p>
                  <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-slate-900/40 to-transparent" />
                </div>

                {/* Features list */}
                <div className="p-6 sm:p-8 flex-1 flex flex-col">
                  <ul className="space-y-3 flex-1">
                    {dienst.features.map((feature) => (
                      <li key={feature} className="flex items-center gap-3 text-slate-300 text-sm">
                        <CheckCircle2 className="w-4 h-4 text-green-400 shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <div className="mt-6 pt-6 border-t border-white/10">
                    <a href="mailto:koen@vorsters.dev" className="flex items-center justify-center gap-2 text-green-400 hover:text-green-300 text-sm font-medium transition-colors">
                      Interesse? Mail me <ArrowRight className="w-4 h-4" />
                    </a>
                  </div>
                </div>
              </GlassCard>
            </AnimatedSection>
          ))}
        </div>
      </section>

      {/* Hoe ik werk */}
      <section className="mb-16 sm:mb-20">
        <AnimatedSection>
          <div className="text-center mb-10 sm:mb-12">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-3">Hoe ik werk</h2>
            <p className="text-slate-400 max-w-lg mx-auto text-sm sm:text-base">
              Een duidelijk proces zodat je altijd weet waar je aan toe bent
            </p>
          </div>
        </AnimatedSection>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          {stappen.map((stap, i) => (
            <AnimatedSection key={stap.nummer} delay={i * 0.1}>
              <GlassCard className="p-6 sm:p-7 h-full flex flex-col relative overflow-hidden">
                <span className="text-6xl sm:text-7xl font-extrabold text-white/5 absolute -top-2 -right-2 select-none leading-none">
                  {stap.nummer}
                </span>
                <span className="text-green-400 font-bold text-sm mb-3 relative">{stap.nummer}</span>
                <h3 className="text-white font-bold text-base sm:text-lg mb-2 relative">{stap.titel}</h3>
                <p className="text-slate-400 text-sm leading-relaxed relative">{stap.beschrijving}</p>
              </GlassCard>
            </AnimatedSection>
          ))}
        </div>
      </section>

      {/* CTA */}
      <AnimatedSection>
        <GlassCard className="p-8 sm:p-12 text-center max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3 sm:mb-4">
            Klaar om samen te bouwen?
          </h2>
          <p className="text-slate-400 mb-6 sm:mb-8 text-sm sm:text-base">
            Vertel me over jouw project — ik plan graag een gratis kennismakingsgesprek in.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center">
            <a href="mailto:koen@vorsters.dev" className="w-full sm:w-auto">
              <GradientButton variant="primary" className="w-full sm:w-auto px-8 py-4 text-base flex items-center justify-center gap-2">
                <Mail className="w-4 h-4" /> Stuur een e-mail
              </GradientButton>
            </a>
            <Link href="/contact" className="w-full sm:w-auto">
              <GradientButton variant="outline" className="w-full sm:w-auto px-8 py-4 text-base">
                Contactpagina
              </GradientButton>
            </Link>
          </div>
        </GlassCard>
      </AnimatedSection>
    </div>
  )
}
