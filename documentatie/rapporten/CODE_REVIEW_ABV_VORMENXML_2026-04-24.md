# Code Review — ABV VormenXML (MR: ABV-VormenXML → develop)

> **Datum**: 24 april 2026
> **Reviewer**: Koen Vorsters
> **MR**: ABV-VormenXML → develop
> **Bestanden**: 16 gewijzigd · +1082 / -4 lijnen
> **Toon**: vriendelijk en constructief 🙂

---

## 🌟 Algemene indruk

Heel solide werk! De Page Object structuur is herkenbaar, consistent en bouwt netjes voort op de bestaande helpers en modals. De twee nieuwe pagina-klassen (`ManueleIngavePage` en `VormenXmlPage`) zijn leesbaar en goed afgebakend. De registratie in `PagesInstances.js` en `PagesObjects.js` is proper gedaan. Er zijn een aantal kleine verbeterpuntjes die de code robuuster en beter onderhoudbaar maken — maar het fundament is goed.

---

## ✅ Wat werkt heel goed

- **Consistente structuur**: beide klassen volgen exact hetzelfde patroon als de bestaande ABV-pagina's — getter-methodes, `waitFor...`, `navigateTo...`, acties. Iemand die het project kent, begrijpt deze klassen meteen.
- **Input validatie**: type checks op string-parameters (`typeof aard !== 'string'`) zijn een fijne defensieve gewoonte. Foutmeldingen zijn duidelijk.
- **API-intercept in `vormenXml()`**: de `cy.intercept` + `cy.wait` op de REST call is precies hoe je asynchrone acties stabiel maakt in Cypress. Goed gedaan.
- **Delegatie naar helpers**: alle tabel-, filter- en checkbox-logica gaat via `Helpers.TableHelper` en `Helpers.CheckboxHelper` — geen duplicatie.
- **Nette registratie**: imports en exports in `PagesObjects.js` en instanties in `PagesInstances.js` zijn netjes en volledig.

---

## 🔍 Bevindingen & suggesties

### 1. Kleine CSS-typo in selector (non-blocking ⚠️)

**Bestand**: `ManueleIngavePage.js` en `VormenXmlPage.js`

```js
// Huidig (ontbreekt sluitende ]):
actiesButton = () => cy.get('[data-testid="Acties"')

// Correct:
actiesButton = () => cy.get('[data-testid="Acties"]')
```

De selector werkt waarschijnlijk wel in de meeste browsers (Cypress is tolerant), maar een ontbrekende `]` is technisch een ongeldige CSS-selector en kan in strictere omgevingen of bij toekomstige Cypress-upgrades problemen geven. Eenvoudig te fixen.

---

### 2. `.wait(500)` — liever wachten op iets zichtbaars (aanbeveling 💡)

**Bestand**: `ManueleIngavePage.js`

```js
// Huidig:
row.find('i').eq(0)
    .scrollIntoView()
    .click({ force: true })
    .wait(500)  // ← hard-coded time wait

// Beter: wacht op de modal zelf
row.find('i').eq(0)
    .scrollIntoView()
    .click({ force: true })
// en dan direct:
Modals.ToevoegenModal.waitForBewerkenModal()
```

Hard-coded `wait(500)` is een bekende Cypress anti-pattern: het maakt tests trager dan nodig en kan toch nog falen op een trage omgeving. Aangezien er vlak erna al een `waitForBewerkenModal()` of `waitForAandachtModal()` wordt aangeroepen, is de `wait(500)` eigenlijk overbodig. Verwijderen maakt de test zowel sneller als robuuster.

Dit geldt op twee plaatsen: `clickAanpassen()` en `verwijderIngaveIcoon()`.

---

### 3. `click({ force: true })` — gebruik met zorg (ter info ℹ️)

**Bestand**: `ManueleIngavePage.js`

```js
row.find('i').eq(0)
    .scrollIntoView()
    .click({ force: true })
```

`force: true` bypassed Cypress z'n zichtbaarheids- en interactiecontroles. Dat is soms nodig (bijv. bij overlappende elementen), maar verbergt ook potentiële UX-problemen. Als het element werkelijk klikbaar is voor een echte gebruiker, is `scrollIntoView()` + gewone `.click()` ideaal. Als `force: true` noodzakelijk is, een korte comment waarom is handig voor toekomstige maintainers.

```js
// Bewust force: true — icon is binnen een relatief gepositioneerde tabel-rij
// die gedeeltelijk buiten de viewport kan vallen.
row.find('i').eq(0)
    .scrollIntoView()
    .click({ force: true })
```

