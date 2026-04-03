# VorstersNV AI Assistent 🏢🤖

Lokale AI-oplossing voor VorstersNV op basis van **Ollama**, **LangChain** en **ChromaDB**.  
Stel vragen aan uw eigen bedrijfsdocumenten (PDF, DOCX, TXT, CSV) — **alle data blijft lokaal**.

---

## Architectuuroverzicht

```
┌─────────────────────────────────────────────────────────────┐
│                    VorstersNV Lokale AI                     │
│                                                             │
│  ┌──────────┐    ┌───────────────┐    ┌──────────────────┐ │
│  │Streamlit │───▶│  FastAPI      │───▶│  Ollama (LLM)    │ │
│  │Frontend  │    │  Backend      │    │  llama3:8b       │ │
│  │:8501     │    │  :8000        │    │  nomic-embed-text│ │
│  └──────────┘    └───────┬───────┘    └──────────────────┘ │
│                          │                                  │
│                  ┌───────▼───────┐                          │
│                  │  ChromaDB     │                          │
│                  │  Vector Store │                          │
│                  │  :8001        │                          │
│                  └───────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

**Gegevensflow (RAG):**
1. Documenten worden geüpload via de Streamlit-interface.
2. De backend splitst ze in chunks en maakt embeddings via Ollama (`nomic-embed-text`).
3. Embeddings worden opgeslagen in ChromaDB.
4. Bij een vraag worden de meest relevante chunks opgehaald en meegegeven als context aan `llama3:8b`.
5. Het antwoord verschijnt in de chat, inclusief bronvermeldingen.

---

## Vereisten

| Onderdeel | Versie |
|-----------|--------|
| Docker    | ≥ 24   |
| Docker Compose | ≥ 2.20 |
| RAM       | ≥ 16 GB aanbevolen |
| GPU (optioneel) | NVIDIA + NVIDIA Container Toolkit |

---

## Snelstart

### 1. Repository klonen en configureren

```bash
git clone https://github.com/koenvorster/Personal_project_VorstersNV.git
cd Personal_project_VorstersNV

# Omgevingsbestand aanmaken
cp .env.example .env
```

### 2. Alle services starten

```bash
docker compose up --build -d
```

### 3. Ollama-modellen installeren

```bash
bash scripts/init_modellen.sh
```

Of handmatig:

```bash
# Chat-model
docker exec -it vorstersNV-ollama ollama pull llama3:8b

# Embed-model (verplicht voor zoekfunctionaliteit)
docker exec -it vorstersNV-ollama ollama pull nomic-embed-text
```

### 4. Applicatie openen

| Service | URL |
|---------|-----|
| 🖥️ Frontend (Streamlit) | http://localhost:8501 |
| 📡 Backend API (FastAPI) | http://localhost:8000/docs |
| 🗄️ ChromaDB | http://localhost:8001 |
| 🦙 Ollama | http://localhost:11434 |

---

## Gebruik

### Documenten uploaden
1. Ga naar **📄 Documenten** in de zijbalk.
2. Upload PDF-, DOCX-, TXT- of CSV-bestanden (max. 50 MB per stuk).
3. Klik op **Verwerken en opslaan** — de documenten worden automatisch geïndexeerd.

### Vragen stellen
1. Ga naar **💬 Chat**.
2. Zorg dat **"Gebruik bedrijfsdocumenten (RAG)"** aan staat.
3. Stel uw vraag in het invoerveld.
4. Het antwoord verschijnt samen met bronvermeldingen.

---

## Projectstructuur

```
VorstersNV/
├── backend/                  # FastAPI + LangChain backend
│   ├── app/
│   │   ├── api/              # Endpoint-routes (chat, documenten, health)
│   │   ├── core/             # Configuratie en dependency injection
│   │   ├── models/           # Pydantic-schema's
│   │   └── services/         # Bedrijfslogica (RAG, ingest)
│   ├── tests/                # Unittests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # Streamlit-interface
│   ├── pages/                # Chat, documenten, status
│   ├── app.py                # Hoofdpagina
│   ├── api_client.py         # HTTP-client voor backend
│   ├── config.py
│   ├── Dockerfile
│   └── requirements.txt
├── scripts/
│   └── init_modellen.sh      # Ollama-modellen automatisch installeren
├── data/uploads/             # Tijdelijke uploadmap
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## GPU-ondersteuning (NVIDIA)

Bewerk `docker-compose.yml` en verwijder het commentaar uit het GPU-blok onder `ollama`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

Zorg dat de [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) geïnstalleerd is.

---

## Configuratie (`.env`)

| Variabele | Standaard | Beschrijving |
|-----------|-----------|--------------|
| `OLLAMA_CHAT_MODEL` | `llama3:8b` | Model voor tekstgeneratie |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Model voor embeddings |
| `CHUNK_SIZE` | `1000` | Tekens per chunk |
| `CHUNK_OVERLAP` | `200` | Overlap tussen chunks |
| `RETRIEVER_TOP_K` | `5` | Aantal te raadplegen chunks per vraag |

---

## Tests uitvoeren

```bash
cd backend
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

---

## Beveiliging

- ✅ Alle LLM-verwerking en embeddings lopen via de lokale Ollama-instantie.
- ✅ ChromaDB wordt niet extern blootgesteld (alleen intern Docker-netwerk).
- ✅ Geen data wordt verzonden naar externe cloud-API's.
- ✅ Uploadmap is afgeschermd — bestanden worden na verwerking verwijderd.

---

## Aanbevolen modellen

| Taak | Model | RAM |
|------|-------|-----|
| Chatbot / RAG | `llama3:8b` | ~8 GB |
| Snel alternatief | `mistral:7b` | ~5 GB |
| Embeddings | `nomic-embed-text` | ~1 GB |
| Grote context | `llama3:70b` | ~40 GB (GPU vereist) |
