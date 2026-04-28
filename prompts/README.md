# 🗣️ Runtime Prompts

Deze map bevat prompts die **runtime worden ingeladen** door de Ollama AI engine.

> ⚠️ Niet te verwarren met `.claude/preprompts/` — dat zijn Claude Code ontwikkelaarshints die
> alleen tijdens de Copilot/Claude sessie worden gebruikt, nooit in productie.

---

## Structuur

| Map | Doel | Geladen door |
|-----|------|-------------|
| `system/` | Systeem-level instructies per agent — bepaalt gedrag en persona | `ollama/agent_runner.py` |
| `preprompt/` | Context-injectie voor sessie-initialisatie — domeinkennis, voorbeelden | `ollama/agent_runner.py` |
| `promptbooks/` | Samengestelde prompt-sequenties voor complexe multi-step taken | `ollama/skill_loader.py` |

---

## Naming convention

```
system/<agent_naam>_system.txt          # bijv. klantenservice_agent_system.txt
preprompt/<agent_naam>_v<versie>.txt    # bijv. klantenservice_agent_v2.txt
preprompt/<agent_naam>_iterations.yml  # feedback loop logs
```

---

## Versie-iteraties

Prompt-versies worden bijgehouden via `ollama/prompt_iterator.py`.
Feedback en scores worden opgeslagen in `<agent_naam>_iterations.yml`.

Gebruik `python scripts/test_agent.py --agent <naam>` om een agent lokaal te testen.
