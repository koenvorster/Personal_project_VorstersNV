'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronDown, ChevronRight, ArrowRight, Bot, BookOpen,
  Zap, Brain, Code2, Shield, Terminal, GitBranch,
  CheckCircle, Layers, Settings, Play,
} from 'lucide-react'
import Link from 'next/link'
import GlassCard from '@/components/ui/GlassCard'

// ─── Types ────────────────────────────────────────────────────────────────────

type ContentBlock =
  | { type: 'paragraph'; text: string }
  | { type: 'heading'; text: string }
  | { type: 'subheading'; text: string }
  | { type: 'list'; items: string[] }
  | { type: 'checklist'; items: string[] }
  | { type: 'code'; language: string; code: string }
  | { type: 'quote'; text: string }
  | { type: 'tip'; emoji?: string; title: string; text: string }
  | { type: 'warning'; title: string; text: string }
  | { type: 'explainer'; emoji: string; title: string; text: string }
  | { type: 'table'; headers: string[]; rows: string[][] }
  | { type: 'grid2'; items: { icon: string; title: string; text: string }[] }
  | { type: 'steps'; items: { title: string; text: string }[] }

interface Section {
  id: string
  icon: typeof Bot
  iconColor: string
  badge: string
  badgeColor: string
  title: string
  subtitle: string
  content: ContentBlock[]
}

// ─── Content ──────────────────────────────────────────────────────────────────

