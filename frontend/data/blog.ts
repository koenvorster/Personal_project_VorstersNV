export type ContentBlock =
  | { type: 'paragraph'; text: string }
  | { type: 'heading'; text: string }
  | { type: 'code'; language: string; code: string }
  | { type: 'list'; items: string[] }
  | { type: 'quote'; text: string }
  | { type: 'image'; src: string; alt: string; caption?: string }
  | { type: 'infobox'; icon?: string; title?: string; text: string; color?: string }
  | { type: 'grid2'; items: { icon?: string; title: string; text: string }[] }
  | { type: 'steps'; items: { title: string; text: string }[] }

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
    slug: 'rovo-agents-software-team-prompting',
    titel: 'Rovo Agents in je software team: de ultieme prompting gids per rol',
    excerpt:
      'Hoe prompt je een Rovo agent als developer, architect, QA of product manager? Een praktische how-to met kant-en-klare prompts, concrete use cases en tips om het maximale uit Atlassian Rovo te halen in elk software development team.',
    datum: '21 april 2026',
    datumISO: '2026-04-21',
    leestijd: '14 min',
    categorie: 'AI',
    categorieKleur: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
    afbeelding:
      'https://images.unsplash.com/photo-1677442135703-1787eea5ce01?auto=format&fit=crop&w=800&q=80',
    inhoud: [
      {
        type: 'paragraph',
        text: 'Atlassian Rovo is geen gewone chatbot. Het is een AI agent die diep geïntegreerd is met je Jira, Confluence, GitHub en Slack-werkruimte — en die de context van je project écht begrijpt. Toch halen de meeste teams maar een fractie uit wat Rovo kan bieden, simpelweg omdat ze niet weten hoe ze het correct moeten aanspreken. In dit artikel deel ik per rol in een software development team precies hoe je Rovo agents het best prompt, welke workflows je kunt automatiseren, en welke valkuilen je moet vermijden.',
      },
      {
        type: 'heading',
        text: 'Wat maakt Rovo anders dan ChatGPT of Copilot?',
      },
      {
        type: 'paragraph',
        text: 'Rovo heeft toegang tot je volledige Atlassian ecosysteem. Dat betekent dat een Rovo agent niet alleen een generiek antwoord geeft — hij zoekt eerst door je Jira-issues, Confluence-pagina\'s, pull requests en teamdiscussies. Hij kent je product backlog, je sprint history, je architectuurdocumentatie en je codereviews. Dat is fundamenteel anders dan een standalone LLM. Goede Rovo prompts benutten die context actief. Slechte prompts behandelen Rovo als een simpele zoekmachine of tekstgenerator.',
      },
      {
        type: 'quote',
        text: 'Een Rovo agent is zo slim als de context die je hem geeft. Geef je weinig context, krijg je generieke antwoorden. Geef je veel context, krijg je antwoorden die specifiek zijn voor jouw product, team en codebase.',
      },
      {
        type: 'heading',
        text: '🧑‍💻 Developer: van ticket naar implementatie',
      },
      {
        type: 'paragraph',
        text: 'Als developer gebruik je Rovo het meest voor het begrijpen van requirements, het opzoeken van gerelateerde code en het versnellen van je implementatie. De sleutel is altijd: geef Rovo de Jira issue key mee, zodat hij de volledige context (acceptance criteria, comments, linked issues) kan ophalen.',
      },
      {
        type: 'list',
        items: [
          'Ticket analyse: "Analyseer PROJ-1234 en geef me een technisch implementatieplan met de edge cases die ik moet testen"',
          'Impact analyse: "Welke componenten en Jira-issues zijn gerelateerd aan de user authentication module? Zoek ook in Confluence naar ADRs over dit onderwerp"',
          'Code review prep: "Kijk naar PR #142 en genereer de beschrijving + een checklist van wat de reviewer moet controleren"',
          'Sprint voorbereiding: "Geef me een overzicht van alle open PROJ-issues die in deze sprint gepland zijn en hun huidige blokkades"',
          'Bug root cause: "PROJ-1567 is een regressie. Zoek naar recente commits en Jira-issues die de betrokken module hebben aangepast"',
        ],
      },
      {
        type: 'code',
        language: 'text',
        code: `// Effectieve developer prompt structuur:
Rovo, analyseer [ISSUE KEY].
Context: ik ben een backend developer werkend aan [component/module].
Mijn vraag: [specifieke technische vraag].
Zoek ook in: [Confluence space / andere Jira projects / GitHub repos].
Output formaat: [bullet list / stap-voor-stap plan / code voorbeeld]`,
      },
      {
        type: 'heading',
        text: '🏗️ Software Architect: ADRs en technische beslissingen',
      },
      {
        type: 'paragraph',
        text: 'Architecten gebruiken Rovo anders dan developers. Het gaat minder over individuele tickets en meer over het grote plaatje: consistentie over meerdere teams, techdebt trends en het bewaken van architectuurprincipes. Rovo kan hier heel waardevol zijn als je hem vraagt om je Confluence spaces en meerdere Jira-projecten tegelijk te doorzoeken.',
      },
      {
        type: 'list',
        items: [
          'ADR genereren: "Schrijf een Architecture Decision Record voor het overstappen van REST naar GraphQL op basis van onze huidige API documentatie in Confluence/API-DOCS"',
          'Techdebt inventaris: "Zoek alle Jira-issues met label \'techdebt\' in PROJ en PLATFORM en geef me een prioriteitstabel op basis van impact en effort"',
          'Consistentie check: "Vergelijk de API-design guidelines in Confluence met de beschrijvingen van de laatste 5 nieuwe endpoints in onze Jira epics"',
          'Dependency analyse: "Welke services zijn er afhankelijk van de order-service op basis van onze service mesh documentatie?"',
          'RFC opstellen: "Stel een RFC op voor het introduceren van event-driven architecture in PLATFORM-team, gebruik de template uit Confluence/RFC-TEMPLATE"',
        ],
      },
      {
        type: 'code',
        language: 'text',
        code: `// Architect prompt voor ADR genereren:
Rovo, ik wil een ADR schrijven over [technische beslissing].

Zoek eerst:
1. Bestaande ADRs in Confluence space "Architecture"
2. Gerelateerde Jira epics in project PLATFORM
3. Eventuele Slack-discussies over dit onderwerp

Schrijf daarna een ADR met de volgende secties:
- Context en probleemstelling
- Overwogen alternatieven (min. 3)
- Beslissing en rationale
- Consequenties (positief en negatief)
- Review datum

Houd de stijl consistent met de bestaande ADRs die je hebt gevonden.`,
      },
      {
        type: 'heading',
        text: '🧪 QA Engineer: testdekking en regressionanalyse',
      },
      {
        type: 'paragraph',
        text: 'Voor QA-engineers is Rovo een enorme tijdsbesparing bij het genereren van testcases en het analyseren van regressions. Rovo kent de acceptance criteria in je Jira-issues en kan die direct omzetten naar concrete testscenario\'s — inclusief edge cases die een mens snel overslaat.',
      },
      {
        type: 'list',
        items: [
          'Test scenario generatie: "Genereer een volledige testmatrix voor PROJ-890 op basis van de acceptance criteria en gerelateerde Confluence test guidelines"',
          'Regressie analyse: "Welke bestaande test cases worden mogelijk beïnvloed door de wijzigingen in PR #178? Zoek in Confluence/QA-TESTCASES"',
          'Bug rapportage: "Schrijf een gedetailleerd bug rapport voor het probleem dat ik beschrijf, volg de template in Confluence/BUG-TEMPLATE en link het aan PROJ-1200"',
          'Release readiness: "Controleer alle issues in de huidige sprint die \'Done\' staan — zijn alle acceptance criteria afgevinkt en zijn er open bugs gelinkt?"',
          'Test coverage gap: "Welke user stories uit PROJ epic \'Checkout flow\' hebben nog geen gelinkte test cases in Zephyr/Confluence?"',
        ],
      },
      {
        type: 'heading',
        text: '📋 Product Manager: backlog en stakeholder communicatie',
      },
      {
        type: 'paragraph',
        text: 'Product managers hebben vaak de uitdaging dat ze informatie uit tientallen bronnen moeten samenvatten: sprint reviews, klantfeedback, technische beperkingen, business requirements. Rovo is hier ideaal voor — geef hem toegang tot meerdere Confluence spaces en Jira-projecten en vraag om syntheses.',
      },
      {
        type: 'list',
        items: [
          'Sprint review samenvatting: "Vat de afgelopen sprint samen voor de stakeholder presentatie: wat is geleverd, wat is geblokkeerd, en wat zijn de risico\'s voor de volgende sprint?"',
          'Roadmap update: "Welke epics in PROJ zijn achter op schema en wat zijn de aangegeven redenen? Geef me een executive summary met aanbevelingen"',
          'User story schrijven: "Schrijf een user story voor het nieuwe betalingsmodule feature op basis van de klantfeedback in Confluence/CUSTOMER-FEEDBACK en de technische constraints in PROJ-ARCH"',
          'Stakeholder rapport: "Maak een weekrapport voor de business stakeholders over de voortgang van PROJ in niet-technische taal"',
          'Prioritering: "Vergelijk alle features in de backlog van PROJ op basis van business value (in de issue-beschrijvingen) en story points — geef een prioriteringsadvies"',
        ],
      },
      {
        type: 'code',
        language: 'text',
        code: `// PM prompt voor stakeholder rapport:
Rovo, maak een stakeholder rapport voor deze week.

Zoek in:
- Jira project PROJ: alle issues die deze week zijn afgerond, geblokkeerd of nieuw aangemaakt
- Confluence space "Product": release notes en roadmap pagina's
- Actuele sprint: velocity en burndown informatie

Schrijf het rapport in niet-technische taal voor een business publiek.
Structuur: Executive Summary (5 zinnen) → Highlights → Risico's → Volgende stap.
Tone: professioneel maar toegankelijk, geen jargon.`,
      },
      {
        type: 'heading',
        text: '🔄 Scrum Master: ceremonies en teamgezondheid',
      },
      {
        type: 'paragraph',
        text: 'Scrum masters gebruiken Rovo het best voor ceremonie-voorbereiding en het identificeren van patronen in het team. Denk aan sprint retro\'s, impediment tracking en het analyseren van velocity trends.',
      },
      {
        type: 'list',
        items: [
          'Retro voorbereiding: "Analyseer de afgelopen 3 sprints in PROJ en identificeer terugkerende patronen in geblokkeerde issues, late deliveries en scope changes"',
          'Daily standup samenvatting: "Geef me een overzicht van alle issues die gisteren van status zijn veranderd in PROJ-sprint-42 en welke issues vandaag \'In Progress\' zijn"',
          'Impediment tracking: "Welke issues in PROJ zijn al meer dan 5 dagen blocked? Wie is de assignee en is er een linked blocker issue?"',
          'Capaciteitsplanning: "Op basis van de story points van de laatste 4 sprints, wat is onze gemiddelde velocity en hoeveel kunnen we plannen voor sprint 43?"',
          'Team health rapport: "Genereer een team health overzicht op basis van sprint data: completion rate, cycle time per story, en frequentie van scope changes"',
        ],
      },
      {
        type: 'heading',
        text: '🔐 Tech Lead: code kwaliteit en kennisdeling',
      },
      {
        type: 'paragraph',
        text: 'Tech leads gebruiken Rovo voor twee grote taken: kennisborging en kwaliteitsbewaking. Rovo kan helpen bij het omzetten van impliciete kennis naar documentatie, en bij het bewaken van coding standards over het hele team.',
      },
      {
        type: 'list',
        items: [
          'Onboarding documentatie: "Schrijf een \'Getting Started\' guide voor nieuwe developers op basis van onze Confluence architectuurpagina\'s en de README in onze GitHub repos"',
          'Coding standards check: "Analyseer de beschrijvingen van de laatste 10 merged PRs in PROJ — worden onze coding guidelines (Confluence/DEV-STANDARDS) consistent gevolgd?"',
          'Knowledge gap detectie: "Welke componenten of services hebben geen of verouderde Confluence documentatie? Vergelijk onze service lijst met gedocumenteerde services"',
          'Mentoring support: "PROJ-2345 is een complex ticket voor een junior developer. Schrijf een technische uitleg met hints zonder de volledige oplossing te geven"',
          'Post-mortem: "Schrijf een post-mortem rapport voor het incident van vorige week op basis van de linked Jira issues en comments, volg de template in Confluence/INCIDENT-TEMPLATE"',
        ],
      },
      {
        type: 'heading',
        text: 'De 5 gouden regels voor effectieve Rovo prompts',
      },
      {
        type: 'list',
        items: [
          '1. Geef altijd een Jira issue key of Confluence page link mee — dan zoekt Rovo in de juiste context in plaats van te gokken',
          '2. Specificeer de output format die je wilt: bullet list, tabel, ADR-template, rapport met secties — Rovo volgt dat nauwkeurig',
          '3. Zeg waar Rovo moet zoeken: "zoek in Confluence space X en Jira project Y" — zonder dit zoekt Rovo te breed',
          '4. Geef je rol en doel aan: "als architect wil ik..." of "als PM moet ik stakeholders informeren over..." — de tone en complexiteit passen zich aan',
          '5. Gebruik iteratieve follow-ups: "verfijn sectie 3 met meer technische detail" of "herschrijf dit voor een niet-technisch publiek" — Rovo onthoudt de context',
        ],
      },
      {
        type: 'heading',
        text: 'Rovo agents vs. Rovo chat: wanneer gebruik je wat?',
      },
      {
        type: 'paragraph',
        text: 'Rovo heeft twee modi: de chat interface (voor ad-hoc vragen) en custom Rovo agents (voor herhaalde, gestandaardiseerde workflows). Een custom agent heeft een vaste instructieset, eigen tools en een specifieke persona. Zo kun je een "Sprint Review Agent" maken die elke vrijdag automatisch de sprint samenvatting genereert en naar Confluence schrijft, of een "PR Description Agent" die bij elke nieuwe pull request automatisch een beschrijving en checklist aanmaakt. De chat interface is perfect voor eenmalige analyses. Custom agents zijn de kracht voor herhaalde processen die je wilt standaardiseren over het hele team.',
      },
      {
        type: 'code',
        language: 'text',
        code: `// Voorbeeld: Custom Rovo Agent instructies voor "Sprint Review Agent"

Naam: Sprint Review Generator
Rol: Je bent een Scrum Master assistent die sprint reviews genereert.

Bij activatie:
1. Zoek de actieve sprint in het Jira project dat de gebruiker aangeeft
2. Haal alle completed, incomplete en carried-over issues op
3. Bereken de velocity (afgeronde SP / geplande SP)
4. Zoek de sprint goals in de sprint beschrijving
5. Genereer een sprint review in deze structuur:
   - Sprint doel: behaald/niet behaald + reden
   - Geleverd: lijst van completed issues met korte beschrijving
   - Niet geleverd: lijst met reden
   - Velocity: getal + trend tov vorige 3 sprints
   - Top 3 learnings voor de retro
   - Risico's voor volgende sprint

Output: schrijf de pagina naar Confluence space "Sprint Reviews" als nieuwe pagina
met titel "Sprint [nummer] Review - [datum]".`,
      },
      {
        type: 'heading',
        text: 'Praktisch beginnen: je eerste week met Rovo',
      },
      {
        type: 'paragraph',
        text: 'Je hoeft niet meteen alles te automatiseren. Begin klein. Kies één herhaalde taak per rol en probeer die eerste week consequent via Rovo te doen. Als developer: gebruik Rovo voor elk ticket dat je oppakt. Als PM: laat Rovo je weekly status rapport schrijven. Als QA: genereer je testcases via Rovo. Na één week weet je precies welke prompts werken, welke je moet verfijnen, en waar je nog handmatige aanpassingen nodig hebt. Vanuit dat inzicht bouw je stap voor stap naar custom agents en volledig geautomatiseerde workflows.',
      },
      {
        type: 'quote',
        text: 'De teams die het meeste halen uit Rovo zijn niet degenen die de meest complexe agents bouwen — het zijn degenen die consequent dezelfde goede prompts gebruiken voor hun dagelijkse taken.',
      },
      {
        type: 'paragraph',
        text: 'Rovo is volop in ontwikkeling. De mogelijkheden van vandaag zijn al indrukwekkend, maar Atlassian voegt continu nieuwe integraties en agent-capabilities toe. Investeer nu in het leren van goede prompt-gewoontes — dat is de vaardigheid die je het langst bijblijft, ongeacht welke nieuwe features er komen. Vragen over specifieke Rovo use cases voor jouw team? Reach out — ik help graag.',
      },
    ],
  },
  {
    slug: 'smart-home-esp32-mqtt-ai',
    titel: 'Mijn Smart Home: ESP32, MQTT, Home Assistant en een AI fleet die alles bestuurt',
    excerpt:
      'Van losse sensoren naar een volledig geïntegreerd smart home platform — hoe ik ESP32-nodes, een MQTT-bus, Home Assistant dashboards en een AI agent fleet combineer tot één slim ecosysteem.',
    datum: '21 april 2026',
    datumISO: '2026-04-21',
    leestijd: '15 min',
    categorie: 'IoT',
    categorieKleur: 'bg-green-500/20 text-green-400 border-green-500/30',
    afbeelding:
      'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?auto=format&fit=crop&w=800&q=80',
    inhoud: [
      {
        type: 'paragraph',
        text: 'Mijn huis is mijn lab. Elke kamer heeft sensoren. Elk apparaat communiceert via een centrale broker. En ondertussen draaien er AI agents die patronen herkennen, anomalieën signaleren en automatisch actie ondernemen. Klinkt futuristisch? Dat is het niet — met ESP32, MQTT, Home Assistant en een klein beetje Python is dit vandaag volledig haalbaar voor ieder. In dit artikel laat ik je zien hoe ik het stap voor stap heb opgebouwd, inclusief alle code en configuratie.',
      },
      {
        type: 'heading',
        text: 'De architectuur in één oogopslag',
      },
      {
        type: 'paragraph',
        text: 'Voordat we in de code duiken, is het belangrijk om het grote plaatje te begrijpen. Het systeem bestaat uit drie lagen. De eerste laag zijn de ESP32-nodes: kleine microcontrollers met sensoren die overal in huis hangen. Ze meten temperatuur, luchtvochtigheid, beweging, licht en luchtkwaliteit. De tweede laag is de MQTT-bus: een lichtgewicht publish/subscribe protocol waarover alle nodes communiceren met een centrale Mosquitto broker op een Raspberry Pi. De derde laag is de intelligence laag: Home Assistant verwerkt de data en toont dashboards, terwijl Python AI agents op de achtergrond patronen analyseren en slimme automatiseringen triggeren.',
      },
      {
        type: 'list',
        items: [
          'ESP32 DevKit C — microcontroller per ruimte',
          'DHT22 — temperatuur & luchtvochtigheid',
          'PIR HC-SR501 — bewegingsdetectie',
          'BMP280 — luchtdruk & hoogte',
          'MQ-135 — luchtkwaliteit (CO₂ indicatie)',
          'Mosquitto MQTT broker op Raspberry Pi 4',
          'Home Assistant OS op dezelfde Pi',
          'Python AI fleet op mijn lokale server',
        ],
      },
      {
        type: 'heading',
        text: 'Stap 1: ESP32 nodes opzetten',
      },
      {
        type: 'paragraph',
        text: 'Elke ESP32 node heeft dezelfde basis firmware. Ik gebruik Arduino-framework met PlatformIO voor dependency management. De node verbindt met WiFi, leest alle aangesloten sensoren uit, en publiceert de data elke 30 seconden op een gestructureerd MQTT topic. Het topic-schema is cruciaal — ik gebruik een hiërarchie die Home Assistant automatisch kan ontdekken via MQTT Discovery.',
      },
      {
        type: 'code',
        language: 'cpp',
        code: `// platformio.ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
lib_deps =
  knolleary/PubSubClient@^2.8
  adafruit/DHT sensor library@^1.4.4
  adafruit/Adafruit BMP280 Library@^2.6.8

// main.cpp — vereenvoudigd
#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

const char* ROOM = "woonkamer";  // Per node aanpassen
const char* MQTT_HOST = "192.168.1.10";

DHT dht(4, DHT22);
WiFiClient espClient;
PubSubClient mqtt(espClient);

void publishSensorData() {
  StaticJsonDocument<256> doc;
  doc["temp"]     = dht.readTemperature();
  doc["humidity"] = dht.readHumidity();
  doc["room"]     = ROOM;
  doc["uptime"]   = millis() / 1000;

  char payload[256];
  serializeJson(doc, payload);

  // Topic: huis/{room}/klimaat
  String topic = String("huis/") + ROOM + "/klimaat";
  mqtt.publish(topic.c_str(), payload, true);  // retained = true
}

void loop() {
  mqtt.loop();
  static unsigned long last = 0;
  if (millis() - last > 30000) {
    publishSensorData();
    last = millis();
  }
}`,
      },
      {
        type: 'heading',
        text: 'Stap 2: MQTT Discovery voor Home Assistant',
      },
      {
        type: 'paragraph',
        text: 'Home Assistant heeft een krachtige MQTT Discovery feature: als een device een configuratiebericht publiceert op een speciaal topic, registreert HA het apparaat automatisch zonder dat je YAML hoeft te schrijven. Dit maakt het toevoegen van nieuwe ESP32 nodes triviaal — één publicatie en de sensor staat in je dashboard.',
      },
      {
        type: 'code',
        language: 'cpp',
        code: `void registerWithHomeAssistant() {
  // Publiceer discovery configuratie voor temperatuursensor
  String config_topic = "homeassistant/sensor/esp32_" 
                      + String(ROOM) + "_temp/config";
  
  StaticJsonDocument<512> cfg;
  cfg["name"]          = String(ROOM) + " Temperatuur";
  cfg["unique_id"]     = String("esp32_") + ROOM + "_temp";
  cfg["state_topic"]   = String("huis/") + ROOM + "/klimaat";
  cfg["value_template"] = "{{ value_json.temp }}";
  cfg["unit_of_measurement"] = "°C";
  cfg["device_class"]  = "temperature";
  
  // Device info — groepeert sensoren per kamer
  JsonObject device = cfg.createNestedObject("device");
  device["identifiers"][0] = String("esp32_") + ROOM;
  device["name"]            = String("Sensor ") + ROOM;
  device["model"]           = "ESP32 DHT22";
  device["manufacturer"]    = "VorstersNV DIY";

  char payload[512];
  serializeJson(cfg, payload);
  mqtt.publish(config_topic.c_str(), payload, true);
}`,
      },
      {
        type: 'heading',
        text: 'Stap 3: Home Assistant — de optimale dashboard setup',
      },
      {
        type: 'paragraph',
        text: 'Home Assistant dashboards kunnen er standaard nogal generiek uitzien. Met de juiste combinatie van custom cards en een doordachte layout maak je er een professioneel command center van. Ik gebruik drie dashboards: een overzichtsdashboard voor dagelijks gebruik, een analytics dashboard voor trends en patronen, en een systeem dashboard voor de gezondheid van alle nodes.',
      },
      {
        type: 'list',
        items: [
          'HACS (Home Assistant Community Store) — voor custom cards',
          'mushroom-cards — moderne, compacte kaartjes per kamer',
          'mini-graph-card — mooie grafieken voor sensortrends',
          'apexcharts-card — geavanceerde visualisaties met meerdere series',
          'layout-card — flexibele grid layout voor het dashboard',
          'browser_mod — browser-specifieke instellingen en popups',
        ],
      },
      {
        type: 'code',
        language: 'yaml',
        code: `# dashboard/woonkamer.yaml — Mushroom room card voorbeeld
type: custom:mushroom-template-card
primary: Woonkamer
secondary: >
  {{ states('sensor.woonkamer_temperatuur') }}°C · 
  {{ states('sensor.woonkamer_luchtvochtigheid') }}%
icon: mdi:sofa
icon_color: >
  {% set temp = states('sensor.woonkamer_temperatuur') | float %}
  {% if temp > 23 %} red
  {% elif temp < 18 %} blue
  {% else %} green {% endif %}
tap_action:
  action: navigate
  navigation_path: /lovelace/woonkamer-detail

# Mini-graph voor trends
- type: custom:mini-graph-card
  entities:
    - entity: sensor.woonkamer_temperatuur
      name: Temperatuur
      color: '#ef4444'
    - entity: sensor.woonkamer_luchtvochtigheid
      name: Vochtigheid
      color: '#3b82f6'
  hours_to_show: 24
  points_per_hour: 4
  line_width: 2
  show:
    labels: true
    points: false
    legend: true`,
      },
      {
        type: 'heading',
        text: 'Stap 4: Automations — het huis laten reageren',
      },
      {
        type: 'paragraph',
        text: 'Dashboards zijn leuk, maar automations zijn de echte kracht. Home Assistant automations worden beschreven in YAML en kunnen reageren op elke sensor, tijdstip of externe trigger. Mijn favoriete automations zijn de comfort-alerts (melding als een kamer te warm of te koud wordt), aanwezigheidsdetectie (koppeling met telefoon GPS), en energie-optimalisatie (apparaten uitschakelen als niemand thuis is).',
      },
      {
        type: 'code',
        language: 'yaml',
        code: `# automations.yaml — Temperatuuralert
- id: temp_alert_slaapkamer
  alias: "Alert: slaapkamer te warm"
  trigger:
    - platform: numeric_state
      entity_id: sensor.slaapkamer_temperatuur
      above: 24
      for:
        minutes: 10
  condition:
    - condition: time
      after: "22:00:00"
      before: "08:00:00"
  action:
    - service: notify.mobile_app_koen_telefoon
      data:
        title: "🌡️ Slaapkamer te warm"
        message: >
          Slaapkamer is {{ states('sensor.slaapkamer_temperatuur') }}°C.
          Raam openzetten aanbevolen.
    - service: mqtt.publish
      data:
        topic: "huis/ai/events"
        payload: >
          {"event": "temp_alert", "room": "slaapkamer",
           "value": "{{ states('sensor.slaapkamer_temperatuur') }}",
           "severity": "warning"}`,
      },
      {
        type: 'heading',
        text: 'Stap 5: De AI fleet integreren',
      },
      {
        type: 'paragraph',
        text: 'Tot hier is alles vrij standaard Home Assistant gebruik. Nu wordt het interessant. Ik heb een Python AI fleet draaien die luistert op het MQTT topic "huis/ai/events" en intelligent reageert. Elke sensor-anomalie triggert een event, de AI fleet analyseert het patroon over tijd, en kan aanbevelingen doen of zelfs automatisch ingrijpen. Het is de laag boven Home Assistant — niet ter vervanging, maar als intelligente co-piloot.',
      },
      {
        type: 'code',
        language: 'python',
        code: `# ai_fleet/smart_home_agent.py
import json
import paho.mqtt.client as mqtt
from dataclasses import dataclass
from collections import deque
from datetime import datetime

@dataclass
class SensorEvent:
    room: str
    event_type: str
    value: float
    timestamp: datetime

class SmartHomeAgent:
    """AI agent die patronen detecteert in sensordata."""
    
    def __init__(self, mqtt_host: str = "192.168.1.10"):
        self.history: dict[str, deque] = {}  # room -> laatste 100 events
        self.client = mqtt.Client()
        self.client.on_message = self._on_message
        self.client.connect(mqtt_host)
        self.client.subscribe("huis/#")
    
    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        try:
            data = json.loads(msg.payload)
        except json.JSONDecodeError:
            return
        
        room = topic.split("/")[1] if "/" in topic else "unknown"
        
        if room not in self.history:
            self.history[room] = deque(maxlen=100)
        
        # Sla op in history
        if "temp" in data:
            event = SensorEvent(
                room=room,
                event_type="temperature",
                value=data["temp"],
                timestamp=datetime.now()
            )
            self.history[room].append(event)
            self._analyze(event)
    
    def _analyze(self, event: SensorEvent):
        """Analyseer of dit event afwijkt van het patroon."""
        history = self.history.get(event.room, [])
        temps = [e.value for e in history if e.event_type == "temperature"]
        
        if len(temps) < 10:
            return  # Onvoldoende data
        
        avg = sum(temps) / len(temps)
        deviation = abs(event.value - avg)
        
        if deviation > 3.0:  # Meer dan 3°C afwijking
            self._publish_insight(
                room=event.room,
                message=f"Ongewone temperatuurschommeling: {event.value:.1f}°C "
                        f"(gemiddelde: {avg:.1f}°C, afwijking: {deviation:.1f}°C)",
                severity="warning" if deviation > 5 else "info"
            )
    
    def _publish_insight(self, room: str, message: str, severity: str):
        """Publiceer AI inzicht terug naar MQTT voor HA notificatie."""
        payload = json.dumps({
            "source": "ai_fleet",
            "room": room,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        })
        self.client.publish("huis/ai/insights", payload)
        print(f"[AI] {room}: {message}")
    
    def run(self):
        print("Smart Home AI Agent gestart...")
        self.client.loop_forever()

if __name__ == "__main__":
    SmartHomeAgent().run()`,
      },
      {
        type: 'heading',
        text: 'Home Assistant luistert naar AI inzichten',
      },
      {
        type: 'paragraph',
        text: 'De AI agent publiceert zijn inzichten op het topic "huis/ai/insights". Home Assistant heeft een automation die op dit topic luistert en de insights doorstuurde als notificatie of als kaartje op het dashboard. Zo heb je een bidirectionele koppeling: HA stuurt events naar AI, AI stuurt inzichten terug naar HA.',
      },
      {
        type: 'code',
        language: 'yaml',
        code: `# configuration.yaml — MQTT sensor voor AI insights
mqtt:
  sensor:
    - name: "AI Inzicht Laatste"
      state_topic: "huis/ai/insights"
      value_template: "{{ value_json.message }}"
      json_attributes_topic: "huis/ai/insights"
      json_attributes_template: >
        {{ {"room": value_json.room, 
            "severity": value_json.severity,
            "timestamp": value_json.timestamp} | tojson }}

# automation — stuur AI inzicht als notificatie
- id: ai_insight_notification
  alias: "AI Fleet: stuur inzicht als notificatie"
  trigger:
    - platform: mqtt
      topic: "huis/ai/insights"
  condition:
    - condition: template
      value_template: >
        {{ trigger.payload_json.severity in ['warning', 'critical'] }}
  action:
    - service: notify.mobile_app_koen_telefoon
      data:
        title: "🤖 AI Inzicht — {{ trigger.payload_json.room }}"
        message: "{{ trigger.payload_json.message }}"`,
      },
      {
        type: 'heading',
        text: 'Energie dashboard: inzicht in verbruik',
      },
      {
        type: 'paragraph',
        text: 'Naast klimaatbeheer heb ik ook slimme stekkers (Shelly Plus 1PM) gekoppeld via MQTT. Die meten het stroomverbruik van individuele apparaten. In combinatie met het HA Energy dashboard krijg ik per dag, week en maand een overzicht van wat de grote verbruikers zijn. De AI agent analyseert patronen: als een apparaat plots meer verbruikt dan normaal, kan dat wijzen op een defect — een vroege waarschuwing die me al eens een dure reparatie heeft bespaard.',
      },
      {
        type: 'quote',
        text: 'Mijn smart home is geen gadget. Het is een lerende infrastructuur die me elke week iets nieuws vertelt over hoe ik woon, energie gebruik en kan optimaliseren.',
      },
      {
        type: 'heading',
        text: 'Tips voor de optimale Home Assistant setup',
      },
      {
        type: 'list',
        items: [
          'Gebruik een Raspberry Pi 4 met SSD (geen SD-kaart) — veel betrouwbaarder en sneller',
          'Zet Home Assistant OS op, niet de Docker versie — updates zijn eenvoudiger',
          'Gebruik MQTT retained messages voor sensoren — dan zijn waarden direct zichtbaar na herstart',
          'Maak aparte dashboards per doel: overzicht, analytics, systeem — één dashboard wordt snel onoverzichtelijk',
          'Gebruik Lovelace YAML mode voor versiecontrole van je dashboard config',
          'Backup automatisch via de ingebouwde Google Drive integratie',
          'Gebruik Node-RED voor complexe automations — visueel programmeren is veel makkelijker dan YAML',
          'Koppel je AI agent via MQTT, niet via de REST API — veel lichter en real-time',
        ],
      },
      {
        type: 'heading',
        text: 'OTA updates: nooit meer fysiek bij de sensor',
      },
      {
        type: 'paragraph',
        text: 'Een van de grootste ergernissen bij hardware projecten: je moet elke sensor fysiek bereiken om firmware te updaten. Met OTA (Over The Air) updates via het ArduinoOTA library stuur ik firmware updates via WiFi. Ik heb een eenvoudig Python script dat alle ESP32-nodes in het netwerk detecteert en de nieuwe firmware pusht. De nodes hervatten automatisch na de update en zijn binnen 30 seconden weer online.',
      },
      {
        type: 'code',
        language: 'python',
        code: `# ota_updater.py — update alle ESP32 nodes via netwerk
import subprocess
import json
from pathlib import Path

NODES = {
    "woonkamer":  "192.168.1.101",
    "slaapkamer": "192.168.1.102",
    "keuken":     "192.168.1.103",
    "bureau":     "192.168.1.104",
}

FIRMWARE = Path("build/esp32dev/firmware.bin")

def update_node(naam: str, ip: str) -> bool:
    print(f"Updaten: {naam} ({ip})...")
    result = subprocess.run([
        "python", "-m", "esptool",
        "--chip", "esp32",
        "--port", f"socket://{ip}:3232",  # OTA port
        "--baud", "115200",
        "write_flash", "0x10000", str(FIRMWARE)
    ], capture_output=True, text=True)
    
    success = result.returncode == 0
    status = "✅ OK" if success else f"❌ FOUT: {result.stderr[:100]}"
    print(f"  {naam}: {status}")
    return success

if __name__ == "__main__":
    results = {naam: update_node(naam, ip) for naam, ip in NODES.items()}
    ok = sum(results.values())
    print(f"\\nResultaat: {ok}/{len(NODES)} nodes succesvol bijgewerkt")`,
      },
      {
        type: 'heading',
        text: 'Wat ik geleerd heb',
      },
      {
        type: 'list',
        items: [
          'Begin klein — één kamer, één sensor. Uitbreiden is eenvoudig als de basis goed zit.',
          'MQTT retained messages zijn essentieel — zonder retained heeft HA geen waarde bij herstart.',
          'Geef elke node een uniek, beschrijvend topic-schema — dit bespaart verwarring later.',
          'Home Assistant MQTT Discovery is magie — gebruik het, schrijf geen manuele YAML sensors.',
          'AI agents via MQTT koppelen is eleganter dan REST polling — real-time en lichtgewicht.',
          'Dashboard ontwerp is werk — mushroom-cards + layout-card is de beste combinatie.',
          'Sla sensorhistorie op in InfluxDB + Grafana voor langetermijnanalyse die HA self niet biedt.',
          'OTA updates zijn geen luxe maar een must — maak het vanaf dag 1 in je firmware.',
        ],
      },
      {
        type: 'paragraph',
        text: 'Wil je zelf aan de slag? De volledige broncode van mijn ESP32 firmware, de Python AI agent en de Home Assistant YAML configuraties staan op mijn GitHub. Vragen of ideeën? Stuur me een bericht — ik help graag. En als je zelf een interessant smart home project hebt, hoor ik het ook graag!',
      },
    ],
  },
  {
    slug: 'ai-control-platform-bouwen',
    titel: 'Hoe ik in enkele dagen een enterprise AI-platform bouwde (en wat ik ervan leerde)',
    excerpt:
      'Van losse AI-agents naar een volledig bestuurd platform met governance, auditing en automatische kwaliteitsbewaking. Hier is wat er werkelijk achter de schermen gebeurt.',
    datum: '21 april 2026',
    datumISO: '2026-04-21',
    leestijd: '12 min',
    categorie: 'AI',
    categorieKleur: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
    afbeelding:
      'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=800&q=80',
    inhoud: [
      {
        type: 'paragraph',
        text: 'De meeste mensen denken dat AI gewoon een chatbot is. Je typt iets, het systeem antwoordt, klaar. Maar wat als je AI niet één vraag wil laten beantwoorden, maar wil inzetten in een heel bedrijfsproces? Wat als je wilt dat AI automatisch reageert op binnenkomende bestellingen, dat het zichzelf verbetert op basis van resultaten, en dat elke beslissing die het neemt netjes wordt bijgehouden voor de boekhouder of auditor? Dan heb je iets heel anders nodig dan een chatbot. Dan heb je een AI Control Platform nodig — en dat is exact wat ik de afgelopen dagen heb gebouwd.',
      },
      {
        type: 'heading',
        text: 'Wat is een AI Control Platform eigenlijk?',
      },
      {
        type: 'paragraph',
        text: 'Vergelijk het met een vliegtuig. Een vliegtuig heeft motoren, maar die motoren vliegen niet zelfstandig. Er is een cockpit die alles bestuurt: welke motor op welk vermogen draait, of de vleugelkleppen open of dicht zijn, hoe hoog en snel het toestel vliegt. De piloot geeft de opdracht, de cockpit vertaalt dat naar duizenden kleine beslissingen. Zo werkt een AI Control Platform ook. De AI-modellen (zoals een lokaal Ollama-model op mijn eigen server) zijn de "motoren" — krachtig, maar blind zonder sturing. De Control Plane is de cockpit. Die beslist welk AI-model welke taak krijgt, hoeveel het mag kosten, hoe risicovol de operatie is, en of er een mens moet meekijken. Elke beslissing wordt geregistreerd in een Decision Journal. Alles wordt gemeten door een Quality Monitor. En wanneer een bepaalde aanpak beter werkt dan een andere, promoot een A/B-systeem die automatisch. Het is AI die zichzelf bestuurt én bewaakt — maar altijd onder menselijk toezicht.',
      },
      {
        type: 'heading',
        text: 'Het probleem: losse agents zijn gevaarlijk',
      },
      {
        type: 'paragraph',
        text: 'Voordat ik dit platform bouwde, had ik al een werkend multi-agent systeem. Dat systeem kon klantenservice beantwoorden, productbeschrijvingen schrijven en bestellingen verwerken. Maar het was een verzameling losse scripts die samenleefden in een map. Geen centraal overzicht. Geen idee welk model wanneer werd aangeroepen. Geen manier om te zeggen: "dit AI-model mag maximaal €0,50 per aanroep kosten" of "voor medische informatie moet er altijd een mens meekijken". Dat is het probleem met losse AI-agents op schaal: ze zijn zoals werknemers zonder manager, zonder onkostennota en zonder evaluatiegesprek. Het werkt — totdat het niet meer werkt, en dan weet je niet waarom.',
      },
      {
        type: 'quote',
        text: 'AI zonder governance is zoals een team zonder manager: alles lijkt goed te gaan tot de eerste crisis, en dan weet niemand meer wie wat heeft beslist.',
      },
      {
        type: 'heading',
        text: 'Wave 1: Het fundament leggen',
      },
      {
        type: 'paragraph',
        text: 'Ik heb het platform opgebouwd in zes "waves" — iteratieve bouwfases waarbij elke wave voortbouwt op de vorige. De eerste wave draait om vertrouwen en structuur. Ik heb getypeerde contracten gedefinieerd in Python: wat is een AIRequest? Wat is een AIResponse? Wat is een PolicyViolation? Dit klinkt technisch, maar het idee is simpel: als alles dezelfde "taal" spreekt, kun je fouten vroeg opvangen. Dan is er de Policy Engine. Dat is een verzameling governance-regels, geschreven als gewone YAML-bestanden. Zoiets als: "Voor alle aanroepen met een risicoscore hoger dan 7, stuur altijd een notificatie naar de manager." Of: "Agents op maturity level 1 (experimenteel) mogen niet draaien in productie." Ten slotte is er het Decision Journal — een logboek van elke beslissing die het systeem neemt. Elke AI-aanroep krijgt een unieke trace-ID, een tijdstempel, de redenering en het eindoordeel. Dat is niet alleen handig voor debugging; het is essentieel als je ooit aan een klant of regelgever moet verantwoorden waarom het systeem iets heeft gedaan.',
      },
      {
        type: 'heading',
        text: 'De Control Plane: wie beslist wat?',
      },
      {
        type: 'paragraph',
        text: 'De Control Plane is het hart van het platform. Elke keer als iemand of iets AI wil gebruiken, gaat de aanroep door de Control Plane. Die kijkt naar acht dimensies tegelijk: wat is de gevraagde capability (klantenservice? SEO? analyse?), wat is de risicoscore van deze taak, in welke omgeving zitten we (test of productie?), wat is het budget, hoeveel latency is acceptabel, welk model past, zijn er actieve policies die dit beperken, en in welke deployment ring zitten we? Op basis van die acht factoren beslist de Control Plane welke agent de taak uitvoert — of blokt hij de aanroep als die niet door de governancecheck komt.',
      },
      {
        type: 'code',
        language: 'python',
        code: '# Zo stroomt een aanroep door het systeem\nrequest = AIRequest(\n    capability="customer_service",\n    input="Ik wil mijn bestelling annuleren",\n    risk_score=3,\n    environment="production",\n    budget_eur=0.10,\n)\n\n# Control Plane valideert en routeert\nresult = await control_plane.route(request)\n# → Policy Engine: OK (risk 3 < threshold 7)\n# → Agent Runner: mistral via Ollama\n# → Cost Governance: €0.002 verbruikt\n# → Decision Journal: trace_id=abc123, verdict=APPROVED\n# → Quality Monitor: latency 340ms, score 0.87\n\nprint(result.antwoord)  # "Uw bestelling is geannuleerd..."',
      },
      {
        type: 'heading',
        text: 'Quality Monitor & A/B Testing: zelflerende AI',
      },
      {
        type: 'paragraph',
        text: 'Een van de onderdelen waar ik het meest trots op ben, is de combinatie van Quality Monitor en AutoPromoter. De Quality Monitor houdt bij hoe goed elke agent presteert: hoe snel antwoordt hij, hoe hoog scoort het antwoord, hoeveel fouten maakt hij? Als de score onder een drempel zakt, gooit het systeem automatisch een alert — DEGRADED of zelfs CRITICAL. Dan is er de A/B Tester. Stel je voor: je hebt twee versies van een prompt voor klantenservice. Versie A zegt "Wees vriendelijk en formeel." Versie B zegt "Wees empathisch en gebruik de voornaam van de klant." Je laat beide versies draaien op echte aanroepen, meet welke beter scoort, en zodra versie B statistisch significant beter is, promoot de AutoPromoter die automatisch naar productie. Geen handmatige ingreep nodig. De AI optimaliseert zichzelf — maar op een gecontroleerde, meetbare manier.',
      },
      {
        type: 'heading',
        text: 'Event Bridge: webhooks worden slim',
      },
      {
        type: 'paragraph',
        text: 'Een van de krachtigste features van het platform is de Event Bridge. Die verbindt externe events (webhooks) met AI skill chains. Een praktisch voorbeeld: als er een nieuwe bestelling binnenkomt in je webshop, stuurt je systeem een webhook naar het platform. De Event Bridge vangt dat event op, herkent het als een "order_created" event, en start automatisch een AI-keten: eerst analyseert een agent de bestelling op fraudepatronen, dan genereert een andere agent een gepersonaliseerde bevestigingsmail, en tot slot wordt alles gelogd in het Decision Journal. Dat alles zonder dat een mens het hoeft aan te sturen. Hetzelfde werkt voor "payment_failed" events: automatisch een vriendelijke herinneringsmail opstellen, klantsegment bepalen, en escaleren als het al de derde keer is. Dit is wat ik bedoel met "event-driven AI": het systeem reageert intelligent op wat er in de wereld gebeurt.',
      },
      {
        type: 'heading',
        text: '1389 tests later...',
      },
      {
        type: 'paragraph',
        text: 'Het platform heeft op dit moment 1389 geautomatiseerde tests die allemaal slagen. Dat getal klinkt indrukwekkend, maar wat betekent het in de praktijk? Het betekent dat als ik morgen een nieuwe feature toevoeg, ik binnen seconden weet of ik iets heb gebroken. Het betekent dat ik met vertrouwen kan refactoren — code opruimen, verbeteren, optimaliseren — zonder angst dat ergens stiekem iets kapotgaat. En het betekent dat elk kritiek stuk logica — de Policy Engine, het Decision Journal, de AutoPromoter — expliciet gedocumenteerd is in de vorm van testcases. Die tests zijn mijn vangnet. Ze zijn ook mijn documentatie. Als je wilt weten hoe het systeem zich gedraagt als een agent een timeout krijgt, lees je de test. Als je wilt weten wat er gebeurt als een policy wordt geschonden, lees je de test. Voor een enterprise-omgeving is dat niet een nice-to-have — het is een vereiste.',
      },
      {
        type: 'heading',
        text: 'Wat ik geleerd heb',
      },
      {
        type: 'list',
        items: [
          'Governance eerst, features later. Het was verleidelijk om meteen coole AI-features te bouwen, maar zonder een solide fundament van policies en audit trails wordt alles een grote spaghetti.',
          'YAML als governance-taal werkt verrassend goed. Business-regels in YAML zijn leesbaar voor niet-ontwikkelaars en kunnen worden beheerd als configuratie, niet als code.',
          'Typed contracts zijn goud waard. Als elke component dezelfde datastructuren gebruikt, vind je fouten in seconden in plaats van uren.',
          'Automatisch testen is niet optioneel bij AI. AI-gedrag is inherent probabilistisch — je kunt niet "even in je hoofd controleren" of het klopt. Je hebt tests nodig.',
          'Event-driven architectuur maakt AI pas echt nuttig. AI die reageert op wat er in je bedrijf gebeurt, is waardevoller dan AI die je handmatig aanroept.',
          'Begin klein, bouw modulair. Elke wave voegde één laag toe. Dat maakte het overzichtelijk en veilig — en ik kon altijd terugvallen op wat al werkte.',
        ],
      },
      {
        type: 'paragraph',
        text: 'Dit project heeft me laten zien dat enterprise AI niet draait om de nieuwste modellen of de duurste cloudoplossingen. Het draait om structuur, vertrouwen en controle. Hetzelfde wat een goede manager doet voor een team, doet een AI Control Platform voor je agents. Ben je benieuwd hoe zoiets er voor jouw organisatie uit zou kunnen zien? Of wil je weten hoe dit te integreren met je bestaande systemen? Stuur me een bericht — ik denk graag mee.',
      },
    ],
  },
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
  {
    slug: 'advanced-ai-workshop-langflow',
    titel: 'Advanced AI Workshop: een project bouwen met Langflow',
    excerpt:
      'Verslag van mijn advanced AI-workshop: van visueel flows bouwen in Langflow tot het koppelen van lokale LLMs, vector stores en externe APIs in een volledig werkend AI-project.',
    datum: '10 april 2026',
    datumISO: '2026-04-10',
    leestijd: '10 min',
    categorie: 'AI',
    categorieKleur: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
    afbeelding:
      'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=800&q=80',
    inhoud: [
      {
        type: 'paragraph',
        text: 'Vorige week nam ik deel aan een geavanceerde AI-workshop met als centraal thema: een volledig AI-project bouwen met Langflow. Langflow is een visuele, drag-and-drop tool waarmee je LLM-pipelines en AI-agents bouwt zonder meteen diep in code te duiken — perfect om snel te prototypen en te experimenteren. Dit is mijn verslag van wat ik leerde, wat er misging, en wat ik meeneem naar mijn eigen projecten.',
      },
      {
        type: 'heading',
        text: 'Wat is Langflow?',
      },
      {
        type: 'paragraph',
        text: 'Langflow is een open-source UI bovenop LangChain. Je bouwt "flows" — visuele grafen van componenten die je aan elkaar koppelt: een LLM hier, een vector store daar, een tool of API-call eraan vast. Wat normaal tientallen regels Python vraagt, bouw je in Langflow in een paar minuten samen. Het eindresultaat kan je exporteren als JSON of rechtstreeks deployen via de ingebouwde API.',
      },
      {
        type: 'list',
        items: [
          'Visuele flow-builder: drag-and-drop componenten verbinden',
          'Ingebouwde support voor OpenAI, Ollama, HuggingFace en meer',
          'Vector store integraties: Chroma, Pinecone, Weaviate',
          'Tool-calling en agents bouwen zonder code',
          'REST API endpoint automatisch gegenereerd per flow',
          'Export naar Python-code voor verdere customisatie',
        ],
      },
      {
        type: 'heading',
        text: 'De workshop: wat we bouwden',
      },
      {
        type: 'paragraph',
        text: 'De workshop was opgedeeld in drie blokken. Eerst een theoretisch overzicht van de LangChain-architectuur en hoe Langflow daar bovenop zit. Dan een hands-on sessie waarbij we een RAG-pipeline (Retrieval-Augmented Generation) bouwden: een AI die antwoorden baseert op je eigen documenten. Tot slot een geavanceerd blok over agents en tool-gebruik.',
      },
      {
        type: 'heading',
        text: 'Blok 1 – RAG-pipeline bouwen',
      },
      {
        type: 'paragraph',
        text: 'Het eerste project: een chatbot die vragen beantwoordt op basis van een set PDF-documenten. In Langflow sleep je een "File Loader" component, koppel je die aan een "Text Splitter", dan aan een "Chroma" vector store, en verbind je die met een "Retrieval QA Chain". Je kiest je LLM-model (we gebruikten Ollama met llama3 lokaal) en klikt op Run. Dat is het.',
      },
      {
        type: 'code',
        language: 'json',
        code: `// Vereenvoudigde flow-structuur (Langflow JSON export)
{
  "nodes": [
    { "id": "loader", "type": "PyPDFLoader", "data": { "file_path": "./docs/" } },
    { "id": "splitter", "type": "CharacterTextSplitter", "data": { "chunk_size": 500 } },
    { "id": "vectorstore", "type": "Chroma", "data": { "collection": "workshop-docs" } },
    { "id": "llm", "type": "Ollama", "data": { "model": "llama3" } },
    { "id": "chain", "type": "RetrievalQA" }
  ],
  "edges": [
    { "source": "loader", "target": "splitter" },
    { "source": "splitter", "target": "vectorstore" },
    { "source": "vectorstore", "target": "chain" },
    { "source": "llm", "target": "chain" }
  ]
}`,
      },
      {
        type: 'paragraph',
        text: 'De kracht zit hem in de snelheid: van nul naar een werkende RAG-chatbot in minder dan 30 minuten. En omdat alles lokaal draait via Ollama, is er geen data die naar externe servers gaat — essentieel als je met gevoelige bedrijfsdocumenten werkt.',
      },
      {
        type: 'heading',
        text: 'Blok 2 – Agents en tool-gebruik',
      },
      {
        type: 'paragraph',
        text: 'Het tweede deel was het interessantste: agents bouwen die zelfstandig tools kunnen aanroepen. We bouwden een agent die het weer kon opvragen, berekeningen kon uitvoeren, en in een database kon zoeken. In Langflow definieer je de tools als aparte componenten en koppel je ze aan een "Agent" node. De LLM beslist zelf welke tool hij aanroept op basis van de vraag.',
      },
      {
        type: 'list',
        items: [
          'Calculator tool: de LLM kan zelf wiskunde uitvoeren',
          'Web search tool: zoeken op het internet voor actuele info',
          'API tool: aanroepen van een externe REST-endpoint',
          'Python REPL: willekeurige Python-code uitvoeren als tool',
          'Geheugen: de agent onthoudt de conversatiegeschiedenis',
        ],
      },
      {
        type: 'quote',
        text: '"Een agent is geen chatbot die antwoorden geeft — het is een autonome werker die taken uitvoert. Geef hem de juiste tools en hij lost problemen op die je zelf niet had voorzien."',
      },
      {
        type: 'heading',
        text: 'Blok 3 – Multi-agent orkestratie',
      },
      {
        type: 'paragraph',
        text: 'Het geavanceerdste onderdeel: meerdere agents laten samenwerken. Eén agent analyseert de vraag, een tweede zoekt relevante informatie op, een derde schrijft de uiteindelijke response. Langflow heeft hier een "Supervisor" component voor die de werkverdeling coördineert. Dit patroon — een orchestrator die sub-agents aanstuurt — gebruiken we ook in mijn VorstersNV-project.',
      },
      {
        type: 'heading',
        text: 'Wat ik meeneem naar mijn eigen projecten',
      },
      {
        type: 'paragraph',
        text: 'De workshop bevestigde een aantal keuzes die ik al had gemaakt voor VorstersNV, maar gaf ook nieuwe inzichten. Langflow gebruik ik nu als prototyping-omgeving: snel een flow uitproberen in de UI, dan exporteren naar Python en integreren in de FastAPI-backend. Zo combineer je de snelheid van visueel bouwen met de kracht van code.',
      },
      {
        type: 'list',
        items: [
          'Langflow als prototyping tool, Python/FastAPI voor productie',
          'RAG toepassen op productdocumentatie en FAQ voor de klantenservice-agent',
          'Multi-agent pattern: orchestrator + gespecialiseerde sub-agents',
          'Lokaal draaien met Ollama blijft de voorkeur voor privacy en kosten',
          'Vector store (Chroma) integreren voor semantisch zoeken in productcatalogus',
        ],
      },
      {
        type: 'heading',
        text: 'Aan de slag met Langflow',
      },
      {
        type: 'paragraph',
        text: 'Langflow is gratis en open-source. Je kunt het lokaal draaien via pip of Docker. De community is actief, er zijn tientallen voorbeeldflows beschikbaar, en de integratie met Ollama werkt out-of-the-box. Of je nu een RAG-chatbot wilt bouwen, een AI-agent voor je klantenservice, of gewoon wil experimenteren met LLMs — Langflow verlaagt de drempel enorm.',
      },
      {
        type: 'code',
        language: 'bash',
        code: `# Langflow lokaal starten
pip install langflow

# Of via Docker
docker run -p 7860:7860 langflowai/langflow:latest

# Open de UI
open http://localhost:7860`,
      },
      {
        type: 'paragraph',
        text: 'Heb je vragen over de workshop, Langflow, of hoe je een AI-agent integreert in je eigen project? Laat het me weten — ik help graag verder.',
      },
    ],
  },
  {
    slug: 'ai-gedreven-testautomatisering',
    titel: 'AI-gedreven testautomatisering: van Jira story naar Cypress test in minuten',
    excerpt:
      'Hoe bouw je een schaalbaar, consistent en traceerbaar testautomatiseringssysteem met Rovo Agents, Copilot CLI en Cypress? Een diepgaande walkthrough van de volledige pipeline — van user story tot CI/CD, inclusief concrete commands, hooks, tagging en quality gates.',
    datum: '21 april 2026',
    datumISO: '2026-04-21',
    leestijd: '18 min',
    categorie: 'Testing & AI',
    categorieKleur: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    afbeelding: '/ai-testautomatisering-presentatie.png',
    inhoud: [
      {
        type: 'image',
        src: '/ai-testautomatisering-presentatie.png',
        alt: 'AI-gedreven testautomatisering presentatie overzicht',
        caption: 'Volledige presentatie: AI-Driven Test Automation System — Rovo + Copilot CLI Agents + Cypress',
      },
      {
        type: 'paragraph',
        text: 'Testautomatisering is al jaren een pijnpunt in software teams. Tests zijn traag om te schrijven, moeilijk te onderhouden, en de link met de originele requirements verdwijnt al snel. We hebben een aanpak gebouwd die dat fundamenteel verandert: een AI-gedreven pipeline waarbij Rovo Agents en Copilot CLI Agents samenwerken om van een Jira User Story automatisch kwalitatieve, traceerbare Cypress tests te genereren. Dit is geen toekomstmuziek — dit draait vandaag in productie.',
      },
      {
        type: 'heading',
        text: '😤 De uitdaging: waarom klassieke testautomatisering faalt',
      },
      {
        type: 'grid2',
        items: [
          { icon: '🐢', title: 'Traag & manueel', text: 'Testcases kosten tijd en zijn foutgevoelig. Developers schrijven ze pas achteraf, als de feature al live is.' },
          { icon: '🎲', title: 'Inconsistent', text: 'Verschillende interpretaties tussen testers. Geen shared definitie van wat "getest" betekent.' },
          { icon: '🔗', title: 'Beperkte traceability', text: 'Moeilijk te linken aan AC\'s, epics of requirements. Een bugfix weet niet welke test hem dekt.' },
          { icon: '⏱️', title: 'Late feedback', text: 'Problemen duiken op in productie of pas bij de release, niet tijdens development.' },
        ],
      },
      {
        type: 'infobox',
        icon: '💡',
        title: 'De kernvraag',
        text: 'We hebben een schaalbare, slimme en consistente aanpak nodig. Eén waarbij AI het repetitieve werk overneemt, en menselijke expertise zich focust op kwaliteitscontrole.',
        color: 'border-cyan-500/30 bg-cyan-500/5',
      },
      {
        type: 'heading',
        text: '🚀 De oplossing: AI Test Automation Pipeline',
      },
      {
        type: 'paragraph',
        text: 'De pipeline bestaat uit 4 fases die naadloos op elkaar aansluiten. Elke fase heeft een eigen AI agent die gespecialiseerd is in zijn taak.',
      },
      {
        type: 'steps',
        items: [
          { title: 'INPUT — Jira User Story', text: 'Startpunt: een Jira story met acceptance criteria, context en businesswaarde. Rovo leest deze volledig in inclusief linked issues en commentaar.' },
          { title: 'PLAN — Test Design met Rovo', text: 'Rovo\'s Analyse Agent en Test Design Agent structureren de story naar testscenario\'s, AC\'s en een Test Contract (JSON formaat).' },
          { title: 'BUILD — Cypress Code met Copilot CLI', text: 'De Contract Agent, Generator Agent en Review Agent vertalen het Test Contract naar uitvoerbare Cypress tests met tags, assertions en herbruikbare commands.' },
          { title: 'DEPLOY — Uitvoering & CI/CD', text: 'Tests draaien automatisch in de pipeline. Smoke tests op elke PR, full regression elke nacht, critical tests bij elke release.' },
        ],
      },
      {
        type: 'heading',
        text: '🤖 AI Agent Fleet: gespecialiseerde rollen',
      },
      {
        type: 'paragraph',
        text: 'Het systeem gebruikt twee categorieën agents: Rovo Agents voor de analyse- en designlaag, en Copilot CLI Agents voor de implementatielaag. Ze communiceren via het Test Contract als tussenlaag.',
      },
      {
        type: 'grid2',
        items: [
          { icon: '🔍', title: 'Rovo: Analyse Agent', text: 'Begrijpt de user story volledig. Leest Jira, linked AC\'s, commentaar en project context. Output: gestructureerde testscenario\'s.' },
          { icon: '🎨', title: 'Rovo: Test Design Agent', text: 'Genereert testcases (happy flows, negative flows, edge cases, performance conditions). Koppelt elke testcase aan een AC.' },
          { icon: '📋', title: 'Copilot CLI: Contract Agent', text: 'Structureert en normaliseert het Test Contract naar JSON formaat. Zorgt voor consistente structuur en naming conventions.' },
          { icon: '⚙️', title: 'Copilot CLI: Generator Agent', text: 'Bouwt de Cypress test files. Genereert herbruikbare commands, fixtures, tags en sterke assertions.' },
        ],
      },
      {
        type: 'infobox',
        icon: '🔬',
        title: 'Copilot CLI: Review Agent',
        text: 'Controleert kwaliteit van de gegenereerde tests. Checkt: AC coverage, assertion kwaliteit, selector stabiliteit, test smell detectie en naming conventions.',
        color: 'border-violet-500/30 bg-violet-500/5',
      },
      {
        type: 'heading',
        text: '📝 Concreet voorbeeld: story LN-1122',
      },
      {
        type: 'paragraph',
        text: 'Bekijken we dit aan de hand van een echte story: LN-1122 "Mapping dropdown". De PO wil in de MVP user flow voltooien zodat onze FE futureproof is en goede performance levert.',
      },
      {
        type: 'grid2',
        items: [
          { icon: '📥', title: 'Xray AI Output', text: 'Testcases: happy flows, negative flows, edge cases, performance conditions. Met tags. Herbruikbare commands. Gekoppeld aan AC\'s.' },
          { icon: '🤖', title: 'Copilot Output', text: 'Cypress Test File: LN-1122-mapping.cy.ts. Met tags, assertions en sterke test coverage. Volledig traceerbaar naar de story.' },
        ],
      },
      {
        type: 'code',
        language: 'cypress — LN-1122-mapping.cy.ts',
        code: `/**
 * Ticket: LN-1122
 * Feature: Mapping dropdown
 * Covers: AC1, AC2, AC3
 * Tags: regression, mapping, #gov, sprint-26
 */
describe("[LN-1122] Mapping dropdown", () => {
  beforeEach(() => {
    cy.login()
    cy.visit("/mapping-overview")
  })

  describe("Happy flows", () => {
    it("MC1: shows all mappings in dropdown", { tags: ["smoke"] }, () => {
      cy.get('[data-testid="mapping-option"]')
        .should("have.length.greaterThan", 1)
    })
  })
})`,
      },
      {
        type: 'quote',
        text: 'Snellere creatie. Betere kwaliteit. Volledige traceability. Schaalbare automation. Dit zijn de vier resultaten die we zien in elk team dat deze pipeline adopteert.',
      },
      {
        type: 'heading',
        text: '⚡ Commands: snelle instructies voor AI',
      },
      {
        type: 'paragraph',
        text: 'De Copilot CLI agents werken met gestandaardiseerde commands. Dit zorgt voor consistent gedrag en herhaalbare resultaten, ongeacht wie het commando uitvoert.',
      },
      {
        type: 'code',
        language: 'bash — Copilot CLI commands',
        code: `# Analyseer een Jira story en genereer testscenario's
/analyze-story LN-1122

# Genereer testcases inclusief edge cases
/generate-testcases --include-edge-cases

# Converteer naar Cypress test file
/convert-to-cypress

# Review gegenereerde tests met coverage check
/review-tests --check-coverage`,
      },
      {
        type: 'heading',
        text: '🔔 Hooks: automatische triggers',
      },
      {
        type: 'paragraph',
        text: 'AI werkt niet alleen op commando — het werkt ook proactief via hooks die automatisch acties triggeren op bepaalde events.',
      },
      {
        type: 'list',
        items: [
          'On File Save: Start test review automatisch zodra een test file wordt opgeslagen',
          'On Commit: Check AC coverage — zijn alle acceptance criteria gedekt door tests?',
          'On Pull Request: Run smoke tests (@smoke tag) als kwaliteitspoort voor merge',
        ],
      },
      {
        type: 'infobox',
        icon: '⚡',
        title: 'Voordeel',
        text: 'Consistente feedback en herhaalbare resultaten. Developers krijgen binnen seconden terugkoppeling zonder manuele stappen.',
        color: 'border-green-500/30 bg-green-500/5',
      },
      {
        type: 'heading',
        text: '🧠 Context: betere output door meer kennis',
      },
      {
        type: 'paragraph',
        text: 'De kwaliteit van AI output hangt direct samen met de context die je meegeeft. Geef je weinig context, krijg je generieke tests. Geef je rijke context, krijg je tests die specifiek zijn voor jouw product.',
      },
      {
        type: 'grid2',
        items: [
          { icon: '✅', title: 'Goede context bevat', text: 'Jira description & AC\'s, testscenario\'s & patronen, project structuur & commands, technische richtlijnen, test data & omgevingen.' },
          { icon: '🎯', title: 'Resultaat', text: 'Relevantere scenario\'s, betere test code, minder manueel bijwerken, hogere AC coverage bij de eerste run.' },
        ],
      },
      {
        type: 'heading',
        text: '🪙 Tokens: slim input, betere prestaties',
      },
      {
        type: 'paragraph',
        text: 'Tokens zijn de eenheid waarmee LLMs input en output meten. Kwaliteit van input = kwaliteit van output. Dat geldt ook hier.',
      },
      {
        type: 'grid2',
        items: [
          { icon: '✅', title: 'Goed token gebruik', text: 'Structuur & focus. Relevante informatie. Duidelijke templates. Test contract (JSON). Compacte, informatiedichte tekst.' },
          { icon: '❌', title: 'Slecht token gebruik', text: 'Te veel losse tekst. Onnodige details. Duplicatie. Ruis en irrelevante context die de AI afleidt.' },
        ],
      },
      {
        type: 'infobox',
        icon: '💡',
        title: 'TIP',
        text: 'Kwaliteit van input = kwaliteit van output. Een goed Test Contract als input levert 70% betere Cypress tests dan een ruwe tekstbeschrijving.',
        color: 'border-amber-500/30 bg-amber-500/5',
      },
      {
        type: 'heading',
        text: '📋 Test Contract: de tussenlaag',
      },
      {
        type: 'paragraph',
        text: 'Het Test Contract is het gestandaardiseerde JSON formaat dat de brug vormt tussen Rovo (analyse) en Copilot CLI (implementatie). Het stabiliseert de samenwerking en voorkomt hallucinaties.',
      },
      {
        type: 'code',
        language: 'json — Test Contract formaat',
        code: `{
  "ticket": "LN-1122",
  "feature": "Mapping dropdown",
  "scenario": "Happy flow — Show all mappings",
  "id": "AC1-MAPP-01",
  "type": "happy",
  "ac": ["AC1", "AC2"],
  "priority": "High",
  "automation": true,
  "title": "Show all mappings"
}`,
      },
      {
        type: 'list',
        items: [
          'Consistente structuur tussen Rovo en Copilot CLI agents',
          'Minder AI hallucinaties doordat het formaat strikt is',
          'Eenvoudigere review door mensen: het contract is leesbaar',
          'Betere traceability: elk scenario linkt aan een ticket en AC',
        ],
      },
      {
        type: 'heading',
        text: '🏷️ Tagging strategie: slim groeperen en uitvoeren',
      },
      {
        type: 'paragraph',
        text: 'Tags bepalen welke tests wanneer draaien. Een goede tagging strategie is essentieel voor snelle feedback en gerichte testexecutie.',
      },
      {
        type: 'code',
        language: 'cypress — Tagging voorbeeld',
        code: `it("login works", {
  tags: ["smoke", "regression", "sprint-26"]
}, () => {
  // test
})`,
      },
      {
        type: 'list',
        items: [
          '🔴 smoke — Kritieke happy flows, draaien op elke PR',
          '🔵 regression — Volledige testcoverage, draaien elke nacht',
          '🟡 critical — Business-kritieke flows, draaien bij elke release',
          '🟢 sprint-26 — Sprint-specifieke tests voor traceability',
          '🟣 feature-mapping — Feature-gebonden tests voor gefocuste executie',
        ],
      },
      {
        type: 'infobox',
        icon: '🤖',
        title: 'AI verstart: testers. Testers in CI/CD',
        text: 'AI genereert de tags op basis van het Test Contract en de story prioriteit. Testers valideren en verfijnen. CI/CD gebruikt de tags om de juiste tests op het juiste moment te draaien.',
        color: 'border-cyan-500/30 bg-cyan-500/5',
      },
      {
        type: 'heading',
        text: '✅ Quality Gates: kwaliteit gegarandeerd',
      },
      {
        type: 'paragraph',
        text: 'Quality gates zijn de poortwachters van je testcodebase. Ze combineren automatische checks, AI review en menselijke validatie.',
      },
      {
        type: 'grid2',
        items: [
          { icon: '🤖', title: 'Automatisch', text: 'Linting & formatting. Naming conventions. Tags aanwezig. Geen duplicate tests. Selectorstabiliteit check.' },
          { icon: '🧠', title: 'AI Review', text: 'AC coverage check. Assertion kwaliteit beoordeling. Selector stabiliteit analyse. Test smell detectie.' },
          { icon: '👤', title: 'Manueel', text: 'Business validatie. Edge case controle. Finale goedkeuring door QA lead.' },
        ],
      },
      {
        type: 'quote',
        text: 'Alle gates groen = Klaar voor merge. Geen uitzonderingen. Geen "we kijken er later naar".',
      },
      {
        type: 'heading',
        text: '🔄 CI/CD integratie: van commit tot zekerheid',
      },
      {
        type: 'steps',
        items: [
          { title: 'PR — Smoke tests (@smoke)', text: 'Bij elke pull request draaien de kritieke smoke tests. Snel (< 5 min), gefocust, blokkerend voor merge.' },
          { title: 'Nightly — Full regression (@regression)', text: 'Elke nacht draait de volledige regressie suite. Alle scenarios, alle edge cases. Resultaten beschikbaar voor standup.' },
          { title: 'Release — Critical tests (@critical)', text: 'Bij elke release naar productie draaien de business-kritieke tests. Automatische rapportage en feedback loop.' },
        ],
      },
      {
        type: 'heading',
        text: '🔁 Feedback Loop & Maturity Model',
      },
      {
        type: 'paragraph',
        text: 'Het systeem leert van zijn resultaten. De feedback loop zorgt dat AI output steeds beter wordt naarmate er meer tests draaien en meer resultaten beschikbaar zijn.',
      },
      {
        type: 'list',
        items: [
          'Execution resultaten worden teruggekoppeld naar Rovo als context voor de volgende sprint',
          'Betere AI output → betere test code → minder manueel bijwerken',
          'Verbeter prompts, templates en commands op basis van wat goed werkt',
          'Maturity model: van basis automatisering → AI-ondersteund → volledig autonoom',
        ],
      },
      {
        type: 'heading',
        text: '📊 Resultaten',
      },
      {
        type: 'grid2',
        items: [
          { icon: '⚡', title: 'Snellere testcreatie', text: 'Tot 70% tijdswinst bij het schrijven van testcases. Van 2 uur naar 20 minuten voor een gemiddelde story.' },
          { icon: '✅', title: 'Consistente kwaliteit', text: 'Minder fouten, sterkere tests. Geen vergeten edge cases, geen ontbrekende assertions.' },
          { icon: '🔗', title: 'Volledige coverage', text: 'Traceerbaar naar AC\'s. Elk testgeval linkt naar een story, elke story naar een epic. Gap detectie ingebouwd.' },
          { icon: '🚀', title: 'Schaalbare automation', text: 'Klaar voor groei. Het systeem schaalt mee met het team en de codebase zonder proportioneel meer manueel werk.' },
        ],
      },
      {
        type: 'heading',
        text: '🚀 Next Step: start vandaag',
      },
      {
        type: 'paragraph',
        text: 'Van playbook naar praktijk. De tools bestaan, de agents zijn klaar, de pipeline is bewezen. Het enige wat nog rest is de eerste stap: kies één Jira story, run /analyze-story, en bekijk wat AI genereert. Van daaruit bouw je iteratief verder.',
      },
      {
        type: 'list',
        items: [
          'Stap 1: Installeer Copilot CLI en configureer je Jira connectie',
          'Stap 2: Kies een user story met duidelijke acceptance criteria',
          'Stap 3: Run /analyze-story [ticket-id] en review het Test Contract',
          'Stap 4: Run /generate-testcases en /convert-to-cypress',
          'Stap 5: Review de gegenereerde tests en merge via je quality gates',
          'Stap 6: Activeer hooks voor automatische coverage checks bij elke commit',
        ],
      },
      {
        type: 'quote',
        text: 'Vragen? Ideeën? Laten we bouwen! De toekomst van testautomatisering is niet volledig autonoom — het is een slimme samenwerking tussen AI en de mensen die het product het best kennen.',
      },
    ],
  },
  {
    slug: 'loonberekening-engine-chain-of-responsibility',
    titel: 'Een loonberekeningsmotor bouwen: Chain of Responsibility in enterprise Java',
    excerpt:
      'Hoe ontwerp je een robuuste, uitbreidbare payroll engine die Belgische belastingregels, RSZ-bijdragen, werkbonus en bedrijfsvoorheffing correct verwerkt? Een diepgaande kijk op het Chain of Responsibility patroon, contextobjecten en fasegerichte architectuur in enterprise Java.',
    datum: '21 april 2026',
    datumISO: '2026-04-21',
    leestijd: '16 min',
    categorie: 'Architectuur',
    categorieKleur: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    afbeelding:
      'https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=800&q=80',
    inhoud: [
      {
        type: 'paragraph',
        text: 'Loonberekening klinkt eenvoudig: bruto min belastingen is netto. In de praktijk is het één van de meest complexe domeinen in enterprise software. Belgische regelgeving kent tientallen uitzonderingen, vijf opeenvolgende berekeningstappen, en voor elke stap verschillende regels per sector, contracttype en persoonlijke situatie. In dit artikel bespreek ik hoe je zo\'n systeem architectureel aanpakt — met het Chain of Responsibility patroon als kern.',
      },
      {
        type: 'infobox',
        icon: '🎯',
        title: 'Wat je leert',
        text: 'Hoe je een complexe rekenmotor opbouwt met Chain of Responsibility · Waarom een context-object beter is dan methodeparameters · Hoe je 5 berekensfases clean scheidt · Hoe Strategy pattern RSZ-varianten netjes afhandelt · Hoe je fiscale edge cases beheersbaar houdt',
        color: 'border-orange-500/30 bg-orange-500/5',
      },
      {
        type: 'heading',
        text: '🏗️ De kern: Chain of Responsibility',
      },
      {
        type: 'paragraph',
        text: 'Het Chain of Responsibility patroon is ideaal voor procesflows waarbij meerdere stappen sequentieel moeten worden uitgevoerd, elke stap de uitvoer van de vorige nodig heeft, en stappen onafhankelijk uitbreidbaar moeten zijn. Een loonberekeningsmotor is een schoolboekvoorbeeld van dit patroon.',
      },
      {
        type: 'code',
        language: 'java',
        code: `// AbstractRekenCommand — basis voor elke berekeningsstap
public abstract class AbstractRekenCommand implements Command {

    @Override
    public boolean execute(Context context) throws Exception {
        RekenContext ctx = (RekenContext) context;
        voerUit(ctx);
        return CONTINUE_PROCESSING; // volgende command in de chain
    }

    protected abstract void voerUit(RekenContext context) throws RekenException;
}

// Concrete implementatie — één stap, één verantwoordelijkheid
public class BerekenBrutoLoon extends AbstractRekenCommand {

    @Override
    protected void voerUit(RekenContext ctx) throws RekenException {
        BigDecimal bruto = berekenVergoedingen(ctx)
            .add(berekenSupplementen(ctx))
            .add(berekenFlexiJobs(ctx));

        ctx.set(RekenBrutoKey.BRUTO_MAANDLOON_KEY, bruto);
    }
}`,
      },
      {
        type: 'paragraph',
        text: 'Elke berekeningsstap is een klasse. Elke klasse heeft één verantwoordelijkheid. De chain wordt opgebouwd door een factory, die op basis van configuratie de volgorde bepaalt. Dit maakt het systeem enorm uitbreidbaar: een nieuwe loonregel is simpelweg een nieuwe klasse die je in de chain invoegt.',
      },
      {
        type: 'heading',
        text: '🔄 De vijf berekensfases',
      },
      {
        type: 'paragraph',
        text: 'Een Belgisch loonpakket wordt altijd in vijf opeenvolgende fases berekend. Elke fase bouwt voort op de resultaten van de vorige. Dit is niet willekeurig: de wetgeving schrijft deze volgorde voor.',
      },
      {
        type: 'steps',
        items: [
          {
            title: 'BRUTO — Het brutoloon',
            text: 'Berekening van het bruto maandloon op basis van de loonschaal, prestaties, supplementen (nacht/weekend/feestdag) en vergoedingen (maaltijdcheques, fietsvergoeding). Deeltijdse medewerkers krijgen een prestatieratio (teller/noemer) toegepast.',
          },
          {
            title: 'SOCIAAL — RSZ-bijdragen',
            text: 'Sociale bijdragen voor werknemer en werkgever. In België zijn er drie sectoren met elk hun eigen regels: DMFA (privésector), DMFAPPL (lokale overheden) en RSZPPO (onderwijs). Werkbonus verlaagt de RSZ voor lage lonen. BBSZ (Bijzondere Bijdrage Sociale Zekerheid) wordt apart berekend in 7 schijven.',
          },
          {
            title: 'BELASTBAAR — Het belastbaar inkomen',
            text: 'Formule: bruto − sociale bijdragen + werkbonus. Speciale gevallen zoals achterstaalbetaling, onthaalouders en vrijwillige brandweer volgen aparte regels. Regime-codes bepalen welke aftrekken van toepassing zijn.',
          },
          {
            title: 'BV — Bedrijfsvoorheffing',
            text: 'De complexste stap. Belastingschijven, forfaitaire beroepskosten, echtgenotensplitsing, verminderingen voor kinderen/invaliden/gepensioneerden, jobkorting, stagiarvermindering en krisistaks. Elke loonsoort (vakantiegeld, achterstal, uittreding mandataris…) heeft een eigen BV-berekening.',
          },
          {
            title: 'NETTO — Het nettoloon',
            text: 'Netto = bruto − alle RSZ-bijdragen − alle BV-varianten + werkbonus + gewestelijke verminderingen + herstructureringsverminderingen. Daarna volgen inhoudingen (groepsverzekering, vakbond, loonbeslag, alimentatie).',
          },
        ],
      },
      {
        type: 'heading',
        text: '🗄️ Het context-object: sleutel tot losse koppeling',
      },
      {
        type: 'paragraph',
        text: 'In een chain van tientallen stappen is het onmogelijk — en onwenselijk — om alle tussenresultaten als methodeparameters door te geven. De oplossing is een context-object: een typed key-value store die door de hele chain wordt doorgegeven.',
      },
      {
        type: 'code',
        language: 'java',
        code: `// Typed enum keys — geen stringly-typed strings
public enum RekenBrutoKey implements RekenChainKey {
    BRUTO_MAANDLOON_KEY,
    BASIS_BEDRAG_KEY
}

public enum RekenRszKey implements RekenChainKey {
    BIJDRAGE_RSZ_KEY,
    BIJDRAGE_TAO_KEY,
    BIJDRAGE_PENSIOEN_VASTBENOEMDEN_KEY,
    BIJZONDERE_BIJDRAGE_KEY  // BBSZ
}

public enum RekenBvKey implements RekenChainKey {
    BEDRIJFSVOORHEFFING_GEWONE_BEZOLDIGING_KEY,
    VERMINDERING_BEDRIJFSVOORHEFFING_FICHE_10_KEY
}

// Gebruik in een command
BigDecimal bruto = ctx.get(RekenBrutoKey.BRUTO_MAANDLOON_KEY);
BigDecimal rsz   = ctx.get(RekenRszKey.BIJDRAGE_RSZ_KEY);
BigDecimal netto = bruto.subtract(rsz); // etc.
ctx.set(RekenNettoKey.NETTO_KEY, netto);`,
      },
      {
        type: 'infobox',
        icon: '💡',
        title: 'Waarom typed enum keys?',
        text: 'Je vermijdt typo\'s in sleutelnamen, je krijgt compile-time controle, en je IDE kan alle gebruikers van een sleutel opzoeken. Een String-gebaseerde context (zoals Apache Commons Chain standaard biedt) is een onderhoudsramp in een systeem met 80+ keys.',
        color: 'border-blue-500/30 bg-blue-500/5',
      },
      {
        type: 'paragraph',
        text: 'De context werkt op twee niveaus: een mainContext voor globale persoonsdata, en een opdrachtContext per aanstelling per berekeningsperiode. Dit is essentieel voor medewerkers met meerdere deeltijdse contracten: elke opdracht wordt apart berekend, maar de totalisatie gebeurt in de mainContext.',
      },
      {
        type: 'heading',
        text: '🎭 Strategy pattern voor sectorvarianten',
      },
      {
        type: 'paragraph',
        text: 'Niet alle werknemers vallen onder dezelfde RSZ-regels. België kent drie grote sectoren, elk met eigen tarieven, plafonds en uitzonderingen. Het Strategy pattern lost dit elegant op:',
      },
      {
        type: 'code',
        language: 'java',
        code: `// Abstract strategy — gemeenschappelijke interface
public abstract class AbstractBerekenSocialeBijdragen extends AbstractRekenCommand {

    protected abstract BigDecimal berekenWerknemerBijdrage(RekenContext ctx);
    protected abstract BigDecimal berekenWerkgeverBijdrage(RekenContext ctx);

    @Override
    protected void voerUit(RekenContext ctx) {
        BigDecimal werknemerRsz = berekenWerknemerBijdrage(ctx);
        BigDecimal werkgeverRsz = berekenWerkgeverBijdrage(ctx);

        ctx.set(RekenRszKey.BIJDRAGE_RSZ_KEY, werknemerRsz);
        ctx.set(RekenPatronaalRszKey.PATRONALE_BIJDRAGE_RSZ_KEY, werkgeverRsz);
    }
}

// Concrete strategies per sector
public class BerekenSocialeBijdragenDmfa extends AbstractBerekenSocialeBijdragen {
    // Privésector — standaard RSZ tarief 13,07%
}

public class BerekenSocialeBijdragenDmfappl extends AbstractBerekenSocialeBijdragen {
    // Lokale overheden — pensioen vastbenoemden, TAO bijdrage
}

public class BerekenSocialeBijdragenRszppo extends AbstractBerekenSocialeBijdragen {
    // Onderwijssector — eigen regime en plafonds
}`,
      },
      {
        type: 'paragraph',
        text: 'De factory selecteert op basis van het statuut van de medewerker de juiste strategie. De rest van de chain hoeft niet te weten welke strategie actief is — hij leest gewoon BIJDRAGE_RSZ_KEY uit de context.',
      },
      {
        type: 'heading',
        text: '📊 Bedrijfsvoorheffing: de complexe kern',
      },
      {
        type: 'paragraph',
        text: 'Bedrijfsvoorheffing (BV) is de meest complexe stap. Niet omdat de wiskunde moeilijk is — het zijn schijven en percentages — maar omdat er zoveel uitzonderingen zijn. Elke loonsoort heeft een eigen BV-berekening met eigen barema\'s:',
      },
      {
        type: 'grid2',
        items: [
          {
            icon: '📋',
            title: 'Reguliere BV',
            text: 'BvGewoon: 6 belastingschijven, forfaitaire beroepskosten, jobkorting, verminderingen voor kinderen/invaliden/gepensioneerden, echtgenotensplitsing.',
          },
          {
            icon: '🗓️',
            title: 'Vakantiegeld & Achterstal',
            text: 'BvVakantiegeld en BvAchterstal volgen art. 171 WIB: afzonderlijk tarief, eigen opzoekingstabellen met 18 grenzen voor achterstal.',
          },
          {
            icon: '🚲',
            title: 'Fiets & Vrijwilligers',
            text: 'BvFietsVergoeding: belastingvrij tot een wettelijk plafond. BvVrijwilligeBrandweer: aparte tarieven voor vrijwillige brandweerlieden.',
          },
          {
            icon: '🏛️',
            title: 'Mandatarissen',
            text: 'BvUittredingMandataris: specifieke regels bij uittreding van politieke mandatarissen. Eigen DMFA-fiche (fiche 18 vs fiche 10).',
          },
        ],
      },
      {
        type: 'code',
        language: 'java',
        code: `// BV schijvenberekening — generiek patroon
private BigDecimal berekenSchijven(BigDecimal jaarBasis, BigDecimal[] grenzen, BigDecimal[] percentages) {
    BigDecimal totaal = BigDecimal.ZERO;
    BigDecimal restBasis = jaarBasis;

    for (int i = 0; i < grenzen.length; i++) {
        BigDecimal ondergrens = i == 0 ? BigDecimal.ZERO : grenzen[i - 1];
        BigDecimal bovengrens = grenzen[i];
        BigDecimal schijf = restBasis.min(bovengrens).subtract(ondergrens).max(BigDecimal.ZERO);
        totaal = totaal.add(schijf.multiply(percentages[i]).divide(HONDERD, SCALE, ROUNDING));
        if (restBasis.compareTo(bovengrens) <= 0) break;
    }
    return totaal;
}

// Afrondingsregel wijzigde op 01/01/2023:
// Vóór 2023: FLOOR (altijd naar beneden)
// Vanaf 2023: HALF_UP (standaard afronding)
private RoundingMode bepaalAfrondingsModus(LocalDate berekeningsDatum) {
    return berekeningsDatum.isBefore(EINDE_AFRONDEN_NAAR_BENEDEN)
        ? RoundingMode.FLOOR
        : RoundingMode.HALF_UP;
}`,
      },
      {
        type: 'heading',
        text: '🔧 Loonbeslag: het laatste vangnet',
      },
      {
        type: 'paragraph',
        text: 'Na het nettoloon kan er nog loonbeslag of onderhoudsgeld worden ingehouden. Dit is wettelijk geregeld: een medewerker moet altijd een minimumloon overhouden, ongeacht de schulden. Het systeem berekent via schijven hoeveel maximaal ingehouden mag worden.',
      },
      {
        type: 'code',
        language: 'java',
        code: `// Loonbeslag: schijvensysteem met wettelijke grenzen
// Medewerker houdt altijd minstens grens1 over
// Tussen grens1 en grens2: pct1 mag worden ingehouden
// Tussen grens2 en grens3: pct2 mag worden ingehouden
// Boven grens3: pct3 mag worden ingehouden (maar max nettoloon)

// Kinderen ten laste verhogen de beschermde ondergrens
// Onderhoudsgeld (alimentatie) heeft voorrang op loonbeslag`,
      },
      {
        type: 'heading',
        text: '🧪 Testen van een rekenmotor',
      },
      {
        type: 'paragraph',
        text: 'Een loonberekeningsmotor is bij uitstek geschikt voor unit testing: elke command is geïsoleerd, de input is een context-object, de output is een context-object. Je test eenvoudig één stap zonder de rest van de chain te activeren.',
      },
      {
        type: 'code',
        language: 'java',
        code: `@Test
void testWerkbonusLaagLoon() {
    // Arrange
    RekenContext ctx = new RekenContext();
    ctx.set(RekenBrutoKey.BRUTO_MAANDLOON_KEY, new BigDecimal("1800.00"));
    ctx.set(RekenRszKey.BIJDRAGE_RSZ_KEY, new BigDecimal("235.26")); // 13,07%

    // Act
    new BerekenWerkbonus().voerUit(ctx);

    // Assert
    BigDecimal werkbonus = ctx.get(RekenRszKey.WERKBONUS_LAGE_LONEN_KEY);
    assertThat(werkbonus).isGreaterThan(BigDecimal.ZERO);
    // Werkbonus verlaagt effectief de RSZ-kost voor lage lonen
}

@Test
void testBvGezinstype_alleenstaande_met_2_kinderen() {
    RekenContext ctx = new RekenContext();
    ctx.set(RekenBvKey.FISKGEZINSTOESTAND_KEY, Fiskgezinstoestand.ALLEENSTAANDE);
    ctx.set(RekenBvKey.KINDEREN_TEN_LASTE_KEY, 2);
    ctx.set(RekenBbKey.BELASTBAAR_KEY, new BigDecimal("2500.00"));

    new BerekenBvGewoon().voerUit(ctx);

    BigDecimal bv = ctx.get(RekenBvKey.BEDRIJFSVOORHEFFING_GEWONE_BEZOLDIGING_KEY);
    // Vermindering voor 2 kinderen + alleenstaande bonus verwacht
    assertThat(bv).isLessThan(new BigDecimal("400.00"));
}`,
      },
      {
        type: 'infobox',
        icon: '⚠️',
        title: 'Integration tests zijn cruciaal',
        text: 'Unit tests per command zijn noodzakelijk, maar niet voldoende. Je hebt ook integratietests nodig die de volledige chain doorlopen met een gekende persoonssituatie en het eindresultaat vergelijken met een handmatig berekend referentiebedrag. Zeker bij wetgevingswijzigingen (nieuwe barema\'s per 1 januari) zijn these "golden file" tests je vangnet.',
        color: 'border-amber-500/30 bg-amber-500/5',
      },
      {
        type: 'heading',
        text: '📐 APO-module: aanpassingen achteraf',
      },
      {
        type: 'paragraph',
        text: 'Geen enkel systeem is perfect. Soms is een manuele correctie noodzakelijk: een verkeerde inhouding, een aanpassing voor een specifiek geval. De APO-module (Aanpassingen Persoonlijk/Organisatie) verwerkt deze correcties op een gecontroleerde manier — ze worden gelogd, gevalideerd en zijn traceerbaar. De chain heeft een early-stop mechanisme als de APO-verwerking aangeeft dat de normale chain niet moet doorgaan.',
      },
      {
        type: 'heading',
        text: '🌐 REST API laag: ontkoppeling van de motor',
      },
      {
        type: 'paragraph',
        text: 'De rekenmotor is bewust ontkoppeld van de REST-laag. De API assembleert de input, roept de motor aan, en transformeert de output naar het response-formaat. Dit laat toe de motor te testen zonder HTTP-context en om de motor herbruikbaar te maken in batch-processen, schedulers of andere kanalen.',
      },
      {
        type: 'code',
        language: 'java',
        code: `@POST
@Path("/bereken")
public Response berekenLoon(LoonBerekeningRequest request) {
    // 1. Assembleer context vanuit request
    RekenContext ctx = contextAssembler.assembly(request);

    // 2. Voer de volledige chain uit
    rekenChain.execute(ctx);

    // 3. Extract resultaten en transformeer naar response
    LoonBerekeningResponse response = resultaatExtractor.extract(ctx);

    return Response.ok(response).build();
}`,
      },
      {
        type: 'heading',
        text: '📋 Lessen voor jouw project',
      },
      {
        type: 'paragraph',
        text: 'Je hoeft geen loonberekeningsmotor te bouwen om van deze architectuur te leren. De patronen zijn universeel toepasbaar in elke domein met complexe, meerstaps-berekeningen: verzekeringspremies, kredietscoring, tariefberekening, hypotheken, subsidieberekeningen.',
      },
      {
        type: 'list',
        items: [
          'Gebruik Chain of Responsibility wanneer je een procesflow hebt met losjes gekoppelde, sequentiële stappen',
          'Definieer typed enum keys voor je context — nooit plain strings als sleutels in een shared datastructuur',
          'Maak elke berekeningstap zo klein mogelijk: één verantwoordelijkheid, één klasse',
          'Gebruik Strategy pattern voor varianten die dezelfde interface hebben maar andere regels volgen',
          'Schrijf unit tests per command én integratietests op eindresultaat met golden files',
          'Isoleer de businesslogica van transport (REST, batch, message queue) — de motor weet niet hoe hij aangeroepen wordt',
          'Documenteer wetgevingswijzigingen expliciet in de code: datums zijn bedrijfslogica, geen constanten die je maar raden kunt',
        ],
      },
      {
        type: 'quote',
        text: 'Complexe domeinlogica is geen reden om spaghetti-code te schrijven. Integendeel: hoe complexer het domein, hoe belangrijker een heldere architectuur. Chain of Responsibility, Strategy en een typed context-object zijn drie patronen die samen een onderhoudbare, testbare en uitbreidbare rekenmotor mogelijk maken — zelfs als de wetgever elk jaar nieuwe regels toevoegt.',
      },
    ],
  },
  {
    slug: 'ai-fleet-productie-klaar-phr-globalconfig',
    titel: 'Van analyse tot productie: hoe een AI agent fleet een heel project transformeerde in één sessie',
    excerpt:
      'Een gedetailleerd verslag van hoe ik met GitHub Copilot en een fleet van parallelle AI agents het phr-globalconfig project van grond tot dak doorlichtte, 70+ E2E tests repareerde en activeerde, een volledig backend security audit uitvoerde en CI/CD kwaliteitspoorten installeerde — allemaal in één werksessie.',
    datum: '23 mei 2026',
    datumISO: '2026-05-23',
    leestijd: '18 min',
    categorie: 'AI',
    categorieKleur: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
    afbeelding:
      'https://images.unsplash.com/photo-1518432031352-d6fc5c10da5a?auto=format&fit=crop&w=800&q=80',
    inhoud: [
      {
        type: 'paragraph',
        text: 'Wat als je een AI niet één taak geeft, maar vijf tegelijk — en ze volledig parallel laat werken? Dat is precies wat ik deed tijdens een intensieve werksessie met het phr-globalconfig project: een Spring Boot 3 + Angular 21 + Cypress 15 applicatie die loonschalen, mappings en verloningsregels beheert voor HR-software. Het resultaat was verbluffend, maar ook confronterend. In dit artikel vertel ik eerlijk wat er goed ging, wat de AI vond, en wat er nog werk vergt voor een echte productie-release.',
      },
      {
        type: 'heading',
        text: '🔍 Wat is phr-globalconfig?',
      },
      {
        type: 'paragraph',
        text: 'phr-globalconfig is een interne configuratie-applicatie voor een HR-platform. Het beheert loonschalen, schaalgroepen, tijdlijnen van geldigheidsperiodes, eGov-mappings en DSL-rekenregels. De stack: Spring Boot backend met MariaDB en Liquibase, een Angular 21 frontend met PrimeNG, en een Cypress 15 E2E test suite met 23 Claude agents en 18 Copilot agents voor AI-gestuurde ontwikkeling. In totaal: 52 Cypress testbestanden, 70 Java bronbestanden en een agent-ecosysteem dat klaar was om ingezet te worden.',
      },
      {
        type: 'infobox',
        icon: '🎯',
        title: 'De startsituatie',
        text: 'Veel E2E tests waren gebroken of geskipped. De AI agent setup had evaluatiemetrics die ontbraken. De backend had nooit een formele security audit gehad. Er was geen CI/CD kwaliteitspoort. Het project was functioneel, maar niet productie-klaar.',
        color: 'border-orange-500/30 bg-orange-500/5',
      },
      {
        type: 'heading',
        text: '🤖 De aanpak: een fleet van parallelle agents',
      },
      {
        type: 'paragraph',
        text: 'In plaats van problemen één voor één aan te pakken, lanceerde ik meerdere gespecialiseerde AI agents tegelijk. Elke agent kreeg een specifieke, afgebakende opdracht mee met volledige context over de codebase, de relevante bestanden en de verwachte output. De agents werkten volledig parallel — terwijl de ene agent E2E tests repareerde, was een andere bezig met de backend audit en een derde met de CI/CD pipeline.',
      },
      {
        type: 'grid2',
        items: [
          {
            icon: '🧪',
            title: 'e2e-timing-fixes agent',
            text: 'Repareerde gebroken timing, wrong selectors en PrimeNG-specifieke interactieproblemen in 4 Cypress testbestanden.',
          },
          {
            icon: '🤝',
            title: 'ai-setup-evaluation agent',
            text: 'Voegde evaluatiemetrics toe aan 5 agents, breidde de README uit van 18 naar 23 agents en bouwde een decision tree.',
          },
          {
            icon: '🗺️',
            title: 'e2e-egov-dsl agent',
            text: 'Deed root cause analyse van 8 volledig falende eGov mapping tests en voegde 4 ontbrekende methoden toe aan MappingPage.js.',
          },
          {
            icon: '⏱️',
            title: 'timeline-unskip agent',
            text: 'Implementeerde 30 tijdlijn-tests volledig, van create tot delete met popup-bevestiging en navigatie over 12+ periodes.',
          },
          {
            icon: '📋',
            title: 'dsl-acceptance agent',
            text: "Schreef 17 nieuwe acceptatietests voor DSL overzicht en detail pagina's en repareerde een hardnekkige cancel-button bug.",
          },
          {
            icon: '🔒',
            title: 'backend-audit agent',
            text: 'Doorlichtte alle 8 controllers, Feijn clients, Liquibase migraties, input validatie en Spring Security configuratie.',
          },
        ],
      },
      {
        type: 'heading',
        text: '🧪 Wave 1: de E2E test problemen',
      },
      {
        type: 'paragraph',
        text: 'De eerste golf agents richtte zich op de meest zichtbare problemen: gebroken of overgeslagen Cypress tests. De AI identificeerde vier categorieën van fouten die telkens terugkwamen.',
      },
      {
        type: 'list',
        items: [
          "p-inputNumber valkuil: clear().type() reset het Angular model naar 0. Fix: focus().type('{selectall}VALUE') — dit is een PrimeNG-specifiek probleem dat moeilijk te vinden is zonder diepgaande componentkennis",
          'Sidebar timing: tests die op een cancel-knop klikten voordat de drawer-animatie volledig open was, faalden willekeurig. Fix: wachten op een zichtbaarheidsguard',
          'Ontbrekende POM-methoden: MappingPage.js miste 4 methoden (mappingList, mappingPeriodCard, auditLogButton, auditLogPanel) waardoor 8 tests volledig crashten',
          "Hardgecodeerde URLs: dsl-testdata-setup.cy.js gebruikte nb-docker-3 URLs die op andere omgevingen niet bestonden. Fix: Cypress.env('globalconfigUrl')",
        ],
      },
      {
        type: 'code',
        language: 'javascript — p-inputNumber correcte interactie (Cypress)',
        code: `// ❌ FOUT: reset het Angular model naar 0 bij clear()
cy.get('[data-testid="amount-input"] .p-inputnumber-input')
  .clear()
  .type('150')

// ✅ CORRECT: selecteer en overschrijf in één beweging
cy.get('[data-testid="amount-input"] .p-inputnumber-input')
  .focus()
  .type('{selectall}150', { force: true })`,
      },
      {
        type: 'paragraph',
        text: 'Dit soort subtiele bugs zijn extreem moeilijk te vinden via handmatig debuggen — de test slaagt lokaal maar faalt in CI — maar een AI agent die de volledige PrimeNG-documentatie en componentstructuur kent, herkent het patroon onmiddellijk.',
      },
      {
        type: 'heading',
        text: '⏱️ Wave 2: 30 tijdlijn-tests van nul naar volledig',
      },
      {
        type: 'paragraph',
        text: 'De tijdlijn-tests waren de zwaarste klus. Er waren al 29 test-namen geschreven (it.skip), maar de implementatie ontbrak volledig. De agent moest op basis van de beschrijving en het page object zelf de volledige testlogica schrijven. Dat betekende: seed data aanmaken via de backend API, navigeren naar de juiste pagina, interageren met de tijdlijn-component, en assertions schrijven.',
      },
      {
        type: 'steps',
        items: [
          {
            title: 'cy.seedTimeline() al aanwezig',
            text: 'De custom command was al geïmplementeerd in commands.js — de agent hoefde die niet te maken, alleen te gebruiken. Een mooi voorbeeld van hoe bestaande infrastructuur waarde heeft.',
          },
          {
            title: "Testscenario's geïmplementeerd",
            text: '30 tests: periodes toevoegen voor/na/tussen, ongeldige datums, annuleren, verwijderen met bevestiging, navigatie over 12+ periodes, waarschuwingsdrempel via cy.clock().',
          },
          {
            title: 'TimelinePage.js selector-fout gecorrigeerd',
            text: 'De agent ontdekte dat saveButton() en cancelButton() de verkeerde selector gebruikten (sidebar-header vs drawer-header). Dit werd tegelijk rechtgezet.',
          },
        ],
      },
      {
        type: 'heading',
        text: '📋 Wave 3: DSL acceptatietests en de cancel-button bug',
      },
      {
        type: 'paragraph',
        text: 'De DSL (Domain Specific Language) module had testbestanden die qua structuur goed waren, maar nauwelijks acceptatiecriteria bevatten. De agent breidde dsl-overview.cy.js uit van 18 naar 25 tests en dsl-detail.cy.js van 28 naar 38 tests. Tegelijk werd een hardnekkige bug gevonden in restore-commands.js: de cancel-knop gebruikte de verkeerde CSS-selector.',
      },
      {
        type: 'code',
        language: 'javascript — restore-commands.js bug',
        code: `// ❌ VOOR: werkte niet na de PrimeNG drawer refactor
cy.get('button.cancel-button').click()

// ✅ NA: canonical data-testid selector
cy.get('[data-testid="drawer-header-cancel-button"]').click()`,
      },
      {
        type: 'paragraph',
        text: 'Dit is een klassiek voorbeeld van regressionschade door een refactor: de template werd aangepast naar een drawer-patroon met data-testid attributen, maar één restore-command was vergeten. De AI vond het door het patroon in de rest van de codebase te vergelijken.',
      },
      {
        type: 'heading',
        text: '🔒 Wave 4: de backend security audit — schrikken geblazen',
      },
      {
        type: 'paragraph',
        text: 'De backend audit was de meest ontnuchterende stap. De AI doorlichtte systematisch alle 8 REST controllers, alle Feign clients, de Liquibase migraties, de input validatie en de Spring Security configuratie. Het verdict was helder: BLOCKERS PRESENT.',
      },
      {
        type: 'infobox',
        icon: '🔴',
        title: 'Kritieke bevinding: geen autorisatie op 30+ endpoints',
        text: 'Geen enkele van de 8 controllers heeft @FgaPermissionCheck of @PreAuthorize annotaties. Dit betekent dat elke geverifieerde JWT-houder alle data kan muteren — inclusief loonschalen verwijderen, schaalgroepen aanpassen en DSL-regels overschrijven.',
        color: 'border-red-500/30 bg-red-500/5',
      },
      {
        type: 'infobox',
        icon: '🔴',
        title: 'Kritieke bevinding: wildcard CORS op alle controllers',
        text: '@CrossOrigin(origins = "*") staat op alle 8 controllers. Elke externe website kan cross-origin API-requests sturen naar de backend. Dit is een ernstig beveiligingslek in een loonverwerkingssysteem.',
        color: 'border-red-500/30 bg-red-500/5',
      },
      {
        type: 'list',
        items: [
          '🟠 Feijn clients zonder fallback of circuit-breaker: bij uitval van een externe service crasht de hele applicatie',
          '🟠 wcs.url is leeg in application.properties: de WCS Feijn client kan nooit verbinding maken',
          '🟠 16 @RequestBody parameters zonder @Valid: elk input-object passeert ongevalideerd de backend in',
          '🟠 Actuator show-values=ALWAYS: alle Spring-properties inclusief secrets zijn leesbaar via /actuator/env',
          '🟡 Geen Content-Security-Policy headers geconfigureerd',
          '🟡 Liquibase: attractionbonus domein mist migratiescripts',
        ],
      },
      {
        type: 'paragraph',
        text: 'Het is belangrijk om dit in context te plaatsen: dit is een intern configuratiesysteem achter Keycloak SSO, niet direct publiek toegankelijk. Maar voor een productie-release in een loonverwerkingsomgeving zijn dit harde blockers die opgelost moeten worden.',
      },
      {
        type: 'heading',
        text: '🚦 Wave 5: CI/CD kwaliteitspoorten en frontend audit',
      },
      {
        type: 'paragraph',
        text: 'De laatste wave richtte zich op preventie: zorgen dat toekomstige wijzigingen niet stilletjes kwaliteit kunnen afbreken. De agent voegde een validate-agents job toe aan de GitHub Actions pipeline en maakte een quality-gate script aan dat bij elke push een PASS/FAIL verdict geeft.',
      },
      {
        type: 'code',
        language: 'yaml — .github/workflows/cypress.yml',
        code: `validate-agents:
  name: Validate Agent Frontmatter
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: '20'
    - name: Validate Claude agents
      run: node .claude/scripts/validate-agents.mjs --quiet

cypress-smoke:
  name: Cypress Smoke Tests
  needs: validate-agents   # ← wacht op validatie
  runs-on: ubuntu-latest
  # ...`,
      },
      {
        type: 'paragraph',
        text: 'De data-testid audit gaf een verrassend goed resultaat: alle 66 Angular templates hadden al correcte data-testid attributen. Dit is het resultaat van de eerder gevoerde refactor naar het drawer-patroon met gestandaardiseerde testid-conventies.',
      },
      {
        type: 'heading',
        text: '📊 De eindbalans: wat is er bereikt?',
      },
      {
        type: 'grid2',
        items: [
          {
            icon: '✅',
            title: '70+ E2E tests geactiveerd',
            text: '30 tijdlijn-tests geïmplementeerd, 17 DSL acceptatietests toegevoegd, 8 eGov mapping tests gerepareerd, cancel-button bug gefixed.',
          },
          {
            icon: '✅',
            title: 'AI agent setup geoptimaliseerd',
            text: '23 agents gevalideerd (0 errors), evaluatiemetrics toegevoegd, README uitgebreid, decision tree voor agent-selectie.',
          },
          {
            icon: '✅',
            title: 'CI/CD kwaliteitspoorten actief',
            text: 'validate-agents in GitHub Actions pipeline, quality-gate.mjs script, PASS/FAIL verdict bij elke push.',
          },
          {
            icon: '📄',
            title: 'BACKEND_SECURITY_AUDIT.md',
            text: '7 bevindingen gedocumenteerd met bestandspaden, regelnummers en concrete fixinstructies. Verdict: BLOCKERS PRESENT.',
          },
        ],
      },
      {
        type: 'heading',
        text: '💡 Wat leerde ik van deze sessie?',
      },
      {
        type: 'paragraph',
        text: 'De kracht van een AI fleet zit niet in de snelheid alleen — het zit in de breedte. Een menselijk team zou weken nodig hebben om al deze domeinen tegelijk te doorzoeken: E2E tests, page objects, backend controllers, security configuratie, CI/CD pipelines én frontend templates. Een goed geconfigureerde AI fleet doet dit in uren. Maar er zijn ook grenzen.',
      },
      {
        type: 'quote',
        text: 'AI agents zijn ongeklopt in het vinden van patronen, het opsporen van inconsistenties en het schrijven van boilerplate. Ze struikelen nog over domeinkennis die nergens in de codebase staat — zoals de vraag of een leeg wcs.url bewust was tijdens development of een configuratiefout is.',
      },
      {
        type: 'list',
        items: [
          'Parallelle agents zijn multiplicatief, niet additief: 5 agents tegelijk levert meer dan 5× de output van 1 agent sequentieel',
          'Context is alles: agents die de volledige file-tree, POM structuur en tech stack krijgen presteren dramatisch beter dan agents met vage opdrachten',
          'Verificatie blijft menselijk: elk agentresultaat moet worden doorgelezen — niet om fouten te zoeken, maar om domeinspecifieke nuances te beoordelen',
          'Audit-first is goud: de backend audit onthulde blockers die zonder AI-hulp maanden verborgen waren gebleven',
          'Kleine bugs, groot effect: de p-inputNumber bug en de cancel-button selector — dit zijn de dingen die CI laten falen terwijl alles lokaal werkt',
        ],
      },
      {
        type: 'heading',
        text: '🚀 Wat staat er nog op de roadmap?',
      },
      {
        type: 'paragraph',
        text: 'De sessie heeft het project significant dichter bij productie gebracht, maar er zijn harde blockers die menselijk werk vereisen. AI kan de diagnose stellen en de fix suggereren — maar het implementeren van fine-grained authorization vereist domeinkennis over wie wat mag zien en aanpassen in een loonverwerkingscontext. Dat is bedrijfslogica, geen codeerwerk.',
      },
      {
        type: 'steps',
        items: [
          {
            title: 'FGA autorisatie implementeren (🔴 blokker)',
            text: 'Per endpoint bepalen welke rollen (beheerder, HR-medewerker, auditor) welke operaties mogen uitvoeren. @FgaPermissionCheck toevoegen op alle 30+ endpoints.',
          },
          {
            title: 'CORS beperken tot allowlist (🔴 blokker)',
            text: "@CrossOrigin('*') vervangen door een expliciete allowlist van toegestane origins per omgeving (tst, acc, prd).",
          },
          {
            title: 'Bean Validation toevoegen (🟠)',
            text: '@Valid op alle 16 @RequestBody parameters, @NotNull/@Size/@Min/@Max op DTO-velden, foutmeldingen testen via E2E.',
          },
          {
            title: 'Feijn resilience (🟠)',
            text: 'FallbackFactory implementeren voor GlobalconfigCoreClient en WcsClient. wcs.url invullen in application.properties.',
          },
          {
            title: 'Actuator beveiligen (🟠)',
            text: 'show-values=NEVER instellen, of actuator endpoints beperken tot een beveiligd admin-pad.',
          },
        ],
      },
      {
        type: 'heading',
        text: '🔑 Conclusie',
      },
      {
        type: 'paragraph',
        text: 'Een AI agent fleet is geen wondermiddel — het is een krachtig gereedschap dat het beste werkt wanneer je het goed configureert, goede context geeft en de resultaten kritisch doorleest. In deze sessie werden meer dan 70 E2E tests geactiveerd, een volledige security audit uitgevoerd, CI/CD kwaliteitspoorten geïnstalleerd en tientallen kleine bugs gerepareerd. Tegelijkertijd onthulde de audit serieuze beveiligingsproblemen die bewijs zijn dat AI-assistentie en domeinexpertise hand in hand moeten gaan.',
      },
      {
        type: 'infobox',
        icon: '🤝',
        title: 'De samenwerking die werkt',
        text: "AI is razendsnel in analyse, patroonherkenning en boilerplate. Mensen zijn onvervangbaar in domeinkennis, prioriteitsstelling en het beoordelen van beveiligingsrisico's in hun bedrijfscontext. Combineer beide — en je hebt een team dat sneller én veiliger werkt.",
        color: 'border-green-500/30 bg-green-500/5',
      },
    ],
  },
  {
    slug: 'beleggen-coach-ai-platform',
    titel: 'Beleggen Coach: hoe ik een AI-gedreven beleggingsapp bouwde met MCP, Copilot agents en een monorepo',
    excerpt:
      'Van onboarding-wizard tot gepersonaliseerde ETF-aanbevelingen: een technische deep-dive in de architectuur van Beleggen Coach — een full-stack beleggingsplatform gebouwd met Next.js, FastAPI, PostgreSQL, Redis en zes domeinspecifieke MCP servers.',
    datum: '22 april 2026',
    datumISO: '2026-04-22',
    leestijd: '16 min',
    categorie: 'Project',
    categorieKleur: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    afbeelding:
      'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=800&q=80',
    inhoud: [
      {
        type: 'paragraph',
        text: 'Beleggen is voor veel mensen een drempel vol jargon, angst en onzekerheid. Toch is vroeg beginnen met eenvoudige, gespreide ETF-beleggingen één van de krachtigste manieren om vermogen op te bouwen. Ik bouwde Beleggen Coach als een persoonlijk project om die drempel te verlagen — een slimme app die beginners begeleidt van profiel tot concreet beleggingsplan, aangedreven door AI en domeinspecifieke data. In dit artikel neem ik je mee door de volledige technische architectuur, de keuzes die ik maakte en de lessen die ik leerde.',
      },
      {
        type: 'heading',
        text: 'Wat is Beleggen Coach?',
      },
      {
        type: 'paragraph',
        text: 'Beleggen Coach is een full-stack webapplicatie die een gebruiker begeleidt door een gestructureerd onboardingproces: profiel opstellen, risicotolerantie bepalen, ETF-suggesties krijgen op maat en een persoonlijk beleggingsplan genereren. De app is gebouwd als een monorepo met twee hoofdapplicaties — een Next.js frontend en een FastAPI backend — aangevuld met zes onafhankelijke MCP (Model Context Protocol) servers die elk een specifiek domein bedienen.',
      },
      {
        type: 'infobox',
        icon: '💡',
        title: 'Wat is MCP?',
        text: 'Model Context Protocol (MCP) is een open standaard van Anthropic waarmee AI-assistenten zoals GitHub Copilot tools kunnen aanroepen via een gestandaardiseerde interface. In Beleggen Coach fungeert elke MCP server als een slimme module die Copilot-agents kunnen bevragen voor domeinkennis — van ETF-data tot gedragscoaching.',
        color: 'border-emerald-500/30 bg-emerald-500/5',
      },
      {
        type: 'heading',
        text: 'De monorepo structuur',
      },
      {
        type: 'paragraph',
        text: 'Het project is opgezet als een pnpm monorepo. Die keuze heeft meerdere voordelen: gedeelde TypeScript-types tussen frontend en backend, één centrale dependency-lock file en eenvoudiger CI/CD setup. De structuur is clean gescheiden: apps/ voor uitvoerbare applicaties, packages/ voor gedeelde code, mcp/ voor alle MCP servers en docs/ voor architectuur- en productdocumentatie.',
      },
      {
        type: 'code',
        language: 'bash',
        code: `beleggen-coach/
├── apps/
│   ├── web/          # Next.js 14 frontend (App Router)
│   └── api/          # FastAPI backend (Python 3.12, uv)
├── mcp/
│   ├── investor-profile-mcp/   # Risicoscore berekening
│   ├── etf-data-mcp/           # ETF-screening & top-3 ranking
│   ├── market-data-mcp/        # Live koersen (yfinance / Alpha Vantage)
│   ├── portfolio-plan-mcp/     # Beleggingsplan generatie & simulatie
│   ├── behavior-coach-mcp/     # Gedragscoaching & emotionele check-ins
│   └── learning-content-mcp/  # Leermateriaal & quiz content
├── packages/
│   └── shared-types/   # Gedeelde TypeScript interfaces
├── db/                 # Alembic migraties
├── docs/
│   ├── architecture/   # Technische architectuurdocumentatie
│   └── product/        # Feature specs & roadmap
└── .github/
    ├── agents/         # Custom Copilot agents (*.agent.md)
    └── copilot-instructions.md`,
      },
      {
        type: 'heading',
        text: 'De systeemarchitectuur',
      },
      {
        type: 'paragraph',
        text: 'De architectuur volgt een gelaagd model. De Next.js frontend communiceert via REST/JSON met de FastAPI backend. De backend beheert de PostgreSQL database (via SQLAlchemy async) en een Redis cache voor sessiedata en snelle opzoekingen. Daaronder hangen de MCP servers als autonome modules die via het stdio-protocol aangesproken worden door Copilot. Externe diensten zoals Clerk (authenticatie), OpenAI API (AI chat) en Yahoo Finance (live koersen) worden op de juiste lagen geïntegreerd.',
      },
      {
        type: 'grid2',
        items: [
          {
            icon: '⚡',
            title: 'Next.js App Router',
            text: 'Server Components voor snelle initiële laadtijd, Client Components voor interactieve dashboards. Routing via /dashboard, /etfs, /plan, /learn, /chat, /portfolio en /analytics.',
          },
          {
            icon: '🐍',
            title: 'FastAPI + uv',
            text: 'Async Python API met SQLAlchemy 2.0 en Alembic voor migraties. uv als supersnelle package manager vervangt pip/poetry. Routers per domein: onboarding, etfs, portfolio, chat.',
          },
          {
            icon: '🗄️',
            title: 'PostgreSQL + Redis',
            text: 'PostgreSQL voor persistente data (profielen, posities, check-ins). Redis voor cache, sessiegeheugen bij AI chat en dagelijks herberekende ETF-rankings.',
          },
          {
            icon: '🔌',
            title: 'MCP via stdio',
            text: 'Elke MCP server draait als een onafhankelijk Python-proces. Copilot roept tools aan via het stdio-protocol. Elke tool geeft een gestandaardiseerd { success, data, error } object terug.',
          },
        ],
      },
      {
        type: 'heading',
        text: 'De zes MCP servers uitgelegd',
      },
      {
        type: 'paragraph',
        text: 'Het hart van het AI-aspect van Beleggen Coach is het netwerk van zes domeinspecifieke MCP servers. Elk bedient een specifiek expertisedomein en kan onafhankelijk worden getest, gedeployed en geüpgraded. Dit is een fundamenteel ander patroon dan één grote AI-aanroep: kennis is verdeeld over specialisten.',
      },
      {
        type: 'steps',
        items: [
          {
            title: 'investor-profile-mcp — Risicoscore',
            text: 'Ontvangt de onboarding-antwoorden (beleggingshorizon, risicobereidheid, maandelijkse inleg, leeftijd) en berekent een genormaliseerde risicoscore (0-100). Hogere score = hogere risicotolerantie = meer aandelengewicht in het plan.',
          },
          {
            title: 'etf-data-mcp — Screening & ranking',
            text: 'Beheert een gecureerde ETF-database met metadata: TER, categorie, regio, benchmark, historische volatiliteit. De tool get_top3_for_profile() combineert profiel-fit met marktdata en momentum voor een dagelijks bijgewerkte Top 3.',
          },
          {
            title: 'market-data-mcp — Live koersen',
            text: 'Haalt live en historische koersen op via yfinance of Alpha Vantage. Berekent volatiliteit, YTD-rendement en drawdown versus historisch gemiddelde. Wordt gecached in Redis om API-rate-limits te respecteren.',
          },
          {
            title: 'portfolio-plan-mcp — Beleggingsplan',
            text: 'Genereert een concreet beleggingsplan op basis van doelkapitaal, tijdshorizon, maandelijkse inleg en gekozen ETFs. Simuleert ook toekomstige portefeuillegroei met verwacht rendement en inflatiocorrectie.',
          },
          {
            title: 'behavior-coach-mcp — Gedragscoaching',
            text: 'Begeleidt de gebruiker bij emotionele beslissingen. Maandelijkse check-ins vragen naar gevoel, nieuws-invloeden en bereidheid om het plan aan te passen. De coach detecteert patroonafwijkingen en stuurt bij met motiverende inzichten.',
          },
          {
            title: 'learning-content-mcp — Leermateriaal',
            text: 'Levert gepersonaliseerd leermateriaal: artikelen, quizzen en mini-lessen op basis van het profiel van de gebruiker en zijn voortgang. Beginner krijgt andere content dan iemand die al 2 jaar belegt.',
          },
        ],
      },
      {
        type: 'heading',
        text: 'Custom Copilot Agents als AI-ontwikkelteam',
      },
      {
        type: 'paragraph',
        text: 'Naast de runtime-MCP-servers bevat het project ook custom Copilot agents in .github/agents/. Dit zijn gespecialiseerde agents die ik gebruik tijdens de ontwikkeling zelf — niet op productie. Ze kennen de volledige codebase, de architectuurprincipes en de product-specs. Zo heb ik agents voor frontend componenten, API-routers, database-migraties en productanalyse die elk hun eigen expert-context meekrijgen via een gedetailleerde agent.md instructie.',
      },
      {
        type: 'code',
        language: 'markdown',
        code: `# .github/copilot-instructions.md (fragment)

## Stack
- Frontend: Next.js 14 App Router, TypeScript, Tailwind CSS
- Backend: FastAPI, Python 3.12, SQLAlchemy 2.0 async, Alembic
- Database: PostgreSQL (via Docker), Redis
- Package manager: pnpm (monorepo), uv (Python)
- MCP: stdio protocol, elk eigen Python-package

## Principes
- Gebruik altijd async/await in FastAPI routes
- MCP tools returnen altijd { success: bool, data: ..., error: str | None }
- TypeScript strict mode — geen any-types
- Elke nieuwe feature begint met een migratie-bestand`,
      },
      {
        type: 'heading',
        text: 'Fase 6: de roadmap',
      },
      {
        type: 'paragraph',
        text: 'Het project is opgezet in fasen. De eerste vijf fasen legden de fundering: onboarding flow, ETF-database, beleggingsplan, leercentrum en maandelijkse check-in. Fase 6 brengt het platform naar een volwassen productieniveau met zeven grote toevoegingen: login & authenticatie via Clerk, een volledig uitgebreid dashboard, AI-chatinterface met streaming, top-3 ETF-aanbevelingen op basis van live marktdata, portefeuille-opvolging, analytisch overzicht en een gecureerde bronpagina.',
      },
      {
        type: 'infobox',
        icon: '🏗️',
        title: 'Fase 6 prioritering',
        text: 'Login & Auth is de basis voor alles persoonlijk. Daarna Dashboard → Bronpagina → Portefeuille → Top 3 ETFs → AI Chat → Analytics. De bronpagina is bewust vroeg gepland: geen afhankelijkheden, snel te bouwen, direct waarde voor de gebruiker.',
        color: 'border-blue-500/30 bg-blue-500/5',
      },
      {
        type: 'heading',
        text: 'AI Chat met guardrails',
      },
      {
        type: 'paragraph',
        text: 'De AI-chatfunctie is technisch interessant én verantwoordelijk complex. De chat-router in FastAPI stuurt de gebruikersvraag naar OpenAI GPT-4o met een systeem-prompt die de context bevat: gebruikersprofiel, huidig plan, en relevante ETF-data opgehaald via MCP. Streaming via Server-Sent Events zorgt voor een vloeiende gebruikerservaring. Wat ik bewust niet doe: expliciete koopadvies geven. De guardrails in de systeem-prompt zorgen dat de AI altijd een disclaimer toevoegt en geen "koop nu" statements maakt.',
      },
      {
        type: 'code',
        language: 'python',
        code: `# apps/api/src/routers/chat.py (vereenvoudigd)
@router.post("/chat")
async def chat(request: ChatRequest, user: TokenData = Depends(get_current_user)):
    profile = await get_user_profile(user.user_id)
    etf_context = await etf_data_mcp.get_top3_for_profile(profile.id)
    
    system_prompt = f"""
    Je bent een beleggingscoach voor beginners.
    Gebruikersprofiel: {profile.model_dump_json()}
    Huidige Top 3 ETFs: {etf_context}
    
    REGELS:
    - Geef nooit expliciete koop- of verkoopadvies
    - Voeg altijd toe: "Dit is geen financieel advies."
    - Leg termen uit in gewone taal
    - Verwijs door naar een financieel adviseur bij complexe vragen
    """
    
    async for chunk in openai_stream(system_prompt, request.messages):
        yield f"data: {chunk}\\n\\n"`,
      },
      {
        type: 'heading',
        text: 'Wat ik leerde van dit project',
      },
      {
        type: 'list',
        items: [
          'MCP is een game-changer voor AI-geïntegreerde applicaties: kennis opdelen in domeinspecifieke servers maakt het systeem veel onderhoudbaarder dan één grote AI-aanroep',
          'uv als Python package manager is razendsnel — een volledige sync van een nieuw project duurt seconden in plaats van minuten',
          'pnpm monorepo + turborepo zorgt voor een nette scheiding maar vereist discipline in het beheer van gedeelde types',
          'Guardrails in de systeem-prompt zijn niet optioneel voor een financiële applicatie — ze zijn de eerste verdedigingslinie tegen onjuist advies',
          'Redis als cache voor ETF-data vermijdt dat elke gebruikersinteractie een dure API-call triggert naar Yahoo Finance of Alpha Vantage',
          'Custom Copilot agents tijdens ontwikkeling versnellen het werk aanzienlijk — ze kennen de architectuurprincipes en code-conventies beter dan een generieke AI',
        ],
      },
      {
        type: 'quote',
        text: 'De beste beleggingsapp is niet de slimste — het is de meest begrijpbare. AI helpt niet door het antwoord te geven, maar door de vraag te verduidelijken.',
      },
      {
        type: 'heading',
        text: 'De code bekijken',
      },
      {
        type: 'paragraph',
        text: 'Het volledige project staat open-source op GitHub: github.com/koenvorster/beleggen-coach. Je vindt er de architectuurdocumentatie in docs/architecture/overview.md, de feature roadmap in docs/product/fase6-features.md en de MCP-serverimplementaties in mcp/. Feedback, issues en pull requests zijn welkom.',
      },
      {
        type: 'infobox',
        icon: '⚠️',
        title: 'Disclaimer',
        text: 'Beleggen Coach is een persoonlijk leer- en demonstratieproject. De app geeft geen financieel advies. Alle ETF-suggesties en beleggingsplannen zijn puur informatief. Raadpleeg een gecertificeerd financieel adviseur voor persoonlijk beleggingsadvies.',
        color: 'border-yellow-500/30 bg-yellow-500/5',
      },
    ],
  },
  {
    slug: 'ai-avonturen-april-2026-copilot-cli-ollama-control-platform',
    titel: 'Mijn AI-lab in april 2026: Copilot CLI, lokale LLMs en een platform dat zichzelf runt',
    excerpt:
      'Van GitHub Copilot CLI als slimme terminal-assistent tot een volledig lokaal AI Control Platform — een eerlijk verslag van wat werkt, wat traag is en wat me verraste tijdens mijn recentste AI-avonturen.',
    datum: '23 april 2026',
    datumISO: '2026-04-23',
    leestijd: '12 min',
    categorie: 'AI',
    categorieKleur: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
    afbeelding:
      'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=800&q=80',
    inhoud: [
      {
        type: 'paragraph',
        text: 'April 2026 was een drukke maand in mijn AI-lab. Ik wil graag eerlijk delen wat ik de laatste weken heb gedaan, wat verrassend goed werkte en waar ik tegenaan liep. Geen gepolijste tutorial — gewoon een oprecht verslag van mijn laatste AI-avonturen. Van GitHub Copilot CLI die mijn terminal overneemt, over Ollama-agents die lokaal codebasissen analyseren, tot een AI Control Platform dat zichzelf bewaakt. Buckle up.',
      },
      {
        type: 'heading',
        text: '🤖 GitHub Copilot CLI: AI in je terminal',
      },
      {
        type: 'paragraph',
        text: 'De grootste verrassing van deze maand was GitHub Copilot CLI. Ik kende Copilot al van in de IDE, maar de CLI-variant is een ander beest. Je opent een terminal, typt wat je wilt bereiken in natuurlijke taal, en Copilot gaat aan de slag — hij leest bestanden, voert commando\'s uit, debugt fouten en legt elke stap uit. Het voelt alsof je een junior developer naast je hebt zitten die nooit moe wordt en altijd de juiste PowerShell-syntax kent.',
      },
      {
        type: 'infobox',
        icon: '💡',
        title: 'Wat is GitHub Copilot CLI?',
        text: 'GitHub Copilot CLI is een interactieve terminal-assistent die je helpt met software engineering taken. Hij heeft toegang tot je bestandssysteem, kan commando\'s uitvoeren, code lezen en schrijven, en integreert met GitHub, Jira, Confluence en MCP-servers. Beschikbaar via GitHub Copilot subscription.',
        color: 'border-violet-500/30 bg-violet-500/5',
      },
      {
        type: 'paragraph',
        text: 'Concreet gebruik ik het voor het opstarten van het VorstersNV-project. Vandaag vroeg ik simpelweg: "kan je dit project lokaal nu draaien?" — en Copilot CLI analyseerde de volledige repo, controleerde welke tools beschikbaar waren (Python 3.12 ✅, Node.js 22 ✅, Ollama ✅, Docker ❌), ontdekte dat Docker Desktop niet geïnstalleerd was, vond de juiste poorten, en startte FastAPI én Next.js op zonder dat ik één commando zelf hoefde in te typen. Dat is de toekomst van developer tooling.',
      },
      {
        type: 'steps',
        items: [
          {
            title: 'Stap 1 — Context verzamelen',
            text: 'Copilot CLI leest docker-compose.yml, .env bestanden, requirements.txt en de projectstructuur om te begrijpen wat het project nodig heeft.',
          },
          {
            title: 'Stap 2 — Beschikbare tools checken',
            text: 'Via PowerShell-commando\'s controleert hij welke tools aanwezig zijn: Python, Node, Docker, Ollama, open poorten.',
          },
          {
            title: 'Stap 3 — Intelligente beslissing',
            text: 'Geen Docker? Dan start hij FastAPI direct met uvicorn en Next.js met npm run dev — zonder dat ik iets hoefde te zeggen.',
          },
          {
            title: 'Stap 4 — Verificatie',
            text: 'Na het opstarten doet hij een /health check op de FastAPI en controleert hij poort 3000 — pas dan meldt hij "klaar".',
          },
        ],
      },
      {
        type: 'heading',
        text: '🧠 Ollama lokaal: de realiteit van CPU-inference',
      },
      {
        type: 'paragraph',
        text: 'Ik draai Ollama lokaal op mijn laptop — een Intel i7-1165G7 zonder dedicated GPU. De eerlijkheid gebiedt me te zeggen: dat is traag. Mistral 7B doet er ~290 seconden over per chunk bij een codebase-analyse. Dat is geen typo — bijna vijf minuten per stuk code. Toch gebruik ik het, want de voordelen zijn reëel: geen cloud kosten, geen data-privacy zorgen, en volledige controle over welk model ik gebruik.',
      },
      {
        type: 'grid2',
        items: [
          {
            icon: '✅',
            title: 'Wat werkt',
            text: 'mistral:7B en llama3.2:3B draaien stabiel op CPU. Ideaal voor korte taken, code review per bestand, en eenvoudige agent-aanroepen.',
          },
          {
            icon: '❌',
            title: 'Wat niet werkt',
            text: 'gpt-oss:20b met MXFP4-quantisatie — niet compatibel met CPU-only. starcoder:3b begrijpt geen instructies, alleen code completion.',
          },
          {
            icon: '⚡',
            title: 'Gaming desktop (gepland)',
            text: 'Met een RTX 3090 of 4070 Ti via OLLAMA_BASE_URL naar de desktopserver: mistral:7B in ~1-2 seconden. Game changer.',
          },
          {
            icon: '🎯',
            title: 'Beste use case nu',
            text: 'Analyse van één bestand tegelijk, met --dry-run eerst om te zien welke bestanden worden gescand vóór de AI aan het werk gaat.',
          },
        ],
      },
      {
        type: 'code',
        language: 'bash',
        code: `# Codebase analyseren met lokale AI (stap voor stap)
# 1. Eerst dry-run: alleen bestanden scannen, geen AI
python scripts/analyse_project.py \\
  --pad C:\\pad\\naar\\klant-project \\
  --dry-run

# 2. Volledige analyse (mistral:7B op CPU — pak een koffie)
python scripts/analyse_project.py \\
  --pad C:\\pad\\naar\\klant-project

# 3. Via gaming desktop server (veel sneller)
# In .env:
# OLLAMA_BASE_URL=http://192.168.1.XXX:11434
# OLLAMA_DEFAULT_MODEL=mistral:7b`,
      },
      {
        type: 'heading',
        text: '🏗️ Het AI Control Platform: van idee naar productie',
      },
      {
        type: 'paragraph',
        text: 'Het grote project van de laatste maanden is het AI Control Platform dat ik heb gebouwd als onderdeel van VorstersNV. Het is ontstaan uit een concrete nood: ik had meer dan 20 Ollama-agents die allemaal los van elkaar draaiden, zonder centraal beheer, zonder audit trail, zonder manier om te weten welke agent goed presteerde en welke niet. De oplossing: één centrale Control Plane die alles orkestreert.',
      },
      {
        type: 'list',
        items: [
          '🎛️ Control Plane: één REST-endpoint (POST /api/ai/run) dat alle AI-aanroepen routeert op basis van 8 dimensies (capability, risk, environment, budget, latency, model, policy, rollout)',
          '📋 Policy Engine: governance-regels als YAML — welke agent mag welke tool gebruiken, wanneer is human-in-the-loop verplicht, welk model wordt ingezet per risiconiveau',
          '📓 Decision Journal: elke AI-beslissing wordt gelogd met trace_id, input, output, rationale en verdict — volledig auditeerbaar',
          '📊 Quality Monitor: real-time alerts wanneer een agent degradeert (CRITICAL/DEGRADED/SLOW status)',
          '🧪 A/B Tester met AutoPromoter: winnende prompt-versies worden automatisch gepromoot, verliezende teruggedraaid',
          '🔗 Event Bridge: Mollie-webhooks en order-events triggeren automatisch de juiste AI skill chain',
        ],
      },
      {
        type: 'quote',
        text: 'Het meest waardevolle was niet de technologie zelf, maar de governance die eromheen zit. Een AI-agent zonder audit trail is een tijdbom — je weet pas dat er iets mis is als het al fout gegaan is.',
      },
      {
        type: 'heading',
        text: '🔬 Wat ik leerde over AI-agent architectuur',
      },
      {
        type: 'paragraph',
        text: 'Na maanden bouwen heb ik een paar harde lessen geleerd die ik nergens anders las. Ten eerste: agents zijn zo goed als hun context. Een agent die alleen de user input krijgt, presteert significant slechter dan een agent die ook de relevante business-context meekrijgt — klanthistorie, ordergegevens, productcategorie. De prompt engineering is slechts 30% van het werk; de andere 70% is het ophalen en structureren van de juiste context vóór de agent aanroep.',
      },
      {
        type: 'paragraph',
        text: 'Ten tweede: monitor alles, vertrouw niets. De Quality Monitor in het platform alarmeert me wanneer een agent structureel slechter presteert. Dat klinkt voor de hand liggend, maar zonder automatische monitoring merk je het pas na tientallen slechte antwoorden aan klanten. De Decision Journal heeft me al drie keer gered: één keer een policy-bug gevonden, één keer een model dat stilletjes andere outputs gaf na een Ollama update, en één keer een agent die op basis van verouderde productdata adviseerde.',
      },
      {
        type: 'code',
        language: 'yaml',
        code: `# Voorbeeld policy in het AI Control Platform
# policies/order_verwerking.yml
policy_id: order-fraud-check
version: "1.2"
applies_to:
  - capability: fraud_detection
  - risk_level: [medium, high, critical]

rules:
  - id: hitl-high-risk
    condition: risk_score >= 75
    action: require_human_approval
    notify: ["fraud-team@vorsternv.be"]

  - id: block-critical
    condition: risk_score >= 95
    action: block_order
    log_to_decision_journal: true

  - id: model-selection
    condition: risk_score >= 50
    preferred_model: mistral:7b  # meer nauwkeurig, trager
    fallback_model: llama3.2:3b  # sneller, minder nauwkeurig`,
      },
      {
        type: 'heading',
        text: '📁 Consultancy tooling: code analyseren voor klanten',
      },
      {
        type: 'paragraph',
        text: 'De nieuwste richting voor VorstersNV is IT/AI-consultancy voor Belgische KMOs. Concreet betekent dat: ik neem een bestaande codebase van een klant, scan die met lokale AI-agents, en lever een rapport met technische bevindingen, risico\'s en aanbevelingen. Geen cloud, geen data die de organisatie verlaat, geen licentiekosten per token. Alles draait lokaal op mijn laptop of op een kleine server bij de klant.',
      },
      {
        type: 'paragraph',
        text: 'De tooling hiervoor is bijna klaar: scripts/analyse_project.py scant de bestanden, code_analyse_agent beoordeelt elk bestand op architectuur en risico\'s, klant_rapport_agent schrijft de samenvatting in klantgerichte taal, en bedrijfsproces_agent mapt het AS-IS proces. De output gaat naar documentatie/analyse/ als Markdown-rapport dat ik kan bezorgen of in een Confluence-pagina zetten.',
      },
      {
        type: 'infobox',
        icon: '🚀',
        title: 'Fase 6 in volle gang',
        text: 'Het VorstersNV platform evolueert van webshop naar freelance IT/AI-consultancy platform. De webshop-functionaliteit blijft, maar de focus ligt nu op tools die ik gebruik voor klantopdrachten: codebase-analyse, procesautomatisering en AI-agent implementatie voor KMOs.',
        color: 'border-emerald-500/30 bg-emerald-500/5',
      },
      {
        type: 'heading',
        text: '🗺️ Wat staat er nog op de planning',
      },
      {
        type: 'list',
        items: [
          'Gaming desktop server configureren als Ollama inference node — OLLAMA_BASE_URL switchen en klaar',
          'Docker Desktop installeren zodat de volledige stack (PostgreSQL + Redis) via één docker compose up draait',
          'Eerste echte klantopdracht: codebase analyse van een bestaand Java ERP-systeem',
          'A/B tester koppelen aan de Quality Monitor zodat slechte prompts automatisch worden teruggedraaid',
          'MCP server voor de consulting module — Confluence integratie voor automatisch rapport genereren',
        ],
      },
      {
        type: 'paragraph',
        text: 'Het tempo ligt hoog, maar dat is precies de charme van een persoonlijk platform: je kiest zelf wat je bouwt, hoe snel en waarvoor. AI maakt dat solo-development tegenwoordig dichter bij team-development komt — niet qua sociale dynamiek, maar qua snelheid en kwaliteit van wat je kunt afleveren. Als je vragen hebt over het platform, de consultancy aanpak of de Ollama setup — reach out. Ik deel graag wat werkt.',
      },
      {
        type: 'quote',
        text: 'AI maakt solo-development sneller, maar maakt het niet makkelijker. De moeilijkste beslissingen — architectuur, prioriteiten, wat je weggooit — die blijf je zelf maken. En dat is precies hoe het hoort.',
      },
    ],
  },
]

export function getBlogPostBySlug(slug: string): BlogPost | undefined {
  return blogPosts.find((p) => p.slug === slug)
}
