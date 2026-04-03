# Klantenservice Promptboek – VorstersNV

Dit promptboek bevat kant-en-klare prompts voor de meest voorkomende klantenservice-scenario's.

---

## Bestellingsstatus opvragen

```
prompt: "Beste klant, ik ga uw bestelling direct voor u opzoeken. Mag ik uw ordernummer of emailadres?"
use_case: klant_vraagt_status
variables: [klant_naam, order_id]
```

## Retour aanvragen

```
prompt: "Ik begrijp dat u een product wilt retourneren. Ik help u graag verder. Kunt u het ordernummer en de reden voor retour doorgeven?"
use_case: retour_aanvraag
variables: [klant_naam, order_id, retour_reden]
```

## Product niet ontvangen

```
prompt: "Wat vervelend dat uw pakket nog niet is aangekomen! Ik ga dit direct voor u uitzoeken bij de vervoerder."
use_case: pakket_niet_ontvangen
variables: [klant_naam, order_id, verwachte_leverdatum]
escalatie: true
```

## Klacht over product

```
prompt: "Het spijt me te horen dat u niet tevreden bent met uw aankoop. Uw feedback is voor ons erg waardevol. Kunt u me meer vertellen over het probleem?"
use_case: product_klacht
variables: [klant_naam, product_naam, klacht_omschrijving]
empathie: hoog
```

## Factuur opvragen

```
prompt: "Natuurlijk kan ik u een factuur sturen. U ontvangt deze binnen enkele minuten op uw emailadres."
use_case: factuur_aanvraag
variables: [klant_naam, order_id, klant_email]
automatisch: true
```

## Openingstijden

```
prompt: "Onze klantenservice is bereikbaar van maandag t/m vrijdag van 9:00 tot 17:00 uur. Heeft u nog andere vragen?"
use_case: openingstijden_vraag
statisch: true
```

## Kortingscode

```
prompt: "Leuk dat u interesse heeft in onze aanbiedingen! Op het moment zijn er de volgende acties beschikbaar: {actieve_aanbiedingen}"
use_case: korting_vraag
variables: [actieve_aanbiedingen]
dynamisch: true
```

---

## Gebruik van dit promptboek

1. Selecteer het juiste scenario
2. Vul de variabelen in vanuit het systeem
3. Pas de toon aan op de klant (formeel/informeel)
4. Voeg altijd een persoonlijke touch toe

## Escalatie-triggers

Escaleer naar een menselijke medewerker bij:
- Agressief of dreigend taalgebruik
- Juridische dreigingen
- Fraudevermoeden
- Complexe klachten na 2 geautomatiseerde antwoorden
- Mediavraagstukken
