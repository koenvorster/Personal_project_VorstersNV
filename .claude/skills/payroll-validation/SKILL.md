---
name: payroll-validation
version: "1.0"
domain: payroll
audience: [agents, developers]
tags: [rsz, loon, bedrijfsvoorheffing, prc, vakantiegeld, maaltijdcheques]
---

# Payroll Validation

## Beschrijving
Kennis over loonberekening validatie voor de PRC (Payroll Review Controller):
RSZ-bijdragen, bedrijfsvoorheffing, nettoloon berekening, anomalie detectie,
vakantiegeld en fiscale voordelen in natura.

## Wanneer gebruiken
- Bij PRC validatie van loonberekeningsbatches
- Bij controle van individuele loonfiches
- Bij anomalie detectie (> 20% afwijking tov vorige maand)
- Bij berekening van vakantiegeld
- Bij validatie van maaltijd- en ecocheques

## Kernkennis

### RSZ bijdragen
| Bijdrage              | Percentage | Basis              |
|-----------------------|------------|--------------------|
| Werkgever RSZ         | 25,00%     | Brutoloon           |
| Werknemer RSZ         | 13,07%     | Brutoloon           |
| Effectieve werkgeverslast | ~33%   | Bruto + werkgever RSZ |

```python
RSZ_WERKNEMER = Decimal("0.1307")
RSZ_WERKGEVER = Decimal("0.2500")

def bereken_rsz(brutoloon: Decimal) -> dict:
    return {
        "rsz_werknemer": (brutoloon * RSZ_WERKNEMER).quantize(Decimal("0.01")),
        "rsz_werkgever": (brutoloon * RSZ_WERKGEVER).quantize(Decimal("0.01")),
        "belastbaar_loon": (brutoloon * (1 - RSZ_WERKNEMER)).quantize(Decimal("0.01")),
    }
```

### Bedrijfsvoorheffing
Schijven 2024 (vereenvoudigd, gezinssituatie: alleenstaande zonder kinderen):

| Belastbaar maandloon     | BV-tarief (benadering) |
|--------------------------|------------------------|
| ≤ 1.095 EUR              | 0%                     |
| 1.095 – 1.945 EUR        | ~26,75%                |
| 1.945 – 3.490 EUR        | ~42,80%                |
| > 3.490 EUR              | ~53,50%                |

De exacte BV-berekening volgt de officiële schalen van FOD Financiën (jaarlijks geïndexeerd).
Gezinskorting: vermindering per persoon ten laste.

```python
def bereken_bv(belastbaar_maandloon: Decimal, personen_ten_laste: int = 0) -> Decimal:
    """Vereenvoudigde BV berekening — gebruik officiële RV-tabellen voor productie."""
    bv_basis = _bereken_bv_basis(belastbaar_maandloon)
    gezinskorting = Decimal(personen_ten_laste) * Decimal("35.00")
    return max(Decimal("0"), bv_basis - gezinskorting).quantize(Decimal("0.01"))
```

### Nettoloon berekening
```
Brutoloon
  - RSZ werknemer (13,07%)
= Belastbaar loon
  - Bedrijfsvoorheffing (schijven)
  + Voordelen in natura (maaltijdcheques, ecocheques)
= Nettoloon
```

```python
def bereken_nettoloon(brutoloon: Decimal, gezinssituatie: str = "alleenstaande",
                      personen_ten_laste: int = 0,
                      maaltijdcheques_aantal: int = 0) -> LoonBerekening:
    rsz = bereken_rsz(brutoloon)
    bv = bereken_bv(rsz["belastbaar_loon"], personen_ten_laste)
    cheque_waarde = Decimal(maaltijdcheques_aantal) * MAALTIJDCHEQUE_WERKNEMERSBIJDRAGE

    netto = rsz["belastbaar_loon"] - bv - cheque_waarde
    return LoonBerekening(
        bruto=brutoloon,
        rsz_werknemer=rsz["rsz_werknemer"],
        belastbaar=rsz["belastbaar_loon"],
        bedrijfsvoorheffing=bv,
        netto=netto.quantize(Decimal("0.01")),
    )
```

### Anomalie detectie
Regels die een alert triggeren:

