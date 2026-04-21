'use client'

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import { Brain, ChevronDown, ExternalLink } from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'
import GradientButton from '@/components/ui/GradientButton'
import Link from 'next/link'
import Image from 'next/image'

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

const architectuurLagen = [
  {
    naam: 'CONTROL PLANE',
    beschrijving: 'Routeert, beslist en valideert — het brein van het systeem. Policy-as-Code governance zorgt dat elk verzoek voldoet aan de regels.',
    borderKleur: 'border-violet-500',
    badgeKleur: 'bg-violet-500/10 border-violet-500/30 text-violet-400',
    textKleur: 'text-violet-400',
  },
  {
    naam: 'CAPABILITY PLANE',
    beschrijving: 'Definieert wat het systeem kan — skill registratie, capability discovery en dynamische routing naar de juiste agent.',
    borderKleur: 'border-blue-500',
    badgeKleur: 'bg-blue-500/10 border-blue-500/30 text-blue-400',
    textKleur: 'text-blue-400',
  },
  {
    naam: 'EXECUTION PLANE',
    beschrijving: 'Agents, tools en modellen die het echte werk doen — lokale LLMs via Ollama, skill chains en event-driven orkestratie.',
    borderKleur: 'border-emerald-500',
    badgeKleur: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
    textKleur: 'text-emerald-400',
  },
  {
    naam: 'TRUST PLANE',
    beschrijving: 'Evals, audit trail en observability — elke beslissing wordt gelogd, geëvalueerd en traceerbaar gehouden.',
    borderKleur: 'border-amber-500',
    badgeKleur: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
    textKleur: 'text-amber-400',
  },
]

const stats = [
  { waarde: '1.389', label: 'Geautomatiseerde tests', kleur: 'text-green-400' },
  { waarde: '9', label: 'API endpoints', kleur: 'text-violet-400' },
  { waarde: '6', label: 'AI skill groepen', kleur: 'text-blue-400' },
  { waarde: '41', label: 'Geïmplementeerde features', kleur: 'text-amber-400' },
]

const skillGroepen = [
  {
    emoji: '🔍',
    naam: 'Dev Intelligence',
    skills: ['analyze_code_changes', 'map_changes_to_business_logic', 'detect_regression_scope'],
    kleur: 'border-blue-500/30 bg-blue-500/5',
  },
  {
    emoji: '🧪',
    naam: 'Test Intelligence',
    skills: ['validate_acceptance_criteria', 'generate_advanced_test_cases', 'detect_regression_risk'],
    kleur: 'border-violet-500/30 bg-violet-500/5',
  },
  {
    emoji: '📊',
    naam: 'Payroll Validation',
    skills: ['compare_with_previous_run', 'detect_salary_anomalies', 'validate_legal_rules'],
    kleur: 'border-emerald-500/30 bg-emerald-500/5',
  },
  {
    emoji: '⚠️',
    naam: 'Risk & Decision',
    skills: ['classify_payroll_risk', 'assess_release_risk', 'suggest_prc_actions'],
    kleur: 'border-amber-500/30 bg-amber-500/5',
  },
  {
    emoji: '💬',
    naam: 'Explanation',
    skills: ['explain_salary_difference', 'explain_code_to_non_dev'],
    kleur: 'border-rose-500/30 bg-rose-500/5',
  },
  {
    emoji: '📋',
    naam: 'Audit',
    skills: ['audit_trace_generator', 'decision_logging'],
    kleur: 'border-slate-500/30 bg-slate-500/5',
  },
]

const techStack = [
  'Python', 'FastAPI', 'Ollama', 'YAML', 'PostgreSQL', 'Docker', 'Next.js', 'Pydantic', 'pytest',
]

