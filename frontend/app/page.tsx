'use client'

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import Link from 'next/link'
import Image from 'next/image'
import {
  Code2, Brain, Server, Terminal, Cpu, Database, Cloud, Wifi,
  ChevronRight, Mail, MapPin, Briefcase,
  GraduationCap, Rocket, ArrowDown
} from 'lucide-react'
import { GithubIcon as Github, LinkedinIcon as Linkedin } from '@/components/icons/BrandIcons'
import GlassCard from '@/components/ui/GlassCard'
import GradientButton from '@/components/ui/GradientButton'

const stats = [
  { value: '4+', label: 'Jaar ervaring' },
  { value: '15+', label: 'Projecten afgeleverd' },
  { value: '9+', label: 'Technologieën' },
  { value: '∞', label: 'Passie voor tech' },
]

const expertises = [
  {
    icon: Code2,
    title: 'Full-Stack Development',
    description: 'Van React/Next.js frontends tot FastAPI backends — ik bouw complete, performante applicaties met moderne tech stacks.',
    gradient: 'from-blue-500 to-blue-700',
    tags: ['React', 'Next.js', 'FastAPI', 'TypeScript'],
  },
  {
    icon: Brain,
    title: 'AI & Machine Learning',
    description: 'Integratie van AI-modellen en LLM\'s in bedrijfsprocessen. Lokale AI met Ollama, prompt engineering en agent-architecturen.',
    gradient: 'from-violet-500 to-violet-700',
    tags: ['Ollama', 'LLM', 'Python', 'Agents'],
  },
  {
    icon: Wifi,
    title: 'IoT & Embedded Systems',
    description: 'Sensornetwerken, microcontrollers en data-acquisitie. Hardware en software naadloos laten samenwerken.',
    gradient: 'from-emerald-500 to-emerald-700',
    tags: ['IoT', 'Embedded', 'MQTT', 'Sensors'],
  },
]

const projecten = [
  {
    naam: 'VorstersNV Platform',
    beschrijving: 'Full-stack webplatform met FastAPI, Next.js, PostgreSQL, Keycloak auth, analytics dashboard en AI-agent integratie via Ollama.',
    tags: ['Python', 'TypeScript', 'Docker', 'AI', 'PostgreSQL'],
    gradient: 'from-green-600 to-emerald-800',
    icon: Server,
  },
  {
    naam: 'AI Agent Orchestrator',
    beschrijving: 'Modulair multi-agent systeem voor klantenservice, SEO-optimalisatie en automatische productbeschrijvingen met lokale LLM\'s.',
    tags: ['Python', 'Ollama', 'LLM', 'YAML', 'Agents'],
    gradient: 'from-violet-600 to-purple-800',
    icon: Brain,
  },
  {
    naam: 'IoT Data Pipeline',
    beschrijving: 'Real-time sensor data verwerking met embedded devices, MQTT protocollen en interactieve cloud dashboards.',
    tags: ['IoT', 'Embedded', 'MQTT', 'Python', 'Cloud'],
    gradient: 'from-blue-600 to-cyan-800',
    icon: Wifi,
  },
]

const techStack = [
  { naam: 'Python', icon: Terminal, kleur: 'from-yellow-500 to-yellow-700' },
  { naam: 'TypeScript', icon: Code2, kleur: 'from-blue-500 to-blue-700' },
  { naam: 'React / Next.js', icon: Code2, kleur: 'from-cyan-500 to-cyan-700' },
  { naam: 'FastAPI', icon: Cpu, kleur: 'from-emerald-500 to-emerald-700' },
  { naam: 'PostgreSQL', icon: Database, kleur: 'from-indigo-500 to-indigo-700' },
  { naam: 'Docker & DevOps', icon: Server, kleur: 'from-blue-600 to-blue-800' },
  { naam: 'AI / LLM', icon: Brain, kleur: 'from-violet-500 to-violet-700' },
  { naam: 'IoT & Embedded', icon: Wifi, kleur: 'from-green-500 to-green-700' },
  { naam: 'Cloud (AWS/Azure)', icon: Cloud, kleur: 'from-orange-500 to-orange-700' },
]

