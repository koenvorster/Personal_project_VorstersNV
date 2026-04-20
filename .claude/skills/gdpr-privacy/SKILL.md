---
name: gdpr-privacy
description: >
  Use when: assessing GDPR/AVG compliance for VorstersNV, reviewing customer data handling,
  checking Mollie payment data retention, evaluating right-to-erasure implementation,
  reviewing cookie consent, or working on the data processing register.
  Triggers: "GDPR", "AVG", "persoonsgegevens", "privacy", "bewaartermijn", "cookie consent",
  "recht vergetelheid", "verwerkingsregister", "datalek", "PSD2", "Mollie privacy"
---

# SKILL: GDPR Privacy — VorstersNV E-commerce

Referentiekennis voor GDPR/AVG compliance in de VorstersNV e-commerce context.

## Juridisch kader

### Toepasselijke wetgeving
- **GDPR/AVG** — Verordening (EU) 2016/679 (van toepassing in België + Nederland)
- **Wet 30 juli 2018** (BE) — omzettingswet GDPR België
- **PSD2** — Payment Services Directive 2 (voor Mollie betalingen)
- **Belgische cookiewet** — Wet 13 juni 2005 betreffende elektronische communicatie
- **AML/WWFT** — anti-witwassen (relevant voor betalingsdata)
- **Boekhoudwet** (BE) — 7 jaar bewaartermijn voor financiële data

### VorstersNV als Verwerkingsverantwoordelijke

VorstersNV is **verwerkingsverantwoordelijke** (Art. 4.7 GDPR) voor klantdata.
Mollie Payments B.V. is **verwerker** (Art. 28 GDPR) — DPA vereist.

## Rechtsgronden (Art. 6 GDPR)

| Verwerking | Rechtsgrond | Artikel |
|------------|-------------|---------|
| Bestelling uitvoeren | Overeenkomst | Art. 6.1.b |
| Factuur bewaren | Wettelijke verplichting | Art. 6.1.c |
| Fraude voorkomen | Legitiem belang | Art. 6.1.f |
| Marketing e-mails | Toestemming | Art. 6.1.a |
| Analytics/cookies | Toestemming | Art. 6.1.a |
| Keycloak login log | Legitiem belang | Art. 6.1.f |

## Bewaartermijnen

| Categorie | Termijn | Rechtsgrondslag |
|-----------|---------|-----------------|
| Bestel- en factuurdata | **7 jaar** | Belgische boekhoudwet |
| Betalingsdata (Mollie records) | **5 jaar** | PSD2 Art. 5 + AML |
| Klantaccount (actief) | Levensduur account + 1 jaar | Art. 17 GDPR |
| Klantaccount (inactief 2 jaar) | Verwijderen/anonimiseren | Proportionaliteit |
| Session cookies (Redis) | **24 uur** | Minimum noodzakelijk |
| Agent interaction logs | **30 dagen** | Proportionaliteit |
| Auth/audit logs (Keycloak) | **3 jaar** | Legitiem belang |
| Marketing consent log | **3 jaar na opt-out** | Bewijslast |

## PII Classificatie

### Direct identificeerbaar (hoog risico)
```python
Customer.email          # Altijd versleuteld in transit (HTTPS)
Customer.naam           # Volledige naam = PII
Customer.telefoon       # Optioneel veld, minimaliseer
Address.straat_nummer   # Locatiedata
Address.postcode        # In combinatie = adres-PII
```

### Indirect identificeerbaar (midden risico)
```python
Order.id                # Op zichzelf niet, maar + tijdstempel + klant = identificeerbaar
agent_interactions.input_hash  # Hash van klantinput — controleer op reversibiliteit
Redis sessie keys       # Kunnen klantgedrag koppelen
```

### Niet-PII (laag risico)
```python
Product.naam
Category.naam
payment.bedrag          # Alleen bedrag zonder kaartnummer = OK
```

## Recht op Vergetelheid (Art. 17) — Implementatiepatroon

