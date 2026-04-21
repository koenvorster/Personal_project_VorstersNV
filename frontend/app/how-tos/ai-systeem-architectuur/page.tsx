'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronDown, Database, Layers, Brain, Zap, Shield, TrendingUp,
  ArrowRight, BookOpen, ExternalLink, Cpu, GitBranch, Network,
} from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'
import Image from 'next/image'
import Link from 'next/link'

// ─── Types ────────────────────────────────────────────────────────────────────

type ContentBlock =
  | { type: 'paragraph'; text: string }
  | { type: 'heading'; text: string }
  | { type: 'list'; items: string[] }
  | { type: 'tip'; title: string; text: string }
  | { type: 'explainer'; emoji: string; title: string; text: string }
  | { type: 'comparison'; left: ComparisonSide; right: ComparisonSide }
  | { type: 'maturity'; levels: MaturityLevel[] }
  | { type: 'layergrid'; layers: LayerCard[] }
  | { type: 'quote'; text: string }
  | { type: 'outcomegrid'; outcomes: OutcomeCard[] }

interface ComparisonSide { title: string; color: string; items: string[] }
interface MaturityLevel { level: string; name: string; desc: string; gain: string; color: string; bg: string }
interface LayerCard { icon: string; title: string; sub: string; items: string[]; color: string; bg: string }
interface OutcomeCard { icon: string; title: string; desc: string; color: string }

interface Section {
  id: string
  icon: typeof Brain
  iconColor: string
  badge: string
  badgeColor: string
  title: string
  subtitle: string
  content: ContentBlock[]
}

// ─── Content ──────────────────────────────────────────────────────────────────

