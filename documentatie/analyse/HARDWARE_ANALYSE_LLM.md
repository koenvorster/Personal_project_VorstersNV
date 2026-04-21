# Hardware Analyse — Lokale LLM Workloads
## VorstersNV IT/AI Consultancy Platform

**Opgesteld:** April 2026  
**Doel:** Analyse van huidige hardware vs. toekomstige gaming desktop server  
voor het draaien van lokale AI-modellen via Ollama.

---

## 1. Huidige Situatie — Laptop

### Specs
| Component | Waarde |
|-----------|--------|
| CPU | Intel Core i7-1165G7 (4 cores / 8 threads, 2.8 GHz) |
| RAM | 32 GB DDR4 |
| GPU | Intel Iris Xe Graphics (gedeeld, ~1 GB gereserveerd) |
| Type | Ultrabook / mobiel — geen dedicated GPU |

### Prestaties met Ollama (gemeten)

| Model | Parameters | Responstijd (1500 chars input) | Status |
|-------|-----------|-------------------------------|--------|
| `llama3.2:latest` | 3.2B | > 120s → timeout | ❌ te traag |
| `mistral:latest` | 7.2B | ~290s (~5 min) | ⚠️ marginaal |
| `gpt-oss:20b` | 20.9B (MXFP4) | 234–326s → lege output | ❌ broken |
| `starcoder:3b` | 3B | n.v.t. — geen instructiemodel | ❌ onbruikbaar |

### Oorzaak trage prestaties
- **Geen GPU inference** — alle berekeningen op CPU
- i7-1165G7 heeft geen AVX-512, slechts AVX2 → beperkte SIMD-versnelling
- Modellen >7B passen niet in GPU VRAM (1 GB) → volledig CPU-gebonden
- `gpt-oss:20b` met MXFP4 quantisatie vereist speciale hardware-instructies die ontbreken → lege output

### Conclusie laptop
> ✅ **Geschikt voor:** development, testen, dry-runs, kleine modellen (<3B)  
> ❌ **Niet geschikt voor:** productie code-analyse, 7B+ modellen, klantrapporten

---

## 2. Toekomstige Situatie — Gaming Desktop als Server

### Architectuur
```
Gaming Desktop PC (server)
├── Ollama (model-server, altijd actief)
├── FastAPI backend (VorstersNV API)
├── PostgreSQL + Redis (via Docker)
└── Toegankelijk via LAN of VPN (laptop als thin client)

Laptop
└── VS Code / browser / analyse-scripts
    └── API calls naar desktop (http://192.168.x.x:11434)
```

---

## 3. Aanbevolen Hardware Configuraties

### Optie A — Budget Gaming PC (€1.200–€1.500)
**GPU: NVIDIA RTX 3060 Ti / RTX 4060 (8 GB VRAM)**

| Component | Spec |
|-----------|------|
| GPU | RTX 4060 (8 GB GDDR6) |
| CPU | AMD Ryzen 7 7700X of Intel i7-13700 |
| RAM | 32 GB DDR5 |
| Opslag | 1 TB NVMe SSD |
| Voeding | 650W 80+ Gold |

**LLM Prestaties:**

| Model | Responstijd verwacht | Past volledig in VRAM? |
|-------|---------------------|----------------------|
| llama3.2:3B | ~2–3s | ✅ Ja |
| mistral:7B | ~5–8s | ✅ Ja |
| codellama:7B | ~5–8s | ✅ Ja |
| llama3:8B | ~8–12s | ✅ Ja |
| llama3:13B (Q4) | ~15–25s | ⚠️ Deels (offloading) |
| llama3:70B | ❌ niet haalbaar | ❌ Nee |

**Pro:**
- ✅ Grote sprong vs. laptop (20–50x sneller voor 7B modellen)
- ✅ Betaalbaar, energiezuinig (TDP 115W)
- ✅ Geschikt voor alle consultancy-use-cases (tot 13B)

**Con:**
- ❌ 70B modellen niet mogelijk
- ❌ Parallel draaien van meerdere grote modellen beperkt

---

### Optie B — Mid-Range Gaming PC (€1.800–€2.200) ⭐ AANBEVOLEN
**GPU: NVIDIA RTX 4070 Ti / RTX 3090 (16–24 GB VRAM)**

| Component | Spec |
|-----------|------|
| GPU | RTX 4070 Ti (12 GB) of RTX 3090 (24 GB, occasion) |
| CPU | AMD Ryzen 9 7900X of Intel i9-13900K |
| RAM | 64 GB DDR5 |
| Opslag | 2 TB NVMe SSD |
| Voeding | 850W 80+ Gold |

**LLM Prestaties (RTX 3090 — 24 GB VRAM):**

| Model | Responstijd verwacht | Past volledig in VRAM? |
|-------|---------------------|----------------------|
| mistral:7B | ~1–2s | ✅ Ja |
| codellama:13B | ~3–5s | ✅ Ja |
| llama3:70B (Q4) | ~20–35s | ✅ Ja (~40 GB Q4 → 24 GB = deels CPU) |
| llama3:70B (Q2) | ~10–18s | ✅ Ja (sterk gekwantiseerd) |
| Meerdere modellen parallel | ✅ | 2–3 kleine modellen tegelijk |

