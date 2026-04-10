'use client'

import { useRef, useState, useEffect } from 'react'
import { motion, useInView } from 'framer-motion'
import {
  Activity, Cpu, HardDrive, Wifi, Clock, Server,
  Database, Bot, CheckCircle2, RefreshCw,
  Terminal, Zap,
} from 'lucide-react'
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

const services = [
  { naam: 'FastAPI Backend', poort: 8000, status: 'online', latency: '12ms', icon: Server },
  { naam: 'PostgreSQL', poort: 5432, status: 'online', latency: '3ms', icon: Database },
  { naam: 'Redis Cache', poort: 6379, status: 'online', latency: '1ms', icon: Zap },
  { naam: 'Keycloak Auth', poort: 8080, status: 'online', latency: '45ms', icon: Activity },
  { naam: 'Ollama LLM', poort: 11434, status: 'offline', latency: '—', icon: Bot },
  { naam: 'Webhook Engine', poort: 9000, status: 'online', latency: '8ms', icon: Wifi },
]

const aiAgents = [
  { naam: 'Klantenservice Agent', model: 'mistral', status: 'actief', runs: 342, uptime: '99.2%' },
  { naam: 'Product Beschrijving', model: 'llama3', status: 'actief', runs: 156, uptime: '97.8%' },
  { naam: 'SEO Agent', model: 'mistral', status: 'standby', runs: 89, uptime: '100%' },
  { naam: 'Order Verwerking', model: 'llama3', status: 'actief', runs: 478, uptime: '99.5%' },
]

const recentLogs = [
  { tijd: '14:32:01', level: 'INFO', bericht: 'Webhook ontvangen: order.created', bron: 'webhook-engine' },
  { tijd: '14:31:45', level: 'INFO', bericht: 'Agent run voltooid: klantenservice (324ms)', bron: 'ollama' },
  { tijd: '14:30:12', level: 'WARN', bericht: 'Redis cache miss ratio > 15%', bron: 'cache' },
  { tijd: '14:29:58', level: 'INFO', bericht: 'Database migration check: up-to-date', bron: 'alembic' },
  { tijd: '14:28:33', level: 'ERROR', bericht: 'Ollama LLM: connection refused op poort 11434', bron: 'ollama' },
  { tijd: '14:27:01', level: 'INFO', bericht: 'Health check: alle services OK (5/6)', bron: 'monitor' },
]

const techStack = [
  { categorie: 'Backend', items: ['Python 3.12', 'FastAPI', 'SQLAlchemy', 'Alembic'] },
  { categorie: 'Frontend', items: ['Next.js 16', 'React 19', 'Tailwind CSS v4', 'Framer Motion'] },
  { categorie: 'Infra', items: ['Docker Compose', 'PostgreSQL', 'Redis', 'Keycloak'] },
  { categorie: 'AI / ML', items: ['Ollama', 'Mistral', 'LLaMA 3', 'LangChain'] },
]

const levelColors: Record<string, string> = {
  INFO: 'text-blue-400',
  WARN: 'text-amber-400',
  ERROR: 'text-red-400',
}

