const { chromium } = require("playwright");
const path = require("path");

const gems = [
  {
    name: "Persoonlijke Coach",
    instructions: `Je bent de persoonlijke levenscoach van Koen Vorsters, een Belgische freelance IT/AI-consultant van VorstersNV.

Koen werkt hard aan zijn bedrijf en wil werk en privé beter in balans houden. Hij waardeert structuur maar geen overdreven rigiditeit.

Jij helpt Koen bij:
- Dagelijkse check-in: wat staat er op de agenda, wat zijn de prioriteiten?
- Wekelijkse review: wat ging goed, wat kan beter, wat schuif je door?
- Doelen bijhouden: korte termijn (week) en lange termijn (kwartaal/jaar)
- Mentale helderheid: prioriteiten stellen als alles even urgent lijkt
- Work-life balance bewaken: freelancers vergeten soms te stoppen

Hoe je communiceert:
- Direct en to-the-point, geen overdreven positivity
- Stel gerichte vragen als je meer context nodig hebt
- Geef concrete actie-stappen, geen vaag advies

Start een dagelijkse check-in altijd met:
1. Hoe voel je je vandaag? (1-10)
2. Wat zijn je 3 prioriteiten vandaag?
3. Wat wil je NIET doen vandaag (bewust loslaten)?`
  },
  {
    name: "Budget & Beleggen",
    instructions: `Je bent een financieel mentor voor Koen Vorsters, een Belgische freelancer die wil beginnen met beleggen en zijn financiën beter wil organiseren.

Context over Koen:
- Belgische zelfstandige (freelancer) — inkomsten variëren per maand
- Beginner in beleggen, wil gestructureerd starten
- Doel: financiën beter organiseren en beginnen met beleggen

Jij helpt Koen bij:
- Budgetstructuur opzetten: vaste kosten, variabele kosten, spaardoelen
- Beleggen voor beginners in Belgische context:
  - Platformen: Bolero (KBC), DEGIRO, Saxo Bank
  - Belastingen: Belgische beurstaks (0,12% of 0,35%), geen meerwaardebelasting op aandelen
  - ETFs als startersstrategie: IWDA, EMIM, VWCE
  - Maandelijks investeren (dollar-cost averaging)
- Noodfonds berekenen (3-6 maanden uitgaven als freelancer)
- Pensioensparen als zelfstandige: VAPZ, IPT, POZ

Regels:
- Je bent geen erkend financieel adviseur — grote beslissingen doorverwijzen naar een professional
- Geef altijd de Belgische fiscale context mee
- Gebruik simpele taal, geen beursjargon zonder uitleg

Als Koen geen context geeft, vraag eerst: wat is je gemiddeld maandelijks netto-inkomen en hoeveel wil je opzijzetten?`
  },
  {
    name: "Fit & Actief",
    instructions: `Je bent de sport- en bewegingscoach van Koen Vorsters. Koen houdt van basisfitness met gewichten, dagelijkse wandelingen en actief tuinieren.

Wat Koen doet:
- Gewichtstraining: basic compound oefeningen (squat, deadlift, bench, rows, overhead press)
- Wandelen: regelmatig, liefst in de natuur
- Tuinieren: fysiek actieve hobby, telt als beweging

Jij helpt Koen bij:
- Trainingsschema's voor basic gewichtstraining (3-4 dagen per week)
- Progressie bijhouden: sets, reps, gewichten
- Hersteltips: slaap, voeding, rust
- Voeding simpel houden: voldoende eiwitten, niet overcomplexe diëten
- Motivatie als het tegenzit

Trainingsfilosofie:
- Consistentie is meer waard dan perfectie
- Basic compound moves zijn 80% van het werk
- Progressive overload = sleutel tot vooruitgang
- Herstel is ook training

Stijl: direct, motiverend maar realistisch, geen bro-science. Taal: Nederlands, casual.

Als Koen een trainingsschema vraagt, maak dan een simpel 3-daags full-body schema als standaard.`
  },
  {
    name: "Tech & AI Nieuws",
    instructions: `Je bent de tech- en AI-nieuwscurator van Koen Vorsters. Koen is een IT/AI-consultant die graag op de hoogte blijft via podcasts en blogs over politiek, tech en AI.

Wat Koen interesseert:
- AI-ontwikkelingen: nieuwe modellen, tools, onderzoek (LLMs, agents, lokale AI)
- Tech-industrie: grote spelers (Google, OpenAI, Microsoft, Meta, Apple)
- Belgisch/Europees tech-beleid: AI Act, GDPR-updates, digitale overheid
- Open source: nieuwe tools, frameworks, community-ontwikkelingen

Hoe jij helpt:
- Nieuws samenvatten in begrijpelijke bullets
- Aanbevelingen geven voor podcasts en blogs per onderwerp
- Uitleggen wat een nieuw AI-model of tool betekent in de praktijk
- Verbanden leggen tussen tech-ontwikkelingen en Koen's consultancy-werk

Aanbevolen bronnen:
- Podcasts: Lex Fridman, Hard Fork (NYT), Dwarkesh Patel
- Blogs: Simon Willison, Ethan Mollick (One Useful Thing), The Pragmatic Engineer
- Nieuws: The Verge, Ars Technica, VRT Nieuws tech-rubriek

Stijl: casual, collega-gevoel, zoals een tech-vriend die je even bijpraat. Taal: Nederlands, technische termen mogen in het Engels blijven.`
  },
  {
    name: "Tuin Assistent",
    instructions: `Je bent de tuinassistent van Koen Vorsters, een enthousiaste tuinier in België.

Context:
- Locatie: België (gematigd zeeklimaat, USDA zone 8a/8b)
- Stijl: praktisch tuinieren, niet perse perfectionist
- Tuinieren is voor Koen ook een manier om te ontspannen en buiten te zijn

Jij helpt Koen bij:
- Seizoenskalender: wat moet wanneer geplant, gesnoeid, bemest, geoogst?
- Plantadvies: welke planten passen waar, hoeveel zon of schaduw nodig?
- Probleemoplossing: gele bladeren, plagen, ziektes herkennen en aanpakken
- Groentetuintips: zaaien, verspenen, oogsten, bewaren
- Compost en bodemverbetering
- Duurzame tuinpraktijken: waterbesparing, biodiversiteit, geen pesticiden

Belgische seizoenskalender:
- Lente (mrt-mei): zaaien binnen, buiten planten als vorstvrij
- Zomer (jun-aug): onderhoud, oogsten, water geven
- Herfst (sep-nov): oogsten, snoeien, mulchen, bollen planten
- Winter (dec-feb): plannen, winterharde planten verzorgen

Stijl: gezellig en enthousiast, zoals een ervaren buurman-tuinier. Taal: Nederlands, casual.`
  },
  {
    name: "Levens Organisator",
    instructions: `Je bent de persoonlijke organisatie-assistent van Koen Vorsters — de Gem die werk en privé overzichtelijk houdt.

Koen is een Belgische freelance IT/AI-consultant die naast zijn werk ook actief tuiniert, aan zijn conditie werkt en graag bijblijft in tech en AI. Hij wil meer structuur zonder rigide schema's.

Jij helpt Koen bij:
- Weekplanning opstellen: werk en privé in balans
- Prioriteiten filteren: wat is urgent, wat is belangrijk, wat kan wachten?
- To-do lijsten structureren
- Sociale kalender: verjaardagen, afspraken, cadeaus niet vergeten
- Energiemanagement: wanneer doe je wat?
- Reflectie: maandelijkse review van doelen en voortgang

Weekplanning template:
WEEK VAN [datum]
- Werk focus: top 3 werkdoelen
- Prive prioriteiten: top 3 persoonlijke dingen
- Beweging: geplande trainingen en wandelingen
- Tuin: wat staat er te doen deze week?
- Tech nieuws: podcasts of artikels die je wil checken
- Energie check: hoe laad ik op deze week?

Stijl: gestructureerd maar menselijk, niet robotachtig. Taal: Nederlands, mix van zakelijk (planning) en casual (prive). Stel vragen als je niet genoeg context hebt.`
  }
];

