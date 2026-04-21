# Kritische Architectuuranalyse: Loonberekeningsmotor
## lpbunified — Rekenmotor Module

| Metadata            | Waarde                                         |
|---------------------|------------------------------------------------|
| **Datum**           | 21 april 2026                                  |
| **Auteur**          | Koen Vorsters                                  |
| **Bronnen**         | `LOONBEREKENING_ANALYSE.txt`, `LOONSCHALEN_ANALYSE.txt`, broncode-analyse |
| **Scope**           | `be.schaubroeck.lpb.rkm.rekenmotor.*`          |
| **Versie systeem**  | lpbunified-master / lpb-lima-server            |
| **Type document**   | Kritische architectuurreview — intern          |

---

## Inhoudsopgave

1. [Samenvatting](#1-samenvatting)
2. [Methodologie](#2-methodologie)
3. [Architecturele sterktes](#3-architecturele-sterktes)
4. [Kritische risicozones](#4-kritische-risicozones)
5. [Techdebt inventaris](#5-techdebt-inventaris)
6. [Testbaarheid en kwaliteitsborging](#6-testbaarheid-en-kwaliteitsborging)
7. [Onderhoud en wetgevingswijzigingen](#7-onderhoud-en-wetgevingswijzigingen)
8. [Onboarding en kennisoverdracht](#8-onboarding-en-kennisoverdracht)
9. [Concrete aanbevelingen per prioriteit](#9-concrete-aanbevelingen-per-prioriteit)
10. [Risicomatrix](#10-risicomatrix)
11. [Conclusie](#11-conclusie)

---

## 1. Samenvatting

De loonberekeningsmotor is de technische kern van het lpbunified-systeem. Het verwerkt Belgische loonberekeningen voor lokale overheden, onderwijs en de privésector, met inachtneming van complexe fiscale wetgeving, RSZ-regels en sectoriële uitzonderingen.

De motor toont een **doordachte basisarchitectuur** die het Chain of Responsibility patroon correct toepast voor een domein dat daar bij uitstek voor geschikt is. De fasescheiding (Bruto → Sociaal → Belastbaar → BV → Netto) is logisch en weerspiegelt de wetgevelijke volgorde.

Tegelijkertijd zijn er **significante risico's** die op korte en middellange termijn aandacht vereisen:

- Een **verouderde kerndependency** (Apache Commons Chain) zonder actief onderhoud
- Een **grote context-object** met 80+ sleutels die de koppeling tussen stappen verbergt
- **Wetgevingsdatums als hardcoded conditionele logica** die accumuleren als techdebt
- Een **C/NLP legacy laag** die parallel loopt aan de Java-implementatie
- Onvoldoende bewijs van **geautomatiseerde regressietests** voor jaarlijkse barema-updates

De motor is **functioneel correct en robuust** voor het huidige gebruik, maar vereist gerichte investeringen om ook op 5–10 jaar horizon onderhoudbaar en uitbreidbaar te blijven.

---

## 2. Methodologie

Deze analyse is gebaseerd op:

- Volledige broncode-analyse van het `rekenmotor` package en subpackages
- Review van de bronanalyse-documenten (`LOONBEREKENING_ANALYSE.txt`, `LOONSCHALEN_ANALYSE.txt`)
- Statische analyse van klasse-hiërarchieën, afhankelijkheden en patronen
- Vergelijking met gangbare enterprise Java best practices (2024–2026)

De analyse is **niet** gebaseerd op dynamische profilingsdata, productie-logs of performance-metingen. Bevindingen over runtime-gedrag zijn extrapolaties op basis van de bronstructuur.

---

## 3. Architecturele Sterktes

### 3.1 Chain of Responsibility — correct toegepast ✅

Het gebruik van het Chain of Responsibility patroon is een sterke keuze voor dit domein. Elke berekeningstap is een zelfstandige klasse (`AbstractRekenCommand`), wat leidt tot:

- **Hoge cohesie per klasse**: één klasse = één berekeningstap
- **Lage koppeling**: stappen kennen elkaar niet, alleen de context
- **Uitbreidbaarheid**: een nieuwe loonregel is een nieuwe klasse, geen aanpassing van bestaande code
- **Testbaarheid**: elke stap is in isolatie testbaar

Dit patroon schaalt goed voor een domein dat continu nieuwe regels en uitzonderingen toevoegt, zoals Belgische loonwetgeving.

### 3.2 Typed enum context-sleutels ✅

De keuze voor typed enum-keys (sealed interfaces/enums per fase) is uitstekend:

```
RekenBrutoKey.BRUTO_MAANDLOON_KEY
RekenRszKey.BIJDRAGE_RSZ_KEY
RekenBvKey.BEDRIJFSVOORHEFFING_GEWONE_BEZOLDIGING_KEY
```

Dit geeft compile-time type-controle, maakt refactoring veilig (IDE vindt alle gebruikers), en voorkomt de "stringly-typed context" antipatroon die in vergelijkbare systemen voor subtle bugs zorgt.

### 3.3 Fasescheiding als architectureel principe ✅

De vijf fases (BRUTO, SOCIAAL, BELASTBAAR, BV, NETTO) zijn niet alleen logisch — ze weerspiegelen exact de wettelijke volgorde zoals bepaald door de Belgische belastingwetgeving. Dit alignment tussen domein en techniek is een teken van mature domeinmodellering.

### 3.4 Strategy pattern voor sectoriële varianten ✅

De driedeling DMFA / DMFAPPL / RSZPPO via `AbstractBerekenSocialeBijdragen` is een correcte toepassing van het Strategy patroon. Nieuwe sectoren (hypothetisch) toevoegen vereist enkel een nieuwe implementatie van de abstracte basisklasse.

### 3.5 Twee-niveau context ✅

Het onderscheid tussen `mainContext` (per persoon) en `opdrachtContext` (per aanstelling) is noodzakelijk voor medewerkers met meerdere deeltijdse contracten. Dit is correct gemodelleerd en reflecteert de werkelijkheid van de doelgroep (lokale overheden met diverse contracttypes).

### 3.6 APO-module als gecontroleerde nooduitgang ✅

Het bestaan van een formele APO-module (Aanpassingen Achteraf) is pragmatisch en realistisch. Geen enkel berekeningssysteem is 100% compleet voor alle randgevallen. De APO-module biedt een gecontroleerd, traceerbaar kanaal voor correcties — beter dan ad-hoc aanpassingen in productiedata.

### 3.7 Custom Money type ✅

Een custom `Money` wrapper over `BigDecimal` met expliciete afrondingsmodi is een correcte keuze voor financiële software. Het vermijdt de bekende `double`/`float` precisiefouten die in financiële systemen catastrofale gevolgen kunnen hebben.

---

## 4. Kritische Risicozones

### 4.1 🔴 KRITIEK: Apache Commons Chain — verlaten library

**Bevinding:** De motor is gebouwd op Apache Commons Chain (`org.apache.commons.chain.Command`).

**Risico:**
- Apache Commons Chain is effectief verlaten. De laatste stabiele release (1.2) dateert van **2008**. Er zijn geen actieve releases, geen security patches, geen Java 21+ optimalisaties.
- De library is gebaseerd op `java.util.Map<String, Object>` als context, waardoor de typed enum-key aanpak **een workaround is bovenop een unsafe fundament**. Intern blijft alles raw-type.
- Bij een Java major upgrade (Java 21 LTS → Java 25 LTS) bestaat het risico op incompatibiliteiten.

**Impact:** Hoog — de volledige keten is afhankelijk van deze library.

**Aanbeveling:**
Vervang Apache Commons Chain door een **custom, lightweight chain implementatie** (50–100 regels Java). Dit is een éénmalige investering die alle externe dependency-risico's elimineert en toelaat om de context volledig type-safe te maken.

```java
// Moderne alternatiefstructuur zonder externe dependency:
@FunctionalInterface
public interface RekenCommand {
    void execute(RekenContext context) throws RekenException;
}

public class RekenChain {
    private final List<RekenCommand> commands;

    public void execute(RekenContext context) throws RekenException {
        for (RekenCommand command : commands) {
            command.execute(context);
        }
    }
}
```

---

### 4.2 🔴 KRITIEK: C/NLP legacy laag parallel aan Java

**Bevinding:** Het systeem bevat een C/C++ NLP-module die legacy rekenlogica uitvoert, parallel aan de Java Spring Boot implementatie.

**Risico:**
- **Twee waarheidsbronnen**: als dezelfde berekening in C en in Java leeft, is het onduidelijk welke de "gold standard" is bij discrepanties.
- **Kennis-silo**: C/NLP expertise is zeldzaam. Als de kenners vertrekken, is de module een black box.
- **Testbaarheid**: C-code is moeilijker te unittesten dan Java, zeker in een CI/CD-context.
- **Build complexity**: twee programmeertalen in één systeem verhoogt de build- en deploymentcomplexiteit.

**Impact:** Hoog — dit is een fundamenteel architectureel risico op lange termijn.

**Aanbeveling:**
Maak een formeel **migratie-inventaris**: welke berekeningen leven nog in de NLP-module? Voor elk: is er een Java-equivalent? Is het equivalent identiek qua resultaat? Stel een roadmap op om de NLP-module systematisch te elimineren, startend met de stukken met de meeste aanraking.

---

### 4.3 🟠 HOOG: Context-object met 80+ sleutels — verborgen koppeling

**Bevinding:** De `RekenContext` bevat naar schatting 80–100 sleutels verdeeld over 10 enum-groepen (RekenChainKey, RekenBrutoKey, RekenRszKey, RekenPatronaalRszKey, RekenBbKey, RekenBvKey, RekenNettoKey, RekenPatronaalPriveRszKey, RekenInfoKey, plus varianten).

**Risico:**
- De context is in theorie een encapsulatie, maar in de praktijk een **shared mutable state** die door alle stappen gelezen en geschreven wordt.
- Een stap die een sleutel schrijft waarop een latere stap rekent, creëert een **impliciete afhankelijkheid** die nergens in de code zichtbaar is.
- Als stap X per ongeluk een sleutel overschrijft die stap Y later leest, is dit een bug die **alleen op integratieniveau** ontdekt wordt.
- Met 80+ sleutels is het **cognitief onmogelijk** om van een willekeurige stap te weten welke sleutels zij produceert vs. consumeert.

**Impact:** Middelhoog bij stabiele code, hoog bij refactoring of toevoeging van nieuwe stappen.

**Aanbeveling:**
Introduceer expliciete **producer/consumer annotaties** per command:

```java
@Produces({RekenBrutoKey.BRUTO_MAANDLOON_KEY})
@Consumes({RekenChainKey.PERSOON_KEY, RekenChainKey.REKENTIJD_KEY})
public class BerekenBrutoLoon extends AbstractRekenCommand { ... }
```

Dit maakt de impliciete koppeling expliciet en laat een validator toe om te controleren dat elke sleutel geproduceerd wordt vóór hij geconsumeerd wordt.

---

### 4.4 🟠 HOOG: Datumgebaseerde conditionals als structurele techdebt

**Bevinding:** Doorheen de codebase zijn er expliciete datumgrenzen als hardcoded constanten:

```java
EINDE_AFRONDEN_NAAR_BENEDEN = 2023-01-01  // afrondingsregel wijziging
DATUM_BLO_KINDERLAST = 2003-07-01         // loonbeslag schijven
DATUM_VERHOGING_GRENS_AANTAL = 2001-01-01  // loonbeslag grenzen
KST_START_WG_BIJDRAGE_MTC                 // maaltijdcheques werkgeversbijdrage
```

Elke wetgevingswijziging voegt nieuwe datumconditioneel toe:
```java
if (berekeningsDatum.isBefore(DATUM_X)) {
    // oud regime
} else {
    // nieuw regime
}
```

**Risico:**
- Dit **accumulatie-patroon** leidt ertoe dat de codebase de volledige historiek van de Belgische belastingwetgeving bevat als geneste if-statements.
- Na 20 jaar: tientallen datumgrenzen, elk met eigen logica, elk die apart getest moet worden.
- Een bug in een historische tak is bijna onmogelijk te ontdekken zonder gericht testen op die specifieke datum.
- Nieuwe medewerkers moeten de volledige fiscale historiek kennen om de code te begrijpen.

**Impact:** Hoog — dit is structurele techdebt die exponentieel groeit.

**Aanbeveling:**
Introduceer een **Tijdsversionering patroon** voor fiscale regels:

```java
// In plaats van: if (datum.isBefore(X)) { ... } else { ... }
// Gebruik een regelregistry die de juiste implementatie selecteert op basis van datum:

FiscaleRegel afRondingsRegel = fiscaleRegelRegistry
    .getRegelVoorDatum(AfrondingsRegel.class, berekeningsDatum);
BigDecimal afgerond = afRondingsRegel.afronden(bedrag, decimalen);
```

Hiermee wordt elke "tijdsvak" een aparte, onafhankelijk testbare klasse.

---

### 4.5 🟠 HOOG: RekenChainFactoryImp — potentieel "god class"

**Bevinding:** `RekenChainFactoryImp` importeert **alle** `BerekXxx` commands en ordent ze in de juiste fase-volgorde.

**Risico:**
- Deze klasse wordt bij **elke** toevoeging van een command aangepast, wat het een aantrekkingspunt voor fouten maakt.
- De volgorde van commands in de chain is business logic, maar zit verstopt in een factory als technische configuratie.
- Er is geen zichtbare validatie dat de volgorde correct is — een fout in de ordening kan pas ontdekt worden bij integratietests.

**Impact:** Middelhoog.

**Aanbeveling:**
Maak de chain-samenstelling **declaratief en data-driven**:

```java
// Via annotations op de commands zelf:
@ChainStep(fase = RekenFase.BRUTO, volgorde = 10)
public class BerekenBrutoLoon extends AbstractRekenCommand { ... }

@ChainStep(fase = RekenFase.SOCIAAL, volgorde = 10)
public class BerekenSocialeBijdragenDmfa extends AbstractRekenCommand { ... }
```

De factory leest dan alle `@ChainStep`-annotaties, sorteert en assembleert automatisch.

---

### 4.6 🟡 MIDDEL: Ongehuwde weduwe-contradictiecheck — fragiel domeinmodel

**Bevinding:** Er is een expliciete contradictiecheck voor de combinatie "ongehuwde weduwe met kinderen ten laste, maar kinderenTenLaste = 0". Dit is een indicatie dat het domeinmodel de invarianten niet afdwingt.

**Risico:**
- Als twee datavelden tegenstrijdig kunnen zijn, is het domeinmodel niet consistent.
- Andere vergelijkbare contradities zijn mogelijk aanwezig maar nog niet ontdekt.

**Aanbeveling:**
Valideer domein-invarianten bij constructie van `PersoonsFiscaliteit`, niet bij gebruik:

```java
// Builder of factory method die de invariant afdwingt:
public static PersoonsFiscaliteit create(
    Fiskgezinstoestand gezinstoestand,
    int kinderenTenLaste,
    boolean ongehuwdeWeduwe) {

    if (ongehuwdeWeduwe && kinderenTenLaste == 0) {
        throw new DomeinConstraintViolatieException(
            "Ongehuwde weduwe vereist minstens 1 kind ten laste");
    }
    return new PersoonsFiscaliteit(gezinstoestand, kinderenTenLaste, ongehuwdeWeduwe);
}
```

---

### 4.7 🟡 MIDDEL: Naamgeving — domein-jargon als drempel

**Bevinding:** De codebase gebruikt consequent Belgisch-juridisch en intern jargon:

| Term         | Betekenis                                    |
|--------------|----------------------------------------------|
| `Opper`      | Tijdsperiode binnen een aanstelling          |
| `Opdracht`   | Aanstelling/benoeming                        |
| `Fisk`       | Fiscaal                                      |
| `BPI`        | Belastbaar Persoonlijk Inkomen               |
| `BBSZ`       | Bijzondere Bijdrage Sociale Zekerheid        |
| `DMFAPPL`    | RSZ-aangifte voor lokale overheden           |
| `Kode`       | Code (interne spelling)                      |
| `GEA/SCA/DIA/NIA/GRA` | Anciënniteitsvormen                |
| `SOGID`      | Schaal Overgangsgroep ID                     |
| `APO`        | Aanpassingen Achteraf (Persoonlijk/Org.)     |

**Impact:** Hoog voor onboarding, laag voor doorgewinterde medewerkers.

**Aanbeveling:**
Creëer en onderhoud een **domein-glossarium** (Markdown of Confluence) met alle termen, hun wettelijke grondslag en hun technische equivalent. Link dit glossarium in de code via een `@see` Javadoc-tag op de kernklassen.

---

## 5. Techdebt Inventaris

| ID  | Omschrijving                                       | Ernst  | Effort | Prioriteit |
|-----|----------------------------------------------------|--------|--------|------------|
| TD1 | Apache Commons Chain vervangen                     | Hoog   | Middel | **P1**     |
| TD2 | C/NLP module inventariseren en migratie plannen    | Hoog   | Hoog   | **P1**     |
| TD3 | Datumconditionele logica externaliseren            | Hoog   | Hoog   | **P2**     |
| TD4 | Context producer/consumer documentatie             | Middel | Laag   | **P2**     |
| TD5 | RekenChainFactoryImp declaratief maken             | Middel | Middel | **P2**     |
| TD6 | Domein-invarianten in model afdwingen              | Middel | Laag   | **P3**     |
| TD7 | Glossarium aanmaken en koppelen                    | Laag   | Laag   | **P3**     |
| TD8 | Golden file regressietests voor barema-updates     | Hoog   | Middel | **P1**     |
| TD9 | Constanten externaliseren naar configuratie        | Middel | Middel | **P2**     |

---

## 6. Testbaarheid en Kwaliteitsborging

### 6.1 Positief: unit testbaarheid per command

De chain-architectuur legt testbaarheid in de structuur in. Elke `AbstractRekenCommand`-implementatie kan in isolatie getest worden door een `RekenContext` te construeren met enkel de vereiste input-sleutels:

```java
@Test
void testWerkbonus_laagLoon_geeftPositieveBijdrage() {
    RekenContext ctx = new RekenContext();
    ctx.set(RekenBrutoKey.BRUTO_MAANDLOON_KEY, Money.of("1800.00"));
    ctx.set(RekenRszKey.BIJDRAGE_RSZ_KEY, Money.of("235.26"));

    new BerekenWerkbonus().voerUit(ctx);

    assertThat(ctx.get(RekenRszKey.WERKBONUS_LAGE_LONEN_KEY))
        .isGreaterThan(Money.ZERO);
}
```

Dit is goed opgezet in de architectuur.

### 6.2 Risico: ontbrekende integratietests met golden files

**Bevinding:** Er zijn geen aanwijzingen (in de beschikbare analyse) van systematische **golden file regressietests** die de volledige chain doorlopen met een set representatieve personen en de eindresultaten vergelijken met verwachte referentiebedragen.

**Dit is het hoogste testrisc in het systeem.**

Bij elke jaarlijkse barema-update (nieuwe schijfgrenzen, aangepaste percentages, gewijzigde werkbonusplafonds) bestaat het risico dat een fout in de implementatie pas ontdekt wordt bij een loonadministrateur die een discrepantie opmerkt.

**Vereiste teststrategie:**

```
Niveau 1: Unit tests per command            ← waarschijnlijk aanwezig
Niveau 2: Integratietests per fase          ← status onbekend
Niveau 3: End-to-end golden file tests      ← kritisch risico als afwezig
Niveau 4: Jaarlijkse wettelijke validatie   ← vereist externe referentie
```

**Aanbeveling:** Maak een set van minimaal 20 **representatieve persona's** (alleenstaande laag loon, gehuwd hoog loon, deeltijds DMFAPPL, gepensioneerde, mandataris, vrijwillige brandweer, ...) met gekende inputdata en verwachte output. Sla deze op als JSON golden files. Run bij elke barema-update automatisch deze golden file tests als regressionpoort.

### 6.3 Ontbrekend: performance tests

Een chain van 40+ commands die voor elke medewerker van een gemeente (100–5000 personen) maandelijks wordt uitgevoerd, kan bij volume een knelpunt worden. Er zijn geen aanwijzingen van performance benchmarks in de beschikbare analyse.

**Aanbeveling:** Voer een jaarlijkse performance benchmark uit: tijd per individuele berekening, tijd voor een batch van 1000 medewerkers, heap-gebruik per berekening.

---

## 7. Onderhoud en Wetgevingswijzigingen

### 7.1 Jaarlijkse barema-update cyclus

Belgische loonwetgeving wijzigt jaarlijks, typisch per 1 januari:
- Nieuwe belastingschijven en percentages
- Aangepaste werkbonusplafonds
- Geïndexeerde BBSZ-grenzen
- Nieuwe jobkortingstabel (22+ grenzen)

Dit impliceert dat de `FiscaleConstant`-service jaarlijks nieuwe data moet bevatten en dat alle tests die afhangen van fiscale constanten opnieuw gevalideerd moeten worden.

**Huidige aanpak:** `FiscaleConstantService.getByDate(LocalDate taxdatum)` — correct. Datumgebaseerde opzoek is de juiste aanpak.

**Risico:** Als de constanten in een database zitten, is de kwaliteit van de dataimport cruciaal. Een fout in de import (verkeerde komma, decimale precisie) leidt tot systematisch foute lonen voor alle medewerkers.

**Aanbeveling:** Implementeer een **dubbele controle bij barema-import**:
1. Automatische validatie: zijn alle vereiste constanten aanwezig voor het nieuwe fiscaal jaar?
2. Steekproeftest: bereken 5 representatieve personen met de nieuwe constanten en vergelijk met handmatige berekening.

### 7.2 Regionalisering van belastingen

De Vlaamse vermindering BV (`VLAAMSE_VERMINDERING_BV`) wijst op toenemende regionalisering van de Belgische belastingen. Dit is een structurele trend: meer gewestelijke uitzonderingen, meer varianten.

**Risico:** Als de motor nu al regionale varianten bevat, zal dit enkel toenemen. De chain-architectuur kan dit aan, maar het context-object en het aantal strategieën zal verder groeien.

**Aanbeveling:** Definieer nu al een **extensiepunt voor gewestelijke regels** in de architectuur, zodat Vlaamse, Waalse en Brusselse varianten systematisch kunnen worden toegevoegd zonder de kern te wijzigen.

---

## 8. Onboarding en Kennisoverdracht

### 8.1 Domeinkennis als kritieke afhankelijkheid

De motor vereist diepgaande kennis van:
1. De Belgische belastingwetgeving (WIB, RSZ-wetgeving)
2. Het sectorale loonverwerkingsdomein (DMFA/DMFAPPL/RSZPPO)
3. De interne terminologie (Opper, Opdracht, APO, ...)
4. De Apache Commons Chain werking
5. De specifieke afrondingsregels en historische uitzonderingen

Dit is een **extreme kennisconcentratie**. Als de kernexperts vertrekken, is de motor voor nieuwe medewerkers bijna ondoorgrondelijk.

### 8.2 Ontbrekende architectuurdocumentatie

Er is geen (in de analyse aantoonbare) ADR (Architectural Decision Record) die de keuze voor Chain of Responsibility, Apache Commons Chain, de twee-niveau context, of de APO-module toelicht.

**Aanbeveling:** Schrijf retrospectief ADRs voor de vijf kernbeslissingen:
- Waarom Chain of Responsibility?
- Waarom Apache Commons Chain (en welke alternatieven werden overwogen)?
- Waarom typed enum-keys?
- Waarom een twee-niveau context?
- Waarom een aparte APO-module?

### 8.3 Positief: Analyse-documenten

Het bestaan van `LOONBEREKENING_ANALYSE.txt` en `LOONSCHALEN_ANALYSE.txt` is een positief teken. Dergelijke systematische documentatie is waardevol voor overdracht.

**Aanbeveling:** Zorg dat deze documenten onderdeel zijn van het CI-proces: bij elke significant codawijziging wordt de analyse automatisch bijgewerkt (of wordt een review afgedwongen).

---

## 9. Concrete Aanbevelingen per Prioriteit

### 🔴 Prioriteit 1 — Onmiddellijk (0–3 maanden)

**P1.1 Golden file regressietests implementeren**
- Maak een set van 20+ persona JSON-bestanden
- Implementeer een geautomatiseerde test die de volledige chain uitvoert en vergelijkt met verwachte output
- Integreer in CI/CD als verplichte kwaliteitspoort

**P1.2 Apache Commons Chain afhankelijkheidsrisico documenteren**
- Voer een formele dependency-audit uit
- Bevestig of de library Java 21+ compatible is
- Start een proof-of-concept voor een custom chain implementatie

**P1.3 C/NLP module inventariseren**
- Maak een lijst van alle berekeningen die nog in C/NLP leven
- Bepaal welke al een Java-equivalent hebben
- Kwantificeer de migratie-effort

---

### 🟠 Prioriteit 2 — Korte termijn (3–12 maanden)

**P2.1 Context producer/consumer documentatie**
- Annoteer alle commands met `@Produces` en `@Consumes`
- Schrijf een validator die controleert dat de context-flow consistent is

**P2.2 Datumconditionele logica refactoring — pilootproject**
- Kies één stap met veel datumgrenzen (bijv. loonbeslag of BV-afrondingsregels)
- Refactor naar een tijdsversionering patroon als piloot
- Evalueer de aanpak en documenteer als ADR

**P2.3 RekenChainFactoryImp declaratief maken**
- Introduceer `@ChainStep(fase, volgorde)` annotaties
- Laat de factory automatisch assembleren via classpath-scanning

**P2.4 Barema-import validatieproces**
- Implementeer een pre-import checklist voor fiscale constanten
- Automatische validatie: volledigheid per fiscaal jaar
- Steekproeftest na import

---

### 🟡 Prioriteit 3 — Middellange termijn (12–24 maanden)

**P3.1 C/NLP migratie**
- Migreer stukken C/NLP naar Java op basis van de P1.3 inventaris
- Start met hoogste aanraakfrequentie of hoogste risico

**P3.2 Domeinmodel versterken**
- Valideer invarianten bij constructie (PersoonsFiscaliteit, RekenTijd, ...)
- Elimineer contradictie-checks in domeinlogica

**P3.3 Kennisdocumentatie**
- Schrijf retrospectieve ADRs voor kernarchitectuurbeslissingen
- Creëer en onderhoud domein-glossarium
- Koppel glossarium aan kernklassen via Javadoc

**P3.4 Gewestelijke extensiepunten**
- Definieer een formeel extensiepunt voor Vlaamse/Waalse/Brusselse varianten
- Maak de gewestelijke verminderingen pluggable

---

## 10. Risicomatrix

```
              WAARSCHIJNLIJKHEID
              Laag          Middel         Hoog
           ┌─────────────┬─────────────┬─────────────┐
    Hoog   │             │  C/NLP      │  Datumcond. │
  IMPACT   │             │  migratie   │  techdebt   │
           ├─────────────┼─────────────┼─────────────┤
    Middel │  Perf.      │  Dep. risk  │  Golden     │
           │  bottleneck │  Commons    │  file tests │
           │             │  Chain      │  ontbreken  │
           ├─────────────┼─────────────┼─────────────┤
    Laag   │  Context    │  Factory    │  Naamgeving │
           │  ordering   │  god class  │  onboarding │
           │  bugs       │             │             │
           └─────────────┴─────────────┴─────────────┘

Legende:
  🔴 Hoog impact + Hoog waarschijnlijk  = Onmiddellijk handelen
  🟠 Hoog impact + Middel               = Korte termijn
  🟡 Middel impact                      = Middellange termijn
  🟢 Laag impact                        = Backlog / nice-to-have
```

### Toprisico's samengevat:

| Risico                                    | Kans    | Impact  | Mitigatie                                 |
|-------------------------------------------|---------|---------|-------------------------------------------|
| Golden file tests ontbreken               | Hoog    | Hoog    | P1.1 — Onmiddellijk implementeren         |
| Apache Commons Chain obsoleet             | Middel  | Hoog    | P1.2 — Audit + PoC custom chain           |
| C/NLP kennisloss bij vertrek experts      | Middel  | Hoog    | P1.3 — Inventaris + migratieroadmap       |
| Datumcond. logica onbeheersbaar           | Hoog    | Middel  | P2.2 — Pilootrefactoring                  |
| Barema-import fout → systematisch foute lonen | Laag | Hoog    | P2.4 — Validatieproces implementeren      |
| Onboarding nieuw talent stagneert         | Middel  | Middel  | P3.3 — Documentatie prioriteit            |

---

## 11. Conclusie

De loonberekeningsmotor van lpbunified is **functioneel correct en architectureel solide** voor het huidige gebruik. De keuze voor Chain of Responsibility, typed context-keys en fasescheiding zijn bewuste, goede beslissingen die de basis leggen voor een onderhoudbaar systeem.

De **drie kritieke aandachtspunten** zijn:

1. **Verouderde dependency** (Apache Commons Chain): een latent risico dat bij een Java-upgrade acuut kan worden. Mitigatie is relatief eenvoudig en loont de investering.

2. **Ontbrekende golden file regressietests**: het grootste **kwaliteitsrisico**. Zonder geautomatiseerde end-to-end validatie is elke barema-update een handmatige verificatieoefening met menselijke foutmarge.

3. **Datumgebaseerde conditionals als accumulerende techdebt**: dit is een structureel patroon dat, onbehandeld, de codebase over 5–10 jaar significant bemoeilijkt. Een pilootrefactoring is de aanbevolen eerste stap.

De motor bewijst dagelijks zijn waarde. De investeringen die hier aanbevolen worden, zijn geen reparatiewerk — ze zijn de garantie dat de motor ook morgen, over 5 jaar en bij elke nieuwe wetgevingswijziging betrouwbaar blijft functioneren.

---

*Document aangemaakt: 21 april 2026*
*Auteur: Koen Vorsters*
*Status: Definitief — intern gebruik*
