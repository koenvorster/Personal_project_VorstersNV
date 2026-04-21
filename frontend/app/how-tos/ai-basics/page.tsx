'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronDown, ChevronRight, ArrowRight, Bot, BookOpen,
  Zap, Brain, Code2, Shield, Lightbulb, Terminal, GitBranch,
  CheckCircle, AlertCircle, Cpu, Search, Hash, Layers,
} from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'
import Image from 'next/image'

// ─── Types ────────────────────────────────────────────────────────────────────

type ContentBlock =
  | { type: 'paragraph'; text: string }
  | { type: 'heading'; text: string }
  | { type: 'subheading'; text: string }
  | { type: 'list'; items: string[] }
  | { type: 'code'; language: string; code: string }
  | { type: 'quote'; text: string }
  | { type: 'tip'; title: string; text: string }
  | { type: 'explainer'; emoji: string; title: string; text: string }
  | { type: 'termgrid'; terms: { icon: string; title: string; text: string }[] }
  | { type: 'workflow'; steps: { num: string; title: string; sub: string; color: string }[] }
  | { type: 'commandblock'; commands: { comment: string; cmd: string }[] }
  | { type: 'goldenrules'; rules: { icon: string; title: string; text: string }[] }
  | { type: 'prompttips'; tips: { icon: string; title: string; text: string }[] }
  | { type: 'agentgrid'; left: AgentGroup; right: AgentGroup }

interface AgentGroup {
  label: string
  sublabel: string
  color: string
  agents: { title: string; desc: string }[]
}

