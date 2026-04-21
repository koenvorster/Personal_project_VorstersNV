---
name: agent-performance
description: >
  Use when: analyzing Ollama agent output quality, comparing prompt versions,
  running validate-agents.mjs, checking agent scores below threshold,
  improving agent prompts, debugging poor agent output.
  Triggers: "agent presteert slecht", "prompt verbeteren", "agent score", "valideer agents",
  "agent output kwaliteit", "prompt optimaliseren", "agent debug", "lage score".
---

# Agent Performance Skill — VorstersNV

## Doel

Analyseer de kwaliteit van Ollama runtime agents en Claude Code agents in het VorstersNV ecosysteem.
Identificeer agents met lage scores, analyseer oorzaken, en geef concrete verbeteringen.

---

## Stap 1: Claude Code Agents Valideren

```bash
# Valideer alle Claude Code agents op correcte YAML frontmatter
node .claude/scripts/validate-agents.mjs

# Met detail-output
node .claude/scripts/validate-agents.mjs --verbose

# Auto-fix eenvoudige fouten
node .claude/scripts/validate-agents.mjs --fix
```

**Wat wordt gevalideerd:**
- `name` aanwezig en kebab-case
- `description` begint met "Delegate to this agent when:"
- `model` is een geldige Claude versie
- `permissionMode` is `default`, `restricted`, of `allow`

---

## Stap 2: Ollama Agent Performance Analyseren

```bash
# Analyseer agent performance (output naar .claude/reports/)
node .claude/scripts/analyse-agent-performance.mjs

# Lees het rapport
cat .claude/reports/agent-performance.json
```

**Lees ook de agent YAML bestanden direct:**

```bash
# Controleer alle Ollama agents
ls agents/*.yml

# Bekijk een specifieke agent
cat agents/klantenservice_agent_v2.yml
```

---

## Stap 3: Scores Interpreteren

### Drempelwaarden

| Score | Status | Actie |
|-------|--------|-------|
| ≥ 0.8 | ✅ Goed | Geen actie nodig |
| 0.6 – 0.79 | ⚠️ Matig | Verbeteringen overwegen |
| < 0.6 | ❌ Slecht | **Prioriteit: direct verbeteren** |

### Score Dimensies

| Dimensie | Beschrijving | Oplossing bij laag |
|----------|-------------|-------------------|
| `bodyScore` | Kwaliteit van de system prompt inhoud | Herstructureer met duidelijkere instructies |
| `frontmatterScore` | Correctheid YAML frontmatter | Controleer verplichte velden |
| `templateScore` | Volledige preprompt template | Voeg ontbrekende variabelen toe |
| `outputScore` | Output format conformiteit | Specificeer output format in system prompt |

---

## Stap 4: Verbeteringen Per Agent

### Structuur van een goede system prompt

```
1. Rol-definitie (kort: "Je bent X voor Y")
2. Context (wat weet de agent over het project?)
3. Input-verwachtingen (welke variabelen krijgt de agent?)
4. Output-format (JSON? Markdown? Plain text?)
5. Specifieke regels (max 5-7 bullets)
6. Grenzen (wat doet de agent NIET?)
```

### Veelvoorkomende Problemen

**Probleem: Vage output**
```yaml
# SLECHT system prompt
system_prompt: "Help de klant met vragen."

# GOED — specifiek output format
system_prompt: |
  Je bent een klantenservice-medewerker voor VorstersNV.
  
  Antwoord ALTIJD in dit JSON-format:
  {
    "toon": "professioneel|vriendelijk|formeel",
    "antwoord": "Jouw antwoord hier",
    "vervolgactie": "geen|escalatie|retour|korting"
  }
  
  Regels:
  - Maximaal 150 woorden
  - Altijd in het Nederlands
  - Nooit korting beloven zonder goedkeuring
```

**Probleem: Ontbrekende template variabelen**
```yaml
# SLECHT — variabele {klant_naam} nooit gedefinieerd
prompt: "Beste {klant_naam}, ..."

# GOED — alle variabelen in input_schema
input_schema:
  properties:
    klant_naam: {type: string}
    order_id: {type: string}
    probleem: {type: string}
  required: [klant_naam, probleem]
```

---

## Stap 5: A/B Testing via prompt_iterator.py

```bash
# Vergelijk twee prompt-versies
python scripts/prompt_iterator.py \
  --agent klantenservice \
  --version v1 v2 \
  --test-cases prompts/preprompt/klantenservice_iterations.yml

# Bekijk resultaten
cat .claude/reports/prompt-comparison.json
```

**Iteratie-workflow:**

1. Maak `prompts/preprompt/{agent}_iterations.yml` aan met 2-3 varianten
2. Draai `prompt_iterator.py` met testcases
3. Vergelijk scores in rapport
4. Kies winnende versie → update `{agent}.yml` met nieuwe `preprompt_ref`
5. Archiveer verliezende versie (verwijder niet — historische referentie)

---

## Stap 6: Agent Performance Rapport

```
╔══════════════════════════════════════════════════════╗
║  AGENT PERFORMANCE RAPPORT  ·  VorstersNV            ║
╚══════════════════════════════════════════════════════╝

📊 Samenvatting
  Totaal agents:    [N] Claude Code + [N] Ollama
  ✅ Goed (≥0.8):  [N]
  ⚠️  Matig:        [N]
  ❌ Slecht (<0.6): [N]

────────────────────────────────────────────────────────

🚨 AGENTS DIE AANDACHT VEREISEN

Agent: [naam]
  Overall score:  [X.XX]
  bodyScore:      [X.XX]  ← [probleem beschrijving]
  frontmatterScore: [X.XX]
  
  Aanbevolen aanpak:
  1. [Concrete stap]
  2. [Concrete stap]

────────────────────────────────────────────────────────

✅ GOED PRESTERENDE AGENTS
  [lijst met naam en score]

────────────────────────────────────────────────────────

📋 AANBEVELINGEN
  [ ] [Actie met prioriteit]
```
