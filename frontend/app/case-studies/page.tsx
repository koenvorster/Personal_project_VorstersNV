import type { Metadata } from 'next'
import Link from 'next/link'
import { CheckCircle2, ExternalLink } from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'
import GradientButton from '@/components/ui/GradientButton'
import AnimatedSection from '@/components/ui/AnimatedSection'

export const metadata: Metadata = {
  title: 'Case Studies — Bewezen resultaten voor Belgische KMOs | VorstersNV',
  description:
    'Ontdek hoe VorstersNV Belgische KMOs helpt met Legacy Code Analyse, AI Agents en Bedrijfsproces Automatisering. Concrete projecten, meetbare resultaten.',
  openGraph: {
    title: 'Case Studies | VorstersNV',
    description:
      'Concrete projecten en bewezen resultaten. Bekijk hoe VorstersNV Belgische KMOs transformeert met AI en moderne technologie.',
    type: 'website',
  },
}

const caseStudies = [
  {
    id: 1,
    dienst: 'Legacy Code Analyse',
    dienstKleur: 'from-blue-500/20 to-blue-600/20 border-blue-500/30',
    dienstBadge: 'bg-blue-500/20 text-blue-400',
    headerGradient: 'from-blue-600 to-indigo-800',
    titel: 'Loonberekeningssysteem Analyse',
    subtitel: 'Van onleesbare legacy code naar volledige documentatie in 3 dagen',
    context: 'Belgische KMO — Payroll & HR sector',
    probleem:
      'Een Java loonberekeningssysteem van 12 jaar oud waarvan de oorspronkelijke developer het bedrijf had verlaten. Niemand begreep nog hoe het systeem werkte. Elke kleine aanpassing kostte weken en bracht risico met zich mee.',
    aanpak: [
      'Dag 1: Codebase inladen, projectstructuur in kaart gebracht (Spring Boot, Chain of Responsibility pattern geïdentificeerd)',
      'Dag 2: 25+ berekeningsklassen ontcijferd, business rules gedocumenteerd per component',
      'Dag 3: Volledig architectuurrapport opgesteld + directiepresentatie',
    ],
    resultaten: [
      '25+ looncomponenten volledig gedocumenteerd in begrijpelijke taal',
      'Architectuurdiagram beschikbaar voor nieuwe developers',
      '3 kritieke technische risico\'s geïdentificeerd en geprioriteerd',
      'Doorlooptijd 3 werkdagen (vs. geschatte 3–4 weken zonder AI)',
    ],
    tags: [
      { label: 'Java', kleur: 'bg-blue-500/20 text-blue-400' },
      { label: 'Spring Boot', kleur: 'bg-green-500/20 text-green-400' },
      { label: 'AI-analyse', kleur: 'bg-violet-500/20 text-violet-400' },
      { label: 'Lokale AI', kleur: 'bg-emerald-500/20 text-emerald-400' },
    ],
    prijsRange: '€500 – €7.000',
    github: null,
  },
  {
    id: 2,
    dienst: 'AI Agents Bouwen',
    dienstKleur: 'from-violet-500/20 to-purple-600/20 border-violet-500/30',
    dienstBadge: 'bg-violet-500/20 text-violet-400',
    headerGradient: 'from-violet-600 to-purple-800',
    titel: 'Beleggingscoach AI Platform',
    subtitel: 'Een persoonlijke AI-beleggingscoach voor Belgische beginners',
    context: 'Eigen showcase project — FinTech / EdTech',
    probleem:
      'De beleggingswereld is ontoegankelijk voor Belgische beginners. Ze hebben nood aan persoonlijk advies dat betaalbaar is. Er bestond geen tool die ETF-keuze, planvorming en gedragscoaching combineert in het Nederlands.',
    aanpak: [
      'Monorepo opgezet met pnpm workspaces: Next.js frontend + FastAPI backend + MCP server',
      'MCP (Model Context Protocol) server gebouwd voor investor-profile domain management',
      'AI-agentarchitectuur met PostgreSQL, Redis en Alembic migraties voor volledige stateful coaching',
    ],
    resultaten: [
      'Volledig werkend AI-platform dat beleggersprofielen aanmaakt en beheert',
      'Gepersonaliseerde ETF-portefeuilles op basis van risicoprofiel',
      'Gedragscoaching en leertraject per gebruiker bijgehouden',
      'Showcase van moderne monorepo-architectuur + MCP + AI-integratie',
    ],
    tags: [
      { label: 'Next.js 15', kleur: 'bg-blue-500/20 text-blue-400' },
      { label: 'FastAPI', kleur: 'bg-emerald-500/20 text-emerald-400' },
      { label: 'MCP Server', kleur: 'bg-violet-500/20 text-violet-400' },
      { label: 'AI Agents', kleur: 'bg-purple-500/20 text-purple-400' },
      { label: 'PostgreSQL', kleur: 'bg-indigo-500/20 text-indigo-400' },
    ],
    prijsRange: '€800 – €10.000',
    github: 'https://github.com/koenvorsters/beleggen-coach',
  },
  {
    id: 3,
    dienst: 'Full-Stack Development',
    dienstKleur: 'from-emerald-500/20 to-green-600/20 border-emerald-500/30',
    dienstBadge: 'bg-emerald-500/20 text-emerald-400',
    headerGradient: 'from-emerald-600 to-teal-800',
    titel: 'Stakeholder Demo Shell',
    subtitel: 'Interactieve look-alike voor stakeholder buy-in vóór de echte implementatie',
    context: 'Overheidsproject — Enterprise IT',
    probleem:
      'Een groot IT-project had stakeholder buy-in nodig vóór de echte implementatie. Klassieke Figma mockups waren te statisch om de key flows te beoordelen. Stakeholders moesten het systeem echt kunnen uitproberen in een browser.',
    aanpak: [
      'In record time interactieve look-alike shell gebouwd van het doelsysteem',
      'Angular 17 + Material Design frontend met Spring Boot backend en mock data APIs',
      'Docker Compose voor één-commando opstart + Cypress-ready voor demo-flow tests',
    ],
    resultaten: [
      'Volledige navigatie en key pages in werkende staat binnen deadline',
      'Stakeholders konden het systeem uitproberen in een echte browser',
      'Buy-in verkregen binnen 1 meeting',
      'Weken abstracte discussie bespaard door tastbare demo',
    ],
    tags: [
      { label: 'Angular 17', kleur: 'bg-red-500/20 text-red-400' },
      { label: 'Spring Boot', kleur: 'bg-green-500/20 text-green-400' },
      { label: 'Docker', kleur: 'bg-blue-500/20 text-blue-400' },
      { label: 'Cypress', kleur: 'bg-emerald-500/20 text-emerald-400' },
    ],
    prijsRange: null,
    github: 'https://github.com/koenvorsters/lima-lookalike',
  },
]

