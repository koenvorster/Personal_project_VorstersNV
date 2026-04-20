---
mode: agent
description: Maak een nieuwe runtime Ollama AI-agent aan voor VorstersNV, inclusief YAML-config, system prompt, preprompt v1 en iteratielog.
---

# Nieuwe Runtime Agent Generator

Maak een complete nieuwe Ollama runtime agent aan voor VorstersNV.

## Gevraagde informatie
- **Agent naam**: [snake_case, bijv. "review_moderatie_agent"]
- **Model**: [llama3 of mistral]
- **Temperature**: [0.1–0.9]
- **Doel**: [wat doet deze agent?]
- **Capabilities**: [lijst van wat de agent kan]

## Wat te genereren

### 1. Agent YAML (`agents/<naam>.yml`)
```yaml
name: <naam>
version: "1.0"
model: <model>
temperature: <temp>
max_tokens: 1024
system_prompt_ref: prompts/system/<naam>.txt
preprompt_ref: prompts/preprompt/<naam>_v1.txt
capabilities:
  - <capability 1>
  - <capability 2>
evaluation:
  feedback_loop: true
  metrics:
    - quality_score
    - relevance_score
sub_agents: []
```

### 2. System Prompt (`prompts/system/<naam>.txt`)
- Persona + rol definitie
- Gedragsregels (wat WEL en NIET doen)
- Output format (hoe antwoorden structureren)
- Taal (Nederlands, formeel/informeel)
- Maximale lengte richtlijn

### 3. Preprompt v1 (`prompts/preprompt/<naam>_v1.txt`)
- Context over VorstersNV
- Domein-specifieke instructies
- 2-3 few-shot voorbeelden
- Specifieke constraints voor deze agent

### 4. Iteratielog (`prompts/preprompt/<naam>_iterations.yml`)
```yaml
agent: <naam>
versies:
  - versie: v1
    datum: <vandaag>
    avg_score: null
    samples: 0
    notitie: "Initiële versie"
```

### 5. Registreer in agent_runner.py
Controleer of de agent automatisch geladen wordt via `list_agents()`.
Zo niet, voeg toe aan de laadlogica.

## Kwaliteitsregels
- System prompt max 500 woorden
- Preprompt max 300 woorden  
- Temperature: laag (0.1-0.3) voor deterministische agents, hoog (0.6-0.8) voor creatieve
- Verbod op: halluceren, financieel advies zonder disclaimers, persoonlijke data lekken