export default function AiLabPage() {
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
            <span className="w-2 h-2 rounded-full bg-green-400 mr-2 animate-pulse" />
            Live Platform
          </span>
          <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-extrabold text-white mb-4 sm:mb-6 leading-tight">
            AI{' '}
            <span className="bg-gradient-to-r from-green-400 via-emerald-400 to-emerald-500 bg-clip-text text-transparent">
              Lab
            </span>
          </h1>
          <p className="text-slate-400 text-base sm:text-lg md:text-xl max-w-2xl mx-auto leading-relaxed">
            Een kijkje achter de schermen van het AI Control Platform dat ik bouw voor VorstersNV —
            enterprise-grade, open-source, lokaal draaiend.
          </p>
        </motion.div>
      </section>

      {/* AI-Driven Software Development Infographic */}
      <section className="mb-16 sm:mb-20">
        <AnimatedSection>
          <div className="text-center mb-8 sm:mb-10">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-3">
              AI-gedreven Softwareontwikkeling
            </h2>
            <p className="text-slate-400 max-w-xl mx-auto text-sm sm:text-base">
              Van user story tot zelfverbeterende pipeline — zo ziet de toekomst van software delivery eruit
            </p>
          </div>
          <div className="max-w-6xl mx-auto">
            <GlassCard className="overflow-hidden p-2">
              <Image
                src="/ai-gedreven-softwareontwikkeling.png"
                alt="AI-gedreven softwareontwikkeling: end-to-end workflow, AI agents, Copilot CLI, feedback loops, model selection en Grafana test intelligence"
                width={1600}
                height={1200}
                className="rounded-lg w-full h-auto"
                data-testid="ai-gedreven-softwareontwikkeling-image"
              />
            </GlassCard>
          </div>
        </AnimatedSection>
      </section>

      {/* Platform Architecture */}
      <section className="mb-16 sm:mb-20">
        <AnimatedSection>
          <div className="text-center mb-10 sm:mb-12">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-3">Platform Architectuur</h2>
            <p className="text-slate-400 max-w-lg mx-auto text-sm sm:text-base">
              Een gelaagd systeem waarbij elke laag zijn eigen verantwoordelijkheid heeft
            </p>
          </div>
        </AnimatedSection>

        <div className="max-w-2xl mx-auto space-y-3 sm:space-y-4">
          {architectuurLagen.map((laag, i) => (
            <AnimatedSection key={laag.naam} delay={i * 0.12}>
              <GlassCard className={`p-5 sm:p-6 border-l-4 ${laag.borderKleur}`}>
                <div className="flex items-start gap-4">
                  <div className="flex-1">
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-mono font-bold border ${laag.badgeKleur} mb-2`}>
                      {laag.naam}
                    </span>
                    <p className="text-slate-400 text-sm leading-relaxed">{laag.beschrijving}</p>
                  </div>
                </div>
              </GlassCard>

              {i < architectuurLagen.length - 1 && (
                <div className="flex justify-center py-1">
                  <ChevronDown className="w-5 h-5 text-slate-600" />
                </div>
              )}
            </AnimatedSection>
          ))}
        </div>
      </section>

      {/* By the Numbers */}
      <section className="mb-16 sm:mb-20">
        <AnimatedSection>
          <div className="text-center mb-8 sm:mb-10">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-3">In Cijfers</h2>
            <p className="text-slate-400 max-w-lg mx-auto text-sm sm:text-base">Wat het platform vandaag kan</p>
          </div>
        </AnimatedSection>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-5 max-w-4xl mx-auto">
          {stats.map((stat, i) => (
            <AnimatedSection key={stat.label} delay={i * 0.08}>
              <GlassCard className="p-5 sm:p-6 text-center h-full flex flex-col items-center justify-center gap-2">
                <span className={`text-3xl sm:text-4xl font-extrabold ${stat.kleur}`}>{stat.waarde}</span>
                <span className="text-slate-400 text-xs sm:text-sm text-center leading-tight">{stat.label}</span>
              </GlassCard>
            </AnimatedSection>
          ))}
        </div>
      </section>

      {/* Skill Groups */}
      <section className="mb-16 sm:mb-20">
        <AnimatedSection>
          <div className="text-center mb-8 sm:mb-10">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-3">Skill Groepen</h2>
            <p className="text-slate-400 max-w-lg mx-auto text-sm sm:text-base">
              Gespecialiseerde AI-skills gegroepeerd per domein
            </p>
          </div>
        </AnimatedSection>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5">
          {skillGroepen.map((groep, i) => (
            <AnimatedSection key={groep.naam} delay={i * 0.1}>
              <GlassCard className={`p-5 sm:p-6 h-full border ${groep.kleur}`}>
                <div className="flex items-center gap-3 mb-3 sm:mb-4">
                  <span className="text-2xl">{groep.emoji}</span>
                  <h3 className="text-white font-bold text-base">{groep.naam}</h3>
                </div>
                <ul className="space-y-1.5">
                  {groep.skills.map((skill) => (
                    <li key={skill} className="flex items-center gap-2 text-xs sm:text-sm">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-500 shrink-0" />
                      <code className="text-slate-400 font-mono">{skill}</code>
                    </li>
                  ))}
                </ul>
              </GlassCard>
            </AnimatedSection>
          ))}
        </div>
      </section>

      {/* Tech Stack */}
      <section className="mb-16 sm:mb-20">
        <AnimatedSection>
          <div className="text-center mb-6 sm:mb-8">
            <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">Tech Stack</h2>
            <p className="text-slate-400 text-sm sm:text-base">Gebouwd op een moderne open-source stack</p>
          </div>
          <div className="flex flex-wrap justify-center gap-2 sm:gap-3 max-w-3xl mx-auto">
            {techStack.map((tech) => (
              <span
                key={tech}
                className="px-3 sm:px-4 py-1.5 sm:py-2 rounded-full bg-white/5 border border-white/10 text-slate-300 text-xs sm:text-sm font-medium hover:bg-white/10 hover:text-white transition-colors"
              >
                {tech}
              </span>
            ))}
          </div>
        </AnimatedSection>
      </section>

      {/* CTA */}
      <AnimatedSection>
        <GlassCard className="p-8 sm:p-12 text-center max-w-3xl mx-auto">
          <div className="inline-flex p-3 rounded-xl bg-green-500/10 border border-green-500/20 mb-4 sm:mb-6">
            <Brain className="w-6 h-6 text-green-400" />
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3 sm:mb-4">
            Meer weten over het platform?
          </h2>
          <p className="text-slate-400 mb-6 sm:mb-8 text-sm sm:text-base">
            Lees het volledige bouwverhaal in mijn blogpost of neem contact op om te bespreken
            hoe dit voor jouw organisatie kan werken.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center">
            <Link href="/blog/ai-control-platform-bouwen" className="w-full sm:w-auto">
              <GradientButton variant="primary" className="w-full sm:w-auto px-8 py-4 text-base flex items-center justify-center gap-2">
                Lees het artikel <ExternalLink className="w-4 h-4" />
              </GradientButton>
            </Link>
            <Link href="/contact" className="w-full sm:w-auto">
              <GradientButton variant="outline" className="w-full sm:w-auto px-8 py-4 text-base">
                Neem contact op
              </GradientButton>
            </Link>
          </div>
        </GlassCard>
      </AnimatedSection>
    </div>
  )
}