```python
# api/services/customer_service.py

async def anonymise_customer(customer_id: int, session: AsyncSession) -> None:
    """
    GDPR Art. 17: Pseudonimiseer klantdata.
    Orders blijven bestaan (fiscale verplichting 7 jaar).
    """
    customer = await session.get(Customer, customer_id)
    if not customer:
        raise ValueError(f"Customer {customer_id} not found")
    
    # Pseudonimiseer: vervang PII door placeholder
    customer.email = f"deleted_{customer_id}@example.invalid"
    customer.naam = "Verwijderd Klant"
    customer.telefoon = None
    
    # Anonimiseer adressen
    for address in customer.addresses:
        address.straat = "Verwijderd"
        address.huisnummer = "0"
        address.postcode = "0000"
        address.gemeente = "Verwijderd"
    
    customer.geanonimiseerd_op = datetime.utcnow()
    await session.flush()
    
    # Log de actie (zonder PII)
    logger.info(f"Customer {customer_id} anonymised at {customer.geanonimiseerd_op}")
```

## Cookie Consent — Implementatiegids

### Cookie classificatie VorstersNV

| Cookie | Type | Consent vereist? |
|--------|------|-----------------|
| `session_id` | Functioneel (winkelwagen) | ❌ Nee |
| `nextauth.session-token` | Functioneel (auth) | ❌ Nee |
| `consent_given` | Functioneel | ❌ Nee |
| `_ga` (Google Analytics) | Analytisch | ✅ Ja |
| `_fbp` (Facebook Pixel) | Marketing | ✅ Ja + opt-in |

### Consent opslaan

```typescript
// frontend/lib/consent.ts
interface ConsentRecord {
  klant_id?: string  // Anoniem ID als niet ingelogd
  analytics: boolean
  marketing: boolean
  gegeven_op: Date
  ip_geanonimiseerd: string  // Eerste 3 octetten van IP (bijv. 195.25.148.xxx)
}

// Sla consent op in DB, NIET alleen localStorage
async function saveConsent(consent: ConsentRecord): Promise<void> {
  await fetch('/api/consent', {
    method: 'POST',
    body: JSON.stringify(consent)
  })
}
```

## Mollie PSD2 Compliance

### Wat VorstersNV mag bewaren
```python
# ✅ Bewaar dit van Mollie webhook
payment_record = {
    "mollie_id": payment.id,          # Referentie naar Mollie
    "order_id": metadata["order_id"],
    "status": payment.status,
    "bedrag": payment.amount.value,   # Bedrag OK
    "aangemaakt_op": datetime.utcnow()
}

# ❌ NOOIT bewaren (Mollie bewaart dit — jij niet)
# payment.details.cardNumber   — kaartnummer
# payment.details.bankAccount  — IBAN
# payment.details.cvv          — CVV (Mollie stuurt dit nooit!)
```

## Datalek Protocol (Art. 33-34 GDPR)

Bij een beveiligingsincident:
1. **Intern detecteren** — log analysen, monitoring
2. **Beoordelen** — bevat het PII? Hoeveel betrokkenen?
3. **Melden aan GBA** — binnen **72 uur** als hoog risico
   - GBA België: https://www.gegevensbeschermingsautoriteit.be
   - Meldformulier: https://www.gegevensbeschermingsautoriteit.be/burger/acties/aangifte-van-een-inbreuk
4. **Betrokkenen informeren** — als hoog risico voor individu (Art. 34)
5. **Documenteren** — ook als geen melding vereist (Art. 33.5)

## Verwerkingsregister Template (Art. 30)

```yaml
verwerkingen:
  - naam: "Bestellingsbeheer"
    doel: "Uitvoering koopovereenkomst"
    rechtsgrondslag: "Art. 6.1.b"
    betrokkenen: ["Klanten"]
    data_categorieën: ["naam", "e-mail", "afleveradres", "bestelde producten"]
    ontvangers: ["Mollie Payments B.V. (verwerker — DPA afgesloten)"]
    derde_land_doorgifte: "Nee"
    bewaartermijn: "7 jaar (fiscaal)"
    beveiliging: "HTTPS, JWT, Keycloak RBAC, versleutelde DB-verbinding"
    
  - naam: "Marketingcommunicatie"
    doel: "Nieuwsbrief, aanbiedingen"
    rechtsgrondslag: "Art. 6.1.a (toestemming)"
    betrokkenen: ["Klanten die toestemming gaven"]
    data_categorieën: ["e-mail", "naam"]
    ontvangers: ["Email service provider"]
    opt_out: "Afmeldlink in elke e-mail"
    bewaartermijn: "Tot opt-out + 3 jaar (bewijslast)"
```
