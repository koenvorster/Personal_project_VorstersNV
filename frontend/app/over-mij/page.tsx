'use client'

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import Image from 'next/image'
import {
  Code2, Cpu, Database, Cloud, Brain, Wifi, Terminal, Server,
  GraduationCap, Briefcase, Rocket, Award, Mail, MapPin, Calendar
} from 'lucide-react'
import { GithubIcon as Github, LinkedinIcon as Linkedin } from '@/components/icons/BrandIcons'
import GlassCard from '@/components/ui/GlassCard'
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

const skills = [
  { naam: 'Python', icon: Terminal, kleur: 'from-yellow-500 to-yellow-700' },
  { naam: 'TypeScript', icon: Code2, kleur: 'from-blue-500 to-blue-700' },
  { naam: 'React / Next.js', icon: Code2, kleur: 'from-cyan-500 to-cyan-700' },
  { naam: 'AI / Machine Learning', icon: Brain, kleur: 'from-violet-500 to-violet-700' },
  { naam: 'IoT & Embedded', icon: Wifi, kleur: 'from-green-500 to-green-700' },
  { naam: 'Docker & DevOps', icon: Server, kleur: 'from-blue-600 to-blue-800' },
  { naam: 'PostgreSQL', icon: Database, kleur: 'from-indigo-500 to-indigo-700' },
  { naam: 'FastAPI', icon: Cpu, kleur: 'from-emerald-500 to-emerald-700' },
  { naam: 'Cloud (AWS / Azure)', icon: Cloud, kleur: 'from-orange-500 to-orange-700' },
  { naam: 'LLM Orchestration', icon: Brain, kleur: 'from-purple-500 to-purple-700' },
  { naam: 'Multi-Agent Systems', icon: Cpu, kleur: 'from-violet-500 to-violet-700' },
  { naam: 'Policy-as-Code', icon: Terminal, kleur: 'from-rose-500 to-rose-700' },
  { naam: 'Prompt Engineering', icon: Code2, kleur: 'from-amber-500 to-amber-700' },
]

const tijdlijn = [
  {
    jaar: '2019 – 2022',
    titel: 'Thomas More — Electronica ICT IoT',
    beschrijving: 'Professionele bachelor met focus op embedded systems, netwerken en IoT-toepassingen. Projecten rond sensornetwerken, microcontrollers en data-acquisitie.',
    icon: GraduationCap,
    kleur: 'from-blue-500 to-blue-700',
  },
  {
    jaar: '2022 – heden',
    titel: 'Product Engineer',
    beschrijving: 'Ontwerp en ontwikkeling van producten op het snijvlak van hardware en software. Verantwoordelijk voor prototyping, testing en productie-optimalisatie.',
    icon: Briefcase,
    kleur: 'from-emerald-500 to-emerald-700',
  },
  {
    jaar: 'Heden',
    titel: 'AI & IT Consulting',
    beschrijving: 'Freelance trajecten voor KMO\'s: procesautomatisering met AI, digitale transformatie, custom software en hands-on workshops.',
    icon: Rocket,
    kleur: 'from-violet-500 to-violet-700',
  },
  {
    jaar: '2025 – 2026',
    titel: 'AI Control Platform Architect',
    beschrijving: 'Ontwerp en realisatie van een enterprise-grade AI Control Platform met governance, audit trail, event-driven skill chains en zelflerende agents. 1389+ geautomatiseerde tests. Vergelijkbaar niveau met enterprise spelers — gebouwd op een moderne open-source stack.',
    icon: Brain,
    kleur: 'from-purple-500 to-purple-700',
  },
]