const sections: Section[] = [
  {
    id: 'data-context',
    icon: Database,
    iconColor: 'text-blue-400',
    badge: 'Laag 1',
    badgeColor: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    title: 'Data & Context',
    subtitle: 'Alles wat AI nodig heeft om te begrijpen — de brandstof van het systeem',
    content: [
      {
        type: 'explainer',
        emoji: '🗂️',
        title: 'In gewoon Nederlands: wat is Data & Context?',
        text: 'AI is zo slim als de informatie die hij krijgt. Stel je voor: je huurt een consultant in, maar geeft hem geen toegang tot je systemen, geen documentatie, en geen context over je bedrijf. Wat hij dan levert, is nutteloos. Data & Context is de laag die zorgt dat de AI precies weet waar hij aan werkt: je code, je documenten, je databank, je tools. Zonder deze laag is AI een slimme maar blinde medewerker.',
      },
      {
        type: 'layergrid',
        layers: [
          {
            icon: '💻',
            title: 'Code Repositories',
            sub: 'Git, PRs, Commits',
            items: ['GitHub / GitLab integratie', 'PR diffs en commit history', 'Branch context en blame info', 'Code search en semantische index'],
            color: 'text-blue-400',
            bg: 'bg-blue-500/5 border-blue-500/20',
          },
          {
            icon: '📄',
            title: 'Documents & Knowledge',
            sub: 'Confluence, Docs, Wikis',
            items: ['Confluence pagina\'s en spaces', 'API documentatie', 'Runbooks en procedures', 'Jira tickets en beslissingen'],
            color: 'text-violet-400',
            bg: 'bg-violet-500/5 border-violet-500/20',
          },
          {
            icon: '🗄️',
            title: 'Databases & Storage',
            sub: 'PostgreSQL, Vector DBs, Files',
            items: ['Gestructureerde bedrijfsdata', 'Vector stores voor semantisch zoeken', 'Logs en audit trails', 'Bestanden en artefacten'],
            color: 'text-emerald-400',
            bg: 'bg-emerald-500/5 border-emerald-500/20',
          },
          {
            icon: '🔌',
            title: 'APIs & Tools',
            sub: 'Jira, Slack, CI/CD, Custom',
            items: ['Jira voor tickets en sprints', 'Slack voor communicatie', 'CI/CD pipelines (GitHub Actions)', 'Custom interne APIs'],
            color: 'text-amber-400',
            bg: 'bg-amber-500/5 border-amber-500/20',
          },
        ],
      },
      {
        type: 'tip',
        title: '💡 Praktijktip: begin met lees-toegang',
        text: 'Geef je AI-systeem eerst alleen leestoegang tot data. Kijk hoe het ermee omgaat. Voeg schrijftoegang pas toe als je het gedrag volledig begrijpt. Slechte data in = slechte antwoorden uit. Garbage in, garbage out — dat geldt dubbel voor AI.',
      },
    ],
  },
  {
    id: 'orchestratie',
    icon: Network,
    iconColor: 'text-violet-400',
    badge: 'Laag 2',
    badgeColor: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
    title: 'Orchestratie Laag',
    subtitle: 'Ontwerp, verbind en controleer — het brein dat alles coördineert',
    content: [
      {
        type: 'explainer',
        emoji: '🎼',
        title: 'In gewoon Nederlands: wat doet een orchestratie laag?',
        text: 'Een orkest heeft niet alleen muzikanten nodig — het heeft een dirigent. De orchestratie laag is die dirigent. Hij beslist welke AI-componenten wanneer worden ingeschakeld, in welke volgorde, met welke data. Tools zoals Langflow laten je dat visueel opzetten: je tekent letterlijk je AI-workflow zoals een blokschema. Prompt & Logic bepaalt hoe de AI denkt. RAG zorgt dat hij de juiste info opzoekt. Guardrails zorgen dat hij binnen de regels blijft.',
      },
      {
        type: 'list',
        items: [
          '🎨 Langflow (Visual Workflow Builder) — sleep-en-neerzet interface om AI workflows te bouwen zonder code',
          '💬 Prompt & Logic — de instructies die bepalen hoe de AI reageert en beslist',
          '🔍 Retrieval & RAG — zoek relevante documenten op uit je kennisbank vóór het antwoorden (Retrieval-Augmented Generation)',
          '🔧 Tools & Integrations — koppel externe systemen: Jira, Slack, GitHub, databases',
          '🛡️ Guardrails & Rules — stel grenzen in: wat mag de AI wel/niet doen, welke output is verboden',
        ],
      },
      {
        type: 'explainer',
        emoji: '🔍',
        title: 'Wat is RAG precies?',
        text: 'RAG staat voor Retrieval-Augmented Generation. In gewoon Nederlands: vóór de AI antwoordt, zoekt hij eerst de meest relevante informatie op uit een kennisbank (dat is de "Retrieval"). Dan genereert hij een antwoord op basis van die opgehaalde info (dat is de "Augmented Generation"). Resultaat: het antwoord is gebaseerd op actuele, specifieke informatie — niet op wat het model ooit heeft geleerd. Dit is hoe je hallusinaties vermindert en accurate antwoorden krijgt over jouw specifieke codebase of bedrijf.',
      },
      {
        type: 'tip',
        title: '⚠️ Guardrails zijn niet optioneel in productie',
        text: 'In een demo werkt alles mooi. In productie zullen gebruikers de grenzen testen — bewust of onbewust. Definieer vanaf dag 1 je guardrails: welke acties vereisen menselijke goedkeuring? Welke data mag nooit worden verstuurd? Welke outputs zijn verboden? Governance is geen afterthought, het is architectuur.',
      },
    ],
  },
  {
    id: 'intelligence',
    icon: Brain,
    iconColor: 'text-emerald-400',
    badge: 'Laag 3',
    badgeColor: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    title: 'Intelligence Laag',
    subtitle: 'Denk, plan en voer uit — de modellen en agents die het werk doen',
    content: [
      {
        type: 'explainer',
        emoji: '🧠',
        title: 'Twee componenten: het model en de agent',
        text: 'De intelligence laag bestaat uit twee delen die samenwerken. Het AI Model is het "brein" — GPT-4, Claude of een open model dat taal begrijpt en genereert. De Agent is het "gedrag" — hij gebruikt dat brein om taken uit te voeren. Vergelijk het met een mens: het model is je intelligentie, de agent is de reden waarom je je intelligentie inzet. Zonder agent is een model een passieve vraag-antwoord machine. Met een agent wordt het een proactieve medewerker.',
      },
      {
        type: 'comparison',
        left: {
          title: '🤖 AI Modellen',
          color: 'border-emerald-500/30',
          items: [
            'GPT-4 / GPT-4.1 — krachtig, breed inzetbaar, Azure/OpenAI',
            'Claude — sterk in redenering, grote context window',
            'Open Models — Llama, Mistral, lokaal draaiend via Ollama',
            'Kies model op basis van: taak, privacy, kost, latency',
            'Mix van modellen is normaal in productie',
          ],
        },
        right: {
          title: '👥 Agent Types',
          color: 'border-violet-500/30',
          items: [
            'Planner Agent — breekt grote taken op in deelstappen',
            'Developer Agent — schrijft, reviewt en debugt code',
            'QA & Test Agent — genereert testcases en voert validaties uit',
            'Ops & Deploy Agent — bewaakt deployments en infrastructure',
            'Elke agent heeft zijn eigen skills, scope en grenzen',
          ],
        },
      },
      {
        type: 'heading',
        text: 'Welk model kies je wanneer?',
      },
      {
        type: 'list',
        items: [
          '🏋️ Complexe redenering & lange documenten → Claude (groot context window)',
          '⚡ Snelle, goedkope taken → GPT-4o-mini of Llama 3.1 8B lokaal',
          '🔒 Privacy-gevoelige data → open model lokaal via Ollama (data verlaat je server niet)',
          '💻 Code generatie & reviews → GPT-4.1, Claude of CodeLlama',
          '🌐 Multimodale taken (tekst + afbeeldingen) → GPT-4V of Claude 3.5 Sonnet',
        ],
      },
    ],
  },
  {
    id: 'actie',
    icon: Zap,
    iconColor: 'text-amber-400',
    badge: 'Laag 4',
    badgeColor: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    title: 'Actie & Integratie',
    subtitle: 'Doe het echte werk — AI die acties onderneemt in de echte wereld',
    content: [
      {
        type: 'explainer',
        emoji: '⚡',
        title: 'Van denken naar doen',
        text: 'Dit is waar AI ophoud te praten en begint te handelen. De actie laag koppelt de intelligence van agents aan echte systemen. Een agent die een PR aanmaakt, tests uitvoert, een Jira ticket bijwerkt en een deployment triggert — dat is de actie laag in werking. Het is ook de laag met het meeste risico: acties zijn onomkeerbaar, of toch moeilijk terug te draaien. Automatiseer hier stap voor stap en houd altijd menselijke oversight voor kritieke acties.',
      },
      {
        type: 'list',
        items: [
          '📝 PRs & Code aanmaken — agent schrijft code, opent een pull request, voegt beschrijving toe',
          '🧪 Tests uitvoeren & CI/CD — trigger pipelines, interpreteer resultaten, rapporteer falen',
          '📋 Issues & Docs updaten — Jira tickets bijwerken, Confluence documenteren, changelogs schrijven',
          '🚀 Deploy & Monitor — deployments triggeren, health checks uitvoeren, anomalieën detecteren',
          '📢 Berichten & Alerts sturen — Slack notificaties, e-mail rapporten, pagerduty alerts',
        ],
      },
      {
        type: 'tip',
        title: '🛡️ Human-in-the-Loop voor kritieke acties',
        text: 'Niet alles mag volledig geautomatiseerd zijn. Definieer welke acties altijd menselijke goedkeuring vereisen: productie deployments, grote data-wijzigingen, financiële transacties, klantcommunicatie. Bouw een approval flow in via Slack of e-mail. Automatie zonder oversight is geen automatie — het is een tijdbom.',
      },
    ],
  },
  {
    id: 'foundation',
    icon: Shield,
    iconColor: 'text-rose-400',
    badge: 'Fundament',
    badgeColor: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
    title: 'Foundation Laag',
    subtitle: 'Beveilig, beheer en schaal — de onzichtbare basis waarop alles rust',
    content: [
      {
        type: 'explainer',
        emoji: '🏗️',
        title: 'Waarom een foundation laag?',
        text: 'Een AI-systeem zonder fundament is als een gebouw zonder fundering — het ziet er goed uit totdat het instort. De foundation laag is wat je productie-klaar maakt: security zodat niet iedereen alles kan doen, observability zodat je problemen ziet vóór gebruikers dat doen, governance zodat je compliant blijft met privacywetgeving, en memory zodat agents context bewaren tussen sessies. Dit is de laag die de kloof overbrugt tussen "het werkt in een demo" en "het werkt in productie".',
      },
      {
        type: 'layergrid',
        layers: [
          {
            icon: '🔒',
            title: 'Security & Access',
            sub: 'SSO, RBAC, Permissions',
            items: ['Single Sign-On met Keycloak/Azure AD', 'Role-Based Access Control per agent', 'API key management en rotatie', 'Audit logs van elke AI-actie'],
            color: 'text-rose-400',
            bg: 'bg-rose-500/5 border-rose-500/20',
          },
          {
            icon: '📊',
            title: 'Observability',
            sub: 'Logs, Traces, Metrics',
            items: ['End-to-end tracing van agent calls', 'Token gebruik en kost monitoring', 'Latency en error rate dashboards', 'Alerts bij abnormaal gedrag'],
            color: 'text-blue-400',
            bg: 'bg-blue-500/5 border-blue-500/20',
          },
          {
            icon: '⭐',
            title: 'Evaluation & Quality',
            sub: 'Testing, Feedback, Evals',
            items: ['Geautomatiseerde eval suites', 'Human feedback loops', 'A/B testen van prompts', 'Regressie testen bij modelupgrades'],
            color: 'text-amber-400',
            bg: 'bg-amber-500/5 border-amber-500/20',
          },
          {
            icon: '🧠',
            title: 'Memory & Context',
            sub: 'Vector Store, History',
            items: ['Conversatiegeheugen per gebruiker', 'Lange-termijn kennisopslag', 'Semantische zoekindex', 'Context compressie voor grote sessies'],
            color: 'text-emerald-400',
            bg: 'bg-emerald-500/5 border-emerald-500/20',
          },
        ],
      },
      {
        type: 'explainer',
        emoji: '⚖️',
        title: 'Governance: GDPR en AI Act compliance',
        text: 'In België en Europa moet elk AI-systeem dat persoonsgegevens verwerkt voldoen aan GDPR. De aankomende EU AI Act voegt daar nog regels aan toe voor "high-risk" AI systemen. Praktisch: log elke AI-beslissing, bewaar niet meer data dan nodig, geef gebruikers inzage in wat de AI over hen weet, en documenteer je model keuzes. Dit klinkt zwaar, maar met de juiste architectuur van bij het begin is het beheersbaar.',
      },
    ],
  },
  {
    id: 'maturiteit',
    icon: TrendingUp,
    iconColor: 'text-green-400',
    badge: 'Groeipad',
    badgeColor: 'bg-green-500/20 text-green-400 border-green-500/30',
    title: 'AI Maturiteitsreis',
    subtitle: 'Stap voor stap van traditioneel werken naar zelfverbeterende AI-systemen',
    content: [
      {
        type: 'explainer',
        emoji: '🗺️',
        title: 'Rome is niet op één dag gebouwd — AI ook niet',
        text: 'De grootste fout die bedrijven maken? Ze willen meteen "Level 3" — volledig autonome AI. Dat werkt niet. Je bouwt vertrouwen op met stap. Je begint met kleine overwinningen: AI die je helpt navigeren. Dan AI die taken voor je doet onder toezicht. Dan AI die zelfstandig werkt met guardrails. En pas op het einde AI-systemen die zichzelf verbeteren. Elk niveau bouwt voort op het vorige. Sla een niveau over en je hebt een stabiliteitsprobleem.',
      },
      {
        type: 'maturity',
        levels: [
          {
            level: 'LEVEL 0',
            name: 'Waterfall / Agile',
            desc: 'Traditionele manier van werken. AI wordt sporadisch gebruikt voor productiviteitstips — Copilot, ChatGPT voor losse vragen. Geen gestructureerde AI integratie.',
            gain: 'Beperkt',
            color: 'text-slate-300',
            bg: 'bg-slate-700/30 border-slate-600/30',
          },
          {
            level: 'LEVEL 1',
            name: 'AI-Assisted',
            desc: 'AI helpt individuele medewerkers: navigeer code, schrijf documentatie, fix kleine bugs. Mensen blijven de leiding houden. Eerste echte productiviteitswinst.',
            gain: '5–20% efficiëntiewinst',
            color: 'text-blue-400',
            bg: 'bg-blue-500/10 border-blue-500/20',
          },
          {
            level: 'LEVEL 2',
            name: 'AI-Directed',
            desc: 'AI neemt autonome deeltaken over: genereert testcases, maakt PR-beschrijvingen, stuurt geautomatiseerde code reviews. Teams werken samen met AI als collega.',
            gain: '20–50% efficiëntiewinst',
            color: 'text-violet-400',
            bg: 'bg-violet-500/10 border-violet-500/20',
          },
          {
            level: 'LEVEL 3',
            name: 'AI-Delegated',
            desc: 'Volledige delivery pipelines draaien autonoom. AI schrijft, test, reviewt en deployt code. Self-improving systems leren van elke run. Mensen focussen op strategie en validatie.',
            gain: '200–1000%+ productiviteitswinst',
            color: 'text-green-400',
            bg: 'bg-green-500/10 border-green-500/20',
          },
        ],
      },
      {
        type: 'tip',
        title: '🎯 Waar ben je nu? Eerlijk zijn loont',
        text: 'Doe een eerlijke assessment: op welk level zit je team vandaag? De meeste Belgische KMOs zitten op Level 0-1. Dat is prima — het is het startpunt. Stel een realistisch doel: binnen 6 maanden naar Level 1, binnen een jaar naar Level 2. Probeer niet naar Level 3 te springen zonder de fundamenten van Level 1 en 2.',
      },
      {
        type: 'heading',
        text: 'Organisatorische enablers — wat maakt het verschil?',
      },
      {
        type: 'list',
        items: [
          '📏 Meet impact, niet lines of code — productiviteit in AI-era meten is anders dan klassiek',
          '🎓 Upskill iedereen, niet alleen developers — PMs, testers, analisten moeten AI kunnen gebruiken',
          '🔄 Nieuwe manieren van werken — agile aanpassen voor AI-assisted sprints',
          '🤝 Support & cultuur — AI faalt zonder buy-in van het team',
          '🧪 Leer door te doen — geen theorie zonder praktijk, start klein en itereer',
        ],
      },
    ],
  },
  {
    id: 'uitkomsten',
    icon: TrendingUp,
    iconColor: 'text-cyan-400',
    badge: 'Resultaten',
    badgeColor: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    title: 'Wat levert het op?',
    subtitle: 'Concrete uitkomsten van een volwassen AI-systeem architectuur',
    content: [
      {
        type: 'outcomegrid',
        outcomes: [
          {
            icon: '⚡',
            title: 'Hogere Productiviteit',
            desc: '20–500% efficiëntiewinst afhankelijk van het maturiteitsniveau. Van uren naar minuten voor routinetaken.',
            color: 'text-amber-400',
          },
          {
            icon: '🎯',
            title: 'Betere Kwaliteit',
            desc: 'Consistente code reviews, geautomatiseerde tests, en validatie zorgen voor minder bugs in productie.',
            color: 'text-green-400',
          },
          {
            icon: '🚀',
            title: 'Snellere Delivery',
            desc: 'Van idee naar productie in de helft van de tijd. AI elimineert bottlenecks in het delivery proces.',
            color: 'text-blue-400',
          },
          {
            icon: '🏢',
            title: 'AI-Ready Organisatie',
            desc: 'Teams die weten hoe ze AI inzetten, bouwen een duurzaam concurrentievoordeel op voor de lange termijn.',
            color: 'text-violet-400',
          },
        ],
      },
      {
        type: 'quote',
        text: 'AI is een systeem, geen tool. Data + Context + Workflows + Agents + Governance = echte waarde. — Kernboodschap van de Full AI System Architecture',
      },
      {
        type: 'explainer',
        emoji: '🎓',
        title: 'De weg vooruit voor jouw bedrijf',
        text: 'De bedrijven die nu investeren in de juiste AI-architectuur — met aandacht voor alle lagen van data tot governance — zijn de bedrijven die in 2026 en daarna het verschil maken. Niet de bedrijven die de duurste modellen kopen, maar de bedrijven die ze correct integreren in hun bestaande processen, met de juiste guardrails, observability en organisatorische enablers. Dat is wat "AI-ready" betekent.',
      },
    ],
  },
]