---

### 4. Index-gebaseerde `i`-selectie is fragiel (aanbeveling 💡)

**Bestand**: `ManueleIngavePage.js`

```js
// Huidig:
row.find('i').eq(0)   // aanpassen
row.find('i').eq(1)   // verwijderen
```

Als er ooit een icoon wordt toegevoegd vóór het aanpas- of verwijder-icoon, breken beide methodes zonder foutmelding — ze klikken dan gewoon op het verkeerde icoon. Indien de iconen een `data-testid` of een specifieke class hebben, is dat beter:

```js
row.find('[data-testid="aanpassen-icoon"]').click()
row.find('[data-testid="verwijder-icoon"]').click()
```

Als dat niet in de template staat, is het de moeite om dat te vragen aan de frontend-developer — het maakt de tests veel stabieler.

---

### 5. `deselectTableHeaderCheckbox` — naam vs. gedrag (kleine nit 🔎)

**Bestand**: `VormenXmlPage.js`

```js
deselectTableHeaderCheckbox(){
    Helpers.CheckboxHelper.setCheckboxState(() => this.tableHeaderCheckbox(), false)
}
```

De methode zet de checkbox altijd op `false` (deselect), maar de naam impliceert dat je hem "deselecteert". Dat klopt — maar het betekent ook dat als de checkbox al `false` is, er niets verandert. Is er ook een use case om te selecteren? Zo ja, overweeg een generieke methode:

```js
setTableHeaderCheckbox(state = false){
    Helpers.CheckboxHelper.setCheckboxState(() => this.tableHeaderCheckbox(), state)
}
```

Kleine nit, geen blocker.

---

### 6. `navigateToVormenXmlPage` gebruikt `click({ force: true })` (ter info ℹ️)

**Bestand**: `VormenXmlPage.js`

```js
navigateToVormenXmlPage(){
    this.vormenXmlMenuItem()
        .should('exist')   // ← controleert alleen dat het in de DOM staat
        .click({ force: true })
}
```

Vergelijk met `ManueleIngavePage`:
```js
navigateToManueleIngavePage(){
    this.manueleIngaveMenuItem()
        .should('be.visible')  // ← controleert zichtbaarheid
        .click()
}
```

Twee kleine inconsistenties:
- `should('exist')` vs. `should('be.visible')` — `be.visible` is strikter en geeft betere foutmeldingen als het menu er niet is
- `click({ force: true })` zonder een zichtbaarheidscheck kan een verborgen element klikken zonder dat Cypress klaagt

Aanbeveling: beide methodes gelijkschakelen naar `should('be.visible').click()` tenzij er een reden is voor `force: true`.

---

## 📋 Samenvatting bevindingen

| # | Bestand | Prioriteit | Beschrijving |
|---|---------|-----------|--------------|
| 1 | Beide | 🔴 Fix | CSS-selector typo: `[data-testid="Acties"` → `[data-testid="Acties"]` |
| 2 | ManueleIngavePage | 🟡 Aanbeveling | Verwijder `.wait(500)` — modal-wait is voldoende |
| 3 | ManueleIngavePage | 🟢 Ter info | `click({ force: true })` — voeg comment toe als het bewust is |
| 4 | ManueleIngavePage | 🟡 Aanbeveling | `i.eq(0)` / `i.eq(1)` → liever `data-testid` icoon-selectors |
| 5 | VormenXmlPage | 🟢 Nit | `deselectTableHeaderCheckbox` → generaliseer indien nodig |
| 6 | VormenXmlPage | 🟡 Aanbeveling | `should('exist')` → `should('be.visible')`, verwijder `force: true` |

**Blocker**: geen
**Mag gemerged worden**: ✅ ja, na fix van punt 1

---

## 💬 Afsluitende noot

Goede MR — de ABV module krijgt er stevige testdekking bij. De Page Object aanpak is clean en consistent met de rest van het project. De meeste opmerkingen zijn kleine verfijningen die de tests robuuster maken voor de lange termijn.

Kleine suggestie voor de toekomst: misschien interessant om bij een volgende sprint samen te bekijken of de inline `i.eq()`-selectors doorheen alle ABV page objects vervangen kunnen worden door `data-testid` — dat zou de hele testsuite een stuk stabieler maken bij UI-wijzigingen.

Goed werk! 🎉

---

*📝 Code review door Koen Vorsters · VorstersNV consultancy · 24 april 2026*
*Gebaseerd op MR ABV-VormenXML (16 bestanden, +1082/-4)*
