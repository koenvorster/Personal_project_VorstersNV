---
name: belgian-commerce
version: "1.0"
domain: commerce
audience: [agents, developers]
tags: [btw, belgie, gdpr, consumentenwet, taalwetgeving, intracom, factuur]
---

# Belgian Commerce

## Beschrijving
Belgische e-commerce regelgeving voor VorstersNV: BTW-tarieven, consumentenwet,
GDPR-implementatie, taalwetgeving, intracom B2B en factuurvereisten.

## Wanneer gebruiken
- Bij BTW-berekening op orders en facturen
- Bij retourafhandeling en herroepingsrecht
- Bij klantcommunicatie (taalvereisten)
- Bij factuurcreatie (verplichte velden)
- Bij EU B2B transacties (intracom BTW-vrijstelling)
- Bij datalekken (GDPR meldplicht)

## Kernkennis

### BTW tarieven
| Tarief | Categorie                                              |
|--------|--------------------------------------------------------|
| 21%    | Standaard — elektronica, kleding, luxegoederen         |
| 12%    | Restaurantdiensten, sociale huisvesting               |
| 6%     | Voeding, boeken, geneesmiddelen, kranten, water        |
| 0%     | Export buiten EU, intracom levering aan BTW-plichtigen |

```python
BTW_RATES = {
    "electronics": Decimal("0.21"),
    "clothing": Decimal("0.21"),
    "food": Decimal("0.06"),
    "books": Decimal("0.06"),
    "medication": Decimal("0.06"),
    "restaurant": Decimal("0.12"),
}

def calculate_btw(price_excl: Decimal, category: str) -> Decimal:
    rate = BTW_RATES.get(category, Decimal("0.21"))
    return (price_excl * rate).quantize(Decimal("0.01"))
```

### BTW-nummer validatie
Belgisch BTW-nummer: `BE` + 10 cijfers (eerste cijfer is 0 of 1).

```python
import re

def validate_btw_number(btw: str) -> bool:
    """Valideert Belgisch BTW-nummer: BE + 10 cijfers."""
    pattern = r'^BE[01]\d{9}$'
    if not re.match(pattern, btw.upper()):
        return False
    # Controlegetal verificatie (modulo 97)
    number = btw[2:]
    check = int(number[-2:])
    base = int(number[:-2])
    return (97 - (base % 97)) == check
```

### Consumentenwet — herroepingsrecht
- **14 kalenderdagen** na ontvangst van het product
- Klant hoeft geen reden op te geven
- Retourkosten zijn voor de klant (tenzij anders vermeld)
- Terugbetaling binnen **14 dagen** na ontvangst retour
- Uitzonderingen: gepersonaliseerde producten, digitale content (na download), bederfelijke goederen

### GDPR België (AVG-implementatie)
| Verplichting              | Termijn / Detail                                        |
|---------------------------|---------------------------------------------------------|
| Meldplicht datalek        | **72 uur** na ontdekking bij GBA (Gegevensbeschermingsautoriteit) |
| Bewaarrecht klantdata     | Max. 7 jaar voor boekhoudkundige data                   |
| Recht op vergetelheid     | Verwerken binnen 30 dagen                               |
| Toestemming marketing     | Opt-in verplicht, opt-out altijd mogelijk               |
| IP-adressen               | Persoonsgegevens — beperkte bewaartermijn               |
| Cookie consent            | Actieve toestemming voor niet-essentiële cookies        |

### Taalwetgeving
| Regio                  | Verplichte communicatietaal |
|------------------------|-----------------------------|
| Vlaanderen             | Nederlands (NL)             |
| Wallonië               | Frans (FR)                  |
| Brussel                | NL + FR (tweetalig)         |
| Duitstalige gemeenschap| Duits (DE)                  |

Klantcommunicatie, facturen en voorwaarden moeten in de taal van de regio van de klant.

```python
REGION_LANGUAGE = {
    "VLG": "nl",
    "WAL": "fr",
    "BRU": "nl",  # fallback NL, maar bied ook FR aan
    "DEU": "de",
}
```

### Intracom — BTW-vrijstelling EU B2B
Voorwaarden:
1. Koper heeft geldig EU BTW-nummer
2. Goederen worden fysiek verplaatst naar ander EU-land
3. Verkoper is BTW-plichtig in België
4. BTW-nummer koper verifiëren via VIES (EU-database)

```python
async def check_intracom_eligible(customer: Customer) -> bool:
    if not customer.btw_number or not customer.btw_number.startswith("BE"):
        return False  # BE-interne levering is niet intracom
    eu_prefixes = ["DE", "FR", "NL", "LU", "IT", "ES"]  # etc.
    country = customer.btw_number[:2]
    return country in eu_prefixes and await vies.validate(customer.btw_number)
```

### Factuurvereisten (verplichte velden)
Een geldige Belgische factuur moet bevatten:
- Factuurnummer (uniek, opeenvolgend)
- Factuurdatum
- Naam en adres verkoper
- BTW-nummer verkoper
- Naam en adres klant (+ BTW-nummer bij B2B)
- Omschrijving goederen/diensten
- Hoeveelheid en eenheidsprijs
- BTW-tarief en BTW-bedrag
- Totaal excl. BTW, BTW-bedrag, totaal incl. BTW
- Betalingstermijn en rekeningnummer

## Voorbeelden

### Factuurberekening met BTW
```python
@dataclass
class InvoiceLine:
    description: str
    quantity: int
    unit_price_excl: Decimal
    btw_rate: Decimal

    @property
    def total_excl(self) -> Decimal:
        return (self.unit_price_excl * self.quantity).quantize(Decimal("0.01"))

    @property
    def btw_amount(self) -> Decimal:
        return (self.total_excl * self.btw_rate).quantize(Decimal("0.01"))

    @property
    def total_incl(self) -> Decimal:
        return self.total_excl + self.btw_amount
```

### GDPR data request verwerking
```python
async def handle_right_to_erasure(customer_id: str) -> None:
    """Verwerkt verzoek tot vergetelheid binnen 30 dagen."""
    await anonymize_personal_data(customer_id)
    await delete_marketing_consents(customer_id)
    # Behoud boekhoudkundige data (7 jaar wettelijke bewaarplicht)
    await mark_account_deleted(customer_id)
    await notify_customer_erasure_complete(customer_id)
```

## Gerelateerde skills
- mollie-payments
- order-lifecycle
- payroll-validation
