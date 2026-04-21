'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Bot, Cpu, GitBranch, Layers, ChevronDown, ChevronRight,
  Zap, Brain, Network, Code2, ArrowRight, BookOpen, Play,
  Shield, Settings, Terminal, Workflow, Webhook, Puzzle, ExternalLink,
} from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'

// ─── Types ────────────────────────────────────────────────────────────────────

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

type ContentBlock =
  | { type: 'paragraph'; text: string }
  | { type: 'heading'; text: string }
  | { type: 'subheading'; text: string }
  | { type: 'list'; items: string[] }
  | { type: 'code'; language: string; code: string }
  | { type: 'quote'; text: string }
  | { type: 'diagram'; nodes: DiagramNode[]; connections: DiagramConnection[] }
  | { type: 'comparison'; left: ComparisonSide; right: ComparisonSide }
  | { type: 'tip'; title: string; text: string }
  | { type: 'explainer'; emoji: string; title: string; text: string }
  | { type: 'steps'; items: { step: string; title: string; text: string }[] }
  | { type: 'prerequisite'; items: string[] }

interface DiagramNode { id: string; label: string; sub?: string; color: string }
interface DiagramConnection { from: string; to: string; label?: string }
interface ComparisonSide { title: string; color: string; items: string[] }

// ─── Content ──────────────────────────────────────────────────────────────────