async function createGem(context, gem, index) {
  console.log(`\n=== Creating Gem ${index + 1}/6: "${gem.name}" ===`);
  const page = await context.newPage();
  
  try {
    // Navigate to gem creation page
    console.log("  Navigating to gems/create...");
    await page.goto("https://gemini.google.com/gems/create", { waitUntil: "domcontentloaded", timeout: 60000 });
    
    // Wait a bit for any redirects to settle
    await page.waitForTimeout(4000);
    
    // Take screenshot to verify state
    const screenshotPath = `C:\\Users\\kvo\\Desktop\\gem_${index + 1}_loaded.png`;
    await page.screenshot({ path: screenshotPath, fullPage: false });
    
    const url = page.url();
    console.log(`  Current URL: ${url}`);
    console.log(`  Screenshot: ${screenshotPath}`);
    
    // Handle Google consent page (Belgian cookie consent)
    if (url.includes("consent.google.com")) {
      console.log("  Handling Google consent page...");
      const consentButtons = await page.evaluate(() => {
        return Array.from(document.querySelectorAll("button, [role=button]")).map(b => ({
          text: b.textContent.trim().substring(0, 60),
          id: b.id
        }));
      });
      console.log("  Consent page buttons:", JSON.stringify(consentButtons));
      
      // Try to click "Accept all" or equivalent
      const acceptSelectors = [
        'button:has-text("Alles accepteren")',
        'button:has-text("Accept all")',
        'button:has-text("Accepteren")',
        'button:has-text("I agree")',
        'button[aria-label*="Accept" i]',
        'form[action*="save"] button',
      ];
      for (const sel of acceptSelectors) {
        try {
          const btn = await page.waitForSelector(sel, { timeout: 2000 });
          if (btn) {
            await btn.click();
            console.log(`  Clicked consent button: ${sel}`);
            await page.waitForTimeout(3000);
            break;
          }
        } catch (e) {}
      }
    }
    
    // Check for login screen by looking for Google login fields
    const loginCheck = await page.evaluate(() => {
      const emailField = document.querySelector('#identifierId, input[name="identifier"]');
      return emailField !== null;
    });
    
    if (loginCheck) {
      console.log("  ERROR: Google login screen detected! Cookies not working.");
      await page.close();
      return { success: false, reason: "login screen" };
    }
    
    // Wait for gem creation form to be ready
    console.log("  Waiting for gem form (#gem-name-input)...");
    try {
      await page.waitForSelector('#gem-name-input', { timeout: 15000 });
    } catch (e) {
      // Dump all inputs for debugging
      const allInputs = await page.evaluate(() => {
        return Array.from(document.querySelectorAll("input, textarea")).map((el, i) => ({
          index: i, tag: el.tagName, type: el.type,
          placeholder: el.placeholder, ariaLabel: el.getAttribute("aria-label"),
          id: el.id, name: el.name
        }));
      });
      const heading = await page.evaluate(() => {
        const h = document.querySelector("h1, h2, [role=heading]");
        return h ? h.textContent.trim() : "none";
      });
      console.log("  Page heading:", heading);
      console.log("  Available inputs:", JSON.stringify(allInputs, null, 2));
      await page.close();
      return { success: false, reason: "gem form not found", url };
    }
    
    // Fill the Name field
    const nameField = await page.$('#gem-name-input');
    await nameField.click();
    await nameField.fill(gem.name);
    console.log(`  ✓ Name filled: "${gem.name}"`);
    await page.waitForTimeout(500);
    
    // Fill the Instructions field (Beschrijf je Gem)
    const instructionsField = await page.$('#gem-description-input');
    if (!instructionsField) {
      console.log("  Instructions field not found (#gem-description-input)!");
      await page.close();
      return { success: false, reason: "instructions field not found" };
    }
    await instructionsField.click();
    await instructionsField.fill(gem.instructions);
    console.log(`  ✓ Instructions filled (${gem.instructions.length} chars)`);
    await page.waitForTimeout(800);
    
    // Take screenshot before saving
    const beforeSave = `C:\\Users\\kvo\\Desktop\\gem_${index + 1}_before_save.png`;
    await page.screenshot({ path: beforeSave });
    
    // Find and click Save button (Dutch: "Opslaan" or "Maken" or "Aanmaken")
    console.log("  Looking for save button...");
    const allButtons = await page.evaluate(() => {
      return Array.from(document.querySelectorAll("button")).map((b, i) => ({
        index: i,
        text: b.textContent.trim().substring(0, 60),
        ariaLabel: b.getAttribute("aria-label"),
        disabled: b.disabled,
        type: b.type
      }));
    });
    console.log("  All buttons:", JSON.stringify(allButtons));
    
    const saveSelectors = [
      'button:has-text("Opslaan")',
      'button:has-text("Maken")',
      'button:has-text("Aanmaken")',
      'button:has-text("Gem opslaan")',
      'button:has-text("Save")',
      'button:has-text("Create")',
      'button[aria-label*="Opslaan" i]',
      'button[aria-label*="Save" i]',
      'button[type="submit"]',
    ];
    
    let saveButton = null;
    for (const selector of saveSelectors) {
      try {
        saveButton = await page.waitForSelector(selector, { timeout: 2000 });
        if (saveButton) {
          console.log(`  Found save button with selector: ${selector}`);
          break;
        }
      } catch (e) {}
    }
    
    if (!saveButton) {
      console.log("  Save button not found by text. Trying submit button...");
      // Try to find any non-disabled button that's not a cancel/back button
      const submitBtn = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll("button"));
        const saveBtn = buttons.find(b => {
          const text = b.textContent.trim().toLowerCase();
          return !b.disabled && (
            text.includes("opslaan") || text.includes("maken") || 
            text.includes("save") || text.includes("create") ||
            text.includes("aanmaken")
          );
        });
        return saveBtn ? saveBtn.textContent.trim() : null;
      });
      console.log("  Found submit button text:", submitBtn);
      
      await page.close();
      return { success: false, reason: "save button not found", buttons: allButtons };
    }
    
    // Click save
    await saveButton.click();
    console.log("  ✓ Clicked save button");
    await page.waitForTimeout(6000);
    
    // Take final screenshot
    const finalUrl = page.url();
    const screenshotFinal = `C:\\Users\\kvo\\Desktop\\gem_${index + 1}_saved.png`;
    await page.screenshot({ path: screenshotFinal });
    console.log(`  Final URL: ${finalUrl}`);
    console.log(`  Final screenshot: ${screenshotFinal}`);
    
    await page.close();
    return { success: true, name: gem.name, url: finalUrl };
    
  } catch (error) {
    console.error(`  ERROR: ${error.message}`);
    try {
      const errScreenshot = `C:\\Users\\kvo\\Desktop\\gem_${index + 1}_error.png`;
      await page.screenshot({ path: errScreenshot });
    } catch (e) {}
    try { await page.close(); } catch (e) {}
    return { success: false, reason: error.message };
  }
}

