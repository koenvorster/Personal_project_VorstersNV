export type ContentBlock =
  | { type: 'paragraph'; text: string }
  | { type: 'heading'; text: string }
  | { type: 'code'; language: string; code: string }
  | { type: 'list'; items: string[] }
  | { type: 'quote'; text: string }

export interface BlogPost {
  slug: string
  titel: string
  excerpt: string
  datum: string
  datumISO: string
  leestijd: string
  categorie: string
  categorieKleur: string
  afbeelding: string
  inhoud: ContentBlock[]
}

export const blogPosts: BlogPost[] = [
  {
    slug: 'ai-chatbots-voor-je-kmo',
    titel: 'Aan de slag met AI chatbots voor je KMO',
    excerpt:
      'Ontdek hoe je met tools als OpenAI en LangChain een slimme chatbot bouwt die je klantenservice automatiseert. Stap voor stap, van API-key tot deployment.',
    datum: '12 juni 2025',
    datumISO: '2025-06-12',
    leestijd: '8 min',
    categorie: 'AI',
    categorieKleur: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
    afbeelding:
      'https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=800&q=80',
    inhoud: [
      {
        type: 'paragraph',
        text: 'AI-chatbots zijn niet langer voorbehouden aan grote bedrijven met diepe zakken. Dankzij open-source modellen en tools als Ollama, LangChain en FastAPI kan elke KMO vandaag een slimme chatbot bouwen die klantvragen beantwoordt, afspraken plant en je team ontlast. In dit artikel leg ik stap voor stap uit hoe ik dat aanpak voor mijn eigen projecten.',
      },
      {
        type: 'heading',
        text: 'Waarom een chatbot voor je KMO?',
      },
      {
        type: 'paragraph',
        text: 'De meeste kleine bedrijven besteden uren per week aan repetitieve klantvragen: "Wat zijn jullie openingsuren?", "Kan ik mijn bestelling volgen?", "Hebben jullie dit product in het blauw?". Een chatbot kan 80% van die vragen direct beantwoorden, 24/7, zonder dat er iemand achter een scherm moet zitten.',
      },
      {
        type: 'paragraph',
        text: 'Het mooie? Je hoeft niet te kiezen tussen een dure cloud-oplossing en een domme FAQ-bot. Met een lokaal draaiend taalmodel heb je volledige controle over je data, geen maandelijkse API-kosten, en tóch indrukwekkende resultaten.',
      },
      {
        type: 'heading',
        text: 'De tech stack',
      },
      {
        type: 'list',
        items: [
          'Ollama — draait LLM-modellen lokaal op je eigen hardware',
          'Python + FastAPI — lichtgewicht backend voor je chatbot API',
          'LangChain — framework om je chatbot context en geheugen te geven',
          'YAML-configuratie — definieer het gedrag van je bot zonder code te wijzigen',
        ],
      },
      {
        type: 'heading',
        text: 'Stap 1: Ollama installeren en een model laden',
      },
      {
        type: 'paragraph',
        text: 'Ollama maakt het belachelijk eenvoudig om lokale LLMs te draaien. Na installatie heb je met één commando een volledig taalmodel beschikbaar:',
      },
      {
        type: 'code',
        language: 'bash',
        code: '# Installeer Ollama\ncurl -fsSL https://ollama.com/install.sh | sh\n\n# Download het Mistral model (licht en snel)\nollama pull mistral\n\n# Test het model\nollama run mistral "Wat is de hoofdstad van België?"',
      },
      {
        type: 'heading',
        text: 'Stap 2: Een simpele chatbot API bouwen',
      },
      {
        type: 'paragraph',
        text: 'Met FastAPI en de Ollama Python client bouw je in minder dan 30 regels een werkende chatbot endpoint:',
      },
      {
        type: 'code',
        language: 'python',
        code: 'from fastapi import FastAPI\nfrom ollama import chat\n\napp = FastAPI()\n\nSYSTEM_PROMPT = """\nJe bent een vriendelijke klantenservice medewerker.\nJe beantwoordt vragen kort en bondig in het Nederlands.\nAls je het antwoord niet weet, zeg dat eerlijk.\n"""\n\n@app.post("/chat")\nasync def chat_endpoint(vraag: str):\n    response = chat(\n        model="mistral",\n        messages=[\n            {"role": "system", "content": SYSTEM_PROMPT},\n            {"role": "user", "content": vraag},\n        ],\n    )\n    return {"antwoord": response["message"]["content"]}',
      },
      {
        type: 'heading',
        text: 'Stap 3: Context toevoegen met LangChain',
      },
      {
        type: 'paragraph',
        text: 'Een chatbot zonder context over je bedrijf is nutteloos. Met LangChain kun je documenten laden (FAQ-pagina\'s, productinfo, handleidingen) en die als context meegeven aan het model. Dit noemen we RAG — Retrieval Augmented Generation.',
      },
      {
        type: 'code',
        language: 'python',
        code: 'from langchain_community.document_loaders import TextLoader\nfrom langchain.text_splitter import CharacterTextSplitter\nfrom langchain_community.vectorstores import FAISS\nfrom langchain_community.embeddings import OllamaEmbeddings\n\n# Laad je bedrijfsdocumenten\nloader = TextLoader("faq.txt")\ndocs = loader.load()\n\n# Splits in chunks en maak embeddings\nsplitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)\nchunks = splitter.split_documents(docs)\ndb = FAISS.from_documents(chunks, OllamaEmbeddings(model="mistral"))\n\n# Zoek relevante context bij een vraag\ndef zoek_context(vraag: str) -> str:\n    resultaten = db.similarity_search(vraag, k=3)\n    return "\\n".join([r.page_content for r in resultaten])',
      },
      {
        type: 'heading',
        text: 'Het resultaat',
      },
      {
        type: 'paragraph',
        text: 'Na deze setup heb je een chatbot die je eigen bedrijfsdocumenten raadpleegt, lokaal draait zonder cloud-afhankelijkheden, en vragen beantwoordt in natuurlijk Nederlands. De volgende stap? Een widget op je website plaatsen of integreren met WhatsApp Business.',
      },
      {
        type: 'quote',
        text: 'Tip: begin klein. Laad eerst je 10 meest gestelde vragen in het systeem en breid geleidelijk uit. Perfectie is de vijand van vooruitgang.',
      },
      {
        type: 'paragraph',
        text: 'In een volgend artikel ga ik dieper in op hoe je meerdere AI-agents kunt laten samenwerken — wat ik in mijn eigen Agent Orchestrator heb gebouwd. Denk aan een agent voor klantenservice, een voor SEO, en een voor productbeschrijvingen, allemaal onafhankelijk maar gecoördineerd.',
      },
    ],
  },
  {
    slug: 'iot-sensoren-python-mqtt',
    titel: 'IoT sensoren uitlezen met Python en MQTT',
    excerpt:
      'Een praktische tutorial over het opzetten van een IoT-sensornetwerk. Van ESP32 naar MQTT broker naar Python dashboard — alles wat je nodig hebt.',
    datum: '28 mei 2025',
    datumISO: '2025-05-28',
    leestijd: '12 min',
    categorie: 'IoT',
    categorieKleur: 'bg-green-500/20 text-green-400 border-green-500/30',
    afbeelding:
      'https://images.unsplash.com/photo-1558346490-a72e53ae2d4f?auto=format&fit=crop&w=800&q=80',
    inhoud: [
      {
        type: 'paragraph',
        text: 'Tijdens mijn opleiding Electronica-ICT aan Thomas More heb ik heel wat uren doorgebracht met microcontrollers en sensoren. Mijn eigen huis is ondertussen volledig "smart" — ik weet exact wanneer de temperatuur in een kamer te warm of te koud wordt. In deze tutorial laat ik zien hoe je een compleet IoT-sensornetwerk opzet: van ESP32 tot Python dashboard.',
      },
      {
        type: 'heading',
        text: 'Wat gaan we bouwen?',
      },
      {
        type: 'paragraph',
        text: 'We bouwen een systeem waarin een ESP32 microcontroller temperatuur- en luchtvochtigheidsdata leest van een DHT22 sensor, deze via MQTT verstuurt naar een broker, en een Python service de data opslaat en visualiseert. De volledige keten, van hardware tot dashboard.',
      },
      {
        type: 'list',
        items: [
          'ESP32 microcontroller met DHT22 sensor',
          'Mosquitto als MQTT broker',
          'Python + paho-mqtt als subscriber',
          'Real-time data opslag in SQLite',
          'Optioneel: een simpel Flask dashboard',
        ],
      },
      {
        type: 'heading',
        text: 'De hardware aansluiten',
      },
      {
        type: 'paragraph',
        text: 'De DHT22 is een betaalbare sensor die zowel temperatuur als luchtvochtigheid meet. Sluit hem aan op de ESP32: VCC naar 3.3V, GND naar GND, en de data-pin naar GPIO 4. Een 10kΩ pull-up weerstand tussen VCC en data is aan te raden voor een stabiel signaal.',
      },
      {
        type: 'heading',
        text: 'ESP32 firmware (MicroPython)',
      },
      {
        type: 'paragraph',
        text: 'Ik gebruik MicroPython op de ESP32 — het laat je Python schrijven op een microcontroller, wat de drempel enorm verlaagt:',
      },
      {
        type: 'code',
        language: 'python',
        code: 'import dht\nimport machine\nimport time\nfrom umqtt.simple import MQTTClient\n\n# Sensor setup\nsensor = dht.DHT22(machine.Pin(4))\n\n# MQTT setup\nclient = MQTTClient("esp32", "192.168.1.100")\nclient.connect()\n\nwhile True:\n    sensor.measure()\n    temp = sensor.temperature()\n    hum = sensor.humidity()\n    \n    payload = f\'{{"temp": {temp}, "humidity": {hum}}}\'\n    client.publish("huis/woonkamer/klimaat", payload)\n    \n    print(f"Verzonden: {temp}°C, {hum}%")\n    time.sleep(30)  # Elke 30 seconden',
      },
      {
        type: 'heading',
        text: 'MQTT Broker opzetten',
      },
      {
        type: 'paragraph',
        text: 'Mosquitto is de meest gebruikte open-source MQTT broker. Met Docker draait hij in seconden:',
      },
      {
        type: 'code',
        language: 'bash',
        code: '# Start Mosquitto met Docker\ndocker run -d --name mosquitto \\\n  -p 1883:1883 \\\n  -v mosquitto-data:/mosquitto/data \\\n  eclipse-mosquitto\n\n# Test met command-line subscriber\nmosquitto_sub -h localhost -t "huis/#" -v',
      },
      {
        type: 'heading',
        text: 'Python subscriber en data opslag',
      },
      {
        type: 'paragraph',
        text: 'Aan de server-kant schrijven we een Python service die luistert naar MQTT berichten en de data opslaat:',
      },
      {
        type: 'code',
        language: 'python',
        code: 'import json\nimport sqlite3\nfrom datetime import datetime\nimport paho.mqtt.client as mqtt\n\n# Database setup\nconn = sqlite3.connect("sensordata.db")\nconn.execute("""\n    CREATE TABLE IF NOT EXISTS metingen (\n        id INTEGER PRIMARY KEY AUTOINCREMENT,\n        ruimte TEXT,\n        temp REAL,\n        humidity REAL,\n        timestamp TEXT\n    )\n""")\n\ndef on_message(client, userdata, msg):\n    data = json.loads(msg.payload)\n    ruimte = msg.topic.split("/")[1]  # bijv. "woonkamer"\n    \n    conn.execute(\n        "INSERT INTO metingen (ruimte, temp, humidity, timestamp) VALUES (?, ?, ?, ?)",\n        (ruimte, data["temp"], data["humidity"], datetime.now().isoformat())\n    )\n    conn.commit()\n    print(f"[{ruimte}] {data[\'temp\']}°C, {data[\'humidity\']}%")\n\nclient = mqtt.Client()\nclient.on_message = on_message\nclient.connect("localhost", 1883)\nclient.subscribe("huis/#")\nclient.loop_forever()',
      },
      {
        type: 'heading',
        text: 'Van hobby naar productie',
      },
      {
        type: 'paragraph',
        text: 'Dit basisopzet schaalt verrassend goed. In mijn eigen woning heb ik meerdere ESP32-sensoren in verschillende kamers, allemaal rapporterend aan dezelfde MQTT broker. De Python service verwerkt alles en ik kan patronen herkennen: wanneer wordt het te warm in de slaapkamer? Hoe lang duurt het om de woonkamer op te warmen?',
      },
      {
        type: 'quote',
        text: 'Technologie is pas krachtig als het echte problemen oplost. Mijn smart home bespaart me niet alleen energie, het leert me ook hoe mijn huis "ademt".',
      },
      {
        type: 'paragraph',
        text: 'De volgende stap? Alerts instellen (Telegram/email als de temperatuur onder 16°C zakt), historische grafieken in een webdashboard, en OTA (Over The Air) updates voor de ESP32 firmware zodat je niet meer fysiek bij elke sensor hoeft te komen.',
      },
    ],
  },
  {
    slug: 'nextjs-fastapi-starter',
    titel: 'Next.js & FastAPI: een full-stack starter guide',
    excerpt:
      'Bouw een moderne full-stack applicatie met Next.js als frontend en FastAPI als backend. Inclusief authentication, database setup en deployment tips.',
    datum: '3 mei 2025',
    datumISO: '2025-05-03',
    leestijd: '15 min',
    categorie: 'Web Development',
    categorieKleur: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    afbeelding:
      'https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=800&q=80',
    inhoud: [
      {
        type: 'paragraph',
        text: 'Next.js en FastAPI zijn samen een krachtige combinatie: je krijgt de snelheid en developer experience van React met server-side rendering, gecombineerd met de performance en type-safety van een Python backend. Dit is exact de stack die ik gebruik voor mijn VorstersNV platform, en in dit artikel deel ik hoe je er zelf mee aan de slag gaat.',
      },
      {
        type: 'heading',
        text: 'Waarom deze combinatie?',
      },
      {
        type: 'list',
        items: [
          'Next.js — React framework met SSR, routing, en geweldige DX',
          'FastAPI — de snelste Python web framework met automatische OpenAPI docs',
          'TypeScript + Python — type-safety aan beide kanten',
          'Docker Compose — alles draait met één commando',
        ],
      },
      {
        type: 'heading',
        text: 'Project structuur',
      },
      {
        type: 'paragraph',
        text: 'Ik hanteer een monorepo structuur waarbij frontend en backend in dezelfde repository leven. Dit vereenvoudigt CI/CD, deployment en het beheer van gedeelde types:',
      },
      {
        type: 'code',
        language: 'text',
        code: 'project/\n├── frontend/          # Next.js applicatie\n│   ├── app/           # App Router pagina\'s\n│   ├── components/    # Herbruikbare componenten\n│   ├── data/          # Gedeelde data en types\n│   └── package.json\n├── api/               # FastAPI backend\n│   ├── main.py        # Entry point\n│   ├── routers/       # API endpoints per domein\n│   └── auth/          # JWT authenticatie\n├── db/                # Database modellen en migraties\n├── docker-compose.yml # Complete stack definitie\n└── Makefile           # Developer shortcuts',
      },
      {
        type: 'heading',
        text: 'FastAPI backend opzetten',
      },
      {
        type: 'paragraph',
        text: 'De backend begint simpel — een FastAPI app met CORS configuratie zodat de Next.js frontend erbij kan:',
      },
      {
        type: 'code',
        language: 'python',
        code: 'from fastapi import FastAPI\nfrom fastapi.middleware.cors import CORSMiddleware\n\napp = FastAPI(title="MijnProject API", version="1.0.0")\n\napp.add_middleware(\n    CORSMiddleware,\n    allow_origins=["http://localhost:3000"],\n    allow_credentials=True,\n    allow_methods=["*"],\n    allow_headers=["*"],\n)\n\n@app.get("/api/health")\nasync def health():\n    return {"status": "ok", "service": "api"}',
      },
      {
        type: 'heading',
        text: 'Database met SQLAlchemy + Alembic',
      },
      {
        type: 'paragraph',
        text: 'Voor de database gebruik ik PostgreSQL met SQLAlchemy als ORM en Alembic voor migraties. Dit geeft je versiebeheer voor je database schema — net zo belangrijk als Git voor je code:',
      },
      {
        type: 'code',
        language: 'python',
        code: 'from sqlalchemy import Column, Integer, String, DateTime\nfrom sqlalchemy.ext.declarative import declarative_base\nfrom datetime import datetime\n\nBase = declarative_base()\n\nclass Project(Base):\n    __tablename__ = "projecten"\n    \n    id = Column(Integer, primary_key=True)\n    naam = Column(String(200), nullable=False)\n    beschrijving = Column(String(2000))\n    created_at = Column(DateTime, default=datetime.utcnow)',
      },
      {
        type: 'heading',
        text: 'Next.js frontend met API calls',
      },
      {
        type: 'paragraph',
        text: 'In de frontend gebruik ik de native fetch API om data op te halen van de backend. Met Next.js App Router kun je dit zowel server-side als client-side doen:',
      },
      {
        type: 'code',
        language: 'typescript',
        code: '// app/projecten/page.tsx — Server Component\nexport default async function ProjectenPage() {\n  const res = await fetch("http://localhost:8000/api/projecten", {\n    cache: "no-store", // altijd verse data\n  });\n  const projecten = await res.json();\n\n  return (\n    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">\n      {projecten.map((project: Project) => (\n        <ProjectCard key={project.id} project={project} />\n      ))}\n    </div>\n  );\n}',
      },
      {
        type: 'heading',
        text: 'Docker Compose: alles in één commando',
      },
      {
        type: 'paragraph',
        text: 'Het mooie van deze stack is dat alles met Docker Compose draait. Database, backend, frontend, cache — één commando en alles staat klaar:',
      },
      {
        type: 'code',
        language: 'yaml',
        code: 'services:\n  database:\n    image: postgres:16-alpine\n    environment:\n      POSTGRES_DB: mijnproject\n      POSTGRES_USER: app\n      POSTGRES_PASSWORD: ${DB_PASSWORD}\n    volumes:\n      - pgdata:/var/lib/postgresql/data\n\n  api:\n    build: .\n    ports:\n      - "8000:8000"\n    depends_on:\n      - database\n\n  frontend:\n    build: ./frontend\n    ports:\n      - "3000:3000"\n    depends_on:\n      - api',
      },
      {
        type: 'heading',
        text: 'Mijn ervaring',
      },
      {
        type: 'paragraph',
        text: 'Deze stack draait nu in productie voor mijn eigen portfolio en platform. De combinatie van Python\'s kracht voor data-processing en AI, met de interactiviteit van React, is voor mij de sweet spot. FastAPI genereert automatisch OpenAPI docs, wat het debuggen en testen een stuk makkelijker maakt.',
      },
      {
        type: 'quote',
        text: 'Start met een werkend skelet en bouw van daaruit op. Een docker-compose.yml met drie services en een Makefile met "make up" en "make down" — dat is alles wat je nodig hebt om productief te zijn.',
      },
      {
        type: 'paragraph',
        text: 'Wil je de volledige broncode zien? Check mijn VorstersNV Platform project voor een werkend voorbeeld van deze stack in actie, inclusief Keycloak authenticatie, Redis caching, en AI-agent integratie.',
      },
    ],
  },
  {
    slug: 'docker-voor-beginners',
    titel: 'Docker voor beginners: je eerste container',
    excerpt:
      'Wat is Docker eigenlijk en waarom zou je het als ontwikkelaar moeten gebruiken? In deze tutorial bouw je stap voor stap je eerste containerized applicatie.',
    datum: '14 april 2025',
    datumISO: '2025-04-14',
    leestijd: '10 min',
    categorie: 'DevOps',
    categorieKleur: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    afbeelding:
      'https://images.unsplash.com/photo-1605745341112-85968b19335b?auto=format&fit=crop&w=800&q=80',
    inhoud: [
      {
        type: 'paragraph',
        text: '"Het werkt op mijn machine" — de meest gevreesde zin in software development. Docker lost dit probleem elegant op door je applicatie samen met al zijn afhankelijkheden te verpakken in een container die overal identiek draait. In deze tutorial neem ik je stap voor stap mee door je eerste Docker-ervaring.',
      },
      {
        type: 'heading',
        text: 'Wat is Docker (en wat is het niet)?',
      },
      {
        type: 'paragraph',
        text: 'Docker is een tool die je applicatie isoleert van het besturingssysteem. Anders dan een virtuele machine deelt een container de kernel van het host-systeem, waardoor containers in milliseconden starten en amper resources verbruiken. Denk eraan als een lichtgewicht, reproduceerbare "doos" voor je software.',
      },
      {
        type: 'list',
        items: [
          'Container ≠ virtuele machine — containers zijn sneller en lichter',
          'Image = de blauwdruk, Container = de draaiende instantie',
          'Dockerfile = het recept om een image te bouwen',
          'Docker Compose = meerdere containers orchestreren',
        ],
      },
      {
        type: 'heading',
        text: 'Je eerste Dockerfile',
      },
      {
        type: 'paragraph',
        text: 'Laten we een simpele Python API containerizen. Maak een Dockerfile aan in de root van je project:',
      },
      {
        type: 'code',
        language: 'dockerfile',
        code: '# Gebruik een lichtgewicht Python base image\nFROM python:3.12-slim\n\n# Stel de werkdirectory in\nWORKDIR /app\n\n# Kopieer en installeer dependencies eerst (voor caching)\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\n\n# Kopieer de applicatie code\nCOPY . .\n\n# Start de applicatie\nCMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]',
      },
      {
        type: 'heading',
        text: 'Bouwen en draaien',
      },
      {
        type: 'paragraph',
        text: 'Met twee commando\'s bouw en start je je container:',
      },
      {
        type: 'code',
        language: 'bash',
        code: '# Bouw het image\ndocker build -t mijn-api .\n\n# Start een container\ndocker run -d -p 8000:8000 --name api mijn-api\n\n# Bekijk logs\ndocker logs -f api\n\n# Stop en verwijder\ndocker stop api && docker rm api',
      },
      {
        type: 'heading',
        text: 'Docker Compose voor meerdere services',
      },
      {
        type: 'paragraph',
        text: 'De echte kracht van Docker komt naar boven wanneer je meerdere services combineert. Met Docker Compose definieer je je hele stack in één YAML-bestand:',
      },
      {
        type: 'code',
        language: 'yaml',
        code: '# docker-compose.yml\nservices:\n  api:\n    build: .\n    ports:\n      - "8000:8000"\n    environment:\n      - DATABASE_URL=postgresql://user:pass@db:5432/app\n    depends_on:\n      - db\n\n  db:\n    image: postgres:16-alpine\n    environment:\n      POSTGRES_USER: user\n      POSTGRES_PASSWORD: pass\n      POSTGRES_DB: app\n    volumes:\n      - pgdata:/var/lib/postgresql/data\n\nvolumes:\n  pgdata:',
      },
      {
        type: 'code',
        language: 'bash',
        code: '# Start alles\ndocker compose up -d\n\n# Bekijk status\ndocker compose ps\n\n# Stop alles\ndocker compose down',
      },
      {
        type: 'heading',
        text: 'Best practices',
      },
      {
        type: 'list',
        items: [
          'Gebruik .dockerignore om node_modules, .git en andere grote mappen uit te sluiten',
          'Multi-stage builds voor kleinere productie-images',
          'Kopieer requirements/package.json eerst voor betere layer caching',
          'Gebruik geen root-gebruiker in je container (USER directive)',
          'Pin je base image versies (python:3.12-slim, niet python:latest)',
        ],
      },
      {
        type: 'heading',
        text: 'Mijn setup',
      },
      {
        type: 'paragraph',
        text: 'In mijn eigen projecten gebruik ik Docker Compose met 7+ services: PostgreSQL, Redis, Keycloak, FastAPI, Ollama, en meer. Alles start met make up en stopt met make down. Nieuwe teamleden zijn in minuten productief, ongeacht hun besturingssysteem.',
      },
      {
        type: 'quote',
        text: 'Docker is als lego voor je infrastructuur: elke service is een blokje dat je onafhankelijk kunt bouwen, testen en vervangen. Begin met twee blokjes en bouw van daaruit.',
      },
      {
        type: 'paragraph',
        text: 'Wil je Docker in actie zien? Bekijk mijn Container Infrastructure project voor een volledig werkende multi-service setup met health checks, volume management en Makefile automation.',
      },
    ],
  },
]

export function getBlogPostBySlug(slug: string): BlogPost | undefined {
  return blogPosts.find((p) => p.slug === slug)
}