const sections: Section[] = [
  {
    id: 'skills',
    icon: Zap,
    iconColor: 'text-amber-400',
    badge: 'Niveau 1',
    badgeColor: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    title: 'Skills',
    subtitle: 'De bouwstenen — wat een agent kan doen',
    content: [
      {
        type: 'explainer',
        emoji: '🔧',
        title: 'In gewoon Nederlands: wat is een skill?',
        text: 'Stel je voor: je hebt een slimme assistent aangenomen. Die assistent is intelligent, maar weet nog niet hoe hij jouw systemen moet gebruiken. Een skill is als een handleiding die je hem geeft: "Als je een e-mail wilt sturen, doe dat zo." Of: "Als je een ticket in Jira wilt opzoeken, gebruik dan deze methode." Skills zijn de specifieke acties die je de AI leert uitvoeren — vergelijkbaar met macro\'s in Excel of sneltoetsen, maar dan voor een AI-agent. Zonder skills kan een AI enkel praten. Mét skills kan hij dingen doen.',
      },
      {
        type: 'prerequisite',
        items: [
          'Basiskennis van wat een API is (een koppeling tussen systemen via het internet)',
          'Je hoeft geen Python te kennen om dit te begrijpen — de code-voorbeelden zijn ter illustratie',
          'Het concept "functie" uit programmeren: iets wat je aanroept met parameters en een resultaat teruggeeft',
        ],
      },
      {
        type: 'paragraph',
        text: 'Een skill is de kleinste eenheid van een AI-systeem: één specifieke, afgebakende actie die een agent kan uitvoeren. Denk aan een moersleutel in een gereedschapskist — hij doet precies één ding, maar doet dat perfect. Skills zijn herbruikbaar, testbaar en composeerbaar.',
      },
      {
        type: 'heading',
        text: 'Wat is een skill precies?',
      },
      {
        type: 'paragraph',
        text: 'Een skill heeft altijd drie componenten: een naam die beschrijft wat hij doet, een duidelijke input-definitie (welke parameters verwacht hij?), en een output-definitie (wat geeft hij terug?). Achter de schermen is een skill niets meer dan een functie — maar een functie die door een AI-agent kan worden aangeroepen op het juiste moment.',
      },
      {
        type: 'list',
        items: [
          '📧 send_email(to, subject, body) — verstuurt een e-mail via de geconfigureerde SMTP server',
          '🔍 search_jira(query, project) — zoekt issues op in Jira en geeft een gestructureerde lijst terug',
          '📊 fetch_analytics(metric, date_range) — haalt data op uit een analytics API',
          '✍️  generate_text(prompt, tone, max_tokens) — genereert tekst via een LLM-model',
          '🗄️  query_database(sql_query) — voert een veilige, read-only query uit op de databank',
          '📸 analyse_image(image_url) — analyseert een afbeelding via een vision model',
        ],
      },
      {
        type: 'code',
        language: 'python',
        code: `# Voorbeeld: een skill definiëren in Python (FastAPI + LangChain stijl)
from langchain.tools import tool
from pydantic import BaseModel

class JiraSearchInput(BaseModel):
    query: str
    project: str = "PROJ"
    max_results: int = 10

@tool("search_jira", args_schema=JiraSearchInput)
def search_jira(query: str, project: str = "PROJ", max_results: int = 10) -> list[dict]:
    """
    Zoekt Jira issues op basis van een zoekterm.
    Geeft een lijst terug van matching issues met titel, status en assignee.
    Gebruik dit wanneer je informatie nodig hebt over tickets, bugs of taken.
    """
    results = jira_client.search_issues(
        f'project = {project} AND text ~ "{query}"',
        maxResults=max_results
    )
    return [
        {"key": i.key, "title": i.fields.summary,
         "status": i.fields.status.name, "assignee": str(i.fields.assignee)}
        for i in results
    ]`,
      },
      {
        type: 'tip',
        title: '💡 Gouden regel voor skills',
        text: 'Een goede skill doet precies één ding. Als je een skill "search_and_summarize_and_send" wilt noemen, split hem dan op in drie aparte skills. Compositie is de taak van de agent, niet van de skill zelf.',
      },
      {
        type: 'explainer',
        emoji: '📦',
        title: 'Waarom dit schema-gedoe?',
        text: 'De code gebruikt "input schema" — een definitie van welke parameters de skill verwacht. Dat is nodig zodat de AI weet hoe hij de skill correct moet aanroepen. Vergelijk het met een formulier op een website: het formulier definieert welke velden verplicht zijn en welk formaat je mag invullen. Zonder schema zou de AI kunnen proberen een skill aan te roepen met foute of ontbrekende parameters.',
      },
      {
        type: 'heading',
        text: 'Skills categorieën',
      },
      {
        type: 'list',
        items: [
          'Lees-skills: ophalen van data uit APIs, databases, bestanden of externe services',
          'Schrijf-skills: aanmaken, updaten of verwijderen van resources — altijd goed bewaken met guardrails',
          'Transformatie-skills: data omzetten, samenvatten, vertalen of herformatteren',
          'Communicatie-skills: e-mails versturen, Slack berichten posten, tickets aanmaken',
          'Analyse-skills: berekeningen uitvoeren, patronen herkennen, rapporten genereren',
          'Orchestratie-skills: andere agents of workflows triggeren (de brug naar sub-agents)',
        ],
      },
      {
        type: 'quote',
        text: 'Skills zijn de vocabulaire van je AI-systeem. Hoe rijker en preciezer je vocabulaire, hoe intelligenter je agent kan communiceren met de wereld.',
      },
    ],
  },
  {
    id: 'agents',
    icon: Bot,
    iconColor: 'text-blue-400',
    badge: 'Niveau 2',
    badgeColor: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    title: 'Agents',
    subtitle: 'De denkers — intelligentie met tools',
    content: [
      {
        type: 'explainer',
        emoji: '🧑‍💼',
        title: 'In gewoon Nederlands: wat is een agent?',
        text: 'Een agent is als een nieuwe medewerker op jouw IT-afdeling. Je geeft hem een takenpakket (zijn skills/tools), een functieomschrijving (zijn system prompt), en een opdracht. Daarna lost hij die opdracht zelfstandig op — hij beslist zelf in welke volgorde hij zijn tools gebruikt, en past zijn plan aan als iets niet werkt. Je hoeft hem niet stap voor stap te begeleiden. Het grote verschil met een gewone chatbot: een chatbot antwoordt enkel op vragen, een agent onderneemt actie in de echte wereld.',
      },
      {
        type: 'paragraph',
        text: 'Een agent is een AI die een doel kan bereiken door zelf te beslissen welke skills hij wanneer gebruikt. Hij krijgt een instructieset (system prompt), een set beschikbare skills (tools), en een doel. Daarna werkt hij autonoom — hij plant, voert uit, evalueert het resultaat, en past zijn aanpak aan indien nodig.',
      },
      {
        type: 'heading',
        text: 'Hoe werkt een agent intern?',
      },
      {
        type: 'explainer',
        emoji: '🔄',
        title: 'De ReAct-loop uitgelegd zonder jargon',
        text: 'ReAct staat voor "Reason + Act". De agent denkt hardop na (Reason), doet dan iets (Act), kijkt wat er is gebeurd (Observe), en herhaalt dit totdat hij klaar is. Het is exact wat jij doet als je een probleem oplost: je denkt na wat de eerste stap is, probeert het, kijkt of het werkt, en past je aan. Het verschil: een agent doet dit in seconden en kan tientallen stappen uitvoeren zonder moe te worden.',
      },
      {
        type: 'paragraph',
        text: 'De meeste moderne agents werken via de ReAct-loop (Reason + Act). De agent denkt eerst na over wat hij moet doen (Reason), voert dan een actie uit via een skill (Act), observeert het resultaat (Observe), en herhaalt dit totdat het doel bereikt is. Dit is fundamenteel anders dan een simpele chatbot die enkel antwoordt op input.',
      },
      {
        type: 'code',
        language: 'text',
        code: `// ReAct loop voorbeeld — een agent lost een taak op:

TAAK: "Schrijf een samenvatting van alle openstaande bugs in PROJ en stuur die naar slack"

Stap 1 — REASON:
  "Ik moet eerst de openstaande bugs ophalen uit Jira voordat ik iets kan samenvatten"

Stap 2 — ACT:
  → skill: search_jira(query="type=Bug AND status=Open", project="PROJ")

Stap 3 — OBSERVE:
  → resultaat: 14 bugs gevonden, diverse priorities

Stap 4 — REASON:
  "Ik heb de data. Nu moet ik een leesbare samenvatting schrijven per priority"

Stap 5 — ACT:
  → skill: generate_text(prompt="Vat deze 14 bugs samen per priority...", tone="professioneel")

Stap 6 — OBSERVE:
  → samenvatting gegenereerd (450 woorden)

Stap 7 — REASON:
  "Samenvatting is klaar. Nu versturen naar Slack #dev-updates"

Stap 8 — ACT:
  → skill: send_slack_message(channel="#dev-updates", message=samenvatting)

Stap 9 — OBSERVE:
  → bericht succesvol verstuurd

Stap 10 — REASON:
  "Taak voltooid. Geen verdere acties nodig."
  → DONE`,
      },
      {
        type: 'heading',
        text: 'De anatomie van een goede agent prompt',
      },
      {
        type: 'paragraph',
        text: 'De system prompt is het hart van elke agent. Een slecht geschreven system prompt leidt tot inconsistent gedrag, hallucinaties of een agent die buiten zijn bevoegdheid treedt. Een goede system prompt heeft altijd vijf elementen:',
      },
      {
        type: 'list',
        items: [
          '1. IDENTITEIT — wie is de agent, wat is zijn expertise en perspectief?',
          '2. DOEL — wat is zijn primaire taak? Eén zin, helder en concreet',
          '3. BESCHIKBARE TOOLS — welke skills mag hij gebruiken en wanneer?',
          '4. GRENZEN — wat mag hij NIET doen? Dit is kritisch voor veiligheid',
          '5. OUTPUT FORMAT — hoe ziet het eindresultaat er uit?',
        ],
      },
      {
        type: 'code',
        language: 'text',
        code: `// Voorbeeld: goed geconfigureerde agent system prompt

IDENTITEIT:
Je bent een Senior Code Review Agent voor het VorstersNV development team.
Je hebt expertise in Python, FastAPI, TypeScript en Next.js.
Je denkt als een ervaren tech lead die kwaliteit en veiligheid centraal stelt.

DOEL:
Analyseer pull requests en geef constructieve, actionable feedback die
de codekwaliteit verbetert zonder de developer te ontmoedigen.

BESCHIKBARE TOOLS:
- fetch_pr_diff: haal de code wijzigingen op van een PR
- search_confluence: zoek naar coding guidelines en best practices
- search_jira: zoek de gekoppelde ticket om context te begrijpen
- post_pr_comment: plaats een comment op de PR
- request_changes / approve_pr: zet de review status

GRENZEN:
- Merge nooit zelf een PR — geef altijd review feedback en laat de developer beslissen
- Stel nooit meer dan 5 kritieke opmerkingen per PR — prioriteer de belangrijkste
- Ga nooit verder dan de aangeleverde codebase — speculeer niet over externe systemen
- Wijs altijd naar de relevante Confluence guideline als die bestaat

OUTPUT FORMAT:
Geef feedback in deze vaste structuur:
1. Samenvatting (2-3 zinnen)
2. Kritieke issues (blokkeren merge): max 5 bullets
3. Suggesties (nice-to-have): max 5 bullets
4. Positieve punten: min 1 (altijd iets positiefs benoemen)
5. Beslissing: REQUEST_CHANGES of APPROVE`,
      },
      {
        type: 'tip',
        title: '⚠️ Veelgemaakte fout',
        text: 'Agents die te veel mogen doen zijn gevaarlijk. Begin altijd met een agent die alleen leest (read-only skills). Voeg schrijfrechten pas toe als je het gedrag volledig begrijpt en getest hebt. Een "oeps, per ongeluk alle issues gesloten" is niet gemakkelijk terug te draaien.',
      },
      {
        type: 'explainer',
        emoji: '📝',
        title: 'De system prompt: het functiedossier van je agent',
        text: 'Een system prompt is de tekst die je aan de AI meegeeft vóór hij begint met werken. Het is zijn functiebeschrijving, zijn werkwijze, en zijn gedragsregels tegelijk. Een slechte system prompt is als een medewerker aanwerven zonder hem te vertellen wat zijn job is. Hij zal wel iets doen, maar waarschijnlijk niet wat jij wilt. De vijf elementen (Identiteit, Doel, Tools, Grenzen, Output) zorgen dat de agent altijd weet: wie ben ik, wat moet ik doen, hoe doe ik het, wat is verboden, en hoe ziet het resultaat eruit.',
      },
      {
        type: 'heading',
        text: 'Agent types: wanneer gebruik je welke?',
      },
      {
        type: 'comparison',
        left: {
          title: '🔁 Reactive Agent',
          color: 'border-blue-500/30',
          items: [
            'Reageert op triggers (webhook, schedule, user input)',
            'Lineair: stap 1 → 2 → 3 → klaar',
            'Voorspelbaar en makkelijk te debuggen',
            'Ideaal voor: notificaties, rapporten, eenvoudige workflows',
            'Voorbeeld: "bij nieuw ticket → analyseer → stuur samenvatting"',
          ],
        },
        right: {
          title: '🧠 Autonomous Agent',
          color: 'border-violet-500/30',
          items: [
            'Plant zelfstandig meerdere stappen vooruit',
            'Kan teruggaan als een stap faalt',
            'Moeilijker te debuggen — vereist goede logging',
            'Ideaal voor: complexe analyses, multi-step onderzoek',
            'Voorbeeld: "analyseer alle techdebt en maak een prioriteitstabel"',
          ],
        },
      },
    ],
  },
  {
    id: 'subagents',
    icon: Network,
    iconColor: 'text-violet-400',
    badge: 'Niveau 3',
    badgeColor: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
    title: 'Sub-agents',
    subtitle: 'De specialisten — agents die agents aansturen',
    content: [
      {
        type: 'explainer',
        emoji: '🏗️',
        title: 'In gewoon Nederlands: waarom sub-agents?',
        text: 'Stel: je vraagt een projectmanager om een sprint-rapport te maken. Die PM gaat niet zelf alle data ophalen, alle code reviewen, én het rapport schrijven — hij verdeelt het werk. Hij vraagt één collega om de sprint-cijfers, een andere om de code-kwaliteit, en een derde om het rapport te schrijven. Sub-agents zijn die collega\'s: gespecialiseerde helpers die de hoofdagent (de orchestrator) inzet voor deeltaken. Resultaat: sneller, beter, en elke specialist kan onafhankelijk worden getest en verbeterd.',
      },
      {
        type: 'paragraph',
        text: 'Sub-agents zijn agents die door een andere agent (de orchestrator) worden aangestuurd om een deeltaak uit te voeren. Net zoals een manager zijn team inzet voor specifieke taken, delegeert een orchestrator agent complexe deeltaken aan gespecialiseerde sub-agents. Elke sub-agent is expert in zijn eigen domein.',
      },
      {
        type: 'heading',
        text: 'Waarom sub-agents?',
      },
      {
        type: 'explainer',
        emoji: '🧠',
        title: 'Wat is een "context window" en waarom is dat belangrijk?',
        text: 'Een AI-model kan maar een bepaalde hoeveelheid tekst "in zijn hoofd" houden tegelijk — dat is het context window. Vergelijk het met werkgeheugen bij mensen: je kunt niet aan 20 dingen tegelijk denken. Als één agent alles moet doen, raakt zijn context snel vol en verliest hij de focus of maakt fouten. Sub-agents lossen dit op: elke agent heeft zijn eigen, kleine context met alleen de informatie die hij nodig heeft voor zijn specifieke deeltaak.',
      },
      {
        type: 'paragraph',
        text: 'Één agent die alles doet is eindig in wat hij kan. Een context window heeft limieten. Een LLM verliest focus bij te brede instructies. Sub-agents lossen dit op: elke agent heeft een kleine, scherpe focus, zijn eigen context, en zijn eigen set skills. De orchestrator coördineert — de sub-agents specialiseren.',
      },
      {
        type: 'code',
        language: 'python',
        code: `# Orchestrator + sub-agents patroon (LangGraph stijl)
from langgraph.graph import StateGraph, END
from agents import (
    RequirementsAgent,  # analyseert tickets en specs
    CodeReviewAgent,    # beoordeelt code kwaliteit
    SecurityAgent,      # scant op security issues
    DocumentationAgent, # genereert/update documentatie
    NotificationAgent,  # communiceert resultaten
)

class PRAnalysisOrchestrator:
    """
    Orchestrator die een complete PR-analyse uitvoert
    door 4 gespecialiseerde sub-agents parallel te draaien
    en hun resultaten te consolideren.
    """

    def analyse_pr(self, pr_number: int) -> dict:
        pr_data = self.fetch_pr(pr_number)

        # Stap 1: parallel analyse door 3 sub-agents
        results = self.run_parallel([
            RequirementsAgent().check(pr_data),   # doet ticket aan code matchen
            CodeReviewAgent().review(pr_data),     # beoordeelt code stijl + logica
            SecurityAgent().scan(pr_data),         # scant op OWASP top 10
        ])

        # Stap 2: documentatie-agent als er wijzigingen nodig zijn
        if results["code_review"].has_api_changes:
            results["docs"] = DocumentationAgent().update(pr_data)

        # Stap 3: consolideer en communiceer
        summary = self.consolidate(results)
        NotificationAgent().notify(pr_number, summary)

        return summary`,
      },
      {
        type: 'heading',
        text: 'Orchestratie patronen',
      },
      {
        type: 'list',
        items: [
          '🔀 Parallel — meerdere sub-agents werken tegelijk aan onafhankelijke deeltaken (snelste aanpak)',
          '🔗 Sequentieel — sub-agent B krijgt de output van sub-agent A als input (gebruik bij afhankelijkheden)',
          '🌳 Hierarchisch — orchestrator → sub-orchestrators → sub-agents (voor zeer complexe pipelines)',
          '🗳️ Voting — meerdere agents analyseren hetzelfde en de meerderheid wint (voor kritieke beslissingen)',
          '🔄 Iteratief — een evaluatie-agent beoordeelt de output en triggert nieuwe iteraties tot de kwaliteitsdrempel gehaald is',
        ],
      },
      {
        type: 'subheading',
        text: 'Praktisch voorbeeld: Sprint Analyse Pipeline',
      },
      {
        type: 'code',
        language: 'text',
        code: `// Sprint Analyse Orchestrator — 5 sub-agents samenwerken

ORCHESTRATOR: "Analyseer sprint 42 en genereer een volledig rapport"

├── SUB-AGENT 1: VelocityAgent (parallel)
│   Skills: fetch_jira_sprint, calculate_velocity, compare_historical
│   Output: velocity rapport + trend grafiek data
│
├── SUB-AGENT 2: QualityAgent (parallel)
│   Skills: fetch_merged_prs, analyse_code_review_comments, count_bugs_introduced
│   Output: code kwaliteitsrapport
│
├── SUB-AGENT 3: ImpedimentAgent (parallel)
│   Skills: fetch_blocked_issues, analyse_block_reasons, calculate_block_time
│   Output: impediment analyse + top 3 oorzaken
│
├── SUB-AGENT 4: SentimentAgent (parallel)
│   Skills: fetch_standup_notes, fetch_retro_comments, analyse_sentiment
│   Output: team gezondheids-score
│
└── SUB-AGENT 5: ReportAgent (sequentieel — wacht op 1-4)
    Input: outputs van alle vorige agents
    Skills: generate_text, create_confluence_page, send_slack_summary
    Output: volledig rapport op Confluence + samenvatting in Slack

TOTALE DOORLOOPTIJD: ~45 seconden (vs 3-4 uur handmatig)`,
      },
      {
        type: 'tip',
        title: '🎯 Design principe: "Single Responsibility"',
        text: 'Elke sub-agent heeft één verantwoordelijkheid. Een VelocityAgent meet snelheid — hij schrijft geen rapporten. Een ReportAgent schrijft rapporten — hij haalt geen data op. Dit maakt elke agent onafhankelijk testbaar en vervangbaar zonder het geheel te breken.',
      },
      {
        type: 'heading',
        text: 'Sub-agent communicatie: hoe praten agents met elkaar?',
      },
      {
        type: 'list',
        items: [
          'Shared State — alle agents lezen en schrijven naar een gedeeld state-object (eenvoudig maar let op race conditions)',
          'Message Passing — agents sturen berichten naar een queue, de volgende agent pikt die op (asynchroon en schaalbaar)',
          'Direct Function Call — de orchestrator roept sub-agents aan als functies en wacht op het resultaat (synchroon, eenvoudig te debuggen)',
          'Event Bus — agents publiceren events en andere agents abonneren zich erop (het MQTT-principe, ideaal voor losse koppeling)',
        ],
      },
      {
        type: 'quote',
        text: 'Sub-agents zijn het moment waarop AI echt krachtig wordt. Eén agent is handig. Een goed georkestreerd netwerk van agents is een autonomous workforce.',
      },
    ],
  },
  {
    id: 'orchestratie',
    icon: Workflow,
    iconColor: 'text-green-400',
    badge: 'Niveau 4',
    badgeColor: 'bg-green-500/20 text-green-400 border-green-500/30',
    title: 'Orchestratie & Governance',
    subtitle: 'De regisseur — controle over het geheel',
    content: [
      {
        type: 'explainer',
        emoji: '🎭',
        title: 'In gewoon Nederlands: wat is governance bij AI?',
        text: 'Nu je teams van agents hebt die samenwerken, heb je ook verkeersregels nodig. Wie mag wat beslissen? Hoe voorkom je dat een agent per ongeluk klantdata verwijdert of een factuur dubbel verstuurt? Governance is het geheel aan regels, limieten en controles dat ervoor zorgt dat je AI-agents betrouwbaar, veilig en controleerbaar werken — ook als je honderden taken per dag automatiseert. Zie het als het arbeidsreglement voor je AI-medewerkers.',
      },
      {
        type: 'paragraph',
        text: 'Wanneer je meerdere agents en sub-agents hebt, heb je orchestratie nodig: een systeem dat beslist wie wat doet, wanneer, met welke middelen, en binnen welke grenzen. Zonder goede orchestratie en governance wordt een multi-agent systeem snel een onbeheersbare black box.',
      },
      {
        type: 'heading',
        text: 'De vier pijlers van agent governance',
      },
      {
        type: 'list',
        items: [
          '🔐 AUTORISATIE — welke agents mogen welke acties uitvoeren? Definieer expliciet per agent welke skills hij heeft en welke data hij mag lezen/schrijven',
          '📋 AUDITABILITY — elke beslissing die een agent maakt moet gelogd worden: welke input, welke redenering, welke output. Dit is kritiek voor compliance en debugging',
          '🛡️ GUARDRAILS — definieer harde grenzen: maximale kosten per run, maximale uitvoeringstijd, verboden acties (nooit productiedata verwijderen, nooit zonder goedkeuring deployen)',
          '👤 HUMAN IN THE LOOP — bepaal bij welke acties een mens moet goedkeuren voordat de agent doorgaat. Dit is geen optioneel feature maar een verplichting voor kritieke systemen',
        ],
      },
      {
        type: 'code',
        language: 'python',
        code: `# Governance wrapper — elke agent-actie loopt hier doorheen
class AgentGovernance:
    def __init__(self, agent_id: str, policy: Policy):
        self.agent_id = agent_id
        self.policy = policy
        self.audit_log = AuditLogger()

    def execute_skill(self, skill_name: str, params: dict) -> SkillResult:
        # 1. Autorisatie check
        if not self.policy.is_allowed(self.agent_id, skill_name):
            raise UnauthorizedSkillError(f"{self.agent_id} mag {skill_name} niet uitvoeren")

        # 2. Guardrail check
        if self.policy.requires_approval(skill_name, params):
            approval = self.request_human_approval(skill_name, params)
            if not approval.granted:
                return SkillResult.rejected(reason=approval.reason)

        # 3. Kosten-check (API calls, LLM tokens)
        if self.cost_tracker.would_exceed_budget(skill_name):
            raise BudgetExceededError("Budget limiet bereikt voor deze run")

        # 4. Uitvoering met timing
        start = time.time()
        try:
            result = self._run_skill(skill_name, params)
        except Exception as e:
            self.audit_log.error(self.agent_id, skill_name, params, str(e))
            raise

        # 5. Audit log
        self.audit_log.success(
            agent=self.agent_id,
            skill=skill_name,
            params=params,
            result=result,
            duration_ms=int((time.time() - start) * 1000),
        )
        return result`,
      },
      {
        type: 'heading',
        text: 'Wanneer wél en wanneer NIET automatiseren?',
      },
      {
        type: 'comparison',
        left: {
          title: '✅ Automatiseer dit',
          color: 'border-green-500/30',
          items: [
            'Herhaalde, voorspelbare taken (sprint rapporten, health checks)',
            'Data-ophalen en samenvatten (lezen is veilig)',
            'Notificaties en statuspagina updates',
            'Testresultaten analyseren en rapporteren',
            'Documentatie genereren op basis van bestaande code/tickets',
          ],
        },
        right: {
          title: '⛔ Behoud menselijke controle',
          color: 'border-red-500/30',
          items: [
            'Productiedeployments en database migraties',
            'Financiële transacties of prijswijzigingen',
            'Klantcommunicatie (e-mails, officiële berichten)',
            'Beveiligingsincidenten afhandelen',
            'Strategische beslissingen op basis van incomplete data',
          ],
        },
      },
      {
        type: 'tip',
        title: '🚀 Stappenplan: van nul naar multi-agent systeem',
        text: 'Stap 1: identificeer één herhaalde taak die minstens 30 minuten per week kost. Stap 2: bouw één agent met 2-3 skills die alleen leest. Stap 3: test grondig, controleer de audit logs. Stap 4: voeg schrijfrechten toe na vertrouwen. Stap 5: identificeer parallelle deeltaken en splits op in sub-agents. Herhaal.',
      },
    ],
  },
]