| Regel                                      | Drempel  | Prioriteit |
|--------------------------------------------|----------|------------|
| Afwijking tov vorige maand                 | > 20%    | HIGH       |
| Negatief nettoloon                         | < 0 EUR  | CRITICAL   |
| RSZ berekening buiten verwacht bereik      | ± 0,01%  | HIGH       |
| Loon hoger dan contractueel maximum        | > 0 EUR  | MEDIUM     |
| Ontbrekende bedrijfsvoorheffing            | BV = 0   | MEDIUM     |
| Aantal werkdagen afwijkend                 | > 3 dagen| LOW        |

```python
def detect_anomalies(huidig: LoonBerekening, vorig: LoonBerekening) -> list[Anomalie]:
    anomalies = []
    afwijking = abs(huidig.netto - vorig.netto) / vorig.netto
    if afwijking > Decimal("0.20"):
        anomalies.append(Anomalie(
            type="AFWIJKING_VORIGE_MAAND",
            prioriteit="HIGH",
            detail=f"Nettoloon afwijking: {afwijking:.1%} (vorig: {vorig.netto}, huidig: {huidig.netto})"
        ))
    if huidig.netto < 0:
        anomalies.append(Anomalie(type="NEGATIEF_NETTO", prioriteit="CRITICAL"))
    return anomalies
```

### Vakantiegeld
**Enkelvoudig vakantiegeld** (uitbetaald bij vakantieperiode):
- 92% van het brutodagloon × aantal vakantiedagen

**Dubbel vakantiegeld** (uitbetaald in mei/juni):
- 85% van het brutoloon van de maand mei

```python
def bereken_dubbel_vakantiegeld(bruto_mei: Decimal) -> Decimal:
    return (bruto_mei * Decimal("0.85")).quantize(Decimal("0.01"))

def bereken_enkelvoudig_vakantiegeld(bruto_daglooon: Decimal, vakantiedagen: int) -> Decimal:
    return (bruto_daglooon * Decimal("0.92") * vakantiedagen).quantize(Decimal("0.01"))
```

### Maaltijdcheques en ecocheques
| Type             | Max werkgeversbijdrage | Max werknemersbijdrage | Fiscaal voordeel      |
|------------------|------------------------|------------------------|-----------------------|
| Maaltijdcheque   | 6,91 EUR/dag           | 1,09 EUR/dag           | Vrijgesteld RSZ + BV  |
| Ecocheque        | 250 EUR/jaar           | n.v.t.                 | Vrijgesteld RSZ + BV  |
| Cadeaucheque     | 40 EUR/jaar            | n.v.t.                 | Vrijgesteld RSZ + BV  |

```python
MAALTIJDCHEQUE_MAX_WERKGEVER = Decimal("6.91")
MAALTIJDCHEQUE_WERKNEMERSBIJDRAGE = Decimal("1.09")
ECOCHEQUE_MAX_JAAR = Decimal("250.00")
```

## Voorbeelden

### Volledige loonberekening
```python
# Werknemer: bruto 3000 EUR, alleenstaande, 0 ten laste, 20 maaltijdcheques
berekening = bereken_nettoloon(
    brutoloon=Decimal("3000.00"),
    gezinssituatie="alleenstaande",
    personen_ten_laste=0,
    maaltijdcheques_aantal=20,
)
# Verwacht resultaat (benadering):
# RSZ werknemer: 392,10 EUR (13,07%)
# Belastbaar: 2607,90 EUR
# BV: ~1115 EUR
# Werknemersbijdrage cheques: 21,80 EUR
# Netto: ~1471 EUR
```

### PRC batch validatie
```python
async def valideer_loonbatch(batch_id: str, repo: LoonRepository) -> BatchValidatieResultaat:
    lonen = await repo.get_batch(batch_id)
    vorige_maand = await repo.get_vorige_maand(batch_id)
    anomalies = []
    for loon in lonen:
        vorig = vorige_maand.get(loon.medewerker_id)
        if vorig:
            anomalies.extend(detect_anomalies(loon, vorig))
    return BatchValidatieResultaat(
        batch_id=batch_id,
        totaal=len(lonen),
        anomalies=anomalies,
        goedgekeurd=len([a for a in anomalies if a.prioriteit == "CRITICAL"]) == 0,
    )
```

## Gerelateerde skills
- belgian-commerce
- ddd-patterns
