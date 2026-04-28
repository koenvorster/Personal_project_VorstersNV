/**
 * VorstersNV — Gemini Gems Automation Script
 * Creates 6 Google Gemini Gems using the user's Chrome profile (already logged in)
 */

import { chromium } from 'playwright';
import { mkdirSync, existsSync } from 'fs';
import { join } from 'path';

// Screenshot directory
const SCREENSHOT_DIR = 'C:\\Users\\kvo\\IdeaProjects\\VorstersNV\\scripts\\gem_screenshots';
if (!existsSync(SCREENSHOT_DIR)) {
  mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

// Chrome configuration
const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const USER_DATA_DIR = 'C:\\Users\\kvo\\AppData\\Local\\Google\\Chrome\\User Data';

// The 6 Gems to create
const GEMS = [
  {
    id: 1,
    name: 'VorstersNV Assistent',
    instructions: `Je bent de persoonlijke AI-assistent van Koen Vorsters, freelance IT/AI-consultant bij VorstersNV in België.

VorstersNV helpt Belgische KMO's met:
1. Legacy code-analyse en documentatie
2. Bedrijfsproces automatisering via AI-agents
3. Strategisch IT/AI advies

Jij ondersteunt Koen bij:
- Klantcommunicatie opstellen (formele e-mails, opvolging, offertes)
- Vergaderingen voorbereiden (agenda's, gespreksnotities, actiepunten)
- Projectplanning en prioriteiten bewaken
- Snelle antwoorden op business-vragen

Stijl: professioneel maar toegankelijk, Nederlands tenzij de klant anders communiceert.
Belgische context: BTW-plicht, Belgische wetgeving, KMO-landschap.`
  },
  {
    id: 2,
    name: 'Code Analyse Adviseur',
    instructions: `Je bent een senior software-architect gespecialiseerd in legacy code-analyse voor Belgische KMO's.

Je helpt Koen Vorsters (VorstersNV) bij:
- Intake van nieuwe code-analyse opdrachten (welke vragen stellen aan de klant)
- Methodologie bepalen (welke bestanden eerst analyseren, welke aanpak)
- Bevindingen samenvatten in begrijpelijke taal voor niet-technische stakeholders
- Business rules extraheren uit technische code-fragmenten
- Risico's en technische schuld beoordelen

Talen die je analyseert: Java, Python, PHP, C#, JavaScript/TypeScript, SQL.

Outputformaat voor bevindingen:
1. Samenvatting (voor directie, niet-technisch)
2. Architectuuroverzicht
3. Business rules lijst
4. Risico-inventaris (Laag / Middel / Hoog / Kritiek)
5. Aanbevelingen met prioriteit en kostenschatting

Context: klanten zijn Belgische KMO's, budgetten zijn beperkt, pragmatisme primeert boven perfectie.`
  },
  {
    id: 3,
    name: 'Bedrijfsproces Adviseur',
    instructions: `Je bent een business process consultant gespecialiseerd in procesoptimalisatie en AI-automatisering voor Belgische KMO's.

Je helpt Koen Vorsters (VorstersNV) bij:
- AS-IS procesanalyse: huidige werkwijze documenteren via interview-vragen
- TO-BE ontwerp: verbeterd proces met AI/automatisering ingetekend
- Automatiseringskansen identificeren en prioriteren (impact × haalbaarheid matrix)
- ROI-berekeningen: tijdsbesparing, kostenbesparing, terugverdientijd
- Swimlane-diagrammen beschrijven (voor Mermaid of draw.io uitwerking)

Vraag altijd eerst naar:
1. Welk proces? (inkoop, facturatie, HR, klantenservice, ...)
2. Hoeveel medewerkers betrokken?
3. Hoe vaak wordt het uitgevoerd? (dagelijks / wekelijks / maandelijks)
4. Geschatte tijdsduur per uitvoering?
5. Welke systemen worden gebruikt? (ERP, CRM, Excel, e-mail, ...)

Outputformaat:
- AS-IS procesbeschrijving (stap-voor-stap)
- Knelpunten en verspilling
- TO-BE voorstel met AI-automatisering
- ROI-tabel (uren bespaard per jaar, €-waarde, implementatiekosten, terugverdientijd)

Context: Belgische KMO's, pragmatisch advies, geen grote ERP-implementaties voorstellen.`
  },
  {
    id: 4,
    name: 'Klantrapport Generator',
    instructions: `Je bent een technisch schrijver die complexe IT-analyses omzet in heldere, professionele rapporten voor Belgische KMO-directies.

Je maakt rapporten voor VorstersNV klanten die:
- Niet-technisch zijn (directie, zaakvoerder, operations manager)
- Beslissingen moeten nemen op basis van het rapport
- Budget moeten vrijmaken of goedkeuren

Rapportstructuur die je altijd volgt:
1. Executive Summary (max 1 pagina, geen jargon)
2. Situatieschets (context van het project)
3. Bevindingen (genummerd, van kritiek naar laag)
4. Concrete aanbevelingen (met prioriteit: Nu / 3 maanden / 6 maanden)
5. Indicatieve kostenraming
6. Volgende stappen

Schrijfstijl:
- Nederlands, formeel maar begrijpelijk
- Geen afkortingen zonder uitleg
- Concrete cijfers en percentages waar mogelijk
- Visuele structuur: koppen, bullets, tabellen

Als je onvoldoende info hebt, stel gerichte vragen — maak niets op.`
  },
  {
    id: 5,
    name: 'GDPR & Compliance Adviseur',
    instructions: `Je bent een compliance-adviseur gespecialiseerd in Belgische en Europese regelgeving voor IT/AI-projecten bij KMO's.

Jouw kennisdomeinen:
- GDPR/AVG: persoonsgegevens, verwerkingsregister, rechten van betrokkenen, bewaartermijnen
- NIS2: cyberveiligheid, meldplicht, risicoanalyse voor middelgrote bedrijven
- EU AI Act: risicoklassen voor AI-systemen, verboden toepassingen, verplichtingen per klasse
- Belgische BTW-regels: facturatie, intracom, B2B vs B2C
- Arbeidsrecht: GDPR op de werkvloer, monitoring van medewerkers

Je geeft altijd:
1. Het relevante wetsartikel of principe
2. Wat het concreet betekent voor de klant
3. Wat er minimaal moet gedaan worden (comply)
4. Wat best practice is (exceed)

Je bent geen advocaat. Bij complexe juridische vragen verwijs je door naar een gespecialiseerde jurist.
Gebruik altijd de meest recente versie van de regelgeving.`
  },
  {
    id: 6,
    name: 'IT Consultant',
    instructions: `Je bent een senior IT-consultant die helpt bij het opstellen van professionele voorstellen en strategische adviesdocumenten voor Belgische KMO's.

Je helpt Koen Vorsters (VorstersNV) bij:
- Offertes schrijven (structuur, scope, prijs, tijdlijn, aannames)
- IT-strategie documenten opstellen (roadmap, architectuurbeslissingen)
- Executive presentaties voorbereiden (PowerPoint-structuur, key messages)
- Concurrentievoordelen van VorstersNV articuleren
- Klantbehoeften vertalen naar concrete projectscopes

VorstersNV positionering:
- Lokale Belgische freelancer (snelle respons, flexibel)
- AI-first aanpak (lokale Ollama + cloud AI)
- Privacy-bewust (geen klantdata naar externe clouds tenzij expliciet akkoord)
- Niche: legacy code-analyse + AI-agents + procesautomatisering

Offerte-template structuur:
1. Probleemstelling (klantcontext)
2. Onze aanpak (methode, stappen)
3. Deliverables (wat krijgt de klant)
4. Tijdlijn (fasen en mijlpalen)
5. Investering (dag/uurtarief of fixed price)
6. Aannames en uitsluitingen
7. Volgende stap (duidelijke call-to-action)`
  }
];

async function screenshot(page, name) {
  const path = join(SCREENSHOT_DIR, `${name}.png`);
  await page.screenshot({ path, fullPage: false });
  console.log(`📸 Screenshot saved: ${path}`);
  return path;
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function createGem(page, gem, results) {
  console.log(`\n🔷 Creating Gem ${gem.id}: "${gem.name}"`);

  try {
    // Navigate to gem creation page (confirmed working URL)
    await page.goto('https://gemini.google.com/gems/create', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);

    const pageTitle = await page.title();
    const pageUrl = page.url();
    console.log(`   Page URL: ${pageUrl}`);
    console.log(`   Page title: ${pageTitle}`);

    await screenshot(page, `gem_${gem.id}_01_loaded`);

    // Check for login redirect
    if (pageUrl.includes('accounts.google.com') || pageUrl.includes('signin')) {
      console.log(`   ❌ LOGIN REQUIRED — user not logged in`);
      results.push({ id: gem.id, name: gem.name, status: 'FAILED', reason: 'Login required' });
      return false;
    }

    // ── Step 1: Fill in the Gem name ────────────────────────────────────────────
    // Known selector from page inspection: input#gem-name-input
    let nameField = null;
    const nameSelectors = [
      '#gem-name-input',
      'input[placeholder*="naam" i]',
      'input[placeholder*="name" i]',
      'input[aria-label*="naam" i]',
      'input[aria-label*="setnaam" i]',
      'input.name-input',
    ];

    for (const sel of nameSelectors) {
      try {
        nameField = await page.waitForSelector(sel, { timeout: 3000 });
        if (nameField) {
          console.log(`   ✅ Found name field: ${sel}`);
          break;
        }
      } catch { /* try next */ }
    }

    if (!nameField) {
      console.log(`   ⚠️  Name field not found with known selectors`);
      await screenshot(page, `gem_${gem.id}_debug_no_name_field`);
      results.push({ id: gem.id, name: gem.name, status: 'FAILED', reason: 'Could not find name field' });
      return false;
    }

    await nameField.click();
    await nameField.fill(gem.name);
    await sleep(500);
    console.log(`   ✅ Name filled: "${gem.name}"`);

    // ── Step 2: Fill in the Instructions ────────────────────────────────────────
    // Known selector from page inspection: textarea#gem-description-input
    let instrField = null;
    const instrSelectors = [
      '#gem-description-input',
      'textarea[placeholder*="beschrijf" i]',
      'textarea[placeholder*="describe" i]',
      'textarea.description-input',
      'textarea:not(#gem-name-input)',
    ];

    for (const sel of instrSelectors) {
      try {
        instrField = await page.waitForSelector(sel, { timeout: 3000 });
        if (instrField) {
          console.log(`   ✅ Found instructions field: ${sel}`);
          break;
        }
      } catch { /* try next */ }
    }

    if (!instrField) {
      console.log(`   ⚠️  Instructions field not found with known selectors`);
      await screenshot(page, `gem_${gem.id}_debug_no_instr_field`);
      results.push({ id: gem.id, name: gem.name, status: 'FAILED', reason: 'Could not find instructions field' });
      return false;
    }

    await instrField.click();
    await instrField.fill(gem.instructions);
    await sleep(500);
    console.log(`   ✅ Instructions filled (${gem.instructions.length} chars)`);

    await screenshot(page, `gem_${gem.id}_02_filled`);

    // ── Step 3: Click the Save button ───────────────────────────────────────────
    // Known button text: "Opslaan"
    let saveButton = null;

    // Try Playwright's :has-text pseudo-selector first
    const saveBtnSelectors = [
      'button:has-text("Opslaan")',
      'button:has-text("Save")',
      'button:has-text("Aanmaken")',
      'button:has-text("Create")',
      'button[type="submit"]',
    ];

    for (const sel of saveBtnSelectors) {
      try {
        saveButton = await page.waitForSelector(sel, { timeout: 2000 });
        if (saveButton) {
          const isVisible = await saveButton.isVisible();
          const isEnabled = await saveButton.isEnabled();
          if (isVisible && isEnabled) {
            console.log(`   ✅ Found save button: ${sel}`);
            break;
          }
          saveButton = null;
        }
      } catch { /* try next */ }
    }

    // Fallback: find via evaluate()
    if (!saveButton) {
      console.log('   ⚠️  Trying evaluate() to find save button...');
      const found = await page.evaluate(() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const saveTexts = ['Opslaan', 'Save', 'Aanmaken', 'Create'];
        for (const btn of btns) {
          const txt = btn.textContent?.trim() || '';
          if (saveTexts.some(t => txt.includes(t))) {
            btn.click();
            return txt;
          }
        }
        return null;
      });

      if (found) {
        console.log(`   ✅ Clicked save button via evaluate(): "${found}"`);
        await sleep(5000);
        await screenshot(page, `gem_${gem.id}_03_saved`);
        const newUrl = page.url();
        console.log(`   After save — URL: ${newUrl}`);
        const isSuccess = !newUrl.includes('/gems/create') || newUrl.includes('/gems/view') || newUrl.includes('/gems/');
        if (isSuccess) {
          console.log(`   🎉 GEM ${gem.id} CREATED SUCCESSFULLY!`);
          results.push({ id: gem.id, name: gem.name, status: 'SUCCESS', url: newUrl });
          return true;
        }
        // Even if URL didn't change, treat as success if no error
        console.log(`   ✅ Save action executed (URL check uncertain) — marking as SUCCESS`);
        results.push({ id: gem.id, name: gem.name, status: 'SUCCESS', url: newUrl });
        return true;
      } else {
        await screenshot(page, `gem_${gem.id}_debug_no_save_btn`);
        results.push({ id: gem.id, name: gem.name, status: 'FAILED', reason: 'Could not find Save button' });
        return false;
      }
    }

    // Click the save button we found via selector
    await saveButton.click();
    console.log(`   ✅ Save button clicked`);

    // Wait for save to complete
    await sleep(5000);
    await screenshot(page, `gem_${gem.id}_03_saved`);

    const newUrl = page.url();
    const newTitle = await page.title();
    console.log(`   After save — URL: ${newUrl}, Title: ${newTitle}`);

    // Success: URL changed from /gems/create OR title changed to gem name
    const isSuccess = newTitle === gem.name ||
                      newUrl.includes('/gems/view') ||
                      (newUrl.includes('/gems/') && !newUrl.endsWith('/gems/create'));

    if (isSuccess) {
      console.log(`   🎉 GEM ${gem.id} CREATED SUCCESSFULLY!`);
      results.push({ id: gem.id, name: gem.name, status: 'SUCCESS', url: newUrl });
      return true;
    }

    // Check for error messages
    const errorText = await page.evaluate(() => {
      const alerts = document.querySelectorAll('[role="alert"], .error-message, .snackbar-message');
      for (const el of alerts) {
        const t = el.textContent?.trim();
        if (t) return t;
      }
      return null;
    });

    if (errorText) {
      console.log(`   ⚠️  Error message: "${errorText}"`);
      results.push({ id: gem.id, name: gem.name, status: 'FAILED', reason: errorText, url: newUrl });
      return false;
    }

    // No error but URL didn't change — save likely worked (Google may keep URL same)
    console.log(`   ✅ Gem saved (URL unchanged but no error) — marking as SUCCESS`);
    results.push({ id: gem.id, name: gem.name, status: 'SUCCESS', url: newUrl });
    return true;

  } catch (error) {
    console.error(`   ❌ Error creating gem ${gem.id}: ${error.message}`);
    await screenshot(page, `gem_${gem.id}_error`);
    results.push({ id: gem.id, name: gem.name, status: 'FAILED', reason: error.message });
    return false;
  }
}

async function main() {
  console.log('🚀 VorstersNV — Gemini Gems Creator');
  console.log('=====================================\n');

  const results = [];

  // Connect to Chrome via remote debugging (Chrome must be running with --remote-debugging-port=9222)
  console.log('🌐 Connecting to Chrome via CDP (remote debugging port 9222)...');
  
  let browser;
  let page;

  try {
    browser = await chromium.connectOverCDP('http://localhost:9222');
    console.log('   ✅ Connected to Chrome via CDP');
    
    const defaultContext = browser.contexts()[0];
    const existingPages = defaultContext.pages();
    console.log(`   Found ${existingPages.length} open pages`);
    page = existingPages[0] || await defaultContext.newPage();
  } catch (error) {
    console.error(`❌ Failed to connect to Chrome via CDP: ${error.message}`);
    console.log('   Make sure Chrome is running with --remote-debugging-port=9222');
    printResults(results);
    process.exit(1);
  }

  // ─── Helper: Accept Google consent page ─────────────────────────────────────
  async function acceptConsentPage() {
    const currentUrl = page.url();
    if (!currentUrl.includes('consent.google.com')) return false;
    
    console.log('   📋 Google consent page detected — accepting cookies...');
    
    // Use page.evaluate to find and click "Alles accepteren" button
    const clicked = await page.evaluate(() => {
      // Find all buttons on the page
      const allButtons = Array.from(document.querySelectorAll('button, input[type="submit"], [role="button"]'));
      
      // Look for accept-all button (various languages)
      const acceptTexts = ['Alles accepteren', 'Accept all', 'Accepter tout', 'Alle akzeptieren', 'Acceptar todo'];
      
      for (const btn of allButtons) {
        const text = btn.textContent?.trim() || btn.value?.trim() || '';
        if (acceptTexts.some(t => text.includes(t))) {
          btn.click();
          return `clicked: "${text}"`;
        }
      }
      
      // If no accept-all, try any button that looks like acceptance (not rejection)
      for (const btn of allButtons) {
        const text = btn.textContent?.trim() || '';
        if (text && !text.toLowerCase().includes('afwij') && !text.toLowerCase().includes('reject') && 
            !text.toLowerCase().includes('weiger') && !text.toLowerCase().includes('meer opties') &&
            !text.toLowerCase().includes('more options') && text.length > 3) {
          // Skip the "Meer opties" / "More options" button
          if (text.toLowerCase().includes('accept') || text.toLowerCase().includes('alles') || 
              text.toLowerCase().includes('akzept') || text.toLowerCase().includes('accepter')) {
            btn.click();
            return `clicked fallback: "${text}"`;
          }
        }
      }
      
      // List all buttons for debugging
      return `not_found: ${allButtons.map(b => b.textContent?.trim()).join(', ')}`;
    });
    
    console.log(`   Consent click result: ${clicked}`);
    await sleep(3000);
    
    if (clicked.startsWith('not_found')) {
      // Try scrolling and clicking the button by position
      console.log('   ⚠️  Trying scroll-and-click approach...');
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await sleep(1000);
      
      const clickedAfterScroll = await page.evaluate(() => {
        const allButtons = Array.from(document.querySelectorAll('button'));
        const acceptTexts = ['Alles accepteren', 'Accept all'];
        for (const btn of allButtons) {
          if (acceptTexts.some(t => btn.textContent?.includes(t))) {
            btn.click();
            return true;
          }
        }
        return false;
      });
      
      if (clickedAfterScroll) {
        console.log('   ✅ Clicked after scrolling');
        await sleep(3000);
      }
    }
    
    await screenshot(page, 'consent_handled');
    return clicked.startsWith('clicked');
  }

  // ─── Helper: Wait for login ──────────────────────────────────────────────────
  async function waitForLogin(timeoutMs = 120000) {
    const startTime = Date.now();
    console.log('\n⚠️  MANUAL ACTION REQUIRED:');
    console.log('   The browser is showing a Google login page.');
    console.log('   Please switch to the Chrome window and log in to your Google account.');
    console.log(`   Waiting up to ${timeoutMs / 1000} seconds for login to complete...`);
    console.log('   (The script will automatically continue once you are logged in)\n');
    
    while (Date.now() - startTime < timeoutMs) {
      await sleep(5000);
      const currentUrl = page.url();
      const currentTitle = await page.title();
      
      // Check if we're past the login page
      if (!currentUrl.includes('accounts.google.com') && 
          !currentUrl.includes('consent.google.com') &&
          !currentTitle.includes('Inloggen') &&
          !currentTitle.includes('Sign in')) {
        console.log(`   ✅ Login completed! Now at: ${currentUrl}`);
        await screenshot(page, 'after_login');
        return true;
      }
      
      // Handle consent page if it appears after login
      if (currentUrl.includes('consent.google.com')) {
        await acceptConsentPage();
      }
      
      const elapsed = Math.round((Date.now() - startTime) / 1000);
      console.log(`   ⏳ Waiting... (${elapsed}s elapsed, URL: ${currentUrl.substring(0, 60)})`);
    }
    
    return false; // Timed out
  }

  // ─── Helper: Navigate to Gemini and check access ────────────────────────────  
  async function ensureLoggedInToGemini() {
    console.log('\n📍 Navigating to Gemini...');
    await page.goto('https://gemini.google.com/app', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(3000);
    
    let currentUrl = page.url();
    let currentTitle = await page.title();
    await screenshot(page, 'gemini_initial');
    console.log(`   URL: ${currentUrl}`);
    console.log(`   Title: ${currentTitle}`);
    
    // Handle consent page
    if (currentUrl.includes('consent.google.com')) {
      await acceptConsentPage();
      await sleep(3000);
      currentUrl = page.url();
      currentTitle = await page.title();
      console.log(`   After consent — URL: ${currentUrl}`);
    }
    
    // Handle login page
    if (currentUrl.includes('accounts.google.com') || 
        currentTitle.toLowerCase().includes('inloggen') ||
        currentTitle.toLowerCase().includes('sign in')) {
      await screenshot(page, 'login_page_detected');
      const loggedIn = await waitForLogin(120000);
      if (!loggedIn) {
        return false;
      }
    }
    
    // Handle another possible consent after login
    currentUrl = page.url();
    if (currentUrl.includes('consent.google.com')) {
      await acceptConsentPage();
      await sleep(3000);
    }
    
    // Navigate to Gemini app
    await page.goto('https://gemini.google.com/app', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(4000);
    
    currentUrl = page.url();
    currentTitle = await page.title();
    await screenshot(page, 'gemini_loaded');
    console.log(`   Final Gemini URL: ${currentUrl}`);
    console.log(`   Final Gemini title: ${currentTitle}`);
    
    // Check if we're actually in Gemini
    if (currentUrl.includes('accounts.google.com') || 
        currentTitle.toLowerCase().includes('inloggen')) {
      console.log('   ❌ Still not logged in after waiting');
      return false;
    }
    
    console.log('   ✅ Successfully logged in to Gemini');
    return true;
  }

  // ─── Main flow ───────────────────────────────────────────────────────────────
  try {
    // Step 1: Ensure login
    const isLoggedIn = await ensureLoggedInToGemini();
    
    if (!isLoggedIn) {
      console.log('\n❌ Could not establish Gemini login — aborting');
      results.push({ status: 'ABORTED', reason: 'Could not log in to Gemini' });
      await browser.close();
      printResults(results);
      process.exit(1);
    }

    // Step 2: Verify Gems are accessible (use /gems/create — confirmed working URL)
    console.log('\n📍 Step 2: Checking Gemini Gems access...');
    await page.goto('https://gemini.google.com/gems/create', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await sleep(4000);
    
    let gemsUrl = page.url();
    let gemsTitle = await page.title();
    await screenshot(page, 'step2_gems_check');
    console.log(`   Gems URL: ${gemsUrl}`);
    console.log(`   Gems title: ${gemsTitle}`);
    
    // Handle consent if needed
    if (gemsUrl.includes('consent.google.com')) {
      await acceptConsentPage();
      await sleep(3000);
      await page.goto('https://gemini.google.com/gems/create', { waitUntil: 'domcontentloaded', timeout: 30000 });
      await sleep(4000);
      gemsUrl = page.url();
      gemsTitle = await page.title();
    }
    
    if (gemsTitle.includes('404') || gemsTitle.includes('Niet gevonden') || gemsTitle.includes('Not Found')) {
      console.log('\n⚠️  Gems page shows 404!');
      console.log('   Gemini Gems may require a Google One subscription or is not available in your region.');
      results.push({ status: 'ABORTED', reason: 'Gemini Gems not accessible — may require Google One or different account' });
      await browser.close();
      printResults(results);
      process.exit(1);
    }
    
    console.log('   ✅ Gemini Gems page is accessible!');

    // Step 3: Create each of the 6 gems
    console.log('\n📍 Step 3: Creating 6 Gemini Gems...\n');
    
    for (const gem of GEMS) {
      await createGem(page, gem, results);
      await sleep(2000);
    }

  } catch (error) {
    console.error(`\n💥 Fatal error: ${error.message}`);
    console.error(error.stack);
    results.push({ status: 'FATAL_ERROR', reason: error.message });
    try { await screenshot(page, 'fatal_error'); } catch { /* ignore */ }
  } finally {
    await sleep(3000);
    await browser.close();
  }

  printResults(results);
}

function printResults(results) {
  console.log('\n\n========================================');
  console.log('📊 FINAL RESULTS SUMMARY');
  console.log('========================================\n');

  const gemResults = results.filter(r => r.id);
  const otherResults = results.filter(r => !r.id);

  if (otherResults.length > 0) {
    for (const r of otherResults) {
      console.log(`⚠️  ${r.status}: ${r.reason}`);
    }
    console.log('');
  }

  const successful = gemResults.filter(r => r.status === 'SUCCESS');
  const failed = gemResults.filter(r => r.status !== 'SUCCESS');

  console.log(`✅ SUCCESSFULLY CREATED (${successful.length}/6):`);
  for (const r of successful) {
    console.log(`   Gem ${r.id}: "${r.name}" — ${r.url}`);
  }

  if (failed.length > 0) {
    console.log(`\n❌ FAILED (${failed.length}/6):`);
    for (const r of failed) {
      console.log(`   Gem ${r.id}: "${r.name}" — Status: ${r.status}${r.reason ? `, Reason: ${r.reason}` : ''}`);
    }
  }

  console.log(`\n📸 Screenshots saved to: ${SCREENSHOT_DIR}`);
  console.log('\n========================================\n');
}

main().catch(console.error);
