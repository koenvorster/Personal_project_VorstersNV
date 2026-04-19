---
mode: agent
description: Debug een falende of underperformende Ollama runtime agent in VorstersNV. Analyseert logs, vergelijkt prompt-versies en geeft concrete verbeteringen.
---

# Agent Debug Workflow

Debug een problematische Ollama runtime agent in VorstersNV.

## Stap 1: Probleem Identificeren

Welk symptoom heeft de agent?

- [ ] **Geen antwoord** — agent timeout of Ollama niet bereikbaar
- [ ] **Verkeerd formaat** — output voldoet niet aan verwacht formaat
- [ ] **Lage kwaliteit** — output is generiek, onnauwkeurig of off-topic
- [ ] **Hallucineert** — agent verzint informatie die niet in de context staat
- [ ] **Te lang/kort** — output lengte klopt niet
- [ ] **Verkeerde taal** — antwoord in Engels terwijl Nederlands verwacht

## Stap 2: Logs Analyseren

```bash
# Bekijk recente agent-logs
ls logs/<agent_naam>/
cat logs/<agent_naam>/<recent_log>.json

# Zoek naar lage-score interacties
python scripts/test_agent.py --agent <naam> --show-low-scores
```

Log formaat om te checken:
```json
{
  "timestamp": "...",
  "model": "llama3",
  "temperature": 0.4,
  "prompt_versie": "v1",
  "input_tokens": 245,
  "output_tokens": 89,
  "feedback_score": 2,
  "response": "..."
}
```

## Stap 3: Ollama Connectivity Check

```bash
# Is Ollama bereikbaar?
curl http://localhost:11434/api/tags

# Is het model geladen?
curl http://localhost:11434/api/tags | python -m json.tool | grep llama3

# Test directe aanroep
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3", "prompt": "Zeg hallo in het Nederlands", "stream": false}'
```

## Stap 4: Prompt Analyse

Controleer de huidige prompts:
- `prompts/system/<agent>.txt` — te lang? te vaag? tegenstrijdige instructies?
- `prompts/prepromt/<agent>_v1.txt` — voorbeelden relevant? context duidelijk?

Veelvoorkomende prompt-problemen:
| Symptoom | Waarschijnlijke oorzaak | Fix |
|----------|------------------------|-----|
| Hallucineert | Geen "ik weet het niet" instructie | Voeg toe: "Als je het niet weet, zeg dat." |
| Te lang | Geen lengte-constraint | Voeg toe: "Maximum 150 woorden." |
| Verkeerd formaat | Geen format-forcing | Voeg JSON/template voorbeeld toe |
| Te generiek | Geen few-shot voorbeelden | Voeg 2-3 goede voorbeelden toe |
| Engelse output | Geen taal-instructie | Voeg toe: "Antwoord ALTIJD in het Nederlands." |

## Stap 5: Fix Implementeren

Geef de verbeterde prompt als `v<N+1>.txt` en documenteer de wijziging in de iteratielog.

Roep `@prompt-engineer` aan voor complexere prompt-optimalisatie.