const sections: Section[] = [
  {
    id: 'quickstart',
    icon: Play,
    iconColor: 'text-green-400',
    badge: 'Stap 1',
    badgeColor: 'bg-green-500/20 text-green-400 border-green-500/30',
    title: 'Quick Start: binnen 5 minuten aan de slag',
    subtitle: 'Installeren, openen en je eerste test draaien',
    content: [
      {
        type: 'explainer',
        emoji: '🚀',
        title: 'Wat is dit?',
        text: 'De e2e map in phr-globalconfig bevat alle Cypress end-to-end tests voor de GlobalConfig Angular app. Je test hier de echte applicatie in een echte browser — van login tot CRUD operaties. Denk eraan als een robot die exact doet wat een tester manueel zou doen.',
      },
      {
        type: 'heading',
        text: 'Installatie',
      },
      {
        type: 'code',
        language: 'bash',
        code: `# Ga naar de e2e map
cd e2e

# Installeer dependencies
npm install

# Open de interactieve Cypress UI (standaard: nb-docker-3)
npm run cy:open`,
      },
      {
        type: 'heading',
        text: 'Beschikbare omgevingen',
      },
      {
        type: 'table',
        headers: ['Command', 'Omgeving', 'Wanneer gebruiken?'],
        rows: [
          ['npm run cy:open', 'nb-docker-3 (standaard)', 'Dagelijks development'],
          ['npm run cy:open:nb1', 'nb-docker-1', 'Alternatieve dev omgeving'],
          ['npm run cy:open:tst', 'TST', 'Pre-release validatie'],
          ['npm run cy:open:local', 'localhost', 'Tests lokaal draaien'],
        ],
      },
      {
        type: 'heading',
        text: 'Tests draaien per module of tag',
      },
      {
        type: 'code',
        language: 'bash',
        code: `# Alleen smoke tests (snelste feedback, ~2 min)
npm run cy:run:smoke

# Per module
npm run cy:run:mapping
npm run cy:run:scale-types
npm run cy:run:scale-groups
npm run cy:run:attraction-bonus
npm run cy:run:audit
npm run cy:run:drawer

# Volledige regressie (alle tests, ~15-20 min)
npm run cy:run:regression`,
      },
      {
        type: 'tip',
        emoji: '💡',
        title: 'Begin altijd met cy:open',
        text: 'Gebruik de interactieve UI (cy:open) als je nieuwe tests schrijft of een falende test debugt. Je ziet live wat Cypress doet in de browser. cy:run is voor CI/CD en headless executie.',
      },
    ],
  },
  {
    id: 'structuur',
    icon: Layers,
    iconColor: 'text-blue-400',
    badge: 'Stap 2',
    badgeColor: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    title: 'Projectstructuur begrijpen',
    subtitle: 'Waar staat wat en waarom',
    content: [
      {
        type: 'explainer',
        emoji: '📁',
        title: 'In gewoon Nederlands',
        text: 'Stel je voor dat de e2e map een professionele testkeuken is. De spec files zijn je recepten (wat testen we?). De page objects zijn je gereedschap (hoe klikken we op die knop?). De fixtures zijn je ingrediënten (testdata). De support/commands zijn vaste technieken die je overal hergebruikt.',
      },
      {
        type: 'code',
        language: 'bash — Mappenstructuur',
        code: `e2e/
├── cypress/
│   ├── e2e/                        # ← Spec files (jouw testscenario's)
│   │   ├── mapping/                #   Mapping module tests
│   │   │   ├── mapping-happy-flow.cy.js
│   │   │   ├── mapping-crud.cy.js
│   │   │   └── mapping-api.cy.js
│   │   ├── scales/                 #   Scale module tests
│   │   ├── scale-types/
│   │   ├── audit/
│   │   ├── negative/               #   Error handling tests
│   │   ├── permissions/            #   Rol-gebaseerde toegangstests
│   │   └── acceptance/             #   Acceptance tests per ticket (LN-xxxx)
│   │
│   ├── fixtures/                   # ← Testdata (JSON bestanden)
│   │   ├── mapping/mappingData.json
│   │   └── scales/scalesData.json
│   │
│   └── support/
│       ├── commands.js             # ← Custom cy.xxx() commands
│       ├── e2e.js                  # ← Globale setup (voor elke test)
│       └── pages/                  # ← Page Object Model
│           ├── PagesInstances.js   #   Singleton factory (importeer dit!)
│           ├── PagesObjects.js     #   Exporteert alle page klassen
│           ├── general/            #   Login, Dashboard, Landing pages
│           ├── mapping/            #   MappingPage.js
│           ├── scales/             #   ScalesPage.js, TimelinePage.js
│           └── scale-types/        #   ScaleTypesPage.js
│
├── settings/                       # ← Per-omgeving configs
│   ├── nb3.config.mts              #   Default (nb-docker-3)
│   ├── nb1.config.mts
│   ├── tst.config.mts
│   └── local.config.mts
│
└── cypress.config.mts              # ← Base configuratie`,
      },
      {
        type: 'tip',
        emoji: '🎯',
        title: 'Gouden regel: spec files bevatten GEEN selectors',
        text: 'Alle CSS/data-testid selectors horen thuis in de Page Object klassen. In je spec file gebruik je alleen methodes zoals mappingPage.visit() of mappingPage.clickAddPeriod(). Dit maakt tests onderhoudbaar: als de selector wijzigt, pas je het op één plaats aan.',
      },
    ],
  },
  {
    id: 'login',
    icon: Shield,
    iconColor: 'text-violet-400',
    badge: 'Stap 3',
    badgeColor: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
    title: 'SSO Login & Gebruikers',
    subtitle: 'Keycloak authenticatie, cy.session() caching en testgebruikers',
    content: [
      {
        type: 'explainer',
        emoji: '🔐',
        title: 'Hoe werkt de login?',
        text: 'GlobalConfig gebruikt Keycloak SSO. Wanneer je naar de app gaat, word je doorgestuurd naar het Keycloak loginscherm (op een ander domein). Cypress lost dit op via cy.origin() — een techniek om acties op andere domeinen veilig uit te voeren. cy.session() slaat de ingelogde sessie op zodat elke test niet opnieuw hoeft in te loggen.',
      },
      {
        type: 'heading',
        text: 'Beschikbare testgebruikers',
      },
      {
        type: 'table',
        headers: ['Key', 'Username', 'Rol', 'Gebruik voor'],
        rows: [
          ['GLOBALCONFIGTEST', 'fga_test_user', 'Full read/write', 'De meeste tests (standaard)'],
          ['ADMIN', 'admin', 'Admin', 'Admin-specifieke flows'],
          ['BEHEERDER', 'beheerder', 'Read-only', 'Permissietests'],
          ['PO_USER', 'fga_po_user', 'PO rol', 'PO-specifieke features'],
        ],
      },
      {
        type: 'heading',
        text: 'Login in je test gebruiken',
      },
      {
        type: 'code',
        language: 'javascript — Gebruik in spec file',
        code: `// ✅ Aanbevolen: loginToGlobalConfig doet login + visit in één stap
beforeEach(function () {
    Pages.LoginPage.loginToGlobalConfig('GLOBALCONFIGTEST')
})

// Of rechtstreeks via de custom command:
cy.loginToGlobalConfig('GLOBALCONFIGTEST')

// Andere gebruiker voor permissietests:
cy.loginToGlobalConfig('BEHEERDER')`,
      },
      {
        type: 'heading',
        text: 'Hoe cy.session() werkt',
      },
      {
        type: 'code',
        language: 'javascript — Intern in commands.js',
        code: `cy.session([userType], () => {
    // 1. Bezoek de app → Angular redirect naar Keycloak
    cy.visit(Cypress.env('globalconfigUrl'))

    // 2. Keycloak is op een ander domein → cy.origin() verplicht
    cy.origin(ssoUrl, { args: { username, password } }, ({ username, password }) => {
        cy.get('a[href*="testusers"]').click()   // Klik "test users" IdP knop
        cy.get('#username').type(username)
        cy.get('#password').type(password)
        cy.get('button[type="submit"]').click()
    })

    // 3. Keycloak redirect terug → app is ingelogd
    cy.url({ timeout: 30000 }).should('include', 'globalconfig')
}, {
    // ✅ Sessie validatie: login hergebruikt als cookies aanwezig zijn
    validate: () => cy.getAllCookies().should('have.length.greaterThan', 0)
})`,
      },
      {
        type: 'tip',
        emoji: '⚡',
        title: 'cy.session() = snelheid',
        text: 'Dankzij cy.session() logt Cypress slechts EENMAAL in per spec file, zelfs als je 10 tests hebt die allemaal een beforeEach met login gebruiken. De sessie wordt gecached en hergebruikt. Dit bespaart minuten testuitvoertijd.',
      },
    ],
  },
  {
    id: 'page-objects',
    icon: Code2,
    iconColor: 'text-cyan-400',
    badge: 'Stap 4',
    badgeColor: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    title: 'Page Object Model',
    subtitle: 'Selectors centraliseren, tests onderhoudbaar maken',
    content: [
      {
        type: 'explainer',
        emoji: '📐',
        title: 'Wat is het Page Object Model?',
        text: 'Het Page Object Model (POM) is een ontwerppatroon waarbij elke pagina of module een eigen JavaScript klasse heeft. Die klasse bevat alle selectors (waar staat de knop?) en acties (klik de knop). Je spec file importeert de page object en roept methodes aan — zonder ooit een selector te schrijven in de test zelf.',
      },
      {
        type: 'heading',
        text: 'Pages importeren via de singleton',
      },
      {
        type: 'code',
        language: 'javascript — Bovenaan elke spec file',
        code: `import Pages from '../../support/pages/PagesInstances.js'

// Pages bevat alle page objects als singletons:
// Pages.LoginPage          → login/auth
// Pages.MappingPage        → /mappings module
// Pages.ScalesPage         → /scales module
// Pages.ScaleTypesPage     → /scale-types module
// Pages.ScaleGroupsListPage
// Pages.AttractionBonusPage
// Pages.AuditPage
// Pages.DslPage            → DSL Rule Sets`,
      },
      {
        type: 'heading',
        text: 'Structuur van een Page Object',
      },
      {
        type: 'code',
        language: 'javascript — MappingPage.js (vereenvoudigd)',
        code: `class MappingPage {
    // ── SELECTORS (als arrow functions → lazy evaluation) ──
    mappingListbox      = () => cy.get('p-listbox')
    mappingRow          = () => cy.get('p-listbox .p-listbox-option')
    historyTimeline     = () => cy.get('[data-testid="history"]')
    validFromInput      = () => cy.get('#input-field-valid-from .p-datepicker-input')

    // Actieknoppen
    addChildValueButton = () => cy.get('.add-mapping-child-button')
    saveButton          = () => cy.get('[data-testid="drawer-header-save-button"]')
    cancelButton        = () => cy.get('[data-testid="drawer-header-cancel-button"]')

    // ── API INTERCEPTS ──
    setupApiIntercepts() {
        cy.intercept('GET', '**/mapping-applications').as('getMappingApplications')
        cy.intercept('GET', '**/mappings/history/**').as('getMappings')
        cy.intercept('POST', '**/mappings').as('createMapping')
        cy.intercept('DELETE', '**/mappings/**').as('deleteMapping')
        return this
    }

    // ── ACTIES (combineren selectors + logica) ──
    visit() {
        cy.navigateTo('/mappings')
        return this
    }

    clickMappingRow(index = 0) {
        this.mappingRow().eq(index).click()
        return this
    }
}

export default MappingPage`,
      },
      {
        type: 'heading',
        text: 'Gebruik in een spec file',
      },
      {
        type: 'code',
        language: 'javascript — spec file',
        code: `import Pages from '../../support/pages/PagesInstances.js'

describe('Mapping - Happy Flow', { tags: ['@mapping', '@regression'] }, () => {

    const mappingPage = Pages.MappingPage  // ← Hergebruik singleton

    beforeEach(function () {
        cy.fixture('mapping/mappingData.json').as('data')
        mappingPage.setupApiIntercepts()   // ← Intercepts instellen
        Pages.LoginPage.loginToGlobalConfig('GLOBALCONFIGTEST')
    })

    it('should load mapping list', function () {
        mappingPage.visit()
        cy.wait('@getMappingApplications', { timeout: 15000 })

        // ✅ Gebruik page object methodes, geen hardcoded selectors
        mappingPage.mappingListbox().should('be.visible')
        mappingPage.mappingRow().should('have.length.greaterThan', 0)

        cy.log('✅ Mapping list geladen')
    })
})`,
      },
      {
        type: 'warning',
        title: '❌ Doe dit NIET',
        text: 'cy.get(".all-mapping-applications").click() rechtstreeks in je spec file. Als de selector wijzigt, moet je elke test aanpassen. Gebruik altijd mappingPage.mappingApplicationDropdown().click().',
      },
    ],
  },
  {
    id: 'custom-commands',
    icon: Terminal,
    iconColor: 'text-amber-400',
    badge: 'Stap 5',
    badgeColor: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    title: 'Custom Commands',
    subtitle: "cy.login(), cy.fillInput() en alle andere hulpcommando's",
    content: [
      {
        type: 'explainer',
        emoji: '🔧',
        title: 'Wat zijn custom commands?',
        text: "Cypress laat je eigen cy.xxx() commando's definiëren. Deze staan in cypress/support/commands.js en zijn beschikbaar in alle tests. Ze bundelen herhaalde acties — zoals een datumveld invullen in een PrimeNG datepicker — in één leesbaar commando.",
      },
      {
        type: 'heading',
        text: 'Authenticatie commands',
      },
      {
        type: 'table',
        headers: ['Command', 'Wat doet het?'],
        rows: [
          ['cy.login(userType)', 'Volledige Keycloak SSO login met cy.session() caching'],
          ['cy.loginToGlobalConfig(userType)', 'cy.login() + cy.visit(globalconfigUrl) + wacht op permissions API'],
        ],
      },
      {
        type: 'heading',
        text: 'Navigatie commands',
      },
      {
        type: 'table',
        headers: ['Command', 'Wat doet het?'],
        rows: [
          ['cy.visitModule(path, waitAlias?)', 'Bezoek een module en wacht optioneel op een API intercept alias'],
          ['cy.navigateTo(path)', 'cy.visit(globalconfigUrl + path) — kortere schrijfwijze'],
          ['cy.waitForPageLoad()', 'Wacht tot spinner verdwijnt en app-root zichtbaar is'],
          ['cy.waitForApi(alias, timeout?)', 'Wacht op intercept en assert 2xx status'],
        ],
      },
      {
        type: 'heading',
        text: 'PrimeNG formulier commands',
      },
      {
        type: 'table',
        headers: ['Command', 'Gebruik voor'],
        rows: [
          ['cy.fillInput(selector, value)', 'Gewone text inputs: clear() + type()'],
          ['cy.fillDatePicker(wrapper, date)', 'PrimeNG p-datePicker: vindt .p-datepicker-input binnenin wrapper'],
          ['cy.fillInputNumber(testId, value)', 'PrimeNG p-inputNumber: via data-testid'],
          ['cy.selectPrimeSelect(trigger, text)', 'PrimeNG p-select: open + klik optie op tekst'],
          ['cy.selectPrimeSelectByIndex(trigger, i)', 'PrimeNG p-select: open + klik optie op index'],
          ['cy.selectDropdown(selector, text)', 'PrimeNG p-dropdown: open + klik optie op tekst'],
          ['cy.fillDate(selector, date)', 'Datum invullen + Enter drukken'],
        ],
      },
      {
        type: 'heading',
        text: 'Feedback & assertions',
      },
      {
        type: 'table',
        headers: ['Command', 'Gebruik voor'],
        rows: [
          ['cy.verifyToast(type, message?)', 'Assert PrimeNG toast: "success", "error" of "warn"'],
          ['cy.confirmPopup()', 'Klik PrimeNG confirm popup accept knop'],
          ['cy.rejectPopup()', 'Klik PrimeNG confirm popup reject knop'],
          ['cy.saveDrawer()', 'Klik [data-testid="drawer-header-save-button"]'],
          ['cy.cancelDrawer()', 'Klik [data-testid="drawer-header-cancel-button"]'],
          ['cy.shouldContainText(selector, text)', 'Assert element zichtbaar + bevat tekst'],
        ],
      },
      {
        type: 'heading',
        text: 'Tabel helpers',
      },
      {
        type: 'table',
        headers: ['Command', 'Wat doet het?'],
        rows: [
          ['cy.getTableRow(tableSelector, content)', 'Geeft de <tr> die de opgegeven tekst bevat'],
          ['cy.clickRowAction(content, buttonSelector)', 'Zoek rij op tekst en klik een knop erin'],
          ['cy.generateTestId(prefix?)', 'Geeft een unieke string voor testdata namen'],
          ['cy.screenshotWithName(name)', 'Screenshot met naam gebonden aan de spec file'],
        ],
      },
      {
        type: 'code',
        language: 'javascript — Praktisch voorbeeld',
        code: `// Datum invullen in PrimeNG datepicker
cy.fillDatePicker('#input-field-valid-from', '01/01/2026')

// Dropdown selecteren op tekst
cy.selectPrimeSelect('.all-mapping-applications', 'Applicatie Naam')

// Toast controleren na opslaan
cy.verifyToast('success', 'Opgeslagen')

// Confirm popup accepteren
cy.confirmPopup()

// Unieke testnaam genereren (voorkomt conflicten)
cy.generateTestId('mapping-test').then(name => cy.log(name))`,
      },
    ],
  },
  {
    id: 'tags',
    icon: GitBranch,
    iconColor: 'text-rose-400',
    badge: 'Stap 6',
    badgeColor: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
    title: 'Tags & teststrategie',
    subtitle: 'Welke tests draaien wanneer en waarom',
    content: [
      {
        type: 'explainer',
        emoji: '🏷️',
        title: 'Wat zijn tags?',
        text: 'Tags zijn labels die je toevoegt aan describe() en it() blokken. Ze bepalen welke tests draaien bij welk commando. Zo kun je "geef mij alleen de kritieke tests" of "run alles van de mapping module" zeggen zonder alle spec files te kennen.',
      },
      {
        type: 'heading',
        text: 'Tag overzicht',
      },
      {
        type: 'table',
        headers: ['Tag', 'Command', 'Scope'],
        rows: [
          ['@smoke', 'cy:run:smoke', 'Kritieke happy flows — elke PR, ~2 min'],
          ['@regression', 'cy:run:regression', 'Alle tests — nightly/pre-release, ~15-20 min'],
          ['@mapping', 'cy:run:mapping', 'Alle mapping module tests'],
          ['@scale-types', 'cy:run:scale-types', 'Scale types module'],
          ['@scale-groups', 'cy:run:scale-groups', 'Scale groups module'],
          ['@attraction-bonus', 'cy:run:attraction-bonus', 'Attraction bonus module'],
          ['@audit', 'cy:run:audit', 'Audit log functionaliteit'],
          ['@drawer', 'cy:run:drawer', 'Alle drawer interacties'],
          ['@general', 'cy:run:general', 'Navigatie, routing'],
        ],
      },
      {
        type: 'heading',
        text: 'Tags toevoegen aan je test',
      },
      {
        type: 'code',
        language: 'javascript — Tag conventies',
        code: `// ✅ Goed: tags op describe EN it niveau
describe('Mapping - CRUD', { tags: ['@mapping', '@regression'] }, () => {

    describe('Smoke', { tags: ['@smoke'] }, () => {
        it('should load mapping page', { tags: '@smoke' }, () => {
            // Kritiek pad → dubbel getagd als smoke
        })
    })

    it('should create a new mapping period', { tags: '@regression' }, () => {
        // Enkel regressie, geen smoke
    })
})`,
      },
      {
        type: 'tip',
        emoji: '✅',
        title: 'Tag elke test correct',
        text: 'Elke describe krijgt minimaal één module tag (bijv. @mapping) én @regression. Voeg @smoke toe enkel voor de kritieke happy flow tests die maximaal 2 minuten mogen duren.',
      },
    ],
  },
  {
    id: 'nieuwe-test',
    icon: Zap,
    iconColor: 'text-emerald-400',
    badge: 'Stap 7',
    badgeColor: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    title: 'Een nieuwe test schrijven',
    subtitle: 'Stap voor stap van Jira ticket naar werkende Cypress test',
    content: [
      {
        type: 'steps',
        items: [
          {
            title: 'Bepaal de module en maak een spec file aan',
            text: 'Maak cypress/e2e/<module>/<module>-<scenario>.cy.js aan. Bijv. mapping/mapping-open-end.cy.js. Naam beschrijft wat je test.',
          },
          {
            title: 'Importeer de Pages singleton',
            text: "Bovenaan het bestand: import Pages from '../../support/pages/PagesInstances.js'. Kies de juiste page: const mappingPage = Pages.MappingPage.",
          },
          {
            title: 'Voeg describe/beforeEach toe',
            text: 'Tag de describe met minimaal @<module> en @regression. In beforeEach: fixture laden, setupApiIntercepts() aanroepen, inloggen.',
          },
          {
            title: 'Schrijf de it() blocks',
            text: 'Gebruik page object methodes. Nooit hardcoded selectors in spec files. Log elke stap met cy.log("✅ ..."). Beschrijving in de derde persoon: "should ...".',
          },
          {
            title: 'Test je spec interactief',
            text: 'Open cypress met npm run cy:open, kies je spec file. Cypress toont live wat er gebeurt. Debug eventuele failures via de time-travel debugger.',
          },
          {
            title: 'Voeg toe aan CI als nodig',
            text: 'Als je een nieuwe module maakt: voeg een npm script toe in package.json. Bijv. "cy:run:mijn-module": "cypress run ... --env grepTags=@mijn-module".',
          },
        ],
      },
      {
        type: 'heading',
        text: 'Compleet voorbeeld: acceptance test voor een ticket',
      },
      {
        type: 'code',
        language: 'javascript — cypress/e2e/acceptance/globalconfig/ln-1234-feature.cy.js',
        code: `import Pages from '../../../support/pages/PagesInstances.js'

/**
 * LN-1234: Nieuwe feature
 * AC1: Gebruiker kan X doen
 * AC2: Foutmelding verschijnt als Y ontbreekt
 */
describe('LN-1234 - Nieuwe Feature', { tags: ['@mapping', '@regression'] }, () => {

    const mappingPage = Pages.MappingPage

    beforeEach(function () {
        cy.fixture('mapping/mappingData.json').as('data')
        mappingPage.setupApiIntercepts()
        Pages.LoginPage.loginToGlobalConfig('GLOBALCONFIGTEST')
    })

    describe('Happy Flow', { tags: ['@smoke'] }, () => {
        it('should allow user to do X', { tags: '@smoke' }, function () {
            mappingPage.visit()
            cy.wait('@getMappingApplications', { timeout: 15000 })

            cy.selectPrimeSelect('.all-mapping-applications', this.data.applicationName)
            cy.wait('@getMappings', { timeout: 15000 })

            mappingPage.clickMappingRow(0)
            cy.wait('@getMappingById', { timeout: 15000 })

            mappingPage.clickAddPeriod()
            cy.fillDatePicker('#input-field-valid-from', '01/01/2026')
            cy.saveDrawer()

            cy.wait('@createMapping').its('response.statusCode').should('eq', 201)
            cy.verifyToast('success')
            cy.log('✅ AC1: Feature werkt correct')
        })
    })

    it('should show error when required field is missing', function () {
        mappingPage.visit()
        cy.wait('@getMappingApplications', { timeout: 15000 })
        mappingPage.clickAddPeriod()
        cy.saveDrawer()
        cy.verifyToast('error')
        cy.log('✅ AC2: Foutmelding getoond')
    })
})`,
      },
      {
        type: 'heading',
        text: "Do's & Don'ts",
      },
      {
        type: 'grid2',
        items: [
          { icon: '✅', title: 'Gebruik page objects', text: 'Alle selectors horen in de Page klasse, niet in de spec file.' },
          { icon: '✅', title: 'Wacht op intercepts', text: 'cy.wait("@getMappings") is betrouwbaarder dan cy.wait(2000).' },
          { icon: '✅', title: 'Log elke stap', text: 'cy.log("✅ ...") maakt debugging een stuk makkelijker.' },
          { icon: '✅', title: 'Isoleer tests', text: 'Elke test moet zelfstandig kunnen draaien, in elke volgorde.' },
          { icon: '❌', title: 'Geen cy.wait(ms)', text: 'Vaste wachttijden zijn fragiel. Wacht op DOM condities of API intercepts.' },
          { icon: '❌', title: 'Geen hardcoded URLs', text: 'Gebruik Cypress.env("globalconfigUrl"), nooit een hardcoded URL.' },
          { icon: '❌', title: 'Geen gedeelde state', text: 'Mutable variabelen tussen tests leiden tot onbetrouwbare resultaten.' },
          { icon: '❌', title: "cy.visit() buiten beforeEach", text: 'Navigatie hoort in beforeEach of de test body, nooit op describe niveau.' },
        ],
      },
    ],
  },
  {
    id: 'primeng',
    icon: Settings,
    iconColor: 'text-pink-400',
    badge: 'Referentie',
    badgeColor: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
    title: 'PrimeNG Component Selectors',
    subtitle: 'De juiste selector voor elk PrimeNG component',
    content: [
      {
        type: 'explainer',
        emoji: '🧩',
        title: 'Waarom een speciale aanpak?',
        text: 'PrimeNG componenten renderen complexe DOM structuren. Een p-datePicker is geen gewone <input> — het is een wrapper component met een eigen <input class="p-datepicker-input"> binnenin. De custom cy.fillDatePicker() en cy.selectPrimeSelect() commands handelen deze complexiteit af. Gebruik die altijd.',
      },
      {
        type: 'table',
        headers: ['Component', 'Selector', 'Custom command'],
        rows: [
          ['p-datePicker input', '.p-datepicker-input', 'cy.fillDatePicker(wrapper, date)'],
          ['p-inputNumber input', '.p-inputnumber-input', 'cy.fillInputNumber(testId, value)'],
          ['p-select optie', '.p-select-overlay .p-select-option', 'cy.selectPrimeSelect(trigger, text)'],
          ['p-dropdown optie', '.p-dropdown-panel .p-dropdown-item', 'cy.selectDropdown(selector, text)'],
          ['Confirm popup OK', '.p-confirmpopup-accept-button', 'cy.confirmPopup()'],
          ['Confirm popup Annul.', '.p-confirmpopup-reject-button', 'cy.rejectPopup()'],
          ['Toast success', '.p-toast-message-success', 'cy.verifyToast("success")'],
          ['Toast error', '.p-toast-message-error', 'cy.verifyToast("error")'],
          ['Drawer opslaan', '[data-testid="drawer-header-save-button"]', 'cy.saveDrawer()'],
          ['Drawer annuleren', '[data-testid="drawer-header-cancel-button"]', 'cy.cancelDrawer()'],
          ['Laadspinner', '.p-progress-spinner', 'cy.waitForPageLoad()'],
        ],
      },
      {
        type: 'tip',
        emoji: '🎯',
        title: 'data-testid = meest stabiele selector',
        text: 'Voor elementen zonder stabiele CSS klasse gebruikt de Angular template [data-testid="..."] attributen. Die veranderen niet bij styling of refactoring. Voeg data-testid toe aan nieuwe componenten als je tests schrijft.',
      },
    ],
  },
  {
    id: 'cicd',
    icon: Brain,
    iconColor: 'text-teal-400',
    badge: 'Referentie',
    badgeColor: 'bg-teal-500/20 text-teal-400 border-teal-500/30',
    title: 'CI/CD & Rapportage',
    subtitle: 'GitHub Actions pipeline, parallelle executie en Mochawesome rapporten',
    content: [
      {
        type: 'explainer',
        emoji: '🤖',
        title: 'Wat draait er in CI?',
        text: 'Bij elke push naar develop of main, en bij elke PR, draait de GitHub Actions pipeline automatisch de Cypress tests. De pipeline gebruikt 3 parallelle containers om de tests sneller af te ronden. Resultaten verschijnen als artifacts: screenshots, videos en een HTML rapport.',
      },
      {
        type: 'list',
        items: [
          'Push naar develop, main of master',
          'Pull Request naar die branches',
          'Manuele dispatch: kies zelf de omgeving (nb3/nb1/tst) en tag (@smoke/@regression)',
        ],
      },
      {
        type: 'table',
        headers: ['Artifact', 'Inhoud', 'Bewaard'],
        rows: [
          ['screenshots/', 'Enkel bij failures — exact wat de browser toonde', '7 dagen'],
          ['videos/', 'Altijd — volledige opname per spec file', '7 dagen'],
          ['HTML rapport', 'Mochawesome rapport met alle testresultaten', '14 dagen'],
          ['JUnit XML', 'Voor integratie met andere tools', '14 dagen'],
        ],
      },
      {
        type: 'code',
        language: 'bash — Rapporten lokaal genereren',
        code: `# Ruim oude resultaten op
npm run clean:results

# Draai alle tests + genereer rapporten
npm run test:full

# Enkel smoke + rapport
npm run test:smoke

# Enkel regressie + rapport
npm run test:regression

# Lokaal identiek aan CI:
npx cypress run --config-file settings/nb3.config.mts --env grepTags=@smoke`,
      },
      {
        type: 'tip',
        emoji: '📊',
        title: 'Xray integratie',
        text: 'Testresultaten worden via het Xray script (npm run xray) automatisch teruggerapporteerd naar Jira. Elke acceptance test in cypress/e2e/acceptance/ die gelinkt is aan een ticket krijgt zijn status bijgewerkt.',
      },
    ],
  },
]