// ─── Content Renderer ─────────────────────────────────────────────────────────

function ContentRenderer({ blocks }: { blocks: ContentBlock[] }) {
  return (
    <div className="space-y-5">
      {blocks.map((block, i) => {
        if (block.type === 'paragraph') {
          return <p key={i} className="text-slate-300 text-sm sm:text-base leading-relaxed">{block.text}</p>
        }
        if (block.type === 'heading') {
          return <h3 key={i} className="text-white font-bold text-base sm:text-lg mt-2">{block.text}</h3>
        }
        if (block.type === 'list') {
          return (
            <ul key={i} className="space-y-2">
              {block.items.map((item, j) => (
                <li key={j} className="flex items-start gap-2 text-slate-300 text-sm leading-relaxed">
                  <span className="mt-0.5 shrink-0">{item.slice(0, 2)}</span>
                  <span>{item.slice(2)}</span>
                </li>
              ))}
            </ul>
          )
        }
        if (block.type === 'tip') {
          return (
            <div key={i} className="rounded-xl bg-blue-500/10 border border-blue-500/20 p-4">
              <p className="text-blue-300 text-sm font-semibold mb-1">{block.title}</p>
              <p className="text-slate-300 text-sm leading-relaxed">{block.text}</p>
            </div>
          )
        }
        if (block.type === 'explainer') {
          return (
            <div key={i} className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xl">{block.emoji}</span>
                <p className="text-amber-300 text-sm font-semibold">{block.title}</p>
              </div>
              <p className="text-slate-300 text-sm leading-relaxed">{block.text}</p>
            </div>
          )
        }
        if (block.type === 'quote') {
          return (
            <blockquote key={i} className="border-l-4 border-green-500/40 pl-4 py-2">
              <p className="text-slate-300 text-sm italic leading-relaxed">"{block.text}"</p>
            </blockquote>
          )
        }
        if (block.type === 'comparison') {
          return (
            <div key={i} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[block.left, block.right].map((side, j) => (
                <div key={j} className={`rounded-xl border p-4 ${side.color} bg-white/5`}>
                  <p className="text-white font-bold text-sm mb-3">{side.title}</p>
                  <ul className="space-y-2">
                    {side.items.map((item, k) => (
                      <li key={k} className="flex items-start gap-2 text-slate-300 text-xs leading-relaxed">
                        <ArrowRight className="w-3 h-3 mt-0.5 shrink-0 text-slate-500" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )
        }
        if (block.type === 'layergrid') {
          return (
            <div key={i} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {block.layers.map((layer, j) => (
                <div key={j} className={`rounded-xl border p-4 ${layer.bg}`}>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xl">{layer.icon}</span>
                    <div>
                      <p className={`font-bold text-sm ${layer.color}`}>{layer.title}</p>
                      <p className="text-slate-500 text-xs">{layer.sub}</p>
                    </div>
                  </div>
                  <ul className="space-y-1.5">
                    {layer.items.map((item, k) => (
                      <li key={k} className="flex items-center gap-2 text-slate-400 text-xs">
                        <span className="w-1 h-1 rounded-full bg-slate-600 shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )
        }
        if (block.type === 'maturity') {
          return (
            <div key={i} className="space-y-3">
              {block.levels.map((lvl, j) => (
                <div key={j} className={`rounded-xl border p-4 ${lvl.bg}`}>
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div>
                      <span className={`text-xs font-mono font-bold ${lvl.color}`}>{lvl.level}</span>
                      <p className="text-white font-bold text-sm">{lvl.name}</p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full bg-white/10 ${lvl.color} font-medium shrink-0`}>
                      {lvl.gain}
                    </span>
                  </div>
                  <p className="text-slate-400 text-xs leading-relaxed">{lvl.desc}</p>
                </div>
              ))}
            </div>
          )
        }
        if (block.type === 'outcomegrid') {
          return (
            <div key={i} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {block.outcomes.map((outcome, j) => (
                <div key={j} className="rounded-xl bg-white/5 border border-white/10 p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">{outcome.icon}</span>
                    <p className={`font-bold text-sm ${outcome.color}`}>{outcome.title}</p>
                  </div>
                  <p className="text-slate-400 text-xs leading-relaxed">{outcome.desc}</p>
                </div>
              ))}
            </div>
          )
        }
        return null
      })}
    </div>
  )
}

function SectionCard({ section, index }: { section: Section; index: number }) {
  const [open, setOpen] = useState(index === 0)
  const Icon = section.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.08 }}
    >
      <GlassCard className="overflow-hidden">
        <button
          onClick={() => setOpen(!open)}
          className="w-full flex items-center justify-between p-5 sm:p-6 text-left hover:bg-white/5 transition-colors"
          data-testid={`section-toggle-${section.id}`}
        >
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-white/5 to-white/10 border border-white/10 flex items-center justify-center shrink-0">
              <Icon className={`w-6 h-6 ${section.iconColor}`} />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${section.badgeColor}`}>
                  {section.badge}
                </span>
              </div>
              <h2 className="text-lg sm:text-xl font-bold text-white">{section.title}</h2>
              <p className="text-sm text-slate-400">{section.subtitle}</p>
            </div>
          </div>
          <ChevronDown className={`w-5 h-5 text-slate-400 transition-transform shrink-0 ${open ? 'rotate-180' : ''}`} />
        </button>

        <AnimatePresence initial={false}>
          {open && (
            <motion.div
              key="body"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="px-5 sm:px-6 pb-6 border-t border-white/10 pt-5">
                <ContentRenderer blocks={section.content} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </GlassCard>
    </motion.div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function AiSysteemArchitectuurPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">

      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center mb-10"
      >
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-sm font-medium mb-4">
          <Layers className="w-4 h-4" />
          Architectuurgids
        </div>
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white mb-4">
          Full AI{' '}
          <span className="bg-gradient-to-r from-violet-400 via-blue-400 to-emerald-400 bg-clip-text text-transparent">
            Systeem Architectuur
          </span>
        </h1>
        <p className="text-slate-400 text-lg max-w-2xl mx-auto leading-relaxed">
          Van data tot actie. Van Level 0 naar Level 3. Een complete gids over hoe je een
          AI-systeem bouwt dat schaalbaar, veilig en productie-klaar is.
        </p>
        <div className="mt-4 inline-flex items-center gap-2 text-sm text-slate-500">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          Gebaseerd op het Full AI System Architecture diagram
        </div>
      </motion.div>

      {/* Diagram */}
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="mb-12"
      >
        <GlassCard className="overflow-hidden p-2">
          <Image
            src="/ai-systeem-architectuur.png"
            alt="Full AI System Architecture diagram: Data & Context → Orchestration → Intelligence → Action & Integration → Outcomes, met Foundation Layer en Maturity Journey"
            width={1600}
            height={1200}
            className="rounded-lg w-full h-auto"
            priority
            data-testid="ai-systeem-architectuur-diagram"
          />
        </GlassCard>
        <p className="text-center text-xs text-slate-600 mt-2">
          "AI is een systeem, geen tool. Data + Context + Workflows + Agents + Governance = echte waarde."
        </p>
      </motion.div>

      {/* Navigatie overzicht */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-10">
        {sections.map((s) => (
          <a
            key={s.id}
            href={`#${s.id}`}
            onClick={(e) => { e.preventDefault(); document.getElementById(s.id)?.scrollIntoView({ behavior: 'smooth' }) }}
            className="rounded-xl bg-white/5 border border-white/10 p-3 text-center hover:bg-white/10 transition-colors cursor-pointer"
          >
            <span className={`text-xs font-medium ${s.iconColor}`}>{s.badge}</span>
            <p className="text-white text-xs font-semibold mt-1 leading-tight">{s.title}</p>
          </a>
        ))}
      </div>

      {/* Sections */}
      <div className="space-y-4">
        {sections.map((section, i) => (
          <div key={section.id} id={section.id}>
            <SectionCard section={section} index={i} />
          </div>
        ))}
      </div>

      {/* Back navigatie */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mt-12 text-center"
      >
        <Link href="/how-tos" className="inline-flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm">
          <ArrowRight className="w-4 h-4 rotate-180" />
          Terug naar alle how-tos
        </Link>
      </motion.div>
    </div>
  )
}