// ─── Components ───────────────────────────────────────────────────────────────

function CodeBlock({ language, code }: { language: string; code: string }) {
  return (
    <div className="rounded-xl overflow-hidden border border-white/10 my-4">
      <div className="flex items-center gap-2 px-4 py-2 bg-slate-800/80 border-b border-white/10">
        <Terminal className="w-3.5 h-3.5 text-slate-400" />
        <span className="text-xs text-slate-400 font-mono">{language}</span>
      </div>
      <pre className="p-4 overflow-x-auto bg-slate-900/60 text-sm text-slate-300 font-mono leading-relaxed whitespace-pre">
        {code}
      </pre>
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

function PrerequisiteBlock({ items }: { items: string[] }) {
  return (
    <div className="my-4 rounded-xl border border-green-500/20 bg-green-500/5 p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-base">✅</span>
        <div className="font-semibold text-green-400 text-sm">Wat je al moet weten om dit te begrijpen</div>
      </div>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className="text-slate-300 text-sm flex gap-2">
            <span className="text-green-500 mt-0.5 shrink-0">•</span>
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}

function ComparisonBlock({ left, right }: { left: ComparisonSide; right: ComparisonSide }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
      {[left, right].map((side) => (
        <div key={side.title} className={`rounded-xl border ${side.color} bg-white/3 p-4`}>
          <div className="font-semibold text-white text-sm mb-3">{side.title}</div>
          <ul className="space-y-2">
            {side.items.map((item, i) => (
              <li key={i} className="text-slate-300 text-sm flex gap-2">
                <ChevronRight className="w-3.5 h-3.5 text-slate-500 mt-0.5 shrink-0" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}

function ContentRenderer({ blocks }: { blocks: ContentBlock[] }) {
  return (
    <div className="space-y-4">
      {blocks.map((block, i) => {
        if (block.type === 'paragraph') {
          return <p key={i} className="text-slate-300 leading-relaxed">{block.text}</p>
        }
        if (block.type === 'heading') {
          return <h3 key={i} className="text-lg font-bold text-white mt-6 mb-2">{block.text}</h3>
        }
        if (block.type === 'subheading') {
          return <h4 key={i} className="text-base font-semibold text-slate-200 mt-4 mb-2">{block.text}</h4>
        }
        if (block.type === 'list') {
          return (
            <ul key={i} className="space-y-2">
              {block.items.map((item, j) => (
                <li key={j} className="flex gap-3 text-slate-300 text-sm">
                  <ArrowRight className="w-4 h-4 text-slate-500 mt-0.5 shrink-0" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          )
        }
        if (block.type === 'code') {
          return <CodeBlock key={i} language={block.language} code={block.code} />
        }
        if (block.type === 'quote') {
          return (
            <blockquote key={i} className="border-l-4 border-blue-500 pl-4 py-1 my-4">
              <p className="text-slate-300 italic">{block.text}</p>
            </blockquote>
          )
        }
        if (block.type === 'tip') {
          return <TipBlock key={i} title={block.title} text={block.text} />
        }
        if (block.type === 'explainer') {
          return <ExplainerBlock key={i} emoji={block.emoji} title={block.title} text={block.text} />
        }
        if (block.type === 'prerequisite') {
          return <PrerequisiteBlock key={i} items={block.items} />
        }
        if (block.type === 'comparison') {
          return <ComparisonBlock key={i} left={block.left} right={block.right} />
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
        {/* Header — always visible, clickable */}
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
              <h2 className="text-xl font-bold text-white">{section.title}</h2>
              <p className="text-sm text-slate-400">{section.subtitle}</p>
            </div>
          </div>
          <ChevronDown className={`w-5 h-5 text-slate-400 transition-transform shrink-0 ${open ? 'rotate-180' : ''}`} />
        </button>

        {/* Collapsible body */}
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

export default function HowTosPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">

      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center mb-12"
      >
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-medium mb-4">
          <BookOpen className="w-4 h-4" />
          Technische Gids
        </div>
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white mb-4">
          Skills · Agents ·{' '}
          <span className="bg-gradient-to-r from-blue-400 via-violet-400 to-green-400 bg-clip-text text-transparent">
            Sub-agents
          </span>
        </h1>
        <p className="text-slate-400 text-lg max-w-2xl mx-auto leading-relaxed">
          Van losse tools naar een volledig autonoom multi-agent systeem. Een diepgaande, praktische gids
          met code, patronen en concrete voorbeelden uit de echte wereld.
        </p>
      </motion.div>

      {/* Guides overzicht */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-10">

        {/* Beginner gids — nieuw */}
        <a href="/how-tos/ai-basics" className="block sm:col-span-2">
          <GlassCard className="p-5 border-green-500/30 bg-green-500/5 hover:bg-green-500/10 hover:border-green-500/50 transition-all cursor-pointer">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center shrink-0">
                <BookOpen className="w-6 h-6 text-green-400" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 border border-green-500/30 font-medium">Niveau 0 · Start hier</span>
                  <span className="text-xs text-slate-500">Aanbevolen voor beginners</span>
                </div>
                <div className="font-bold text-white text-base mb-1">🚀 Gids 0: AI Basis voor IT Professionals</div>
                <div className="text-xs text-slate-400">Terminologie (AI, LLM, RAG, Token...) · Rovo & Copilot agents · De volledige test workflow · Prompting tips & Golden Rules — inclusief cheat sheet</div>
              </div>
              <ExternalLink className="w-4 h-4 text-slate-500 shrink-0 mt-1" />
            </div>
          </GlassCard>
        </a>

        <GlassCard className="p-5 border-blue-500/20 bg-blue-500/5 hover:bg-blue-500/10 transition-colors cursor-default">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center shrink-0">
              <Layers className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <div className="text-xs text-blue-400 font-medium mb-1">📍 Je bent hier</div>
              <div className="font-bold text-white text-sm mb-1">Gids 1: Skills · Agents · Sub-agents</div>
              <div className="text-xs text-slate-400">Fundamenten van AI agent architectuur met Python/LangChain</div>
            </div>
          </div>
        </GlassCard>
        <a href="/how-tos/claude-copilot" className="block">
          <GlassCard className="p-5 h-full border-violet-500/20 hover:bg-violet-500/10 hover:border-violet-500/40 transition-all cursor-pointer">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-violet-500/20 flex items-center justify-center shrink-0">
                <Webhook className="w-5 h-5 text-violet-400" />
              </div>
              <div className="flex-1">
                <div className="text-xs text-violet-400 font-medium mb-1">→ Gids 2</div>
                <div className="font-bold text-white text-sm mb-1">Gids 2: Claude · Copilot · Webhooks & Plugins</div>
                <div className="text-xs text-slate-400">Tool use, MCP servers, Copilot Extensions en event-driven triggers</div>
              </div>
              <ExternalLink className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
            </div>
          </GlassCard>
        </a>

        <a href="/how-tos/cypress-globalconfig" className="block sm:col-span-2">
          <GlassCard className="p-5 border-cyan-500/20 bg-cyan-500/5 hover:bg-cyan-500/10 hover:border-cyan-500/40 transition-all cursor-pointer">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/20 flex items-center justify-center shrink-0">
                <Code2 className="w-5 h-5 text-cyan-400" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 font-medium">Gids 3 · Testing</span>
                  <span className="text-xs text-slate-500">PHR GlobalConfig</span>
                </div>
                <div className="font-bold text-white text-sm mb-1">🧪 Gids 3: Cypress E2E Testing in GlobalConfig</div>
                <div className="text-xs text-slate-400">Quick start · Page Object Model · SSO login · Custom commands · Tags & CI/CD — een complete gids voor het team</div>
              </div>
              <ExternalLink className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
            </div>
          </GlassCard>
        </a>

        <a href="/how-tos/ai-systeem-architectuur" className="block sm:col-span-2">
          <GlassCard className="p-5 border-violet-500/20 bg-violet-500/5 hover:bg-violet-500/10 hover:border-violet-500/40 transition-all cursor-pointer">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-xl bg-violet-500/20 flex items-center justify-center shrink-0">
                <Layers className="w-5 h-5 text-violet-400" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-400 border border-violet-500/30 font-medium">Gids 4 · Architectuur</span>
                  <span className="text-xs text-slate-500">Full AI System</span>
                </div>
                <div className="font-bold text-white text-sm mb-1">🏗️ Gids 4: Full AI Systeem Architectuur</div>
                <div className="text-xs text-slate-400">Data & Context · Orchestratie · Intelligence · Actie · Foundation Layer · Maturiteitsreis Level 0–3 — van tool naar systeem</div>
              </div>
              <ExternalLink className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
            </div>
          </GlassCard>
        </a>
      </div>

      {/* Voor wie is dit? */}
      <div className="mb-10 rounded-2xl border border-white/10 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
        <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
          <span className="text-lg">👥</span> Voor wie is deze gids?
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-xl bg-green-500/10 border border-green-500/20 p-4">
            <div className="text-green-400 font-semibold text-sm mb-2">✅ Geschikt voor jou als je...</div>
            <ul className="space-y-1.5 text-xs text-slate-300">
              <li>• Je weet wat een API is</li>
              <li>• Je ooit code hebt gezien of geschreven</li>
              <li>• Je werkt in IT (dev, ops, PM, architect)</li>
              <li>• Je wil begrijpen wat AI agents écht zijn</li>
            </ul>
          </div>
          <div className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-4">
            <div className="text-amber-400 font-semibold text-sm mb-2">⚡ Wat je leert</div>
            <ul className="space-y-1.5 text-xs text-slate-300">
              <li>• Verschil skills vs agents vs sub-agents</li>
              <li>• Hoe de ReAct-loop intern werkt</li>
              <li>• Orchestratie patronen met code</li>
              <li>• Governance voor productie-AI</li>
            </ul>
          </div>
          <div className="rounded-xl bg-violet-500/10 border border-violet-500/20 p-4">
            <div className="text-violet-400 font-semibold text-sm mb-2">🔍 Leeswijzer</div>
            <ul className="space-y-1.5 text-xs text-slate-300">
              <li>• 🟡 Amber kaders = menselijke taal uitleg</li>
              <li>• 🔵 Blauwe kaders = tips & waarschuwingen</li>
              <li>• 🟢 Groene kaders = voorkennis vereist</li>
              <li>• Code blokken zijn optioneel (illustratie)</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Progress indicator */}
      <div className="flex items-center justify-center gap-2 mb-10 flex-wrap">
        {sections.map((s, i) => {
          const Icon = s.icon
          return (
            <div key={s.id} className="flex items-center gap-2">
              <button
                onClick={() => document.getElementById(`section-${s.id}`)?.scrollIntoView({ behavior: 'smooth' })}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-colors hover:bg-white/10 ${s.badgeColor}`}
              >
                <Icon className="w-3.5 h-3.5" />
                {s.title}
              </button>
              {i < sections.length - 1 && (
                <ChevronRight className="w-4 h-4 text-slate-600" />
              )}
            </div>
          )
        })}
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
        <GlassCard className="p-6 sm:p-8">
          <Play className="w-8 h-8 text-green-400 mx-auto mb-3" />
          <h3 className="text-xl font-bold text-white mb-2">Klaar om te bouwen?</h3>
          <p className="text-slate-400 text-sm mb-4 max-w-lg mx-auto">
            Bekijk mijn AI Lab voor de concrete implementatie van skills, agents en sub-agents
            in het VorstersNV AI Control Platform.
          </p>
          <div className="flex gap-3 justify-center flex-wrap">
            <a
              href="/ai-lab"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-500 to-violet-500 text-white text-sm font-semibold hover:opacity-90 transition-opacity"
            >
              <Brain className="w-4 h-4" /> Bekijk AI Lab
            </a>
            <a
              href="/blog/rovo-agents-software-team-prompting"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-white/10 text-white text-sm font-medium hover:bg-white/5 transition-colors"
            >
              <Bot className="w-4 h-4" /> Rovo Agents gids
            </a>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  )
}
