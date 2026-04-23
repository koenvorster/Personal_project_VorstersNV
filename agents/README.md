# VorstersNV — Ollama Agent Catalogue

Dit zijn de **32 runtime agents** die het VorstersNV platform lokaal aandrijven via [Ollama](https://ollama.com).
Ze worden aangeroepen door `api/routers/agents.py` via de `PromptIterator` klasse.

> **Let op:** Dit zijn **runtime agents** voor het platform (webshop + consultancy).
> Ze zijn _niet_ dezelfde als de GitHub Copilot dev-agents in `.github/agents/` of de Claude Code agents in `.claude/agents/`.
> Zie [Agent Taxonomy](#agent-taxonomy) voor het onderscheid.

---

## Agent Taxonomy

Het project heeft **drie lagen** van AI agents:

| Laag | Locatie | Doel | Runtime |
|------|---------|------|---------|
| **Runtime agents** (dit bestand) | `agents/*.yml` | Bedienen het webshop-platform voor klanten | Ollama (llama3 / mistral) |
| **Copilot dev agents** | `.github/agents/` | Ondersteunen Koen bij development in VS Code / GitHub | GitHub Copilot |
| **Claude dev agents** | `.claude/agents/` | Ondersteunen Koen bij complexe taken in Claude Code | Claude (Anthropic) |

---

## Agent Overzicht

### Orchestrators & Architectuur

| Agent | Model | Temp | Rol |
|-------|-------|------|-----|
| `architect_agent` | llama3 | 0.35 | Top-level Solution Architect — ontwerpt DDD-architectuur, delegeert naar developer_agent + test_orchestrator |
| `test_orchestrator_agent` | llama3 | 0.3 | Coördineert alle test sub-agents, definieert teststrategieën |

### Webshop & Klantinteractie

| Agent | Model | Temp | Rol |
|-------|-------|------|-----|
| `checkout_begeleiding_agent` | llama3 | 0.3 | Begeleidt klant door checkout-flow, FAQ, winkelwagenhulp |
| `klantenservice_agent` | llama3 | 0.4 | Algemene klantenservice, klachten, retouren, FAQ |
| `aanbeveling_agent` | mistral | 0.6 | Productaanbevelingen op basis van browsgeschiedenis & profiel |
| `loyaliteit_agent` | llama3 | 0.5 | Beheert loyalty punten, rewards, VIP-acties |
| `betaling_status_agent` | llama3 | 0.2 | Status-updates Mollie-betalingen, webhook verwerking |
| `order_verwerking_agent` | llama3 | 0.1 | Verwerkt bestellingen, voorraadcontrole, bevestigingsemails |
| `retour_verwerking_agent` | llama3 | 0.2 | Retouren aanmaken, terugbetaling initiëren, statuspoll |

### Product & Content

| Agent | Model | Temp | Rol |
|-------|-------|------|-----|
| `product_beschrijving_agent` | llama3 | 0.7 | Genereert rijke SEO-vriendelijke productbeschrijvingen |
| `seo_agent` | llama3 | 0.5 | On-page SEO-analyse, metadata-suggesties, canonical-tags |
| `content_moderatie_agent` | llama3 | 0.1 | Controleert user-generated content op beleidsovertredingen |
| `voorraad_advies_agent` | llama3 | 0.2 | Voorraad-alert, herbesteladvies, seizoenspatronen |

### Security & Fraude

| Agent | Model | Temp | Rol |
|-------|-------|------|-----|
| `fraude_detectie_agent` | llama3 | 0.1 | Detecteert verdachte betalingen, hoog-risico bestellingen |
| `security_permissions_agent` | llama3 | 0.2 | Authenicatie, rollen, permissie-audits |

### Development & Engineering

| Agent | Model | Temp | Rol |
|-------|-------|------|-----|
| `developer_agent` | llama3 | 0.4 | Implementeert features, DDD-patterns, API endpoints |
| `automation_agent` | llama3 | 0.25 | CI/CD-taken, scripts, deployment automation |
| `clean_code_reviewer_agent` | llama3 | 0.2 | Code reviews op SOLID, DRY, security best practices |
| `playwright_mcp_agent` | llama3 | 0.3 | Browser automation via Playwright MCP — e.g. paginatests |

### Testing

| Agent | Model | Temp | Rol |
|-------|-------|------|-----|
| `test_design_agent` | llama3 | 0.3 | Ontwerpt testcases, scenario's, Gherkin specs |
| `test_data_designer_agent` | llama3 | 0.2 | Genereert realistische testdata + edge cases |
| `regression_selector_agent` | llama3 | 0.2 | Kiest welke regressietests te draaien na een wijziging |

### Domain & Email

| Agent | Model | Temp | Rol |
|-------|-------|------|-----|
| `ddd_modeling_agent` | llama3 | 0.25 | Modelleert DDD aggregates, entities, value objects |
| `domain_validation_agent` | llama3 | 0.2 | Valideert domein-invarianten en business rules |
| `email_template_agent` | llama3 | 0.6 | Genereert getailorde transactionele e-mailteksten |

### Freelance IT/AI Consultancy 🆕

| Agent | Model | Temp | Rol |
|-------|-------|------|-----|
| `bedrijfsproces_agent` | llama3 | 0.35 | AS-IS/TO-BE procesanalyse, automatiseringskansen, ROI-berekening |
| `code_analyse_agent` | llama3 | 0.25 | Technische analyse van codebase-chunks — architectuur, kwaliteit, risico's |
| `java_chunk_analyse_agent` | llama3 | 0.2 | Java-specifieke chunk-analyse — Spring patterns, class-structuur, afhankelijkheden |
| `klant_rapport_agent` | llama3 | 0.4 | Genereert klantgerichte samenvattingen van technische analyses |
| `review_analyzer_agent` | llama3 | 0.3 | Analyseert klantreviews — sentiment, patronen, verbeterpunten |
| `product_recommender_agent` | mistral | 0.6 | Productaanbevelingen op basis van klantprofiel en koopgeschiedenis |
| `consultancy_orchestrator` | llama3 | 0.3 | End-to-end consultancy workflow — coördineert code_analyse + klant_rapport |

---

## Configuratiestructuur

Elke agent YAML heeft de volgende velden:

```yaml
name: <agent_naam>
version: 3.0
type: specialist | orchestrator | sub_agent | ...
description: |
  <korte beschrijving van de rol>
model: llama3 | mistral
temperature: 0.1 – 0.7   # laag = deterministisch, hoog = creatief
max_tokens: 2048 – 8192
system_prompt_ref: prompts/system/<naam>_system.txt
preprompt_ref: prompts/preprompt/<naam>_v1.yml   # ⚠️ typo is intentioneel (load-bearing)
capabilities:
  - capability_naam
sub_agents:            # optioneel — gedelegeerde sub-agents
  - sub_agent_naam
```

> ⚠️ **Bekende typo**: `preprompt_ref` (mist de tweede 'p'). Dit is een load-bearing typo die in
> 25 YAML-bestanden, `agent_runner.py`, CI-scripts en de `prompts/preprompt/` directory bestaat.
> Het herstellen vereist een gecoördineerde rename van alle bestanden tegelijk. Zie `vn-p3-preprompt-typo` in het backlog.

---

## Lokaal draaien

```bash
# Zorg dat Ollama draait
ollama serve

# Models pullen (eenmalig)
ollama pull llama3
ollama pull mistral

# FastAPI backend starten
cd api
uvicorn api.main:app --reload --port 8000

# Agent aanroepen via API
curl -X POST http://localhost:8000/api/agents/architect_agent/run \
  -H "Content-Type: application/json" \
  -d '{"input": "Ontwerp een nieuw loyalty module"}'
```

---

## Prompts

Elke agent heeft bijbehorende prompt-bestanden:

```
prompts/
├── system/       # Systeemprompts (rol, toon, beperkingen)
└── preprompt/     # Context/instructie prompts per agent (YAML format)
```
