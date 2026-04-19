# LinkedIn: Van idee naar AI-webshop — wat ik leerde in één project

---

🚀 **Ik bouwde een AI-aangedreven webshop. Dit is wat ik leerde.**

De afgelopen weken bouwde ik VorstersNV — een volledig functioneel e-commerce platform met lokale AI-agents, een moderne webshop en een complete CI/CD pipeline. Niet als tutorial, maar als echt project.

Hier zijn mijn 5 grootste inzichten:

---

**1. AI hoeft niet in de cloud te draaien**

Met [Ollama](https://ollama.ai) heb ik `llama3` en `mistral` lokaal gedraaid. Geen API-kosten, geen data die mijn bedrijf verlaat. De klantenservice agent, de SEO-agent en de product-beschrijving agent draaien volledig op mijn eigen machine.

Voor een Belgisch bedrijf dat werkt met klantdata is dit goud waard.

---

**2. GitHub Copilot CLI veranderde hoe ik code schrijf**

Ik schreef niet meer gewoon code — ik had een gesprek met mijn codebase. Backend rewriten, Alembic-bugs debuggen, 100 tests genereren, GitHub Actions opzetten... allemaal in één terminal-sessie.

Het is niet "autocomplete op steroïden". Het is meer als een senior collega die altijd beschikbaar is, nooit moe wordt en je code echt begrijpt.

---

**3. De fundering bepaalt alles**

Ik was verleid om snel een mooie UI te bouwen. Maar de uren die ik investeerde in:
- Een goede database structuur (SQLAlchemy async + Alembic)
- Veilige prijs-validatie (altijd vanuit DB, nooit van de client)
- Gast checkout (geen verplichte login = meer conversie)

...betaalden zich dubbel terug.

---

**4. Agents zijn gewoon YAML + een goede prompt**

```yaml
name: klantenservice_agent
model: llama3
capabilities:
  - klantvragen_beantwoorden
  - retour_verwerken
  - escalatie_detecteren
```

Dat is het. De magie zit in de system prompt en de preprompt. Door dit in YAML te houden kon ik snel itereren zonder code te veranderen.

---

**5. Security is geen afterthought**

- JWT audience verificatie (`verify_aud`) moet aan staan in productie
- JWKS cache zonder TTL = key rotation werkt niet
- Prijzen op de client zijn manipuleerbaar — gebruik altijd DB-prijzen

Kleine details, grote impact. Gelukkig ontdekte ik dit *voor* productie.

---

**De stack:**

`FastAPI` + `Next.js 14` + `PostgreSQL` + `Ollama` + `Docker` + `GitHub Actions`

En de geheime ingredient: **GitHub Copilot CLI** — de reden waarom dit project in weken klaar was in plaats van maanden.

---

Volgende stap: Mollie betalingen integreren en alles hosten op mijn thuis Linux-server zodat vrienden en collega's het kunnen uitproberen. 🏠

Ben jij ook bezig met een project waarbij AI en e-commerce samenkomen? Laat het me weten in de reacties — ik deel graag meer.

---

*#AI #WebDevelopment #FastAPI #NextJS #Ollama #GitHubCopilot #BelgischTech #Ecommerce #SoftwareEngineering*

---

> 💡 **Wil je de volledige how-to lezen?** De technische handleiding met code voorbeelden staat op mijn blog/GitHub.
