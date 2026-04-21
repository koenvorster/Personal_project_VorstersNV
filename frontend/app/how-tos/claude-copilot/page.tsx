'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronDown, ChevronRight, ArrowRight, Terminal,
  Webhook, Puzzle, Bot, BookOpen, Zap, Code2,
  GitBranch, Settings, Shield, Play, Brain, Link2,
} from 'lucide-react'
import GlassCard from '@/components/ui/GlassCard'

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
  | { type: 'prerequisite'; items: string[] }
  | { type: 'comparison'; left: ComparisonSide; right: ComparisonSide }

interface ComparisonSide { title: string; color: string; items: string[] }

interface Section {
  id: string
  icon: typeof Bot
  iconColor: string
  gradientFrom: string
  gradientTo: string
  badge: string
  badgeColor: string
  title: string
  subtitle: string
  content: ContentBlock[]
}

// ─── Content ──────────────────────────────────────────────────────────────────

const sections: Section[] = [
  {
    id: 'claude',
    icon: Brain,
    iconColor: 'text-orange-400',
    gradientFrom: 'from-orange-500/20',
    gradientTo: 'to-amber-500/20',
    badge: 'Anthropic',
    badgeColor: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    title: 'Claude als AI Agent',
    subtitle: 'Tool use, extended thinking en system prompts',
    content: [
      {
        type: 'explainer',
        emoji: '🧠',
        title: 'Wat is Claude en waarom gebruik je het als agent?',
        text: 'Claude is een AI-model gemaakt door Anthropic — een Amerikaans AI-bedrijf opgericht door ex-OpenAI medewerkers. Je kunt Claude vergelijken met een extreem capabele medewerker die kan lezen, schrijven en complex redeneren. Maar van nature heeft hij geen "handen": hij kan niet uit zichzelf acties uitvoeren in systemen. Tool Use (ook wel "function calling" genoemd) geeft hem die handen: de mogelijkheid om jouw functies aan te roepen, zoals een API bevragen, een bestand lezen of een bericht sturen. Zo wordt Claude van een chatbot een echte agent.',
      },
      {
        type: 'prerequisite',
        items: [
          'Een Anthropic account en API key (anthropic.com) — gratis tier beschikbaar voor tests',
          'Basiskennis Python of JavaScript (code-voorbeelden zijn in Python)',
          'Begrip van wat een JSON object is (sleutel-waarde paren: {"naam": "koen"})',
        ],
      },
      {
        type: 'paragraph',
        text: 'Claude (Anthropic) is een van de krachtigste foundation models voor agent-taken. Wat Claude onderscheidt van andere modellen is zijn uitzonderlijk lange context window (200K tokens), zijn sterke redeneervaardigheden via "extended thinking", en zijn native tool use ondersteuning. Claude is bij uitstek geschikt als de "brain" van een complexe multi-agent pipeline.',
      },
      {
        type: 'heading',
        text: 'Tool Use: Claude skills geven',
      },
      {
        type: 'paragraph',
        text: 'Via de Anthropic API geef je Claude een lijst van tools (skills). Claude beslist zelf wanneer hij welke tool gebruikt. Je definieert elke tool met een naam, beschrijving en JSON schema voor de parameters. De beschrijving is cruciaal — Claude leest die om te begrijpen wanneer hij de tool moet inzetten.',
      },
      {
        type: 'code',
        language: 'python',
        code: `import anthropic

client = anthropic.Anthropic()

# Definieer tools (skills) voor Claude
tools = [
    {
        "name": "search_jira",
        "description": """Zoek Jira issues op basis van een query.
        Gebruik dit wanneer je informatie nodig hebt over tickets, bugs of taken.
        Geeft een lijst van matching issues terug met key, titel, status en assignee.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "De zoekterm of JQL query"
                },
                "project": {
                    "type": "string",
                    "description": "Het Jira project key (bijv. PROJ)",
                    "default": "PROJ"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum aantal resultaten",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_confluence_page",
        "description": """Maak een nieuwe Confluence pagina aan.
        Gebruik dit ALLEEN wanneer de gebruiker expliciet vraagt om documentatie te schrijven.
        Vraag altijd bevestiging voor je een pagina aanmaakt.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "space_key": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string", "description": "Pagina inhoud in Markdown"},
                "parent_id": {"type": "string", "description": "Optioneel: parent pagina ID"}
            },
            "required": ["space_key", "title", "content"]
        }
    }
]

def run_agent(user_message: str):
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=SYSTEM_PROMPT,  # zie volgende code blok
            tools=tools,
            messages=messages
        )

        # Voeg Claude's antwoord toe aan de geschiedenis
        messages.append({"role": "assistant", "content": response.content})

        # Klaar — geen tool calls meer
        if response.stop_reason == "end_turn":
            return response.content[-1].text

        # Verwerk tool calls
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result)
                })

        # Stuur tool resultaten terug naar Claude
        messages.append({"role": "user", "content": tool_results})`,
      },
      {
        type: 'heading',
        text: 'De perfecte Claude system prompt structuur',
      },
      {
        type: 'paragraph',
        text: 'Claude volgt system prompts bijzonder nauwgezet. Anders dan sommige andere modellen "negeert" Claude je instructies zelden — mits je ze helder en concreet formuleert. De volgende structuur werkt het best voor agent-taken:',
      },
      {
        type: 'code',
        language: 'python',
        code: `SYSTEM_PROMPT = """
# Identiteit
Je bent een Senior Development Assistant voor het VorstersNV platform.
Je hebt grondige kennis van Python, FastAPI, TypeScript, Next.js en DevOps.
Je communiceert in het Nederlands tenzij de gebruiker anders vraagt.

# Primaire taak
Help developers met code analyse, documentatie en Jira-workflowbeheer.
Je zoekt altijd eerst naar relevante context in Jira en Confluence
voordat je antwoord geeft of documentatie schrijft.

# Werkwijze (VOLG DEZE VOLGORDE ALTIJD)
1. Begrijp de vraag volledig — vraag om verduidelijking als iets onduidelijk is
2. Zoek relevante context via de beschikbare tools
3. Analyseer de gevonden informatie
4. Geef een concreet, actionable antwoord
5. Stel follow-up acties voor indien relevant

# Beschikbare tools — gebruik ze proactief
- search_jira: gebruik bij elke vraag over tickets, bugs of taken
- create_confluence_page: ALLEEN na expliciete vraag van de gebruiker

# Absolute grenzen (NOOIT OVERSCHRIJDEN)
- Maak nooit een Confluence pagina zonder expliciete bevestiging
- Ga niet buiten de aangeleverde Jira/Confluence data
- Speculeer nooit over productiesystemen — vraag altijd om data

# Output stijl
- Gebruik Markdown voor langere antwoorden
- Bullet lists voor opsommingen
- Code blokken voor code en configuratie
- Altijd concreet en actionable — geen vage algemeenheden
"""`,
      },
      {
        type: 'heading',
        text: 'Extended Thinking: Claude laten nadenken',
      },
      {
        type: 'paragraph',
        text: 'Extended Thinking is Claude\'s vermogen om een interne redeneerslag te maken vóór hij antwoordt. Dit is bijzonder krachtig voor complexe analyses, architectuurbeslissingen of multi-step problemen. Je activeert het via de API — Claude denkt dan "hardop" (zichtbaar in de response) en geeft daarna een kwalitatief beter antwoord.',
      },
      {
        type: 'code',
        language: 'python',
        code: `# Extended Thinking inschakelen voor complexe taken
response = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=16000,
    thinking={
        "type": "enabled",
        "budget_tokens": 10000  # hoeveel tokens Claude mag "denken"
    },
    messages=[{
        "role": "user",
        "content": """Analyseer de architectuur van ons systeem op basis van deze
        Jira epic beschrijvingen en identificeer de top 3 technische risico's.
        Geef ook een concrete mitigatieplan per risico."""
    }]
)

# Response bevat twee soorten blocks:
for block in response.content:
    if block.type == "thinking":
        print("Claude's redenering:", block.thinking)  # intern denkproces
    elif block.type == "text":
        print("Antwoord:", block.text)  # het eigenlijke antwoord`,
      },
      {
        type: 'tip',
        title: '🧠 Wanneer Extended Thinking gebruiken?',
        text: 'Extended Thinking loont bij: architectuurreviews, complexe bug analyses, techdebt prioritering, en elke taak waarbij meerdere trade-offs afgewogen moeten worden. Voor eenvoudige taken (data ophalen, samenvatten) is het overkill en duurder.',
      },
      {
        type: 'heading',
        text: 'Claude vs. GPT-4 voor agent-taken',
      },
      {
        type: 'comparison',
        left: {
          title: '🟠 Claude (Anthropic)',
          color: 'border-orange-500/30',
          items: [
            '200K context window — ideaal voor grote codebases',
            'Extended Thinking voor complexe redenering',
            'Strikt in het volgen van instructies en grenzen',
            'Sterk in lange document analyse en synthese',
            'Computer Use beta: kan UI\'s bedienen',
            'Ideaal voor: code review, architectuur, research',
          ],
        },
        right: {
          title: '🟢 GPT-4 (OpenAI)',
          color: 'border-green-500/30',
          items: [
            'Sterk ecosysteem (plugins, function calling)',
            'Assistants API met threads en file search',
            'Snellere iteraties op kortere taken',
            'Breed geïntegreerd in Microsoft/Azure stack',
            'GPT-4o: multimodaal (beeld, audio)',
            'Ideaal voor: chatbots, real-time interactie, breed gebruik',
          ],
        },
      },
    ],
  },

  {
    id: 'copilot',
    icon: Code2,
    iconColor: 'text-blue-400',
    gradientFrom: 'from-blue-500/20',
    gradientTo: 'to-cyan-500/20',
    badge: 'GitHub',
    badgeColor: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    title: 'GitHub Copilot CLI & Extensions',
    subtitle: 'Skills, agents en Copilot Spaces in je workflow',
    content: [
      {
        type: 'explainer',
        emoji: '🤖',
        title: 'Wat is Copilot CLI eigenlijk — en wat maakt het uniek?',
        text: 'GitHub Copilot begon als een slimme autocomplete in je code-editor. Intussen is het geëvolueerd naar iets veel krachtiger: een agent die rechtstreeks in je terminal leeft, je bestanden kan lezen, code kan uitvoeren, en zelfs sub-agents kan opstarten voor complexe taken. Copilot CLI (het systeem waarmee je nu praat) is geen zoekmotor of gewone chatbot — het is een AI die acties kan ondernemen in jouw ontwikkelomgeving. Copilot Extensions gaan nog verder: die laten externe tools (Jira, Sentry, AWS, Datadog) rechtstreeks integreren in de Copilot-interface.',
      },
      {
        type: 'paragraph',
        text: 'GitHub Copilot is geëvolueerd van een autocomplete tool naar een volledig agent-ecosysteem. Via Copilot CLI, Copilot Extensions en Copilot Spaces kun je een persoonlijke AI-assistent bouwen die jouw codebase, projectcontext en werkwijze door en door kent.',
      },
      {
        type: 'heading',
        text: 'Copilot CLI: agent-interactie vanuit de terminal',
      },
      {
        type: 'paragraph',
        text: 'Copilot CLI (dit systeem) is meer dan een chatinterface. Het heeft toegang tot je bestanden, kan code uitvoeren, tools aanroepen en zelfs achtergrondagenten starten die autonoom werken. De kracht zit in de combinatie van taalvaardigheid én directe tooluitvoering.',
      },
      {
        type: 'code',
        language: 'bash',
        code: `# Copilot CLI gebruiken vanuit je project directory

# Stel vragen over je codebase — Copilot leest mee
gh copilot explain "src/agents/orchestrator.py"

# Laat Copilot een refactor uitvoeren
gh copilot suggest "refactor the auth module to use dependency injection"

# Gebruik als agent voor complexe taken
gh copilot "analyseer alle Python files in src/ op security vulnerabilities
            en maak een rapport in docs/security-audit.md"

# Met file context meegeven
gh copilot -f requirements.txt "zijn er bekende CVEs in deze dependencies?"

# Copilot als code reviewer (werkt op de huidige git diff)
git diff | gh copilot "review deze wijzigingen en geef feedback als senior developer"`,
      },
      {
        type: 'heading',
        text: 'Copilot Spaces: jouw kennisbank',
      },
      {
        type: 'paragraph',
        text: 'Copilot Spaces zijn private kennisbanken die je kunt koppelen aan Copilot. Je voedt een Space met documentatie, ADRs, coding standards en architectuuroverzichten. Daarna "weet" Copilot automatisch alles over je project en team — zonder dat je elke keer context moet herhalen.',
      },
      {
        type: 'code',
        language: 'markdown',
        code: `# Structuur van een effectieve Copilot Space

## /coding-standards
- python-style-guide.md       # PEP8 + teamspecifieke regels
- typescript-conventions.md   # Naming, folder structuur
- api-design-principles.md    # REST conventions, error handling

## /architecture
- system-overview.md          # High-level architectuurdiagram beschrijving
- service-boundaries.md       # Welke service doet wat
- data-models.md              # Kern database entities
- adr/                        # Architecture Decision Records

## /processes
- pr-review-checklist.md      # Wat controleert een reviewer
- deployment-runbook.md       # Hoe deployen we
- incident-playbook.md        # Hoe gaan we om met outages

## /team
- onboarding.md               # New developer guide
- team-contacts.md            # Wie weet wat

# In Copilot chat:
"@space wat zijn onze API design principes voor error responses?"
"@space hoe moet ik een nieuwe service opzetten volgens ons onboarding document?"`,
      },
      {
        type: 'heading',
        text: 'Copilot Extensions bouwen',
      },
      {
        type: 'paragraph',
        text: 'Copilot Extensions laten je Copilot integreren met externe systemen. Je bouwt een GitHub App die de Copilot Extension API implementeert. Gebruikers kunnen daarna via @jouw-extensie vanuit Copilot Chat interageren met jouw systeem — zonder de IDE te verlaten.',
      },
      {
        type: 'code',
        language: 'typescript',
        code: `// Copilot Extension server — Next.js API route
// app/api/copilot-extension/route.ts

import { NextRequest, NextResponse } from 'next/server'
import { verifyGitHubSignature } from '@/lib/github-signature'

export async function POST(req: NextRequest) {
  // Verifieer dat het request van GitHub komt
  const body = await req.text()
  const signature = req.headers.get('x-hub-signature-256') ?? ''

  if (!verifyGitHubSignature(body, signature)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const payload = JSON.parse(body)
  const userMessage = payload.messages.at(-1)?.content ?? ''

  // Verwerk het commando
  if (userMessage.includes('sprint status')) {
    const sprintData = await fetchCurrentSprint()
    return createSSEResponse(formatSprintStatus(sprintData))
  }

  if (userMessage.includes('open bugs')) {
    const bugs = await searchJira('type=Bug AND status=Open')
    return createSSEResponse(formatBugList(bugs))
  }

  return createSSEResponse('Ik begrijp je vraag niet. Probeer: "sprint status" of "open bugs"')
}

// Extensions moeten Server-Sent Events (SSE) gebruiken
function createSSEResponse(content: string): Response {
  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    start(controller) {
      // Copilot verwacht dit specifieke SSE formaat
      const data = JSON.stringify({
        choices: [{ delta: { content }, finish_reason: null }]
      })
      controller.enqueue(encoder.encode(\`data: \${data}\\n\\n\`))

      const done = JSON.stringify({
        choices: [{ delta: {}, finish_reason: 'stop' }]
      })
      controller.enqueue(encoder.encode(\`data: \${done}\\n\\n\`))
      controller.close()
    }
  })

  return new Response(stream, {
    headers: { 'Content-Type': 'text/event-stream' }
  })
}`,
      },
      {
        type: 'tip',
        title: '🔧 Copilot CLI custom agents',
        text: 'In Copilot CLI kun je agents definiëren via `.github/agents/` directory in je repo. Elke agent heeft een Markdown instructiebestand met naam, beschrijving, tools en prompt. Copilot CLI detecteert ze automatisch en je kunt ze aanroepen via @agent-naam in de chat.',
      },
      {
        type: 'code',
        language: 'markdown',
        code: `# .github/agents/code-reviewer.md
# Copilot CLI custom agent definitie

---
name: code-reviewer
description: Senior code review agent die PRs beoordeelt op kwaliteit, veiligheid en architectuurconformiteit
tools: [read_file, list_files, grep, run_shell]
---

## Identiteit
Je bent een ervaren tech lead met 10+ jaar ervaring in Python en TypeScript.
Je beoordeelt code op: correctheid, veiligheid, performantie en onderhoudbaarheid.

## Werkwijze
1. Lees de gewijzigde files via de beschikbare tools
2. Controleer op de volgende categorieën:
   - Security: SQL injection, XSS, hardcoded secrets, onveilige dependencies
   - Performance: N+1 queries, onnodig grote objecten in memory, blocking calls
   - Code quality: DRY violations, te lange functies (>50 regels), onduidelijke namen
   - Test coverage: zijn kritieke paden gedekt?
3. Geef feedback in dit formaat:
   🔴 KRITIEK (blokkeert merge): ...
   🟡 SUGGESTIE (nice-to-have): ...
   🟢 GOED (benoem wat goed is): ...

## Grenzen
- Stel nooit voor om externe libraries toe te voegen zonder security-check
- Merge nooit zelf een PR
- Maximum 5 kritieke opmerkingen per review`,
      },
    ],
  },

  {
    id: 'webhooks',
    icon: Webhook,
    iconColor: 'text-green-400',
    gradientFrom: 'from-green-500/20',
    gradientTo: 'to-emerald-500/20',
    badge: 'Triggers',
    badgeColor: 'bg-green-500/20 text-green-400 border-green-500/30',
    title: 'Webhooks als agent triggers',
    subtitle: 'Real-time events koppelen aan AI workflows',
    content: [
      {
        type: 'explainer',
        emoji: '🔔',
        title: 'Webhooks in gewoon Nederlands: de deurbel-analogie',
        text: 'Zonder webhook moet jouw systeem constant gaan kijken of er iets nieuws is ("is er al een nieuwe commit?", "is er al een nieuw ticket?") — dat heet polling en is inefficiënt. Een webhook werkt andersom: zodra er iets gebeurt in een extern systeem (GitHub, Jira, Slack), stuurt dat systeem automatisch een HTTP-bericht naar jouw agent. Jouw agent "slaapt" en wordt wakker zodra er iets te doen is. Het is precies zoals een deurbel: jij hoeft niet constant voor de deur te staan wachten — de deurbel laat je weten wanneer er iemand is.',
      },
      {
        type: 'paragraph',
        text: 'Webhooks zijn de zenuwbanen van een event-driven AI systeem. Ze stellen agents in staat om real-time te reageren op events: een nieuwe commit, een gefaald deployment, een Jira-ticket dat geblokkeerd raakt, of een klant die een specifieke actie uitvoert. Zonder webhooks moet je pollen — met webhooks push je events naar je agents zodra ze plaatsvinden.',
      },
      {
        type: 'heading',
        text: 'Webhook architectuur voor agents',
      },
      {
        type: 'list',
        items: [
          'GitHub webhooks: trigger bij push, PR open/close, CI falen, code review request',
          'Jira webhooks: trigger bij status change, assignment, priority update of blocker',
          'Slack webhooks (Incoming): agents sturen berichten naar channels',
          'Slack Event API (Outgoing): agents luisteren naar berichten en commando\'s in Slack',
          'Stripe/Mollie webhooks: betaalgebeurtenissen triggeren order-agents',
          'Custom webhooks: elk intern systeem kan events posten naar je agent gateway',
        ],
      },
      {
        type: 'code',
        language: 'python',
        code: `# FastAPI webhook gateway — het centrale ingangspunt voor alle agent triggers
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer
import hmac, hashlib, json
from agents import dispatch_agent

app = FastAPI()

# ─── GitHub Webhook ───────────────────────────────────────────────────────────
@app.post("/webhooks/github")
async def github_webhook(request: Request, background: BackgroundTasks):
    # Verifieer de HMAC-SHA256 signature (NOOIT overslaan!)
    body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256", "")
    expected = "sha256=" + hmac.new(
        GITHUB_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(sig, expected):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = request.headers.get("X-GitHub-Event")
    payload = json.loads(body)

    # Dispatch naar de juiste agent op basis van event type
    if event == "pull_request" and payload["action"] == "opened":
        background.add_task(
            dispatch_agent,
            agent="code-review-agent",
            context={"pr_number": payload["number"], "repo": payload["repository"]["full_name"]}
        )

    elif event == "workflow_run" and payload["workflow_run"]["conclusion"] == "failure":
        background.add_task(
            dispatch_agent,
            agent="ci-failure-agent",
            context={"run_id": payload["workflow_run"]["id"], "branch": payload["workflow_run"]["head_branch"]}
        )

    return {"status": "accepted"}  # Altijd snel antwoorden — agent draait op de achtergrond


# ─── Jira Webhook ─────────────────────────────────────────────────────────────
@app.post("/webhooks/jira")
async def jira_webhook(request: Request, background: BackgroundTasks):
    # Jira gebruikt een shared secret in de URL — minder veilig, maar eenvoudiger
    token = request.query_params.get("token")
    if token != JIRA_WEBHOOK_TOKEN:
        raise HTTPException(status_code=401)

    payload = await request.json()
    event = payload.get("webhookEvent")

    if event == "jira:issue_updated":
        fields = payload.get("changelog", {}).get("items", [])
        status_change = next((f for f in fields if f["field"] == "status"), None)

        if status_change and status_change["toString"] == "Blocked":
            background.add_task(
                dispatch_agent,
                agent="impediment-agent",
                context={"issue_key": payload["issue"]["key"], "blocker": status_change}
            )

    return {"status": "accepted"}


# ─── Slack Events API ─────────────────────────────────────────────────────────
@app.post("/webhooks/slack")
async def slack_events(request: Request, background: BackgroundTasks):
    payload = await request.json()

    # Slack vergt URL verificatie bij eerste setup
    if payload.get("type") == "url_verification":
        return {"challenge": payload["challenge"]}

    event = payload.get("event", {})

    # Bot commando's herkennen: "@bot sprint status"
    if event.get("type") == "app_mention":
        text = event.get("text", "").lower()
        background.add_task(
            dispatch_agent,
            agent="slack-command-agent",
            context={"text": text, "channel": event["channel"], "user": event["user"]}
        )

    return {"status": "ok"}`,
      },
      {
        type: 'heading',
        text: 'Webhook security: de vijf geboden',
      },
      {
        type: 'list',
        items: [
          '1. ALTIJD signature verificatie — gebruik HMAC-SHA256, nooit gewoon een geheime URL',
          '2. Antwoord binnen 3 seconden — verwerk de agent logica asynchroon (background task/queue)',
          '3. Idempotentie — sla het webhook ID op, verwerk elk event maar één keer (deduplication)',
          '4. Retry handling — GitHub en Slack hersturen bij timeout; zorg dat dubbele events geen problemen geven',
          '5. Rate limiting — begrens het aantal events per IP/source om misbruik en DoS te voorkomen',
        ],
      },
      {
        type: 'subheading',
        text: 'Lokaal testen met ngrok',
      },
      {
        type: 'code',
        language: 'bash',
        code: `# Webhooks lokaal testen zonder productie deployment

# 1. Start je lokale webhook server
uvicorn main:app --port 8000

# 2. Maak een publieke tunnel via ngrok
ngrok http 8000
# → geeft je een URL: https://abc123.ngrok.io

# 3. Configureer de webhook URL in GitHub/Jira/Slack
# GitHub: Settings → Webhooks → Add webhook
# Payload URL: https://abc123.ngrok.io/webhooks/github
# Content type: application/json
# Secret: jouw GITHUB_SECRET waarde

# 4. Inspecteer inkomende webhooks
# ngrok dashboard: http://localhost:4040
# Toont alle requests, headers, bodies en responses

# 5. Replay een webhook voor testing
curl -X POST http://localhost:4040/api/requests/http \
  -d '{"id": "abc123"}'  # replay specifiek request

# Tip: gebruik een .env.webhook bestand voor lokale secrets
# en laad die apart van je productie .env`,
      },
      {
        type: 'tip',
        title: '⚡ Event Queue voor robuustheid',
        text: 'Voor productie is een event queue (Redis, RabbitMQ of AWS SQS) tussen de webhook endpoint en de agent aanbevolen. Je webhook endpoint schrijft het event naar de queue en antwoordt direct. Een worker process haalt events op en dispatcht ze naar agents. Dit voorkomt verlies bij crashes en maakt horizontaal schalen eenvoudig.',
      },
    ],
  },

  {
    id: 'plugins',
    icon: Puzzle,
    iconColor: 'text-violet-400',
    gradientFrom: 'from-violet-500/20',
    gradientTo: 'to-purple-500/20',
    badge: 'Extensibility',
    badgeColor: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
    title: 'Plugins & MCP Integraties',
    subtitle: 'Model Context Protocol en plugin ecosysteem',
    content: [
      {
        type: 'explainer',
        emoji: '🔌',
        title: 'MCP uitgelegd: de USB-standaard voor AI',
        text: 'Vroeger had elke AI-tool zijn eigen manier om met externe systemen te praten. Claude had zijn eigen integraties, Copilot de zijne, en LangChain weer een andere. Dat is als apparaten die elk een eigen type stekker nodig hadden. MCP (Model Context Protocol) is de USB-standaard die dit oplost: je bouwt één server die je tools blootstelt via het MCP-protocol, en plots kunnen Claude, Copilot, én elke andere MCP-compatibele AI er gebruik van maken. Bouw het één keer, gebruik het overal.',
      },
      {
        type: 'prerequisite',
        items: [
          'Begrip van wat een API-server is (een programma dat luistert naar verzoeken en antwoordt)',
          'Optioneel: Python kennis voor het MCP server voorbeeld',
          'Optioneel: Node.js kennis voor het VS Code chat participant voorbeeld',
        ],
      },
      {
        type: 'paragraph',
        text: 'Het Model Context Protocol (MCP) is een open standaard van Anthropic die definieert hoe AI modellen kunnen communiceren met externe tools en databronnen. MCP is als USB-C voor AI: één universele interface waarmee elke AI-client (Claude, Copilot, elke LangChain agent) verbinding kan maken met elke MCP server (Jira, GitHub, databases, APIs).',
      },
      {
        type: 'heading',
        text: 'MCP: de universele plugin standaard',
      },
      {
        type: 'code',
        language: 'python',
        code: `# Een eigen MCP server bouwen — toegankelijk vanuit Claude, Copilot, etc.
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent
import mcp.server.stdio

# Maak een MCP server die Jira blootstelt als tools
server = Server("vorsternv-jira-mcp")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """Welke tools biedt deze MCP server aan?"""
    return [
        Tool(
            name="search_issues",
            description="Zoek Jira issues op. Geeft key, titel, status en assignee terug.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "JQL query of zoekterm"},
                    "project": {"type": "string", "default": "PROJ"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_issue_detail",
            description="Haal alle details op van een specifiek Jira issue inclusief comments.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {"type": "string", "description": "Bijv. PROJ-1234"}
                },
                "required": ["issue_key"]
            }
        ),
        Tool(
            name="create_issue",
            description="Maak een nieuw Jira issue aan. Vraag ALTIJD bevestiging voor je dit gebruikt.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string"},
                    "summary": {"type": "string"},
                    "description": {"type": "string"},
                    "issue_type": {"type": "string", "enum": ["Bug", "Task", "Story"]}
                },
                "required": ["project", "summary", "issue_type"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Voer een tool uit en geef het resultaat terug."""
    if name == "search_issues":
        results = await jira_client.search(arguments["query"], arguments.get("project", "PROJ"))
        return [TextContent(type="text", text=format_issues(results))]

    elif name == "get_issue_detail":
        issue = await jira_client.get_issue(arguments["issue_key"])
        return [TextContent(type="text", text=format_issue_detail(issue))]

    elif name == "create_issue":
        # Extra bevestiging via een confirmation flag
        issue = await jira_client.create_issue(arguments)
        return [TextContent(type="text", text=f"✅ Issue aangemaakt: {issue.key}")]

    raise ValueError(f"Onbekende tool: {name}")

# Start de MCP server (communiceert via stdio of SSE)
async def main():
    async with mcp.server.stdio.stdio_server() as (read, write):
        await server.run(read, write, InitializationOptions(
            server_name="vorsternv-jira-mcp",
            server_version="1.0.0"
        ))`,
      },
      {
        type: 'heading',
        text: 'MCP configureren in Claude Desktop en Copilot',
      },
      {
        type: 'code',
        language: 'json',
        code: `// claude_desktop_config.json — koppel je MCP server aan Claude Desktop
// Locatie: ~/Library/Application Support/Claude/ (macOS)
//          %APPDATA%\\Claude\\ (Windows)
{
  "mcpServers": {
    "vorsternv-jira": {
      "command": "python",
      "args": ["/path/to/your/mcp_server.py"],
      "env": {
        "JIRA_URL": "https://vorsternv.atlassian.net",
        "JIRA_TOKEN": "jouw-api-token"
      }
    },
    "vorsternv-github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..."
      }
    },
    "vorsternv-postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_URL": "postgresql://user:pass@localhost/vorsternv"
      }
    }
  }
}

// Na herstart van Claude Desktop: Claude heeft direct toegang tot
// al je Jira issues, GitHub repos en de PostgreSQL database
// via de tools in de chat interface`,
      },
      {
        type: 'heading',
        text: 'Nuttige bestaande MCP servers',
      },
      {
        type: 'list',
        items: [
          '@modelcontextprotocol/server-github — GitHub repos, issues, PRs, code search',
          '@modelcontextprotocol/server-postgres — veilige read-only SQL queries op PostgreSQL',
          '@modelcontextprotocol/server-filesystem — bestanden lezen en schrijven met directory restricties',
          '@modelcontextprotocol/server-brave-search — webzoekfunctie via Brave Search API',
          '@modelcontextprotocol/server-slack — Slack berichten en channels lezen',
          'mcp-server-fetch — willekeurige HTTP requests (als geconfigureerde web scraper)',
          'mcp-server-memory — persistente geheugenopslag tussen sessies',
          'mcp-atlassian — Jira + Confluence gecombineerd in één server',
        ],
      },
      {
        type: 'subheading',
        text: 'VS Code Copilot: custom chat participants',
      },
      {
        type: 'code',
        language: 'typescript',
        code: `// VS Code extensie — voeg een custom @participant toe aan Copilot Chat
// package.json
{
  "contributes": {
    "chatParticipants": [{
      "id": "vorsternv.assistant",
      "name": "vorsternv",
      "description": "VorstersNV development assistent — kent je codebase, Jira en architectuur",
      "isSticky": true
    }]
  }
}

// extension.ts
import * as vscode from 'vscode'

export function activate(context: vscode.ExtensionContext) {
  const participant = vscode.chat.createChatParticipant(
    'vorsternv.assistant',
    async (request, ctx, stream, token) => {
      const userPrompt = request.prompt

      // Voeg automatisch projectcontext toe
      const workspaceFiles = await getRelevantFiles(userPrompt)
      const jiraContext = await fetchJiraContext(userPrompt)

      // Bouw een rijke prompt op
      const messages = [
        vscode.LanguageModelChatMessage.User(\`
          Jij bent de VorstersNV development assistent.
          Je hebt toegang tot de volgende projectbestanden:
          \${workspaceFiles.map(f => f.path + ":\\n" + f.content).join("\\n---\\n")}

          Relevante Jira issues:
          \${jiraContext}

          Gebruikersvraag: \${userPrompt}
        \`)
      ]

      // Stream het antwoord via Copilot's LLM
      const response = await request.model.sendRequest(messages, {}, token)
      for await (const chunk of response.text) {
        stream.markdown(chunk)
      }

      // Voeg follow-up acties toe
      stream.button({
        command: 'vorsternv.openRelatedTicket',
        title: '🔗 Open Jira ticket'
      })
    }
  )

  participant.iconPath = vscode.Uri.joinPath(context.extensionUri, 'icon.png')
}`,
      },
      {
        type: 'tip',
        title: '🔌 Plugin vs. MCP vs. Extension: wanneer wat?',
        text: 'MCP is de toekomst — gebruik het voor nieuwe integraties. Het werkt met Claude, Copilot en elke LangChain agent. VS Code Extensions zijn beter voor diepere IDE-integratie (inline suggestions, sidebar panels). Copilot Extensions zijn ideaal als je een integratie wilt aanbieden aan het bredere GitHub-gebruikerspubliek via de Marketplace.',
      },
      {
        type: 'heading',
        text: 'Complete stack: alles samen',
      },
      {
        type: 'code',
        language: 'text',
        code: `// Volledige AI-tooling stack voor een modern development team

┌─────────────────────────────────────────────────────────┐
│                    DEVELOPER INTERFACE                   │
├──────────────┬──────────────────┬───────────────────────┤
│ VS Code      │ Claude Desktop   │ Terminal               │
│ + Copilot    │ + MCP servers    │ + Copilot CLI          │
│ Extension    │                  │ + Custom agents        │
└──────┬───────┴────────┬─────────┴───────────┬───────────┘
       │                │                     │
       ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────┐
│                  MCP / PLUGIN LAYER                     │
│  GitHub MCP │ Jira MCP │ Postgres MCP │ Filesystem MCP  │
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│                   AGENT GATEWAY (FastAPI)               │
│                                                         │
│  /webhooks/github  →  Code Review Agent                 │
│  /webhooks/jira    →  Impediment Agent                  │
│  /webhooks/slack   →  Slack Command Agent               │
│  /api/agents/run   →  On-demand Agent Execution         │
└──────────────────────────────┬──────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────┐
│                    AGENT ORCHESTRATOR                   │
│                                                         │
│  Claude Opus (brain)  +  Skills  +  Sub-agents          │
│                                                         │
│  ├── RequirementsAgent   ├── CodeQualityAgent           │
│  ├── SecurityAgent       ├── DocumentationAgent         │
│  └── NotificationAgent   └── ReportAgent               │
└─────────────────────────────────────────────────────────┘`,
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
        if (block.type === 'paragraph') return <p key={i} className="text-slate-300 leading-relaxed">{block.text}</p>
        if (block.type === 'heading') return <h3 key={i} className="text-lg font-bold text-white mt-6 mb-2">{block.text}</h3>
        if (block.type === 'subheading') return <h4 key={i} className="text-base font-semibold text-slate-200 mt-4 mb-2">{block.text}</h4>
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
          <blockquote key={i} className="border-l-4 border-violet-500 pl-4 py-1 my-4">
            <p className="text-slate-300 italic">{block.text}</p>
          </blockquote>
        )
        if (block.type === 'tip') return <TipBlock key={i} title={block.title} text={block.text} />
        if (block.type === 'explainer') return <ExplainerBlock key={i} emoji={block.emoji} title={block.title} text={block.text} />
        if (block.type === 'prerequisite') return <PrerequisiteBlock key={i} items={block.items} />
        if (block.type === 'comparison') return <ComparisonBlock key={i} left={block.left} right={block.right} />
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
            <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${section.gradientFrom} ${section.gradientTo} border border-white/10 flex items-center justify-center shrink-0`}>
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

export default function ClaudeCopilotPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">

      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="text-center mb-12"
      >
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-sm font-medium mb-4">
          <Zap className="w-4 h-4" />
          Praktische Gids
        </div>
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white mb-4">
          Claude · Copilot ·{' '}
          <span className="bg-gradient-to-r from-orange-400 via-violet-400 to-green-400 bg-clip-text text-transparent">
            Webhooks & Plugins
          </span>
        </h1>
        <p className="text-slate-400 text-lg max-w-2xl mx-auto leading-relaxed">
          Van Claude tool use en extended thinking tot GitHub Copilot Extensions, MCP servers
          en event-driven webhook architectuur — alles met werkende code.
        </p>
      </motion.div>

      {/* Nav pills */}
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
              {i < sections.length - 1 && <ChevronRight className="w-4 h-4 text-slate-600" />}
            </div>
          )
        })}
      </div>

      {/* Voor wie is dit? */}
      <div className="mb-8 rounded-2xl border border-white/10 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-6">
        <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
          <span className="text-lg">👥</span> Voor wie is deze gids?
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-xl bg-green-500/10 border border-green-500/20 p-4">
            <div className="text-green-400 font-semibold text-sm mb-2">✅ Geschikt als je...</div>
            <ul className="space-y-1.5 text-xs text-slate-300">
              <li>• Gids 1 hebt gelezen (of al weet wat agents zijn)</li>
              <li>• Werkt met Claude, GitHub Copilot of beide</li>
              <li>• Wil begrijpen hoe event-driven AI werkt</li>
              <li>• Plugins en MCP wil integreren in je workflow</li>
            </ul>
          </div>
          <div className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-4">
            <div className="text-amber-400 font-semibold text-sm mb-2">⚡ Wat je leert</div>
            <ul className="space-y-1.5 text-xs text-slate-300">
              <li>• Claude tool use met werkende Python code</li>
              <li>• Copilot CLI commando's en Extensions bouwen</li>
              <li>• Webhook gateway opzetten (FastAPI)</li>
              <li>• Eigen MCP server schrijven en configureren</li>
            </ul>
          </div>
          <div className="rounded-xl bg-violet-500/10 border border-violet-500/20 p-4">
            <div className="text-violet-400 font-semibold text-sm mb-2">🔍 Leeswijzer</div>
            <ul className="space-y-1.5 text-xs text-slate-300">
              <li>• 🟡 Amber kaders = menselijke taal uitleg</li>
              <li>• 🔵 Blauwe kaders = tips & waarschuwingen</li>
              <li>• 🟢 Groene kaders = voorkennis checklist</li>
              <li>• Code blokken zijn ter illustratie, niet verplicht</li>
            </ul>
          </div>
        </div>
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
        className="mt-12"
      >
        <GlassCard className="p-6 sm:p-8">
          <div className="flex flex-col sm:flex-row items-center gap-6">
            <div className="flex gap-3">
              <div className="w-10 h-10 rounded-xl bg-orange-500/20 flex items-center justify-center">
                <Brain className="w-5 h-5 text-orange-400" />
              </div>
              <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
                <Code2 className="w-5 h-5 text-blue-400" />
              </div>
              <div className="w-10 h-10 rounded-xl bg-green-500/20 flex items-center justify-center">
                <Webhook className="w-5 h-5 text-green-400" />
              </div>
              <div className="w-10 h-10 rounded-xl bg-violet-500/20 flex items-center justify-center">
                <Puzzle className="w-5 h-5 text-violet-400" />
              </div>
            </div>
            <div className="flex-1 text-center sm:text-left">
              <h3 className="text-lg font-bold text-white mb-1">Meer leren over agents?</h3>
              <p className="text-slate-400 text-sm">Bekijk de fundamentele Skills & Agents gids of het Rovo-artikel voor Atlassian-specifieke workflows.</p>
            </div>
            <div className="flex gap-3 flex-wrap justify-center">
              <a href="/how-tos" className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white/10 border border-white/10 text-white text-sm font-medium hover:bg-white/20 transition-colors">
                <BookOpen className="w-4 h-4" /> Skills & Agents
              </a>
              <a href="/blog/rovo-agents-software-team-prompting" className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-violet-500/30 text-violet-300 text-sm font-medium hover:bg-violet-500/10 transition-colors">
                <Link2 className="w-4 h-4" /> Rovo Gids
              </a>
            </div>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  )
}
