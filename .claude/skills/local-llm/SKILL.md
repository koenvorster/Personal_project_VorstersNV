---
name: local-llm
version: "1.0"
domain: infrastructure
audience: [agents, developers]
tags: [ollama, local-ai, gpu, hardware, slow-model, timeout, analyse_project]
---

# Local LLM Strategie

## Beschrijving
Kennis over het werken met lokale Ollama-modellen op hardware met/zonder GPU.
Bevat timeoutstrategie, chunk-sizing, model-selectie en server-setup.

## Wanneer gebruiken
- Bij `analyse_project.py` timeouts of lege responses
- Bij model-selectie voor een nieuw agent YAML
- Bij plannen van gaming desktop als Ollama server
- Bij debuggen van langzame of broken model outputs

## Hardware Situatie

### Huidig: Laptop (CPU-only)
| Spec | Waarde |
|------|--------|
| CPU | Intel i7-1165G7 (geen AVX-512) |
| RAM | 32GB |
| GPU | Intel Iris Xe (1GB gedeeld VRAM — **geen CUDA**) |
| Gevolg | Alle modellen draaien op CPU, ~290s/chunk voor mistral:7B |

### Gepland: Gaming Desktop (GPU-server)
```bash
# .env instelling voor remote Ollama
OLLAMA_BASE_URL=http://<desktop-ip>:11434

# Aanbevolen GPU: RTX 3090 (24GB) of RTX 4070 Ti (12GB)
# Verwachte snelheid: mistral:7B in ~1-2s, llama3:8B in ~2-3s
```

## Model Status op Laptop

| Model | Status | Probleem / Oplossing |
|-------|--------|---------------------|
| `mistral:latest` (7.2B Q4_K_M) | ✅ Werkt | Traag: 290s/chunk — gebruik kleine chunks |
| `llama3.2:latest` (3.2B Q4_K_M) | ✅ Werkt | Sneller maar minder kwaliteit |
| `gpt-oss:20b` (MXFP4) | ❌ Broken | MXFP4 vereist hardware-instructies absent op i7-1165G7 — retourneert 0 tokens |
| `starcoder:3b` | ⚠️ Beperkt | Alleen code-completion, geen chat/instructies |

## Configuratie voor Trage Hardware

### OllamaClient timeout
```python
# ollama/client.py — lijn 24
httpx.AsyncClient(timeout=360.0)   # 6 minuten voor CPU-only
```

### Agent YAML voor CPU
```yaml
model: mistral:latest       # Niet gpt-oss:20b
temperature: 0.1            # Lage temperature = minder tokens genereren
max_tokens: 512             # Maximaal 512 — compacte output vereist
```

### Chunk-sizing in analyse_project.py
```python
MAX_CHUNK_CHARS = 1_500     # Kleine chunks voor CPU (was 6000)
MAX_FILES_FULL = 20         # Max bestanden volledig lezen
```

## Aanpak bij Empty Responses

**Symptoom**: model retourneert 0 tokens, geen fout
**Oorzaak**: gpt-oss:20b MXFP4 quantization incompatibel
**Oplossing**:
```bash
# Controleer response in logs
# Schakel over naar mistral:
```
```yaml
# In agent YAML:
model: mistral:latest
```

## Ollama Server Setup (Gaming Desktop)

```bash
# Op desktop: installeer Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start als netwerk-server (bereikbaar voor laptop)
OLLAMA_HOST=0.0.0.0:11434 ollama serve

# Pull modellen
ollama pull codellama:13b
ollama pull llama3:8b
ollama pull mistral:7b

# Op laptop: set endpoint in .env
OLLAMA_BASE_URL=http://192.168.x.x:11434
```

## Model Aanbevelingen per Use Case

| Use Case | CPU (laptop) | GPU Desktop |
|----------|-------------|-------------|
| Code analyse | `mistral:latest` (traag) | `codellama:13b` |
| Rapport schrijven | `mistral:latest` | `llama3:8b` |
| Snel antwoord | `llama3.2:latest` | `llama3.2:latest` |
| Grote codebase | ❌ Niet praktisch | `mixtral:8x7b` |

## Gerelateerde skills
- agent-performance
- project-explainer
