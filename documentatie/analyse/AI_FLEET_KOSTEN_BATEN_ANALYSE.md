# AI Fleet Kosten-Batenanalyse
## Loonberekening-analyse met VorstersNV Agent Orchestratie

| Metadata            | Waarde                                                    |
|---------------------|-----------------------------------------------------------|
| **Datum**           | 21 april 2026                                             |
| **Auteur**          | Koen Vorsters                                             |
| **Context**         | Hypothetische toepassing van VorstersNV fleet-architectuur op lpbunified rekenmotor-analyse |
| **Vergelijkingsbasis** | Handmatige uitvoering (referentie) vs. AI-fleet uitvoering |
| **Type document**   | Kosten-batenanalyse — intern                              |

---

## Inhoudsopgave

1. [Situatieschets: wat is er manueel gedaan?](#1-situatieschets-wat-is-er-manueel-gedaan)
2. [De VorstersNV fleet-architectuur](#2-de-vorsstersnv-fleet-architectuur)
3. [Fleet-ontwerp voor dit specifieke project](#3-fleet-ontwerp-voor-dit-specifieke-project)
4. [Tijdsanalyse: manueel vs. AI-fleet](#4-tijdsanalyse-manueel-vs-ai-fleet)
5. [Kostprijsberekening](#5-kostprijsberekening)
6. [Kwaliteitsvergelijking](#6-kwaliteitsvergelijking)
7. [Risico's en beperkingen van de AI-aanpak](#7-risicos-en-beperkingen-van-de-ai-aanpak)
8. [ROI-berekening en terugverdientijd](#8-roi-berekening-en-terugverdientijd)
9. [Schaalbaarheid: wat als er meer projecten zijn?](#9-schaalbaarheid-wat-als-er-meer-projecten-zijn)
10. [Aanbeveling en conclusie](#10-aanbeveling-en-conclusie)

---

## 1. Situatieschets: wat is er manueel gedaan?

Voor de lpbunified rekenmotor zijn de volgende deliverables geproduceerd:

| # | Deliverable                               | Bestand                                     |
|---|-------------------------------------------|---------------------------------------------|
| 1 | Broncode-analyse (inventarisatie)         | `LOONBEREKENING_ANALYSE.txt` (925 regels)   |
| 2 | Loonschalen-analyse                       | `LOONSCHALEN_ANALYSE.txt`                   |
| 3 | Kritische architectuurreview              | `LOONBEREKENING_KRITISCHE_ANALYSE.md`       |
| 4 | Blogpost (architectuur/Chain of Resp.)    | Gepubliceerd op VorstersNV blog             |

**Manuele uitvoering vereist:**
- Diepgaande Java-kennis
- Kennis van enterprise design patterns
- Kennis van Belgische loonwetgeving
- Technisch schrijfvaardigheid
- Kritisch architectureel inzicht

Dit zijn **schaarse, dure competenties** die zelden in één persoon gecombineerd zijn.

---

## 2. De VorstersNV Fleet-Architectuur

VorstersNV is een AI-orchestratieplatform dat agents, skills en sub-agents combineert in configureerbare workflows. De kern-concepten:

```
┌─────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR AGENT                          │
│           (plant, verdeelt, consolideert resultaten)            │
└──────────────┬─────────────────┬─────────────────┬─────────────┘
               │                 │                 │
    ┌──────────▼──────┐ ┌────────▼────────┐ ┌──────▼──────────┐
    │   FLEET A       │ │   FLEET B       │ │   FLEET C       │
    │   Code Analysis │ │   Review &      │ │   Content       │
    │   Fleet         │ │   Kritiek Fleet │ │   Fleet         │
    └──────────┬──────┘ └────────┬────────┘ └──────┬──────────┘
               │                 │                 │
    ┌──────────▼──────┐ ┌────────▼────────┐ ┌──────▼──────────┐
    │ Sub-agents:     │ │ Sub-agents:     │ │ Sub-agents:     │
    │ • CodeReader    │ │ • Critic        │ │ • BlogWriter    │
    │ • PatternFinder │ │ • RiskAssessor  │ │ • TechEditor    │
    │ • DomainMapper  │ │ • Recommender   │ │ • Formatter     │
    │ • DocWriter     │ │ • Prioritizer   │ │ • Publisher     │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
```

**Kernprincipes:**
- Agents werken **parallel** binnen een fleet
- Fleets werken **sequentieel** of **parallel** naargelang afhankelijkheden
- De orchestrator beheert de **context** en **output-routing**
- Elke agent heeft een **specifieke skill** en een **beperkte scope**
- Menselijke review blijft het **kwaliteitscontrolepunt**

---

## 3. Fleet-ontwerp voor dit Specifieke Project

### Fleet A — Code Analysis Fleet

**Trigger:** Beschikbaarheid van Java-broncode  
**Parallellisatie:** Ja — sub-agents werken per package

```
Fleet A: Code Analysis
├── Agent A1: StructuurScanner
│   Skill: scan Java package-hiërarchie, extraheer klasse-relaties
│   Input:  Java broncode directory
│   Output: Klasse-hiërarchie + dependency graph (JSON)
│   Tijd:   ~8 min (automatisch)
│
├── Agent A2: PatternDetector
│   Skill: identificeer design patterns (CoR, Strategy, Factory, ...)
│   Input:  A1 output + geselecteerde klassen
│   Output: Pattern-inventaris met bewijs-snippets
│   Tijd:   ~12 min (automatisch)
│
├── Agent A3: DomainMapper
│   Skill: extraheer domeinbegrippen, business rules, datumgrenzen
│   Input:  broncode + A2 output
│   Output: Domein-glossarium concept + business rules lijst
│   Tijd:   ~15 min (automatisch)
│
└── Agent A4: DocWriter
    Skill: schrijf gestructureerde technische analyse
    Input:  A1 + A2 + A3 outputs
    Output: LOONBEREKENING_ANALYSE.txt equivalent
    Tijd:   ~10 min (automatisch)

Fleet A totaal: ~25 min (A1+A2+A3 parallel, A4 daarna)
Menselijke review: 30 min
```

---

### Fleet B — Kritische Review Fleet

**Trigger:** Voltooiing Fleet A  
**Parallellisatie:** Gedeeltelijk

```
Fleet B: Kritische Review
├── Agent B1: ArchitectCritic
│   Skill: evalueer architectuurkeuzes vs. best practices 2024–2026
│   Input:  Fleet A output + architectuurstandaarden
│   Output: Sterktes + zwaktes lijst (ruwe bevindingen)
│   Tijd:   ~10 min
│
├── Agent B2: DependencyAuditor
│   Skill: analyseer externe dependencies (versies, onderhoudsstatus, CVEs)
│   Input:  pom.xml / build.gradle + Fleet A output
│   Output: Dependency-risicotabel
│   Tijd:   ~8 min (parallel met B1)
│
├── Agent B3: TechDebtQuantifier
│   Skill: kwantificeer techdebt op basis van patronen en antipatronen
│   Input:  B1 + B2 output
│   Output: Techdebt-inventaris met ernst/effort scores
│   Tijd:   ~10 min
│
└── Agent B4: ReportWriter
    Skill: schrijf gestructureerd kritisch architectuurrapport
    Input:  B1 + B2 + B3 outputs
    Output: LOONBEREKENING_KRITISCHE_ANALYSE.md equivalent
    Tijd:   ~12 min

Fleet B totaal: ~30 min (B1+B2 parallel, B3 daarna, B4 daarna)
Menselijke review + aanvullingen: 45 min
```

---

### Fleet C — Content Fleet

**Trigger:** Fleet A output (kan parallel met Fleet B)  
**Parallellisatie:** Ja

```
Fleet C: Content Creation
├── Agent C1: BlogStrategist
│   Skill: bepaal invalshoek, doelgroep, toon, structuur voor blogpost
│   Input:  Fleet A output + bestaande blog-stijlgids
│   Output: Blog outline (titels, secties, key points)
│   Tijd:   ~5 min
│
├── Agent C2: TechWriter
│   Skill: schrijf technische blogpost op basis van outline
│   Input:  C1 outline + Fleet A output
│   Output: Draft blogpost met code voorbeelden
│   Tijd:   ~15 min (parallel na C1)
│
└── Agent C3: Publisher
    Skill: formatteer naar blog.ts ContentBlock formaat, push naar data
    Input:  C2 output + blog.ts schema
    Output: Directe toevoeging aan blog.ts
    Tijd:   ~5 min

Fleet C totaal: ~25 min
Menselijke review: 20 min
```

---

### Orchestrator flow

```
Stap 1: Mens levert broncode-locatie + projectcontext (5 min)
         │
Stap 2: Fleet A — Code Analysis (25 min automatisch)
         │
         ├──► Fleet B — Kritische Review (30 min automatisch)
         │
         └──► Fleet C — Content (25 min automatisch, parallel met B)
                    │
Stap 3: Mens reviewt alle outputs (45 + 20 = 65 min)
         │
Stap 4: Orchestrator consolideert, pusht naar repo (5 min automatisch)

TOTAAL MANUELE TIJDSINVESTERING: ~75 minuten (1u15)
TOTAAL AUTOMATISCHE TIJD: ~55 minuten (agent klokwandtijd)
TOTALE DOORLOOPTIJD: ~130 minuten (2u10) — meeste manuele tijd is review
```

---

## 4. Tijdsanalyse: Manueel vs. AI-Fleet

### 4.1 Manuele aanpak — gedetailleerde tijdsraming

| Activiteit                                        | Junior (jr) | Senior (sr) | Expert (exp) |
|---------------------------------------------------|-------------|-------------|--------------|
| Broncode lezen en begrijpen (925 regels analyse)  | 8 u         | 4 u         | 2,5 u        |
| Klasse-hiërarchie en patronen identificeren       | 4 u         | 2 u         | 1 u          |
| Domeinbegrippen en business rules documenteren    | 3 u         | 1,5 u       | 1 u          |
| LOONBEREKENING_ANALYSE.txt schrijven              | 4 u         | 2 u         | 1,5 u        |
| Kritische architectuurreview schrijven            | 6 u         | 3 u         | 2 u          |
| Risicomatrix en aanbevelingen uitwerken           | 3 u         | 1,5 u       | 1 u          |
| Blogpost schrijven                                | 3 u         | 2 u         | 1,5 u        |
| **Totaal**                                        | **31 u**    | **16 u**    | **10,5 u**   |

> **Opmerking:** "Expert" = iemand met 10+ jaar Java enterprise ervaring én kennis van Belgische loonwetgeving én technisch schrijfvaardigheid. Dit profiel is extreem schaars.

### 4.2 AI-fleet aanpak — tijdsraming

| Activiteit                                        | Automatisch | Manuele review | Totaal   |
|---------------------------------------------------|-------------|----------------|----------|
| Broncode-analyse (Fleet A)                        | 25 min      | 30 min         | 55 min   |
| Kritische review (Fleet B)                        | 30 min      | 45 min         | 75 min   |
| Blogpost (Fleet C, parallel met B)                | 25 min      | 20 min         | 45 min   |
| Orchestrator setup + context leveren              | 5 min       | 5 min          | 10 min   |
| Consolidatie en push                              | 5 min       | 5 min          | 10 min   |
| **Totaal**                                        | **~55 min** | **~75 min**    | **~130 min** |

> **Opmerking:** Fleets B en C lopen parallel, dus de **klokwandtijd** is korter dan de optelsom.

### 4.3 Vergelijkingstabel

| Dimensie                   | Manueel (senior) | AI-Fleet       | Verschil        |
|----------------------------|------------------|----------------|-----------------|
| **Totale tijdsinvestering** | 16 uur           | 1u15 (manueel deel) | **-14,75 uur** |
| **Doorlooptijd (kalender)** | 2–3 dagen        | ~2,5 uur       | **-94%**        |
| **Vereist profiel**        | Senior + expert  | Medior IT      | Lager profiel   |
| **Herhaalbaar?**           | Nee (handmatig)  | Ja (playbook)  | Volledig        |
| **Schaalbaarheid**         | Lineair          | Sublineair     | Significant     |
| **Consistentie output**    | Variabel         | Hoog           | Beter           |

---

## 5. Kostprijsberekening

### 5.1 Manuele kosten (referentie)

| Profiel          | Uurtarief (markt) | Uren  | Totaal      |
|------------------|-------------------|-------|-------------|
| Senior developer | €95/u             | 16 u  | **€1.520**  |
| Expert (hybrid)  | €130/u            | 10,5 u| **€1.365**  |

> Externe consultant / freelance tarieven gebruikt als referentie.

### 5.2 AI-Fleet kosten

**Eenmalige setup (VorstersNV fleet configuratie):**

| Component                                         | Tijdsinvestering | Kosten (intern) |
|---------------------------------------------------|------------------|-----------------|
| Fleet A config (agents, prompts, skills)          | 4 uur            | €380            |
| Fleet B config (critic agents, rubrics)           | 4 uur            | €380            |
| Fleet C config (blog-agent, schema-integratie)    | 2 uur            | €190            |
| Orchestrator integratie + testen                  | 4 uur            | €380            |
| **Eenmalige setup totaal**                        | **14 uur**       | **€1.330**      |

**Terugkerende kosten per uitvoering:**

| Component                                         | Kosten per run  |
|---------------------------------------------------|-----------------|
| LLM API-tokens (Claude / GPT-4o, ~500k tokens)   | €8–€15          |
| Compute (VorstersNV platform, cloud)              | €2–€5           |
| Manuele review tijd (medior, 1u15 @ €65/u)        | €81             |
| **Totaal per uitvoering**                         | **€91–€101**    |

### 5.3 Break-even analyse

```
Setup kost:                    €1.330 (eenmalig)
Besparing per uitvoering:      €1.520 - €101 = €1.419 (vs. senior manueel)

Break-even: €1.330 / €1.419 = 0,94 uitvoeringen
→ Break-even bereikt na de EERSTE volledige uitvoering.

Bij 2e uitvoering: netto winst €1.419
Bij 5e uitvoering: netto winst €7.095 − €1.330 = €5.765 totaal
Bij 10e uitvoering: netto winst €14.190 − €1.330 = €12.860 totaal
```

**Visualisatie break-even:**

```
Kosten €
 15.000 │                              ╱  Manueel
        │                           ╱
 12.000 │                        ╱
        │                     ╱
  9.000 │                  ╱       ╱ AI Fleet
        │               ╱      ╱
  6.000 │            ╱      ╱
        │         ╱      ╱
  3.000 │ Setup╱╱     ╱  ← Break-even ≈ run 1
  1.330 │    ╱╱    ╱
        │  ╱╱   ╱
      0 └──────────────────────────────────
         0    2    4    6    8   10  Runs
```

---

## 6. Kwaliteitsvergelijking

### 6.1 Waar AI-fleet beter scoort

| Criterium                       | Manueel        | AI-Fleet       | Voordeel     |
|---------------------------------|----------------|----------------|--------------|
| **Volledigheid inventarisatie** | Afhankelijk van aandacht | Systematisch, elke klasse | Fleet ✅ |
| **Consistente opmaak**          | Variabel       | Template-gedreven | Fleet ✅  |
| **Snelheid**                    | Langzaam       | Snel           | Fleet ✅     |
| **Schaalbaarheid**              | Lineair        | Sublineair     | Fleet ✅     |
| **Herhaalbaar (audits, updates)** | Nee          | Ja             | Fleet ✅     |
| **Geen "moe worden"**           | Risico bij lange sessies | Consistent | Fleet ✅ |

### 6.2 Waar manuele aanpak beter scoort

| Criterium                            | Manueel        | AI-Fleet       | Voordeel     |
|--------------------------------------|----------------|----------------|--------------|
| **Domeinexpertise integreren**       | Diep           | Oppervlakkig   | Manueel ✅   |
| **Nieuwe, onverwachte inzichten**    | Mogelijk       | Beperkt        | Manueel ✅   |
| **Nuance in critieken**              | Hoog           | Matig          | Manueel ✅   |
| **Impliciete kennisintegratie**      | Ja             | Nee            | Manueel ✅   |
| **Verantwoordelijkheid output**      | Duidelijk      | Onduidelijk    | Manueel ✅   |

### 6.3 Hybride model als optimum

De **optimale aanpak is hybride**:

```
AI Fleet → 80% van het werk (inventarisatie, structuur, eerste draft)
Menselijke expert → 20% van het werk (diepte, nuance, validatie, verantwoording)

Resultaat: kwaliteit van een expert in 1/5 van de tijd
```

Het manueel geproduceerde document `LOONBEREKENING_KRITISCHE_ANALYSE.md` illustreert dit perfect:
- De **structuur en volledigheid** had een fleet kunnen genereren
- De **specifieke kritieken** (APO-module risico, contradictiecheck, Fiskgezinstoestand nuance) vereisten domeinkennis die een expert inbrengt
- De **aanbevelingen met Java-codevoorbeelden** vereisten senior Java kennis

---

## 7. Risico's en Beperkingen van de AI-aanpak

### 7.1 Hallucinations in technische analyse

**Risico:** AI kan klassen, methoden of afhankelijkheden "verzinnen" die niet bestaan, of relaties onjuist beschrijven.

**Mitigatie:**
- Agent A1 (StructuurScanner) werkt uitsluitend op daadwerkelijke code — geen interpretatie, enkel extractie
- Elke agent-output wordt gevalideerd door een volgende agent (peer review in de chain)
- Menselijke review als finale kwaliteitspoort

**Restrisico:** Matig — acceptabel met de bovenstaande mitigaties.

### 7.2 Verlies van domeinexpertise

**Risico:** Als een fleet de analyses uitvoert, bouwt het team minder domeinkennis op.

**Mitigatie:**
- De menselijke review is essentieel: de reviewer moet de output kritisch evalueren, niet enkel goedkeuren
- Documenteer expliciet welke inzichten uit de review kwamen vs. de fleet
- Gebruik fleets als versneller, niet als vervanging van leerproces

**Restrisico:** Middel — vereist actief tegenbeleid.

### 7.3 Afhankelijkheid van prompt-kwaliteit

**Risico:** De kwaliteit van de fleet-output is sterk afhankelijk van de kwaliteit van de prompts en rubrics.

**Mitigatie:**
- Investeer in prompt engineering als core competentie
- Bewaar en versie-beheer prompts in Git
- Test prompts op nieuwe projecten voor je ze als "productie" beschouwt

**Restrisico:** Laag tot middel — beheersbaar met een prompting-standaard.

### 7.4 Confidentialiteit van broncode

**Risico:** Broncode die naar externe LLM APIs gestuurd wordt (OpenAI, Anthropic) verlaat de organisatiegrenzen.

**Mitigatie:**
- Gebruik **on-premise LLM** (Llama 3, Mistral, Code Llama) voor code-analyse van vertrouwelijke broncode
- Of gebruik **enterprise API** met data-processing agreement (Azure OpenAI, Anthropic Enterprise)
- VorstersNV-architectuur moet een configureerbare LLM-backend ondersteunen

**Restrisico:** Hoog als niet geadresseerd — kritisch aandachtspunt bij implementatie.

### 7.5 Setup-investering als drempel

**Risico:** De eenmalige setup van €1.330 en 14 uur is een drempel voor kleine projecten.

**Mitigatie:**
- Generieke fleet-templates herbruikbaar maken voor alle Java-projecten
- De "Code Analysis Fleet" is niet lpbunified-specifiek — elk Java-project profiteert ervan
- Setup-investering amortiseren over meerdere projecten

**Restrisico:** Laag na eerste amortisatie.

---

## 8. ROI-berekening en Terugverdientijd

### 8.1 Conservatief scenario (2 projecten/jaar)

```
Jaar 1:
  Setup kosten:           - €1.330
  Run 1 (Q1):             + €1.419
  Run 2 (Q3):             + €1.419
  Netto jaar 1:           + €1.508

Jaar 2:
  Run 3 (Q1):             + €1.419
  Run 4 (Q3):             + €1.419
  Netto jaar 2:           + €2.838

ROI na 2 jaar:            (€4.346 bespaard − €1.330 setup) / €1.330 = 227%
```

### 8.2 Realistisch scenario (5 projecten/jaar, incl. updates)

```
Jaarlijkse besparingen:   5 × €1.419 = €7.095

Terugkerende kosten/jaar:
  LLM API (5 runs):       5 × €12 = €60
  Review tijd (5 runs):   5 × €81 = €405
  Totaal terugkerend:     €465/jaar

Netto besparing/jaar:     €7.095 − €465 = €6.630

ROI (excl. setup):        €6.630 / €465 = 1.326%
Terugverdientijd setup:   €1.330 / €6.630 = 0,2 jaar (~2,5 maanden)
```

### 8.3 Optimistisch scenario (maandelijkse codebase-updates + meerdere projecten)

Als de fleet gebruikt wordt voor:
- Maandelijkse analyse-updates bij grote wetgevingswijzigingen
- Onboarding-documentatie voor nieuwe medewerkers
- Technische due diligence bij projectoverdrachten
- Architectuurreviews voor andere systemen (niet enkel lpbunified)

```
Geschatte jaarlijkse uitvoeringen:   15–20
Jaarlijkse bruto besparing:          15 × €1.419 = €21.285
Terugkerende jaarkosten:             15 × €91 = €1.365
Netto besparing:                     €19.920/jaar

ROI eerste jaar (incl. setup):       (€19.920 − €1.330) / €1.330 = 1.398%
```

### 8.4 ROI-overzicht

| Scenario          | Runs/jaar | Netto besparing jaar 1 | ROI jaar 1 | Terugverdientijd |
|-------------------|-----------|------------------------|------------|------------------|
| Conservatief      | 2         | €1.508                 | 113%       | ~5 maanden       |
| Realistisch       | 5         | €5.300                 | 398%       | ~2,5 maanden     |
| Optimistisch      | 15        | €18.590                | 1.398%     | < 1 maand        |

---

## 9. Schaalbaarheid: wat als er meer projecten zijn?

### 9.1 De vliegwieleffect van fleet-templates

Eenmaal de Code Analysis Fleet geconfigureerd is voor lpbunified (Java/Spring Boot), is de **marginalekost voor een volgend Java-project bijna nul**:

```
Project 1 (lpbunified):   Setup €1.330 + run €101 = €1.431
Project 2 (ander Java):   Setup €200 (aanpassing) + run €101 = €301
Project 3 (ander Java):   Setup €100 (fine-tuning) + run €101 = €201
Project N:                Setup €50 (minimale aanpassing) + run €101 = €151
```

Elke bijkomende run van een vergelijkbaar Java-project kost na amortisatie slechts ~€150, terwijl de manuele kost €1.520 blijft.

### 9.2 Toepasbare use cases buiten lpbunified

| Project type                           | Fleet herbruikbaarheid | Verwachte besparing/run |
|----------------------------------------|------------------------|-------------------------|
| Andere Java Spring Boot modules        | 90%                    | €1.300–€1.400           |
| Angular/TypeScript frontend-analyse    | 60%                    | €800–€1.000             |
| Database schema review                 | 50%                    | €600–€800               |
| Microservices architectuurreview       | 70%                    | €1.000–€1.200           |
| Legacy C/COBOL inventarisatie          | 30%                    | €400–€600               |

### 9.3 Teamlevel impact

Als het volledige ontwikkelteam gebruik kan maken van de fleets:

```
Team van 5 developers × 2 analyses/jaar × €1.419 besparing = €14.190/jaar
Team van 10 developers × 3 analyses/jaar × €1.419 besparing = €42.570/jaar
```

Bij een team van 10 developers is de ROI zo hoog dat de setup-investering verdwijnt in de ruis.

---

## 10. Aanbeveling en Conclusie

### 10.1 Aanbeveling

**Implementeer de fleet-architectuur in twee fasen:**

**Fase 1 — Piloot (4–6 weken, €1.330 setup):**
- Bouw Fleet A (Code Analysis) voor Java-projecten
- Test op lpbunified als referentieproject
- Valideer output kwaliteit vs. manuele analyse
- Stel menselijke review-rubric op

**Fase 2 — Uitbreiding (2–3 maanden na succesvolle piloot):**
- Voeg Fleet B (Kritische Review) toe
- Voeg Fleet C (Content/Blog) toe
- Configureer orchestrator voor automatische trigger bij codewijzigingen
- Rol uit naar andere Java-projecten in de portfolio

**Fase 3 — Volwassenheid (6–12 maanden):**
- Automatische maandelijkse analyse-updates
- On-premise LLM voor vertrouwelijke code
- Fleet-templates als interne standard voor alle projecten

### 10.2 Kritische succesfactoren

1. **Menselijke review is niet onderhandelbaar** — fleet zonder review is een hallucinatie-machine
2. **Prompt kwaliteit vereist investering** — slechte prompts = slechte output, ongeacht de architectuur
3. **On-premise LLM voor vertrouwelijke code** — zonder dit is de aanpak een juridisch risico
4. **Domeinexpertise behouden** — gebruik fleets als versneller, niet als excuus om expertise niet te ontwikkelen

### 10.3 Conclusie

| Vraag                                     | Antwoord                                             |
|-------------------------------------------|------------------------------------------------------|
| Hoeveel tijd bespaart het?                | 14,75 uur per uitvoering (senior profiel)            |
| Hoe lang duurt de uitvoering met fleet?   | ~1u15 manuele input, ~2u10 totale doorlooptijd       |
| Wanneer is het break-even?                | Na de eerste uitvoering                              |
| Wat is de ROI na 1 jaar (realistisch)?    | 398% — bij 5 projecten/jaar                          |
| Is de kwaliteit gelijkwaardig?            | 80% automatisch + 20% expert = beter dan 100% junior |
| Wat zijn de grootste risico's?            | Confidentialiteit, hallucinations, prompt-kwaliteit  |
| Is het de moeite?                         | **Ja — onomwonden.**                                 |

Het huidige document dat je nu leest is zelf een voorbeeld van het hybride model in werking: de **structuur, volledigheid en snelheid** van AI-ondersteuning, gecombineerd met de **domeinkennis, nuance en verantwoordelijkheid** van een menselijke expert.

**Dat is de toekomst van technische analyse.**

---

*Document aangemaakt: 21 april 2026*
*Auteur: Koen Vorsters*
*Gebaseerd op: LOONBEREKENING_ANALYSE.txt, LOONBEREKENING_KRITISCHE_ANALYSE.md, VorstersNV architectuurprincipes*
*Status: Definitief — intern gebruik*
