import type { LucideIcon } from 'lucide-react'
import { Server, Brain, Wifi, Database, Cpu, Terminal } from 'lucide-react'

export interface Project {
  slug: string
  naam: string
  korte: string
  beschrijving: string
  categorie: string
  tags: string[]
  icon: LucideIcon
  gradient: string
  status: 'Actief' | 'Afgerond'
  features: string[]
  github?: string
  demo?: string
}

export const projecten: Project[] = [
  {
    slug: 'vorsters-platform',
    naam: 'VorstersNV Platform',
    korte: 'Full-stack webplatform met AI-agent integratie en analytics dashboard.',
    beschrijving: 'Een compleet full-stack webplatform gebouwd met FastAPI als backend, Next.js als frontend, PostgreSQL voor data, Keycloak voor authenticatie en Redis voor caching. Het platform bevat een analytics dashboard met real-time metrics, een geïntegreerd AI-agentsysteem via Ollama voor geautomatiseerde klantenservice, SEO-optimalisatie en productbeschrijvingen. Gecontaineriseerd met Docker Compose voor eenvoudige deployment.',
    categorie: 'Full-Stack',
    tags: ['Python', 'TypeScript', 'Docker', 'PostgreSQL', 'Next.js', 'FastAPI', 'Redis', 'Keycloak'],
    icon: Server,
    gradient: 'from-green-600 to-emerald-800',
    status: 'Actief',
    features: [
      'FastAPI backend met async endpoints en Pydantic validatie',
      'Next.js 16 frontend met Tailwind CSS en Framer Motion',
      'PostgreSQL database met Alembic migraties',
      'Keycloak SSO authenticatie met JWT tokens',
      'Redis caching voor performance optimalisatie',
      'AI agent integratie via Ollama (lokale LLMs)',
      'Analytics dashboard met KPIs en grafieken',
      'Docker Compose setup met 7+ services',
    ],
    github: 'https://github.com/koenvorsters',
  },
  {
    slug: 'ai-control-platform',
    naam: 'AI Control Platform',
    korte: 'Enterprise-grade AI platform met governance, audit trail en zelflerende agents.',
    beschrijving:
      'Een volledig AI Control Platform gebouwd in 6 iteratieve waves. Het platform bestuurt alle AI-aanroepen via een centrale Control Plane met 8-dimensionele routing, dwingt governance af via Policy-as-Code in YAML, registreert elke AI-beslissing in een Decision Journal voor volledige auditbaarheid, bewaakt kwaliteit via een Quality Monitor met automatische alerts, en optimaliseert prompts automatisch via een A/B-testsysteem. Webhooks triggeren intelligent event-driven skill chains. Eén REST-endpoint (POST /api/ai/run) orkestreert de volledige stack.',
    categorie: 'AI / ML',
    tags: ['Python', 'FastAPI', 'LLM', 'Ollama', 'Policy-as-Code', 'YAML', 'TypeScript', 'Multi-Agent', 'Observability'],
    icon: Brain,
    gradient: 'from-purple-600 to-violet-900',
    status: 'Actief',
    features: [
      'Control Plane met 8-dimensionele routing (capability, risk, env, budget, latency, model, policy, rollout)',
      'Policy Engine: governance regels als YAML — HITL, tool access, maturity levels',
      'Decision Journal: elke AI-beslissing geauditeerd met trace_id, rationale en verdict',
      'Quality Monitor: real-time alerts bij degraded agents, CRITICAL/DEGRADED/SLOW statussen',
      'A/B Tester met AutoPromoter: winnende prompts worden automatisch gepromoot',
      'Event Bridge: webhooks (order, payment) triggeren automatisch AI skill chains',
      'MCP Tool Registry: gecentraliseerd beheer van alle AI-tools met cost tracking',
      '6 Capability Maturity Levels (L1 experimenteel → L4 business-critical)',
      'Deployment Rings (Ring 0 lokaal → Ring 4 full productie)',
      '1389 geautomatiseerde tests — 100% van eigen code gedekt',
    ],
    github: 'https://github.com/koenvorsters',
  },
  {
    slug: 'ai-agent-orchestrator',
    naam: 'AI Agent Orchestrator',
    korte: 'Multi-agent systeem voor automatisering met lokale LLMs.',
    beschrijving:
      'Een modulair multi-agent systeem (V3) dat volledig lokaal draait via Ollama zonder externe API-afhankelijkheden. V3 introduceert event-driven orchestratie met skill chains: externe events (webhooks, systeemtriggers) activeren automatisch gerichte agent-ketens op basis van event type en risicoscore. Agents zijn ingedeeld in 6 groepen (G1 Dev Intelligence t/m G6 Audit) en worden geconfigureerd via YAML-bestanden met gedefinieerde rollen, systeemprompts en iteratieve prompt pipelines.',
    categorie: 'AI / ML',
    tags: ['Python', 'Ollama', 'LLM', 'YAML', 'Agents', 'Prompt Engineering'],
    icon: Brain,
    gradient: 'from-violet-600 to-purple-800',
    status: 'Actief',
    features: [
      'V3 event-driven skill chain orchestrator',
      '6 agent groepen (G1 Dev Intelligence t/m G6 Audit)',
      'Context-driven chain selectie op basis van event type en risicoscore',
      'SkillChainOrchestrator met checkpoint recovery',
      'Multi-agent architectuur met YAML-configuratie',
      'Lokale LLM inference via Ollama (geen cloud vereist)',
      'Iteratieve prompt pipelines met kwaliteitscontrole',
      'Agent rollen: klantenservice, SEO, productbeschrijving, orderverwerking',
      'Gestructureerde logging met JSON output',
      'Orchestrator voor parallelle agent executie',
      'Prompt iteration systeem voor kwaliteitsverbetering',
    ],
    github: 'https://github.com/koenvorsters',
  },
  {
    slug: 'iot-data-pipeline',
    naam: 'IoT Data Pipeline',
    korte: 'Real-time sensor data verwerking met embedded devices.',
    beschrijving: 'Een end-to-end IoT oplossing die embedded microcontrollers verbindt met cloud dashboards. Sensordata wordt via MQTT protocol verstuurd, verwerkt door Python services en gevisualiseerd in real-time dashboards. Het systeem dekt de volledige keten: van hardwaresensor tot bruikbare inzichten.',
    categorie: 'IoT',
    tags: ['IoT', 'Embedded', 'MQTT', 'Python', 'Cloud', 'Sensors'],
    icon: Wifi,
    gradient: 'from-blue-600 to-cyan-800',
    status: 'Afgerond',
    features: [
      'Embedded microcontroller programmering',
      'MQTT protocol voor real-time datacommunicatie',
      'Python data processing en transformatie',
      'Interactieve cloud dashboards',
      'Sensor calibratie en foutdetectie',
      'Schaalbaarheid voor meerdere devices',
    ],
  },
  {
    slug: 'docker-infra',
    naam: 'Container Infrastructure',
    korte: 'Reproduceerbare multi-service Docker architectuur.',
    beschrijving: 'Een reproduceerbare multi-service Docker architectuur die een compleet development- en productie-ecosysteem opspant met één commando. Bevat PostgreSQL databases, Redis caching, Keycloak identity provider, Ollama ML inference, webhook handlers en meer — allemaal georchestreerd via Docker Compose en geautomatiseerd met Makefile targets.',
    categorie: 'DevOps',
    tags: ['Docker', 'Docker Compose', 'CI/CD', 'Linux', 'Makefile', 'PostgreSQL'],
    icon: Database,
    gradient: 'from-orange-600 to-amber-800',
    status: 'Actief',
    features: [
      '7+ Docker Compose services in één stack',
      'Makefile met targets voor development en productie',
      'Health checks en automatische restart policies',
      'Volume management voor persistente data',
      'Environment-based configuratie',
      'Eenvoudige onboarding: make up en alles draait',
    ],
  },
  {
    slug: 'webhook-engine',
    naam: 'Webhook Event Engine',
    korte: 'Event-driven webhook processing voor notificatie- en systeemflows.',
    beschrijving: 'Een event-driven webhook handler gebouwd met Flask voor het asynchrone verwerken van systeemnotificaties en events. Het systeem garandeert idempotente verwerking, heeft ingebouwde retry-logica en produceert gestructureerde audit logs voor volledige traceerbaarheid.',
    categorie: 'Full-Stack',
    tags: ['Python', 'Flask', 'Webhooks', 'Redis', 'Events', 'Async'],
    icon: Cpu,
    gradient: 'from-rose-600 to-pink-800',
    status: 'Afgerond',
    features: [
      'Event-driven architectuur met webhook handlers',
      'Idempotente verwerking van systeemnotificaties',
      'Retry-logica met exponentiële backoff',
      'Gestructureerde JSON logging voor audit trails',
      'Redis queue voor asynchrone job verwerking',
      'Handler registry pattern voor uitbreidbaarheid',
    ],
  },
  {
    slug: 'analytics-dashboard',
    naam: 'Analytics Dashboard',
    korte: 'Real-time KPI dashboard met aparte analytics database.',
    beschrijving: 'Een dedicated analytics systeem met een eigen PostgreSQL database, Alembic migraties en FastAPI endpoints. Biedt visualisatie van business metrics, agent performance en systeemgezondheid. Ontworpen voor schaalbaarheid met gescheiden read/write databases.',
    categorie: 'Full-Stack',
    tags: ['Python', 'PostgreSQL', 'FastAPI', 'Analytics', 'Alembic', 'Charts'],
    icon: Terminal,
    gradient: 'from-indigo-600 to-blue-800',
    status: 'Actief',
    features: [
      'Eigen analytics database (gescheiden van main DB)',
      'Alembic migraties voor schema management',
      'FastAPI endpoints voor metrics queries',
      'Real-time KPI berekeningen',
      'Agent performance tracking',
      'Systeem health monitoring',
    ],
  },
]

export function getProjectBySlug(slug: string): Project | undefined {
  return projecten.find((p) => p.slug === slug)
}

export const categories = ['Alles', 'Full-Stack', 'AI / ML', 'IoT', 'DevOps'] as const
export type Category = (typeof categories)[number]