interface Section {
  id: string
  icon: typeof Bot
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
    id: 'terminologie',
    icon: BookOpen,
    iconColor: 'text-blue-400',
    badge: 'Stap 1',
    badgeColor: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    title: 'Terminologie: Wat is Wat?',
    subtitle: 'De basiswoorden die je moet kennen — zonder jargon uitgelegd',
    content: [
      {
        type: 'explainer',
        emoji: '📚',
        title: 'Waarom zijn deze termen belangrijk?',
        text: 'Als je met collega\'s, tools of documentatie werkt rond AI, zal je deze woorden constant tegenkomen. Ze zijn de bouwstenen van alle AI-gesprekken. Als je ze kent, snap je meteen waar iemand het over heeft — of het nu in een Teams-vergadering is, een GitHub issue, of een Jira ticket.',
      },
      {
        type: 'termgrid',
        terms: [
          {
            icon: '🤖',
            title: 'AI (Artificial Intelligence)',
            text: 'Slimme technologie die leert van data en taken kan uitvoeren die normaal menselijke intelligentie vereisen. Denk aan beeldherkenning, taalvertaling en aanbevelingssystemen.',
          },
          {
            icon: '✨',
            title: 'Generative AI',
            text: 'AI die nieuwe content maakt: tekst, code, afbeeldingen, tests of scenario\'s — op basis van jouw input (prompt). ChatGPT, Claude en Copilot zijn Generative AI tools.',
          },
          {
            icon: '💬',
            title: 'LLM (Large Language Model)',
            text: 'Een groot taalmodel dat taal begrijpt en genereert. GPT-4, Claude en Gemini zijn voorbeelden. Ze zijn getraind op enorme hoeveelheden tekst en kunnen daardoor "denken" in taal.',
          },
          {
            icon: '📝',
            title: 'Prompt',
            text: 'De instructie of vraag die jij aan de AI geeft. "Schrijf een test voor deze functie" is een prompt. Hoe beter en specifieker je prompt, hoe beter de output van de AI.',
          },
          {
            icon: '📦',
            title: 'Context',
            text: 'De informatie die je meestuurt samen met je prompt: requirements, code, testdata, screenshots. AI heeft geen geheugen — elke keer opnieuw moet je hem context geven om slimme antwoorden te krijgen.',
          },
          {
            icon: '🤖',
            title: 'AI Agent',
            text: 'Een gespecialiseerde rol die de AI speelt binnen een proces. Bijvoorbeeld: een Analyse Agent die user stories analyseert, of een Test Generator Agent die Cypress tests schrijft.',
          },
          {
            icon: '🔍',
            title: 'RAG (Retrieval Augmented Generation)',
            text: 'Een techniek waarbij de AI eerst informatie ophaalt uit jouw eigen data (repo, Confluence, Jira) en die gebruikt om betere, contextuele antwoorden te geven. Zo "kent" de AI jouw project.',
          },
          {
            icon: '🔢',
            title: 'Token',
            text: 'De kleinste stukjes tekst waarin een AI input verdeelt. "Hello world" = 2 tokens. Tokens bepalen de kosten (je betaalt per token) en de limieten (context window = max tokens tegelijk).',
          },
        ],
      },
      {
        type: 'tip',
        title: '💡 Snel overzicht: hoe hangen ze samen?',
        text: 'Jij schrijft een PROMPT met CONTEXT → een LLM (Generative AI) verwerkt die → een AI AGENT voert een taak uit → via RAG kan die agent jouw eigen data raadplegen → alles kost TOKENS.',
      },
    ],
  },
  {
    id: 'agents',
    icon: Bot,
    iconColor: 'text-violet-400',
    badge: 'Stap 2',
    badgeColor: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
    title: 'AI Agents & Gespecialiseerde Rollen',
    subtitle: 'Rovo Agents vs Copilot CLI Agents — wie doet wat?',
    content: [
      {
        type: 'explainer',
        emoji: '🎭',
        title: 'Agents als team: ieder zijn specialiteit',
        text: 'Eén AI die alles doet werkt minder goed dan een team van gespecialiseerde agents. Precies zoals in een echt software team: je hebt een business analist, een developer, een tester en een reviewer — elk met zijn eigen expertise. In AI-test automatisering heb je Rovo Agents (voor analyse & ontwerp) en Copilot CLI Agents (voor implementatie & review).',
      },
      {
        type: 'agentgrid',
        left: {
          label: 'ROVO AGENTS',
          sublabel: 'Test Design Layer',
          color: 'border-violet-500/40 bg-violet-500/5',
          agents: [
            { title: '🔍 Analyse Agent', desc: 'Begrijpt de user story, acceptatiecriteria en projectcontext. Zet vage requirements om in concrete testvereisten.' },
            { title: '📋 Test Design Agent', desc: 'Genereert testscenario\'s en testcases op basis van de analyse. Denkt aan happy paths, edge cases en negatieve scenario\'s.' },
          ],
        },
        right: {
          label: 'COPILOT CLI AGENTS',
          sublabel: 'Implementation Layer',
          color: 'border-blue-500/40 bg-blue-500/5',
          agents: [
            { title: '📄 Contract Agent', desc: 'Structureert en normaliseert de testcases naar een Test Contract (JSON) — de brug tussen design en implementatie.' },
            { title: '⚡ Test Generator Agent', desc: 'Bouwt de echte Cypress test code op basis van het contract. Genereert `test.cy.ts` bestanden.' },
            { title: '✅ Review Agent', desc: 'Controleert de gegenereerde tests op kwaliteit, volledigheid en correctheid. Vindt edge cases die gemist zijn.' },
          ],
        },
      },
      {
        type: 'explainer',
        emoji: '🔄',
        title: 'Hoe werken Rovo en Copilot samen?',
        text: 'Rovo agents draaien in Atlassian (Jira/Confluence) en zijn sterk in analyse en design — ze begrijpen tickets, user stories en acceptatiecriteria. Copilot CLI agents draaien in je terminal en zijn sterk in code generatie en review — ze schrijven echte Cypress tests. Samen vormen ze een volledige pipeline: van user story tot werkende, gereviewed test.',
      },
      {
        type: 'tip',
        title: '⚠️ Vergeet niet: AI is co-piloot, geen autopiloot',
        text: 'De agents genereren tests — maar jij moet ze reviewen en valideren. AI maakt fouten, mist domeinkennis of genereert edge cases die niet relevant zijn. Jij bent verantwoordelijk voor de kwaliteit, niet de AI.',
      },
    ],
  },
  {
    id: 'workflow',
    icon: GitBranch,
    iconColor: 'text-green-400',
    badge: 'Stap 3',
    badgeColor: 'bg-green-500/20 text-green-400 border-green-500/30',
    title: 'De AI Test Workflow',
    subtitle: 'Van Jira Story naar geautomatiseerde Cypress test in 4 stappen',
    content: [
      {
        type: 'explainer',
        emoji: '🗺️',
        title: 'De workflow in één zin',
        text: 'Je begint met een Jira Story (INPUT), Rovo ontwerpt het testplan (PLAN), Copilot CLI schrijft de code (BUILD), en CI/CD voert de tests automatisch uit bij elke commit (DEPLOY). Elke stap bouwt voort op de vorige — het is een geolied lopend band proces.',
      },
      {
        type: 'workflow',
        steps: [
          { num: '01', title: 'INPUT', sub: 'Jira Story · ACs & Context', color: 'bg-blue-600' },
          { num: '02', title: 'PLAN', sub: 'Test Design met Rovo', color: 'bg-violet-600' },
          { num: '03', title: 'BUILD', sub: 'Cypress Code met Copilot CLI', color: 'bg-green-600' },
          { num: '04', title: 'DEPLOY', sub: 'Uitvoering & CI/CD', color: 'bg-rose-600' },
        ],
      },
      {
        type: 'subheading',
        text: 'Stap 1 — INPUT: De Jira Story als startpunt',
      },
      {
        type: 'paragraph',
        text: 'Alles begint bij een goed geschreven Jira Story met duidelijke Acceptance Criteria (ACs). Hoe beter de story, hoe beter de AI-agents kunnen werken. Voeg altijd context toe: schermafdrukken, gebruikersrollen, randgevallen die je kent. De AI leest letterlijk wat je invult — garbage in, garbage out.',
      },
      {
        type: 'subheading',
        text: 'Stap 2 — PLAN: Rovo ontwerpt de tests',
      },
      {
        type: 'paragraph',
        text: 'De Rovo Analyse Agent leest de story en ACs. De Test Design Agent genereert vervolgens een reeks testscenario\'s: normale gevallen (happy path), foutgevallen (error handling), grensgevallen (edge cases) en performance scenario\'s. Dit is het "test design" — wat gaan we testen en hoe?',
      },
      {
        type: 'list',
        items: [
          'Test Case: een beschrijving van wat we testen — "Als gebruiker inlogt met fout wachtwoord, krijg hij een duidelijke foutmelding"',
          'Test Script / Test Code: de geautomatiseerde test in Cypress die die case uitvoert',
          'Test Contract: de gestandaardiseerde tussenlaag (JSON) tussen design en implementatie — Rovo genereert dit, Copilot leest het',
        ],
      },
      {
        type: 'subheading',
        text: 'Stap 3 — BUILD: Copilot CLI schrijft de code',
      },
      {
        type: 'paragraph',
        text: 'De Contract Agent normaliseert het design naar een Test Contract (JSON bestand). De Test Generator Agent zet dat contract om in echte Cypress test bestanden (`test.cy.ts`). De Review Agent controleert de kwaliteit en voegt ontbrekende edge cases toe. Je krijgt werkende Cypress tests zonder ze zelf volledig te schrijven.',
      },
      {
        type: 'subheading',
        text: 'Stap 4 — DEPLOY: CI/CD voert alles automatisch uit',
      },
      {
        type: 'paragraph',
        text: 'De gegenereerde tests landen in je repository. Bij elke commit of pull request draait CI/CD (GitHub Actions, Jenkins, etc.) de volledige test suite automatisch. Mislukt een test? Je krijgt meteen feedback. De Review & Feedback Loop zorgt dat AI reviewt, jij verbetert, en het systeem continu beter wordt.',
      },
      {
        type: 'tip',
        title: '🔁 CI/CD in gewoon Nederlands',
        text: 'CI/CD staat voor Continuous Integration / Continuous Deployment. Het is een systeem dat automatisch je code bouwt en test bij elke wijziging. "Geen enkel stuk code wordt gemerged zonder dat de tests groen zijn." Zo vangt het systeem fouten op vóór ze naar productie gaan.',
      },
    ],
  },
  {
    id: 'praktisch',
    icon: Terminal,
    iconColor: 'text-amber-400',
    badge: 'Stap 4',
    badgeColor: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    title: 'Prompting, Commands & Golden Rules',
    subtitle: 'Hoe je de AI het best aanstuurt — met quick commands en gouden regels',
    content: [
      {
        type: 'explainer',
        emoji: '🎯',
        title: 'Prompting is een vaardigheid die je kan leren',
        text: 'Een slechte prompt geeft een slechte output — maar dat is niet de schuld van de AI. Het schrijven van goede prompts (prompting) is een echte vaardigheid, zoals schrijven of communiceren. De vier tips hieronder zijn de meest impactvolle dingen die je kunt doen om de kwaliteit van AI-output drastisch te verbeteren.',
      },
      {
        type: 'prompttips',
        tips: [
          {
            icon: '✏️',
            title: 'Wees Specifiek',
            text: 'Geef duidelijke instructies en benoem wat je wel/niet wilt. "Schrijf een test" is slecht. "Schrijf een Cypress test voor het login-formulier, inclusief validatie bij leeg wachtwoord" is goed.',
          },
          {
            icon: '📦',
            title: 'Geef Context',
            text: 'Deel requirements, code, voorbeelden en structuur. Plak de user story erbij. Plak de bestaande code. Hoe meer relevante context, hoe beter de AI kan helpen.',
          },
          {
            icon: '</>',
            title: 'Gebruik Voorbeelden',
            text: 'Laat zien hoe je het verwacht. "Schrijf het zoals dit voorbeeld" werkt beter dan een lange beschrijving. AI leert van goede voorbeelden en kopieert de stijl en structuur.',
          },
          {
            icon: '🔄',
            title: 'Herbruik & Optimaliseer',
            text: 'Gebruik een promptbook en verbeter je prompts na elke iteratie. Sla goede prompts op als template. Na 3-5 iteraties heb je een prompt die consistent werkt.',
          },
        ],
      },
      {
        type: 'heading',
        text: 'Quick Commands (Copilot CLI)',
      },
      {
        type: 'explainer',
        emoji: '⌨️',
        title: 'Wat zijn deze "cg-" commando\'s?',
        text: 'De "cg-" commando\'s zijn gespecialiseerde Copilot CLI commando\'s voor test generatie. "cg" staat voor "copilot generate" (of een vergelijkbare afkorting in jouw setup). Je roept ze aan vanuit je terminal met een bestandsnaam als argument. Ze zijn de directe interface naar de Copilot CLI agents.',
      },
      {
        type: 'commandblock',
        commands: [
          { comment: '# Normaliseer requirements vanuit een Xray bestand', cmd: 'cg-normalize xray.txt' },
          { comment: '# Genereer een Test Contract (JSON) op basis van de requirements', cmd: 'cg-generate contract.json' },
          { comment: '# Review een bestaand Cypress test bestand op kwaliteit', cmd: 'cg-review test.cy.ts' },
          { comment: '# Voeg ontbrekende edge cases toe aan een bestaande story', cmd: 'cg-add-edges story.txt' },
          { comment: '# Fix een flaky (onstabiele) Cypress test automatisch', cmd: 'cg-fix-flaky test.cy.ts' },
        ],
      },
      {
        type: 'subheading',
        text: 'Tags voor tests: organiseer je test suite',
      },
      {
        type: 'paragraph',
        text: 'Tags zijn labels die je aan tests toevoegt om ze te categoriseren. In CI/CD kun je dan selectief alleen bepaalde tags draaien: enkel smoke tests bij een snelle check, de volledige regression suite bij een release.',
      },
      {
        type: 'list',
        items: [
          '🔵 smoke — snelle basischecks die bevestigen dat het systeem werkt (draai bij elke commit)',
          '🟣 regression — volledig regressiepakket om te controleren dat niets gebroken is (draai bij elke release)',
          '🔴 critical — testen die nooit mogen falen — betalingen, authenticatie, kernfunctionaliteit',
          '🟡 sprint-26 — sprint-specifieke tags om nieuwe features apart te kunnen testen',
          '🟠 feature-mapping — koppelt tests aan specifieke features voor traceability',
        ],
      },
      {
        type: 'heading',
        text: 'Golden Rules',
      },
      {
        type: 'goldenrules',
        rules: [
          {
            icon: '⚡',
            title: 'AI is een co-piloot, geen autopiloot',
            text: 'Jij blijft verantwoordelijk voor kwaliteit. Review altijd wat de AI genereert — het is een assistent, geen vervanger.',
          },
          {
            icon: '✅',
            title: 'Goede input = betere output',
            text: 'Investeer in context en sterke prompts. 5 minuten meer context geven bespaart 30 minuten slechte output corrigeren.',
          },
          {
            icon: '🧠',
            title: 'Werk met Agents',
            text: 'Verdeel het werk over gespecialiseerde agents. Eén agent die alles doet werkt minder goed dan een team van specialisten.',
          },
          {
            icon: '🔄',
            title: 'Review, leer, verbeter',
            text: 'Gebruik feedback om je prompts en tests continu te verbeteren. AI leert van jouw correcties — en jij leert van de AI.',
          },
        ],
      },
      {
        type: 'quote',
        text: 'De kracht van AI zit niet in één perfecte prompt, maar in een slimme workflow met structuur, review en samenwerking.',
      },
    ],
  },
]