export default function DashboardPage() {
  const [uptime, setUptime] = useState('0d 0h 0m')
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    // Simulate uptime counter
    const start = new Date(Date.now() - 14 * 24 * 60 * 60 * 1000 - 7 * 60 * 60 * 1000 - 23 * 60 * 1000)
    const update = () => {
      const diff = Date.now() - start.getTime()
      const d = Math.floor(diff / 86400000)
      const h = Math.floor((diff % 86400000) / 3600000)
      const m = Math.floor((diff % 3600000) / 60000)
      setUptime(`${d}d ${h}h ${m}m`)
    }
    update()
    const interval = setInterval(update, 60000)
    return () => clearInterval(interval)
  }, [])

  const handleRefresh = () => {
    setRefreshing(true)
    setTimeout(() => setRefreshing(false), 1000)
  }

  const onlineCount = services.filter(s => s.status === 'online').length

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-8 sm:mb-10">
          <div>
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-1">Tech Playground</h1>
            <p className="text-slate-400 text-sm sm:text-base">Live overzicht van de infrastructuur achter dit platform</p>
          </div>
          <button
            onClick={handleRefresh}
            className="flex items-center gap-2 text-xs sm:text-sm text-slate-400 hover:text-white transition-colors self-start sm:self-auto"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Ververs</span>
          </button>
        </div>
      </motion.div>

      {/* Status overview cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3 sm:gap-5 mb-8 sm:mb-10">
        {[
          { title: 'Services Online', value: `${onlineCount}/${services.length}`, icon: CheckCircle2, gradient: 'bg-gradient-to-br from-emerald-500 to-emerald-700' },
          { title: 'Uptime', value: uptime, icon: Clock, gradient: 'bg-gradient-to-br from-blue-500 to-blue-700' },
          { title: 'AI Agents', value: `${aiAgents.filter(a => a.status === 'actief').length} actief`, icon: Bot, gradient: 'bg-gradient-to-br from-violet-500 to-violet-700' },
          { title: 'Totale Runs', value: aiAgents.reduce((s, a) => s + a.runs, 0).toLocaleString(), icon: Cpu, gradient: 'bg-gradient-to-br from-orange-500 to-orange-700' },
        ].map((card, i) => (
          <AnimatedSection key={card.title} delay={i * 0.08}>
            <div className="backdrop-blur-md bg-white/5 border border-white/10 rounded-2xl p-4 sm:p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs sm:text-sm text-slate-400 mb-1">{card.title}</p>
                  <p className="text-xl sm:text-3xl font-bold text-white">{card.value}</p>
                </div>
                <div className={`p-2 sm:p-3 rounded-xl ${card.gradient}`}>
                  <card.icon className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                </div>
              </div>
            </div>
          </AnimatedSection>
        ))}
      </div>

      {/* Services + AI Agents */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-4 sm:mb-6">
        {/* Service Health */}
        <AnimatedSection delay={0.1}>
          <GlassCard className="p-4 sm:p-6">
            <h2 className="text-base sm:text-lg font-bold text-white mb-4 sm:mb-5 flex items-center gap-2">
              <HardDrive className="w-5 h-5 text-blue-400" />
              Service Health
            </h2>
            <div className="space-y-3">
              {services.map((service) => (
                <div key={service.naam} className="flex items-center justify-between">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`w-2 h-2 rounded-full shrink-0 ${service.status === 'online' ? 'bg-emerald-400 shadow-emerald-400/50 shadow-sm' : 'bg-red-400 shadow-red-400/50 shadow-sm'}`} />
                    <service.icon className="w-4 h-4 text-slate-500 shrink-0" />
                    <span className="text-slate-300 text-sm truncate">{service.naam}</span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0 ml-2">
                    <span className="text-xs text-slate-500 font-mono">:{service.poort}</span>
                    <span className={`text-xs font-medium ${service.status === 'online' ? 'text-emerald-400' : 'text-red-400'}`}>
                      {service.latency}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </AnimatedSection>

        {/* AI Agents */}
        <AnimatedSection delay={0.15}>
          <GlassCard className="p-4 sm:p-6">
            <h2 className="text-base sm:text-lg font-bold text-white mb-4 sm:mb-5 flex items-center gap-2">
              <Bot className="w-5 h-5 text-violet-400" />
              AI Agent Status
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-500 text-xs uppercase tracking-wider border-b border-white/10">
                    <th className="pb-3 text-left">Agent</th>
                    <th className="pb-3 text-left">Model</th>
                    <th className="pb-3 text-right">Runs</th>
                    <th className="pb-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {aiAgents.map((agent) => (
                    <tr key={agent.naam} className="border-b border-white/5 last:border-0">
                      <td className="py-3 text-white font-medium text-xs sm:text-sm">{agent.naam}</td>
                      <td className="py-3 text-slate-400 font-mono text-xs">{agent.model}</td>
                      <td className="py-3 text-right text-slate-300">{agent.runs}</td>
                      <td className="py-3 text-right">
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          agent.status === 'actief'
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : 'bg-slate-500/20 text-slate-400'
                        }`}>
                          {agent.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </AnimatedSection>
      </div>

      {/* Logs + Tech Stack */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Recent Logs */}
        <AnimatedSection delay={0.2}>
          <GlassCard className="p-4 sm:p-6 lg:col-span-2">
            <h2 className="text-base sm:text-lg font-bold text-white mb-4 sm:mb-5 flex items-center gap-2">
              <Terminal className="w-5 h-5 text-green-400" />
              Recente Logs
            </h2>
            <div className="space-y-2 font-mono text-xs">
              {recentLogs.map((log, i) => (
                <div key={i} className="flex gap-2 sm:gap-3 items-start">
                  <span className="text-slate-600 shrink-0">{log.tijd}</span>
                  <span className={`shrink-0 font-semibold w-11 ${levelColors[log.level]}`}>{log.level}</span>
                  <span className="text-slate-300 break-all">{log.bericht}</span>
                </div>
              ))}
            </div>
          </GlassCard>
        </AnimatedSection>

        {/* Tech Stack */}
        <AnimatedSection delay={0.25}>
          <GlassCard className="p-4 sm:p-6">
            <h2 className="text-base sm:text-lg font-bold text-white mb-4 sm:mb-5 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-orange-400" />
              Tech Stack
            </h2>
            <div className="space-y-4">
              {techStack.map((group) => (
                <div key={group.categorie}>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">{group.categorie}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {group.items.map((item) => (
                      <span key={item} className="text-xs px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-slate-300">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </AnimatedSection>
      </div>
    </div>
  )
}