const certificaten = [
  {
    titel: 'Professionele Bachelor Electronica-ICT',
    instelling: 'Thomas More Hogeschool',
    jaar: '2022',
    icon: GraduationCap,
  },
  {
    titel: 'IoT & Embedded Systems',
    instelling: 'Thomas More — Specialisatie',
    jaar: '2022',
    icon: Wifi,
  },
  {
    titel: 'AI & Machine Learning Fundamentals',
    instelling: 'Online Certificering',
    jaar: '2024',
    icon: Brain,
  },
  {
    titel: 'Docker & Container Orchestration',
    instelling: 'Online Certificering',
    jaar: '2023',
    icon: Server,
  },
  {
    titel: 'AI Platform Engineering',
    instelling: 'Praktijkervaring — VorstersNV',
    jaar: '2026',
    icon: Brain,
  },
  {
    titel: 'Policy-as-Code & AI Governance',
    instelling: 'Praktijkervaring — VorstersNV',
    jaar: '2026',
    icon: Award,
  },
]

export default function OverMijPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      {/* Hero / Bio */}
      <section className="mb-16 sm:mb-20">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="flex flex-col lg:flex-row items-center gap-8 sm:gap-10"
        >
          {/* Profile photo */}
          <div className="shrink-0">
            <div className="w-40 h-40 sm:w-48 sm:h-48 md:w-56 md:h-56 rounded-2xl overflow-hidden shadow-2xl shadow-green-500/20 ring-4 ring-white/10">
              <Image
                src="/profile.jpg"
                alt="Koen Vorsters"
                width={224}
                height={224}
                className="w-full h-full object-cover object-top"
                priority
              />
            </div>
          </div>

          {/* Bio text */}
          <div className="text-center lg:text-left max-w-2xl">
            <span className="inline-flex items-center px-3 sm:px-4 py-1.5 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-xs sm:text-sm font-medium mb-3 sm:mb-4">
              Product Engineer · AI Platform Architect
            </span>
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white mb-3 sm:mb-4">
              Koen Vorsters
            </h1>
            <p className="text-slate-400 text-base sm:text-lg leading-relaxed mb-3">
              Product Engineer &amp; AI Platform Architect met een passie voor technologie en innovatie. Afgestudeerd aan Thomas More in Electronica-ICT met specialisatie IoT. Ik bouw enterprise-grade AI-systemen die écht werken: van lokale LLM-orchestratie tot volledige AI Control Platforms met governance, auditing en zelflerende agents.
            </p>
            <p className="text-slate-500 text-sm sm:text-base leading-relaxed mb-4">
              Met een unieke combinatie van hardware-achtergrond (embedded systems, IoT) en moderne software-expertise (AI-platforms, multi-agent orchestratie, Policy-as-Code) breng ik een breed perspectief naar elk project. Mijn AI Control Platform staat op hetzelfde niveau als enterprise spelers — maar gebouwd op een open-source stack die voor iedereen toegankelijk is.
            </p>

            {/* Personal quote */}
            <div className="border-l-2 border-green-500/40 pl-4 mb-5">
              <p className="text-slate-400 text-sm italic">
                &ldquo;AI is pas krachtig als het bestuurd, geauditeerd en schaalbaar is. Ik bouw platforms, geen chatbots.&rdquo;
              </p>
            </div>

            {/* Quick info + socials */}
            <div className="flex flex-wrap items-center justify-center lg:justify-start gap-3 sm:gap-4">
              <span className="inline-flex items-center gap-1.5 text-slate-400 text-sm">
                <MapPin className="w-4 h-4 text-green-400" /> België
              </span>
              <span className="inline-flex items-center gap-1.5 text-slate-400 text-sm">
                <Calendar className="w-4 h-4 text-green-400" /> Beschikbaar
              </span>
              <div className="flex items-center gap-2 ml-0 sm:ml-2">
                <a href="https://www.linkedin.com/in/koen-vorsters/" target="_blank" rel="noopener noreferrer" className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all">
                  <Linkedin className="w-4 h-4" />
                </a>
                <a href="https://github.com/koenvorsters" target="_blank" rel="noopener noreferrer" className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all">
                  <Github className="w-4 h-4" />
                </a>
                <a href="mailto:koen@vorsters.dev" className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all">
                  <Mail className="w-4 h-4" />
                </a>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Skills & Technologieën */}
      <section className="mb-16 sm:mb-20">
        <AnimatedSection>
          <div className="text-center mb-8 sm:mb-10">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-3">Skills & Technologieën</h2>
            <p className="text-slate-400 max-w-lg mx-auto text-sm sm:text-base">De tools en technologieën waarmee ik dagelijks werk</p>
          </div>
        </AnimatedSection>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3 sm:gap-4">
          {skills.map((skill, i) => (
            <AnimatedSection key={skill.naam} delay={i * 0.05}>
              <GlassCard hover className="p-4 sm:p-5 text-center h-full flex flex-col items-center justify-center gap-2 sm:gap-3">
                <div className={`inline-flex p-2.5 sm:p-3 rounded-xl bg-gradient-to-br ${skill.kleur}`}>
                  <skill.icon className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                </div>
                <span className="text-white text-xs sm:text-sm font-semibold">{skill.naam}</span>
              </GlassCard>
            </AnimatedSection>
          ))}
        </div>
      </section>

      {/* Platform Stats */}
      <section className="mb-16 sm:mb-20">
        <AnimatedSection>
          <div className="text-center mb-8 sm:mb-10">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-3">In Cijfers</h2>
            <p className="text-slate-400 max-w-lg mx-auto text-sm sm:text-base">Wat het AI Control Platform vandaag kan</p>
          </div>
        </AnimatedSection>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-5 max-w-4xl mx-auto">
          {[
            { waarde: '1.389', label: 'Geautomatiseerde tests', kleur: 'text-green-400' },
            { waarde: '41', label: 'Features gebouwd', kleur: 'text-violet-400' },
            { waarde: '6', label: 'AI skill groepen', kleur: 'text-blue-400' },
            { waarde: '8', label: 'REST API endpoints', kleur: 'text-amber-400' },
          ].map((stat, i) => (
            <AnimatedSection key={stat.label} delay={i * 0.08}>
              <GlassCard className="p-5 sm:p-6 text-center h-full flex flex-col items-center justify-center gap-2">
                <span className={`text-3xl sm:text-4xl font-extrabold ${stat.kleur}`}>{stat.waarde}</span>
                <span className="text-slate-400 text-xs sm:text-sm text-center leading-tight">{stat.label}</span>
              </GlassCard>
            </AnimatedSection>
          ))}
        </div>
      </section>

      {/* Tijdlijn / Carrièrepad */}
      <section className="mb-16 sm:mb-20">
        <AnimatedSection>
          <div className="text-center mb-10 sm:mb-12">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-3">Mijn Pad</h2>
            <p className="text-slate-400 max-w-lg mx-auto text-sm sm:text-base">Van opleiding tot ondernemer — mijn carrièreverloop</p>
          </div>
        </AnimatedSection>

        <div className="relative max-w-3xl mx-auto">
          {/* Vertical line */}
          <div className="absolute left-6 md:left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-green-500/50 via-emerald-500/30 to-transparent" />

          {tijdlijn.map((item, i) => (
            <AnimatedSection key={item.titel} delay={i * 0.15}>
              <div className={`relative flex items-start gap-4 sm:gap-6 mb-10 sm:mb-12 ${i % 2 === 0 ? 'md:flex-row' : 'md:flex-row-reverse'}`}>
                {/* Dot on timeline */}
                <div className="absolute left-6 md:left-1/2 -translate-x-1/2 z-10">
                  <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-gradient-to-br ${item.kleur} flex items-center justify-center shadow-lg ring-4 ring-slate-950`}>
                    <item.icon className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                  </div>
                </div>

                {/* Content card */}
                <div className={`ml-16 sm:ml-20 md:ml-0 md:w-[calc(50%-3rem)] ${i % 2 === 0 ? 'md:pr-4' : 'md:pl-4 md:ml-auto'}`}>
                  <GlassCard className="p-4 sm:p-6">
                    <span className="text-xs font-semibold text-green-400 uppercase tracking-wider">{item.jaar}</span>
                    <h3 className="text-base sm:text-lg font-bold text-white mt-1 mb-2">{item.titel}</h3>
                    <p className="text-slate-400 text-xs sm:text-sm leading-relaxed">{item.beschrijving}</p>
                  </GlassCard>
                </div>
              </div>
            </AnimatedSection>
          ))}
        </div>
      </section>

      {/* Certificaten & Opleidingen */}
      <section className="mb-16 sm:mb-20">
        <AnimatedSection>
          <div className="text-center mb-8 sm:mb-10">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-3">Certificaten & Opleidingen</h2>
            <p className="text-slate-400 max-w-lg mx-auto text-sm sm:text-base">Formele opleidingen en bijkomende certificeringen</p>
          </div>
        </AnimatedSection>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
          {certificaten.map((cert, i) => (
            <AnimatedSection key={cert.titel} delay={i * 0.08}>
              <GlassCard hover className="p-5 sm:p-6 h-full flex flex-col">
                <div className="flex items-center gap-3 mb-3 sm:mb-4">
                  <div className="p-2 sm:p-2.5 rounded-lg bg-green-500/10 border border-green-500/20">
                    <cert.icon className="w-4 h-4 sm:w-5 sm:h-5 text-green-400" />
                  </div>
                  <Award className="w-4 h-4 text-slate-600" />
                </div>
                <h3 className="text-white font-semibold text-sm mb-1">{cert.titel}</h3>
                <p className="text-slate-500 text-xs mb-2">{cert.instelling}</p>
                <span className="mt-auto text-xs font-medium text-slate-600">{cert.jaar}</span>
              </GlassCard>
            </AnimatedSection>
          ))}
        </div>
      </section>

      {/* Contact Section */}
      <AnimatedSection>
        <div className="text-center mb-8 sm:mb-10">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-3">Neem Contact Op</h2>
          <p className="text-slate-400 max-w-lg mx-auto text-sm sm:text-base">
            Interesse in een samenwerking? Ik sta altijd open voor een gesprek.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-5 max-w-3xl mx-auto">
          <a href="mailto:koen@vorsters.dev" className="group">
            <GlassCard hover className="p-6 sm:p-8 text-center h-full flex flex-col items-center gap-3">
              <div className="p-3 rounded-xl bg-green-500/10 border border-green-500/20 group-hover:bg-green-500/20 transition-colors">
                <Mail className="w-6 h-6 text-green-400" />
              </div>
              <h3 className="text-white font-semibold text-sm">E-mail</h3>
              <p className="text-slate-400 text-xs">koen@vorsters.dev</p>
            </GlassCard>
          </a>

          <a href="https://www.linkedin.com/in/koen-vorsters/" target="_blank" rel="noopener noreferrer" className="group">
            <GlassCard hover className="p-6 sm:p-8 text-center h-full flex flex-col items-center gap-3">
              <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 group-hover:bg-blue-500/20 transition-colors">
                <Linkedin className="w-6 h-6 text-blue-400" />
              </div>
              <h3 className="text-white font-semibold text-sm">LinkedIn</h3>
              <p className="text-slate-400 text-xs">Koen Vorsters</p>
            </GlassCard>
          </a>

          <a href="https://github.com/koenvorsters" target="_blank" rel="noopener noreferrer" className="group">
            <GlassCard hover className="p-6 sm:p-8 text-center h-full flex flex-col items-center gap-3">
              <div className="p-3 rounded-xl bg-slate-500/10 border border-slate-500/20 group-hover:bg-slate-500/20 transition-colors">
                <Github className="w-6 h-6 text-slate-300" />
              </div>
              <h3 className="text-white font-semibold text-sm">GitHub</h3>
              <p className="text-slate-400 text-xs">koenvorsters</p>
            </GlassCard>
          </a>
        </div>
      </AnimatedSection>
    </div>
  )
}