export default function CaseStudiesPage() {
  return (
    <div className="min-h-screen">
      {/* Header */}
      <section className="py-20 px-4 sm:px-6 text-center">
        <AnimatedSection>
          <span className="inline-flex items-center px-4 py-2 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-sm font-medium mb-6">
            Bewezen resultaten
          </span>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-white mb-6 leading-tight">
            Onze aanpak{' '}
            <span className="bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent">
              in actie
            </span>
          </h1>
          <p className="text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Van legacy code die niemand meer begreep tot AI-platformen die echt werken.
            Concrete projecten, meetbare resultaten.
          </p>
        </AnimatedSection>
      </section>

      {/* Case Studies */}
      <section className="py-8 px-4 sm:px-6 pb-24">
        <div className="max-w-5xl mx-auto space-y-16">
          {caseStudies.map((cs, i) => (
            <AnimatedSection key={cs.id} delay={i * 0.1}>
              <GlassCard className="overflow-hidden" data-testid={`case-study-card-${cs.id}`}>
                {/* Card header */}
                <div className={`h-3 bg-gradient-to-r ${cs.headerGradient}`} />

                <div className="p-6 sm:p-8 md:p-10">
                  {/* Meta row */}
                  <div className="flex flex-wrap items-center gap-3 mb-5">
                    <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${cs.dienstKleur}`}>
                      {cs.dienst}
                    </span>
                    <span className="text-slate-500 text-sm">{cs.context}</span>
                    {cs.prijsRange && (
                      <span className="ml-auto text-sm font-medium text-slate-300">
                        {cs.prijsRange}
                      </span>
                    )}
                  </div>

                  <h2 className="text-2xl sm:text-3xl font-bold text-white mb-2">{cs.titel}</h2>
                  <p className="text-slate-400 mb-8 text-sm sm:text-base">{cs.subtitel}</p>

                  <div className="grid md:grid-cols-2 gap-8">
                    {/* Probleem + Aanpak */}
                    <div className="space-y-6">
                      <div>
                        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
                          Het probleem
                        </h3>
                        <p className="text-slate-400 text-sm leading-relaxed">{cs.probleem}</p>
                      </div>

                      <div>
                        <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
                          De aanpak
                        </h3>
                        <ol className="space-y-2">
                          {cs.aanpak.map((stap, j) => (
                            <li key={j} className="flex gap-3 text-sm text-slate-400">
                              <span className={`shrink-0 w-5 h-5 rounded-full bg-gradient-to-br ${cs.headerGradient} flex items-center justify-center text-[10px] font-bold text-white mt-0.5`}>
                                {j + 1}
                              </span>
                              {stap}
                            </li>
                          ))}
                        </ol>
                      </div>
                    </div>

                    {/* Resultaten */}
                    <div>
                      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">
                        Resultaten
                      </h3>
                      <ul className="space-y-2.5">
                        {cs.resultaten.map((r, j) => (
                          <li key={j} className="flex gap-3 text-sm text-slate-300">
                            <CheckCircle2 className="w-4 h-4 text-green-400 shrink-0 mt-0.5" />
                            {r}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Footer row */}
                  <div className="mt-8 pt-6 border-t border-white/10 flex flex-wrap items-center gap-3">
                    <div className="flex flex-wrap gap-2 flex-1">
                      {cs.tags.map((tag) => (
                        <span key={tag.label} className={`text-xs px-2.5 py-1 rounded-lg border border-white/10 ${tag.kleur}`}>
                          {tag.label}
                        </span>
                      ))}
                    </div>
                    <div className="flex items-center gap-3">
                      {cs.github && (
                        <a
                          href={cs.github}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
                          aria-label={`GitHub repository van ${cs.titel}`}
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          GitHub
                        </a>
                      )}
                      <Link href="/contact">
                        <GradientButton variant="outline" className="text-xs px-4 py-2">
                          Vergelijkbaar project? →
                        </GradientButton>
                      </Link>
                    </div>
                  </div>
                </div>
              </GlassCard>
            </AnimatedSection>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4 sm:px-6">
        <AnimatedSection>
          <div className="max-w-3xl mx-auto text-center">
            <GlassCard className="p-8 sm:p-12">
              <h2 className="text-2xl sm:text-3xl font-bold text-white mb-4">
                Klaar voor uw project?
              </h2>
              <p className="text-slate-400 mb-8 text-sm sm:text-base max-w-xl mx-auto">
                Elk bedrijf heeft unieke uitdagingen. Laten we samen bekijken hoe AI en
                moderne technologie uw specifieke situatie kunnen transformeren.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link href="/diensten">
                  <GradientButton variant="primary" className="w-full sm:w-auto px-8 py-4">
                    Bekijk onze diensten
                  </GradientButton>
                </Link>
                <Link href="/contact">
                  <GradientButton variant="outline" className="w-full sm:w-auto px-8 py-4">
                    Plan een gratis gesprek
                  </GradientButton>
                </Link>
              </div>
            </GlassCard>
          </div>
        </AnimatedSection>
      </section>
    </div>
  )
}
