'use client'

import { Bot, TrendingUp, TrendingDown, AlertTriangle, Star } from 'lucide-react'
import GlassCard from './GlassCard'

export interface AgentAnalytics {
  agent_naam: string
  prompt_versie: string
  totaal_interacties: number
  beoordeelde_interacties: number
  gemiddelde_score: number
  lage_scores: number
  verbeter_suggesties: string[]
  status: string
}

interface Props {
  agent: AgentAnalytics
}

const AGENT_LABELS: Record<string, string> = {
  klantenservice_agent: 'Klantenservice',
  product_beschrijving_agent: 'Productbeschrijving',
  seo_agent: 'SEO',
  order_verwerking_agent: 'Orderverwerking',
  fraude_detectie_agent: 'Fraudedetectie',
  retour_verwerking_agent: 'Retourverwerking',
  voorraad_advies_agent: 'Voorraadadvies',
}

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round((score / 5) * 100)
  const color =
    score >= 4.0 ? 'bg-emerald-400' :
    score >= 3.0 ? 'bg-amber-400' :
    score > 0    ? 'bg-red-400' :
                   'bg-slate-600'

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-slate-300 w-6 text-right">
        {score > 0 ? score.toFixed(1) : '—'}
      </span>
    </div>
  )
}

export default function AgentScoreCard({ agent }: Props) {
  const label = AGENT_LABELS[agent.agent_naam] ?? agent.agent_naam
  const hasScore = agent.beoordeelde_interacties > 0
  const isWarn = agent.lage_scores >= 3
  const isCritical = agent.lage_scores >= 6

  return (
    <div className="backdrop-blur-md bg-white/5 border border-white/10 rounded-2xl p-4 flex flex-col gap-3 hover:border-white/20 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className={`p-1.5 rounded-lg shrink-0 ${
            isCritical ? 'bg-red-500/20' :
            isWarn     ? 'bg-amber-500/20' :
                         'bg-violet-500/20'
          }`}>
            <Bot className={`w-4 h-4 ${
              isCritical ? 'text-red-400' :
              isWarn     ? 'text-amber-400' :
                           'text-violet-400'
            }`} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white truncate">{label}</p>
            <p className="text-xs text-slate-500 font-mono">v{agent.prompt_versie}</p>
          </div>
        </div>
        {isCritical && (
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
        )}
      </div>

      {/* Score bar */}
      <ScoreBar score={agent.gemiddelde_score} />

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div>
          <p className="text-xs text-slate-500">Interacties</p>
          <p className="text-sm font-bold text-white">{agent.totaal_interacties.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Beoordeeld</p>
          <p className="text-sm font-bold text-white">{agent.beoordeelde_interacties}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Laag score</p>
          <p className={`text-sm font-bold ${agent.lage_scores > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
            {agent.lage_scores}
          </p>
        </div>
      </div>

      {/* Status badge */}
      <div className="flex items-center justify-between">
        <span className={`text-xs px-2 py-0.5 rounded-full ${
          hasScore
            ? 'bg-emerald-500/15 text-emerald-400'
            : 'bg-slate-500/15 text-slate-400'
        }`}>
          {hasScore ? '● actief feedback' : '○ geen feedback'}
        </span>
        {hasScore && (
          <div className="flex items-center gap-1">
            <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
            <span className="text-xs text-amber-300 font-mono">
              {agent.gemiddelde_score.toFixed(1)}/5
            </span>
          </div>
        )}
      </div>

      {/* Suggestie */}
      {agent.verbeter_suggesties.length > 0 && (
        <p className="text-xs text-amber-400/80 leading-relaxed border-t border-white/5 pt-2">
          ⚠ {agent.verbeter_suggesties[0]}
        </p>
      )}
    </div>
  )
}