// ─── Components ──────────────────────────────────────────────────────────────

function ContentRenderer({ block }: { block: ContentBlock }) {
  if (block.type === 'paragraph') {
    return <p className="text-slate-300 leading-relaxed mb-4">{block.text}</p>
  }
  if (block.type === 'heading') {
    return <h3 className="text-lg font-bold text-white mt-8 mb-3 border-b border-white/10 pb-2">{block.text}</h3>
  }
  if (block.type === 'subheading') {
    return <h4 className="text-base font-semibold text-slate-200 mt-5 mb-2">{block.text}</h4>
  }
  if (block.type === 'list') {
    return (
      <ul className="mb-4 space-y-2">
        {block.items.map((item, i) => (
          <li key={i} className="flex items-start gap-3 text-slate-300 text-sm">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0 mt-2" />
            <span className="leading-relaxed">{item}</span>
          </li>
        ))}
      </ul>
    )
  }
  if (block.type === 'checklist') {
    return (
      <ul className="mb-4 space-y-2">
        {block.items.map((item, i) => (
          <li key={i} className="flex items-start gap-3 text-slate-300 text-sm">
            <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span className="leading-relaxed">{item}</span>
          </li>
        ))}
      </ul>
    )
  }
  if (block.type === 'code') {
    return (
      <div className="mb-5 rounded-xl overflow-hidden border border-white/10">
        <div className="flex items-center gap-2 px-4 py-2 bg-white/5 border-b border-white/10">
          <span className="w-3 h-3 rounded-full bg-red-500/70" />
          <span className="w-3 h-3 rounded-full bg-amber-500/70" />
          <span className="w-3 h-3 rounded-full bg-green-500/70" />
          <span className="ml-2 text-xs text-slate-500 font-mono">{block.language}</span>
        </div>
        <pre className="p-4 overflow-x-auto bg-slate-950/60 text-sm">
          <code className="text-slate-300 font-mono whitespace-pre">{block.code}</code>
        </pre>
      </div>
    )
  }
  if (block.type === 'quote') {
    return (
      <blockquote className="mb-4 border-l-2 border-cyan-500/40 pl-5 py-1">
        <p className="text-slate-400 italic leading-relaxed text-sm">{block.text}</p>
      </blockquote>
    )
  }
  if (block.type === 'tip') {
    return (
      <div className="mb-4 rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-4">
        <div className="flex items-start gap-3">
          <span className="text-lg shrink-0">{block.emoji ?? '💡'}</span>
          <div>
            <p className="font-semibold text-emerald-300 text-sm mb-1">{block.title}</p>
            <p className="text-slate-300 text-sm leading-relaxed">{block.text}</p>
          </div>
        </div>
      </div>
    )
  }
  if (block.type === 'warning') {
    return (
      <div className="mb-4 rounded-xl border border-rose-500/30 bg-rose-500/5 p-4">
        <p className="font-semibold text-rose-300 text-sm mb-1">{block.title}</p>
        <p className="text-slate-300 text-sm leading-relaxed">{block.text}</p>
      </div>
    )
  }
  if (block.type === 'explainer') {
    return (
      <div className="mb-5 rounded-xl border border-amber-500/30 bg-amber-500/5 p-5">
        <div className="flex items-start gap-3">
          <span className="text-2xl shrink-0">{block.emoji}</span>
          <div>
            <p className="font-semibold text-amber-300 mb-1">{block.title}</p>
            <p className="text-slate-300 text-sm leading-relaxed">{block.text}</p>
          </div>
        </div>
      </div>
    )
  }
  if (block.type === 'table') {
    return (
      <div className="mb-5 overflow-x-auto rounded-xl border border-white/10">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-white/5 border-b border-white/10">
              {block.headers.map((h, i) => (
                <th key={i} className="text-left px-4 py-3 text-slate-300 font-semibold whitespace-nowrap">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {block.rows.map((row, ri) => (
              <tr key={ri} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                {row.map((cell, ci) => (
                  <td key={ci} className={`px-4 py-3 text-slate-400 text-xs ${ci === 0 ? 'font-mono' : ''}`}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }
  if (block.type === 'grid2') {
    return (
      <div className="mb-5 grid sm:grid-cols-2 gap-3">
        {block.items.map((item, i) => (
          <div key={i} className="rounded-xl border border-white/10 bg-white/5 p-4">
            <div className="text-xl mb-1">{item.icon}</div>
            <p className="text-white font-semibold text-sm mb-1">{item.title}</p>
            <p className="text-slate-400 text-sm leading-relaxed">{item.text}</p>
          </div>
        ))}
      </div>
    )
  }
  if (block.type === 'steps') {
    return (
      <div className="mb-5 space-y-3">
        {block.items.map((item, i) => (
          <div key={i} className="flex gap-4 items-start rounded-xl border border-white/10 bg-white/5 p-4">
            <div className="shrink-0 w-8 h-8 rounded-full bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-bold text-sm">
              {i + 1}
            </div>
            <div>
              <p className="text-white font-semibold text-sm mb-0.5">{item.title}</p>
              <p className="text-slate-400 text-sm leading-relaxed">{item.text}</p>
            </div>
          </div>
        ))}
      </div>
    )
  }
  return null
}

function SectionCard({ section, index }: { section: Section; index: number }) {
  const [open, setOpen] = useState(index === 0)
  const Icon = section.icon

  return (
    <GlassCard className="overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-4 p-5 sm:p-6 text-left hover:bg-white/5 transition-colors"
      >
        <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 bg-white/5 border border-white/10">
          <Icon className={`w-5 h-5 ${section.iconColor}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${section.badgeColor}`}>
              {section.badge}
            </span>
          </div>
          <h2 className="text-base sm:text-lg font-bold text-white leading-tight">{section.title}</h2>
          <p className="text-slate-400 text-xs sm:text-sm mt-0.5 truncate">{section.subtitle}</p>
        </div>
        <div className="shrink-0">
          {open ? <ChevronDown className="w-5 h-5 text-slate-400" /> : <ChevronRight className="w-5 h-5 text-slate-400" />}
        </div>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            key="content"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
          >
            <div className="px-5 sm:px-6 pb-6 border-t border-white/10 pt-5">
              {section.content.map((block, i) => (
                <ContentRenderer key={i} block={block} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </GlassCard>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function CypressGlobalConfigPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.4 }}>
        <Link href="/how-tos" className="inline-flex items-center gap-2 text-slate-400 hover:text-white text-sm mb-8 transition-colors">
          <ChevronRight className="w-4 h-4 rotate-180" />
          Terug naar How-to&apos;s
        </Link>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <span className="text-xs font-semibold px-3 py-1 rounded-full border bg-cyan-500/20 text-cyan-400 border-cyan-500/30">
            Gids 3 · Testing
          </span>
          <span className="text-xs text-slate-500">PHR GlobalConfig</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white mb-3">
          Cypress E2E Testing in GlobalConfig
        </h1>
        <p className="text-slate-400 text-base sm:text-lg max-w-2xl leading-relaxed">
          Een praktische gids voor collega&apos;s: hoe werkt onze Cypress setup, hoe schrijf je een nieuwe test,
          welke commands gebruik je en hoe lees je de rapporten?
        </p>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }} className="mb-8">
        <GlassCard className="p-5 sm:p-6 border-cyan-500/20 bg-cyan-500/5">
          <div className="grid sm:grid-cols-3 gap-4">
            <div>
              <p className="text-xs font-semibold text-cyan-400 mb-1">👤 Voor wie?</p>
              <p className="text-slate-300 text-sm">Developers en testers die werken aan het phr-globalconfig project</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-cyan-400 mb-1">🎯 Wat je leert</p>
              <p className="text-slate-300 text-sm">Tests schrijven, Page Objects gebruiken, tags, CI/CD en debugging</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-cyan-400 mb-1">📦 Tech stack</p>
              <p className="text-slate-300 text-sm">Cypress 15 · @cypress/grep · Angular 21 · PrimeNG · Keycloak SSO</p>
            </div>
          </div>
        </GlassCard>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.2 }} className="mb-8 flex flex-wrap gap-2">
        {sections.map((s) => (
          <button
            key={s.id}
            onClick={() => document.getElementById(s.id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
            className="text-xs px-3 py-1.5 rounded-full border border-white/10 bg-white/5 text-slate-300 hover:text-white hover:border-cyan-500/40 hover:bg-cyan-500/10 transition-all"
          >
            {s.title.split(':')[0]}
          </button>
        ))}
      </motion.div>

      <div className="space-y-4">
        {sections.map((section, i) => (
          <motion.div
            key={section.id}
            id={section.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 + i * 0.05 }}
          >
            <SectionCard section={section} index={i} />
          </motion.div>
        ))}
      </div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.5 }} className="mt-10">
        <GlassCard className="p-6 sm:p-8 text-center border-cyan-500/20">
          <p className="text-3xl mb-4">🧪</p>
          <h3 className="text-xl font-bold text-white mb-2">Klaar om te testen?</h3>
          <p className="text-slate-400 text-sm mb-6 max-w-md mx-auto">
            Vragen over een specifieke test, een falende spec of een nieuwe module toevoegen?
            Raadpleeg eerst de TESTING.md in de e2e map, of vraag het aan Koen.
          </p>
          <div className="flex flex-wrap gap-3 justify-center">
            <Link href="/how-tos" className="inline-flex items-center gap-2 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/30 text-cyan-300 px-5 py-2.5 rounded-xl text-sm font-medium transition-colors">
              <BookOpen className="w-4 h-4" />
              Andere How-to&apos;s
            </Link>
            <Link href="/blog/ai-gedreven-testautomatisering" className="inline-flex items-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 px-5 py-2.5 rounded-xl text-sm font-medium transition-colors">
              <ArrowRight className="w-4 h-4" />
              AI Testautomatisering blog
            </Link>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  )
}