**Pro:**
- ✅ Alle huidige én toekomstige consultancy-agents draaien vlot
- ✅ 70B modellen haalbaar met Q4 quantisatie
- ✅ Meerdere clients tegelijk bedienen via Ollama API
- ✅ RTX 3090 occasion: €500–€700 (uitstekende prijs-kwaliteit)

**Con:**
- ❌ RTX 3090: hoog stroomverbruik (350W TDP)
- ❌ Hogere aanschafprijs

---

### Optie C — High-End AI Workstation (€3.000+)
**GPU: NVIDIA RTX 4090 (24 GB VRAM) of dual GPU**

| Component | Spec |
|-----------|------|
| GPU | RTX 4090 (24 GB GDDR6X) |
| CPU | AMD Ryzen Threadripper of Intel i9 |
| RAM | 128 GB DDR5 ECC |
| Opslag | 4 TB NVMe RAID |

**LLM Prestaties:**

| Model | Responstijd verwacht |
|-------|---------------------|
| mistral:7B | < 1s |
| llama3:70B (Q4) | ~8–15s |
| Mixtral 8x7B | ~5–10s |
| Meerdere agents parallel | ✅ Volledige fleet tegelijk |

**Pro:**
- ✅ Productie-grade, meerdere klanten tegelijk bedienen
- ✅ Toekomstbestendig voor 2–3 jaar

**Con:**
- ❌ Hoge aanschafprijs
- ❌ Stroomverbruik ~600W onder load
- ❌ Overkill voor solo freelancer in beginfase

---

## 4. Vergelijkingstabel

| Criterium | Laptop (huidig) | Budget PC (€1.5K) | Mid-Range PC (€2K) ⭐ | High-End (€3K+) |
|-----------|----------------|-------------------|----------------------|-----------------|
| 7B model snelheid | ~290s | ~5–8s | ~1–2s | <1s |
| 13B model | ❌ timeout | ~20s | ~5s | ~2s |
| 70B model | ❌ | ❌ | ~25s (Q2) | ~10s |
| Meerdere agents | ❌ | ⚠️ 1–2 | ✅ 3–4 | ✅ 6+ |
| Stroomverbruik | ~25W | ~200W | ~350W | ~600W |
| Aanschafprijs | — | €1.200–1.500 | €1.800–2.200 | €3.000+ |
| Gebruik als server | ⚠️ (laptop) | ✅ | ✅ | ✅ |
| Geschikt voor klanten | ❌ | ✅ KMO | ✅ KMO + enterprise | ✅ alle |

---

## 5. Plan: Gaming Desktop als Ollama Server

### Stap 1 — Desktop opzetten als server
```powershell
# Op de desktop: Ollama installeren als Windows-service
ollama serve  # standaard poort 11434

# Of via Docker:
docker run -d --gpus all -p 11434:11434 ollama/ollama
```

### Stap 2 — Laptop verbinden als thin client
```bash
# In .env op laptop:
OLLAMA_BASE_URL=http://192.168.1.100:11434  # IP van desktop

# analyse_project.py gebruikt dit automatisch via OllamaClient
```

### Stap 3 — Modellen op desktop laden
```bash
# Op desktop:
ollama pull codellama:13b   # beste voor code-analyse
ollama pull llama3:8b       # beste voor rapporten  
ollama pull mistral:7b      # goede allrounder
```

### Stap 4 — VorstersNV services op desktop draaien
```bash
# docker-compose.yml aanpassen: alle services op desktop
docker compose up -d  # PostgreSQL, Redis, FastAPI, Ollama
```

---

## 6. Aanbeveling

### Voor nu (laptop):
- ✅ Gebruik `mistral:7B` voor **1 bestand per keer** met `--max-bestanden 1`
- ✅ Bouw de `java_extractor.py` pre-processor (input reduceren 70KB → 5KB)
- ✅ Script en infra zijn klaar — wacht op betere hardware

### Aankoopaanbeveling:
> **RTX 3090 (24 GB, occasion) of RTX 4070 Ti (12 GB, nieuw)**  
> Beide zijn de sweet-spot voor consultancy LLM werk:  
> snelle 7B–13B inference, betaalbaar, lang meegaan.

### Niet aanbevolen:
- ❌ **Claude API als vervanging** — kost geld per token, geen privacy voor klantcode
- ❌ **Mac Studio** — goed voor LLMs maar niet compatibel met huidige Windows tooling
- ❌ **Goedkope laptop upgraden** — probleem zit in GPU, niet RAM of CPU

---

## 7. Impact op Consultancy Diensten

Met **Optie B (RTX 3090/4070 Ti)**:

| Dienst | Huidig (laptop) | Met desktop server |
|--------|-----------------|-------------------|
| Code-analyse (1 bestand) | ~5 min | ~10 seconden |
| Volledige codebase 50 bestanden | ❌ uren | ~10 minuten |
| Klantrapport genereren | ~5 min | ~30 seconden |
| Live demo bij klant (via VPN) | ❌ | ✅ |
| Meerdere projecten parallel | ❌ | ✅ |

> **Conclusie:** De overstap naar een gaming desktop als Ollama server is de  
> snelste en goedkoopste manier om het consultancy platform productie-klaar te maken.  
> Privacy van klantcode blijft gewaarborgd (alles lokaal, geen cloud).