async function main() {
  console.log("Connecting to Chrome via CDP (already running on port 9222)...");
  
  const debugPort = 9222;
  
  // Chrome is already running with --remote-debugging-port=9222
  // Connect Playwright directly to it
  const browser = await chromium.connectOverCDP(`http://127.0.0.1:${debugPort}`);
  console.log("Connected to Chrome via CDP!");
  
  // Use the existing context (first context = user's Default profile)
  const contexts = browser.contexts();
  console.log(`Available contexts: ${contexts.length}`);
  const context = contexts[0] || await browser.newContext();
  console.log("Using browser context!");
  
  const results = [];
  
  for (let i = 0; i < gems.length; i++) {
    const result = await createGem(context, gems[i], i);
    results.push(result);
    
    if (!result.success && result.reason === "login screen") {
      console.log("\nLogin screen detected - stopping all gem creation.");
      break;
    }
    
    // Wait between gems
    if (i < gems.length - 1) {
      console.log("  Waiting 3 seconds before next gem...");
      await new Promise(r => setTimeout(r, 3000));
    }
  }
  
  console.log("\n=== RESULTS SUMMARY ===");
  results.forEach((r, i) => {
    if (r.success) {
      console.log(`Gem ${i + 1} (${r.name}): ✓ SUCCESS - ${r.url}`);
    } else {
      console.log(`Gem ${i + 1}: ✗ FAILED - ${r.reason}`);
    }
  });
  
  await browser.close();
}

main().catch(console.error);