// ─── Components ───────────────────────────────────────────────────────────────

function CodeBlock({ language, code }: { language: string; code: string }) {
  return (
    <div className="my-4 rounded-xl bg-slate-900 border border-white/10 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-white/5 border-b border-white/10">
        <span className="text-xs text-slate-400 font-mono">{language}</span>
      </div>
      <pre className="p-4 text-sm text-slate-300 font-mono overflow-x-auto leading-relaxed whitespace-pre">{code}</pre>
    </div>
  )
}

function TipBlock({ title, text }: { title: string; text: string }) {
  return (
    <div className="my-4 rounded-xl border border-blue-500/30 bg-blue-500/5 p-4">
      <div className="font-semibold text-blue-300 text-sm mb-1">{title}</div>
      <div className="text-slate-300 text-sm leading-relaxed">{text}</div>
    </div>
  )
}

function ExplainerBlock({ emoji, title, text }: { emoji: string; title: string; text: string }) {
  return (
    <div className="my-4 rounded-xl border border-amber-500/30 bg-amber-500/5 p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl">{emoji}</span>
        <div className="font-semibold text-amber-300 text-sm">{title}</div>
      </div>
      <div className="text-slate-300 text-sm leading-relaxed">{text}</div>
    </div>
  )
}

function TermGrid({ terms }: { terms: { icon: string; title: string; text: string }[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 my-4">
      {terms.map((t) => (
        <div key={t.title} className="rounded-xl border border-white/10 bg-white/3 p-4 flex gap-3">
          <div className="w-9 h-9 rounded-lg bg-blue-500/15 flex items-center justify-center text-lg shrink-0">{t.icon}</div>
          <div>
            <div className="font-semibold text-white text-sm mb-1">{t.title}</div>
            <div className="text-slate-400 text-xs leading-relaxed">{t.text}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

function WorkflowBlock({ steps }: { steps: { num: string; title: string; sub: string; color: string }[] }) {
  return (
    <div className="flex flex-col sm:flex-row gap-2 my-6">
      {steps.map((step, i) => (
        <div key={step.num} className="flex sm:flex-col items-center gap-3 sm:gap-2 flex-1">
          <div className={`rounded-xl ${step.color} p-4 text-white text-center flex-1 w-full`}>
            <div className="text-2xl font-black opacity-60 mb-1">{step.num}</div>
            <div className="font-bold text-sm">{step.title}</div>
            <div className="text-xs opacity-80 mt-1">{step.sub}</div>
          </div>
          {i < steps.length - 1 && (
            <ChevronRight className="w-4 h-4 text-slate-500 shrink-0 rotate-90 sm:rotate-0" />
          )}
        </div>
      ))}
    </div>
  )
}

function CommandBlock({ commands }: { commands: { comment: string; cmd: string }[] }) {
  return (
    <div className="my-4 rounded-xl bg-slate-900 border border-white/10 overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2 bg-white/5 border-b border-white/10">
        <div className="flex gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500/70" />
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500/70" />
          <span className="w-2.5 h-2.5 rounded-full bg-green-500/70" />
        </div>
        <span className="text-xs text-slate-400 font-mono ml-2">terminal</span>
      </div>
      <div className="p-4 space-y-2">
        {commands.map((c, i) => (
          <div key={i}>
            <div className="text-slate-500 text-xs font-mono">{c.comment}</div>
            <div className="text-green-400 text-sm font-mono font-semibold">{c.cmd}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function PromptTips({ tips }: { tips: { icon: string; title: string; text: string }[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 my-4">
      {tips.map((t) => (
        <div key={t.title} className="rounded-xl border border-violet-500/20 bg-violet-500/5 p-4">
          <div className="text-2xl mb-2">{t.icon}</div>
          <div className="font-bold text-white text-sm mb-1">{t.title}</div>
          <div className="text-slate-400 text-xs leading-relaxed">{t.text}</div>
        </div>
      ))}
    </div>
  )
}

function GoldenRules({ rules }: { rules: { icon: string; title: string; text: string }[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 my-4">
      {rules.map((r) => (
        <div key={r.title} className="rounded-xl border border-amber-500/20 bg-gradient-to-br from-amber-500/5 to-orange-500/5 p-4">
          <div className="text-2xl mb-2">{r.icon}</div>
          <div className="font-bold text-white text-sm mb-1">{r.title}</div>
          <div className="text-slate-400 text-xs leading-relaxed">{r.text}</div>
        </div>
      ))}
    </div>
  )
}

function AgentGrid({ left, right }: { left: AgentGroup; right: AgentGroup }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
      {[left, right].map((group) => (
        <div key={group.label} className={`rounded-xl border p-4 ${group.color}`}>
          <div className="font-bold text-white text-sm mb-0.5">{group.label}</div>
          <div className="text-xs text-slate-400 mb-3">{group.sublabel}</div>
          <div className="space-y-3">
            {group.agents.map((a) => (
              <div key={a.title} className="bg-white/5 rounded-lg p-3">
                <div className="font-semibold text-white text-xs mb-1">{a.title}</div>
                <div className="text-slate-400 text-xs leading-relaxed">{a.desc}</div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

function ContentRenderer({ blocks }: { blocks: ContentBlock[] }) {
  return (
    <div className="space-y-4">
      {blocks.map((block, i) => {
        if (block.type === 'paragraph') return <p key={i} className="text-slate-300 leading-relaxed">{block.text}</p>
        if (block.type === 'heading') return <h3 key={i} className="text-lg font-bold text-white mt-6 mb-2">{block.text}</h3>
        if (block.type === 'subheading') return <h4 key={i} className="text-base font-semibold text-slate-200 mt-5 mb-2">{block.text}</h4>
        if (block.type === 'list') return (
          <ul key={i} className="space-y-2">
            {block.items.map((item, j) => (
              <li key={j} className="flex gap-3 text-slate-300 text-sm">
                <ArrowRight className="w-4 h-4 text-slate-500 mt-0.5 shrink-0" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        )
        if (block.type === 'code') return <CodeBlock key={i} language={block.language} code={block.code} />
        if (block.type === 'quote') return (
          <blockquote key={i} className="border-l-4 border-amber-500 pl-4 py-1 my-4">
            <p className="text-slate-300 italic">{block.text}</p>
          </blockquote>
        )
        if (block.type === 'tip') return <TipBlock key={i} title={block.title} text={block.text} />
        if (block.type === 'explainer') return <ExplainerBlock key={i} emoji={block.emoji} title={block.title} text={block.text} />
        if (block.type === 'termgrid') return <TermGrid key={i} terms={block.terms} />
        if (block.type === 'workflow') return <WorkflowBlock key={i} steps={block.steps} />
        if (block.type === 'commandblock') return <CommandBlock key={i} commands={block.commands} />
        if (block.type === 'prompttips') return <PromptTips key={i} tips={block.tips} />
        if (block.type === 'goldenrules') return <GoldenRules key={i} rules={block.rules} />
        if (block.type === 'agentgrid') return <AgentGrid key={i} left={block.left} right={block.right} />
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
              <h2 className="text-xl font-bold text-white">{section.title}</h2>
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

export default function AIBasicsPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">

      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center mb-10"
      >
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-sm font-medium mb-4">
          <BookOpen className="w-4 h-4" />
          Beginnersgids · Niveau 0
        </div>
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white mb-4">
          AI Basis voor{' '}
          <span className="bg-gradient-to-r from-blue-400 via-violet-400 to-green-400 bg-clip-text text-transparent">
            IT Professionals
          </span>
        </h1>
        <p className="text-slate-400 text-lg max-w-2xl mx-auto leading-relaxed">
          Van "wat is een LLM?" tot een volledige AI test automatisering workflow — stap voor stap
          uitgelegd voor iedereen met een IT-achtergrond.
        </p>
      </motion.div>

      {/* Cheat Sheet Preview */}
      <motion.div
        initial={{ opacity: 0, scale: 0.97 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="mb-10"
      >
        <GlassCard className="p-5">
          <div className="flex items-start gap-4 mb-4">
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center shrink-0">
              <Layers className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <div className="font-bold text-white text-sm">Cheat Sheet: AI Test Automatisering</div>
              <div className="text-xs text-slate-400 mt-0.5">Jouw snelle gids naar AI gedreven testen met Rovo, Copilot CLI & Cypress — alle termen op één pagina</div>
            </div>
          </div>
          <div className="rounded-xl overflow-hidden border border-white/10">
            <Image
              src="/ai-test-cheatsheet.png"
              alt="AI Test Automatisering Cheat Sheet — terminologie, agents, workflow, commands en golden rules"
              width={900}
              height={1270}
              className="w-full h-auto"
              priority
            />
          </div>
          <p className="text-xs text-slate-500 text-center mt-3">
            👆 De volledige gids hieronder legt elk onderdeel van deze cheat sheet in detail uit
          </p>
        </GlassCard>
      </motion.div>

      {/* Voor wie? banner */}
      <div className="mb-8 rounded-2xl border border-white/10 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
        <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
          <span className="text-lg">👥</span> Voor wie is deze gids?
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-xl bg-green-500/10 border border-green-500/20 p-4">
            <div className="text-green-400 font-semibold text-sm mb-2">✅ Perfect als je...</div>
            <ul className="space-y-1.5 text-xs text-slate-300">
              <li>• Werkt in IT maar weinig met AI hebt gedaan</li>
              <li>• De termen hoort maar niet goed begrijpt</li>
              <li>• Wil starten met AI test automatisering</li>
              <li>• De cheat sheet wil begrijpen</li>
            </ul>
          </div>
          <div className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-4">
            <div className="text-amber-400 font-semibold text-sm mb-2">⚡ Wat je leert</div>
            <ul className="space-y-1.5 text-xs text-slate-300">
              <li>• 8 essentiële AI termen (AI, LLM, RAG...)</li>
              <li>• Hoe Rovo en Copilot samenwerken</li>
              <li>• De volledige test workflow stap voor stap</li>
              <li>• Prompting tips & gouden regels</li>
            </ul>
          </div>
          <div className="rounded-xl bg-violet-500/10 border border-violet-500/20 p-4">
            <div className="text-violet-400 font-semibold text-sm mb-2">📖 Daarna lees je...</div>
            <ul className="space-y-1.5 text-xs text-slate-300">
              <li>• <a href="/how-tos" className="underline hover:text-white">Gids 1: Skills · Agents · Sub-agents</a></li>
              <li>• <a href="/how-tos/claude-copilot" className="underline hover:text-white">Gids 2: Claude · Copilot · MCP</a></li>
              <li>• <a href="/blog" className="underline hover:text-white">Blog: Rovo Agents in je dev team</a></li>
              <li>• 🟡 Amber = menselijke taal, 🔵 Blauw = tips</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Nav pills */}
      <div className="flex items-center justify-center gap-2 mb-8 flex-wrap">
        {sections.map((s, i) => {
          const Icon = s.icon
          return (
            <div key={s.id} className="flex items-center gap-2">
              <button
                onClick={() => document.getElementById(`section-${s.id}`)?.scrollIntoView({ behavior: 'smooth' })}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-colors hover:bg-white/10 ${s.badgeColor}`}
              >
                <Icon className="w-3.5 h-3.5" />
                {s.title.split(':')[0]}
              </button>
              {i < sections.length - 1 && <ChevronRight className="w-4 h-4 text-slate-600" />}
            </div>
          )
        })}
      </div>

      {/* Back link */}
      <div className="mb-6">
        <a href="/how-tos" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors">
          <ChevronRight className="w-4 h-4 rotate-180" />
          Terug naar How-to's overzicht
        </a>
      </div>

      {/* Sections */}
      <div className="space-y-4">
        {sections.map((section, i) => (
          <div key={section.id} id={`section-${section.id}`}>
            <SectionCard section={section} index={i} />
          </div>
        ))}
      </div>

      {/* Footer CTA */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mt-12 text-center"
      >
        <GlassCard className="p-8">
          <div className="text-3xl mb-3">🚀</div>
          <h3 className="text-xl font-bold text-white mb-2">Klaar voor de volgende stap?</h3>
          <p className="text-slate-400 text-sm mb-6 max-w-md mx-auto">
            Nu je de basisconcepten kent, ga je dieper in op hoe agents echt werken en hoe je ze zelf bouwt.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <a
              href="/how-tos"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold transition-colors"
            >
              <ArrowRight className="w-4 h-4" />
              Gids 1: Skills & Agents
            </a>
            <a
              href="/how-tos/claude-copilot"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-white/20 hover:bg-white/10 text-white text-sm font-semibold transition-colors"
            >
              <ArrowRight className="w-4 h-4" />
              Gids 2: Claude & Copilot
            </a>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  )
}