const tijdlijn = [
  {
    jaar: '2019 – 2022',
    titel: 'Thomas More — Electronica-ICT (IoT)',
    icon: GraduationCap,
    kleur: 'from-blue-500 to-blue-700',
  },
  {
    jaar: '2022 – heden',
    titel: 'Product Engineer',
    icon: Briefcase,
    kleur: 'from-emerald-500 to-emerald-700',
  },
  {
    jaar: 'Nu',
    titel: 'AI & IT Consulting — Freelance',
    icon: Rocket,
    kleur: 'from-violet-500 to-violet-700',
  },
]

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

export default function HomePage() {
  return (
    <div className="overflow-x-hidden">
      {/* Hero */}
      <section className="relative min-h-[100svh] flex items-center justify-center px-4 sm:px-6">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-64 sm:w-96 h-64 sm:h-96 bg-green-600/20 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-52 sm:w-80 h-52 sm:h-80 bg-emerald-600/20 rounded-full blur-3xl" />
          <div className="absolute top-1/2 left-1/2 w-40 sm:w-64 h-40 sm:h-64 bg-violet-600/10 rounded-full blur-3xl" />
        </div>

        <div className="relative z-10 text-center max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="mx-auto mb-6 sm:mb-8 w-24 h-24 sm:w-28 sm:h-28 rounded-2xl overflow-hidden shadow-2xl shadow-green-500/20 ring-2 ring-green-500/30"
          >
            <Image
              src="/profile.jpg"
              alt="Koen Vorsters"
              width={112}
              height={112}
              className="w-full h-full object-cover object-top"
              priority
            />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-flex items-center px-3 sm:px-4 py-1.5 sm:py-2 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-xs sm:text-sm font-medium mb-4 sm:mb-6">
              <MapPin className="w-3 h-3 sm:w-3.5 sm:h-3.5 mr-1.5" /> België — Beschikbaar voor projecten
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-extrabold mb-4 sm:mb-6 leading-[1.1]"
          >
            Hi, ik ben{' '}
            <span className="bg-gradient-to-r from-green-400 via-emerald-400 to-emerald-500 bg-clip-text text-transparent">
              Koen Vorsters
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.15 }}
            className="text-xl sm:text-2xl md:text-3xl font-bold text-white/90 mb-4 sm:mb-6"
          >
            Developer · Engineer · Innovator
          </motion.p>

          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="text-base sm:text-lg md:text-xl text-slate-400 mb-8 sm:mb-10 max-w-2xl mx-auto leading-relaxed px-2"
          >
            Product Engineer met passie voor AI, IoT en full-stack development.
            Ik help bedrijven groeien door slimme digitale oplossingen te bouwen.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center px-4 sm:px-0"
          >
            <Link href="/over-mij" className="w-full sm:w-auto">
              <GradientButton variant="primary" className="w-full sm:w-auto text-base px-8 py-4 flex items-center justify-center gap-2">
                Over mij <ChevronRight className="w-4 h-4" />
              </GradientButton>
            </Link>
            <Link href="/projecten" className="w-full sm:w-auto">
              <GradientButton variant="outline" className="w-full sm:w-auto text-base px-8 py-4 flex items-center justify-center gap-2">
                Bekijk projecten
              </GradientButton>
            </Link>
            <Link href="/contact" className="w-full sm:w-auto">
              <GradientButton variant="outline" className="w-full sm:w-auto text-base px-8 py-4 flex items-center justify-center gap-2">
                Neem contact op <Mail className="w-4 h-4" />
              </GradientButton>
            </Link>
          </motion.div>

          {/* Social links */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.7, delay: 0.5 }}
            className="flex items-center justify-center gap-4 mt-8 sm:mt-10"
          >
            <a href="https://www.linkedin.com/in/koen-vorsters/" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn profiel" className="p-3 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all duration-200">
              <Linkedin className="w-5 h-5" />
            </a>
            <a href="https://github.com/koenvorsters" target="_blank" rel="noopener noreferrer" aria-label="GitHub profiel" className="p-3 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all duration-200">
              <Github className="w-5 h-5" />
            </a>
            <a href="mailto:koen@vorsters.dev" aria-label="Stuur een e-mail" className="p-3 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all duration-200">
              <Mail className="w-5 h-5" />
            </a>
          </motion.div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 0.5 }}
          className="absolute bottom-6 sm:bottom-8 left-1/2 -translate-x-1/2"
        >
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ repeat: Infinity, duration: 2 }}
          >
            <ArrowDown className="w-5 h-5 text-slate-500" />
          </motion.div>
        </motion.div>
      </section>

      {/* Quick timeline bar */}
      <section className="py-8 sm:py-12 px-4 sm:px-6">
        <AnimatedSection>
          <div className="max-w-5xl mx-auto">
            <GlassCard className="p-4 sm:p-6 md:p-8">
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-8 md:gap-12">
                {tijdlijn.map((item, i) => (
                  <div key={item.titel} className="flex items-center gap-3 sm:gap-4">
                    <div className={`p-2 sm:p-2.5 rounded-lg bg-gradient-to-br ${item.kleur} shrink-0`}>
                      <item.icon className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                    </div>
                    <div className="min-w-0">
                      <div className="text-white font-semibold text-sm sm:text-base truncate">{item.titel}</div>
                      <div className="text-slate-500 text-xs sm:text-sm">{item.jaar}</div>
                    </div>
                    {i < tijdlijn.length - 1 && (
                      <ChevronRight className="w-4 h-4 text-slate-600 hidden sm:block ml-2" />
                    )}
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>
        </AnimatedSection>
      </section>

      {/* Stats bar */}
      <section className="py-4 sm:py-8 px-4 sm:px-6">
        <AnimatedSection>
          <div className="max-w-5xl mx-auto">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 md:gap-6">
              {stats.map((stat, i) => (
                <motion.div
                  key={stat.label}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: i * 0.1 }}
                >
                  <GlassCard className="p-4 sm:p-6 text-center">
                    <div className="text-2xl sm:text-3xl md:text-4xl font-extrabold bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent">
                      {stat.value}
                    </div>
                    <div className="text-slate-400 text-xs sm:text-sm mt-1">{stat.label}</div>
                  </GlassCard>
                </motion.div>
              ))}
            </div>
          </div>
        </AnimatedSection>
      </section>

      {/* Expertises */}
      <section className="py-16 sm:py-20 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <AnimatedSection>
            <div className="text-center mb-10 sm:mb-14">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-3 sm:mb-4">
                Waar ik in uitblink
              </h2>
              <p className="text-slate-400 max-w-xl mx-auto text-sm sm:text-base px-4">
                Van concept tot productie — ik combineer software engineering met hardware kennis voor complete oplossingen.
              </p>
            </div>
          </AnimatedSection>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
            {expertises.map((expertise, i) => (
              <AnimatedSection key={expertise.title} delay={i * 0.15}>
                <GlassCard hover className="p-6 sm:p-8 h-full flex flex-col">
                  <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${expertise.gradient} mb-4 sm:mb-5 self-start`}>
                    <expertise.icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-lg font-bold text-white mb-2 sm:mb-3">{expertise.title}</h3>
                  <p className="text-slate-400 text-sm leading-relaxed mb-4 flex-1">{expertise.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {expertise.tags.map((tag) => (
                      <span key={tag} className="text-xs px-2.5 py-1 rounded-lg bg-white/5 text-slate-400 border border-white/10">
                        {tag}
                      </span>
                    ))}
                  </div>
                </GlassCard>
              </AnimatedSection>
            ))}
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="py-16 sm:py-20 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <AnimatedSection>
            <div className="text-center mb-10 sm:mb-14">
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-3 sm:mb-4">Tech Stack</h2>
              <p className="text-slate-400 text-sm sm:text-base">De technologieën waar ik dagelijks mee werk</p>
            </div>
          </AnimatedSection>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4 max-w-3xl mx-auto">
            {techStack.map((tech, i) => (
              <AnimatedSection key={tech.naam} delay={i * 0.05}>
                <GlassCard hover className="p-3 sm:p-4 flex items-center gap-2.5 sm:gap-3">
                  <div className={`inline-flex p-1.5 sm:p-2 rounded-lg bg-gradient-to-br ${tech.kleur} shrink-0`}>
                    <tech.icon className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white" />
                  </div>
                  <span className="text-xs sm:text-sm font-medium text-white truncate">{tech.naam}</span>
                </GlassCard>
              </AnimatedSection>
            ))}
          </div>
        </div>
      </section>

      {/* Projecten */}
      <section className="py-16 sm:py-20 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <AnimatedSection>
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 sm:mb-12 gap-4">
              <div>
                <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-2">Uitgelichte projecten</h2>
                <p className="text-slate-400 text-sm sm:text-base">Een selectie van mijn recente werk</p>
              </div>
              <Link href="/projecten" className="flex items-center gap-2 text-green-400 hover:text-green-300 text-sm font-medium transition-colors">
                Alle projecten <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          </AnimatedSection>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {projecten.map((project, i) => (
              <AnimatedSection key={project.naam} delay={i * 0.1}>
                <GlassCard hover className="overflow-hidden group h-full flex flex-col">
                  <div className={`h-28 sm:h-32 bg-gradient-to-br ${project.gradient} flex items-center justify-center relative`}>
                    <project.icon className="w-8 sm:w-10 h-8 sm:h-10 text-white/30" />
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-950/60 to-transparent" />
                  </div>
                  <div className="p-5 sm:p-6 flex-1 flex flex-col">
                    <h3 className="font-semibold text-white mb-2 text-base sm:text-lg">{project.naam}</h3>
                    <p className="text-slate-400 text-sm leading-relaxed mb-4 flex-1">{project.beschrijving}</p>
                    <div className="flex flex-wrap gap-1.5 sm:gap-2">
                      {project.tags.map((tag) => (
                        <span key={tag} className="text-[11px] sm:text-xs px-2 py-0.5 sm:py-1 rounded-md bg-white/5 text-slate-400 border border-white/10">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </GlassCard>
              </AnimatedSection>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 sm:py-20 px-4 sm:px-6">
        <AnimatedSection>
          <div className="max-w-3xl mx-auto text-center">
            <GlassCard className="p-8 sm:p-12">
              <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3 sm:mb-4">Interesse in een samenwerking?</h2>
              <p className="text-slate-400 mb-6 sm:mb-8 text-sm sm:text-base px-2">
                Op zoek naar een developer voor uw project? Neem gerust contact op — ik denk graag mee over uw digitale uitdagingen.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center">
                <Link href="/over-mij" className="w-full sm:w-auto">
                  <GradientButton variant="primary" className="w-full sm:w-auto px-8 py-4 text-base">
                    Meer over mij
                  </GradientButton>
                </Link>
                <a href="mailto:koen@vorsters.dev" className="w-full sm:w-auto">
                  <GradientButton variant="outline" className="w-full sm:w-auto px-8 py-4 text-base flex items-center justify-center gap-2">
                    <Mail className="w-4 h-4" /> Contact
                  </GradientButton>
                </a>
              </div>
            </GlassCard>
          </div>
        </AnimatedSection>
      </section>
    </div>
  )
}
