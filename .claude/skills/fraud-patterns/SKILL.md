---
name: fraud-patterns
description: >
  Use when: assessing fraud risk on VorstersNV orders, calculating risk scores,
  implementing velocity checks, evaluating device fingerprinting signals,
  designing the fraude_detectie_agent pipeline, or debugging blocked orders.
  Triggers: "fraud", "risicoscore", "velocity check", "fraude detectie",
  "fraude blokkering", "device fingerprint", "fraude agent", "risicobeoordeling"
---

# SKILL: Fraud Detection Patterns — VorstersNV

Referentiekennis voor fraude-detectie in het VorstersNV e-commerce platform:
risicoscores, red flags, velocity checks, device fingerprinting en GDPR-conforme
opslag van signalen via de `fraude_detectie_agent` (Ollama/mistral).

## Pipeline Overzicht

```
Nieuwe Order ontvangen
        │
        ▼
┌─────────────────────┐
│  Fase 1: Context    │  ← IP, user-agent, account-leeftijd, chargeback-history
│  Verzamelen         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Fase 2: Risk Score │  ← Weeg alle red flags op (score 0-100)
│  Berekenen          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Fase 3: Beslissing │  ← APPROVE / REVIEW / BLOCK
└──────────┬──────────┘
           │
       ┌───┴───┐
       ▼       ▼
  Goedkeuren  Blokkeren / Escaleren naar fraud-team
```

## Wanneer gebruiken
- Voor elke nieuwe order — altijd een risicoscore berekenen
- Bij hoge bedragen (> 200 EUR)
- Bij nieuwe accounts (< 30 dagen oud)
- Bij afwijkende geo-locatie of VPN-gebruik
- Bij meerdere betalingspogingen in korte tijd
- Bij implementatie of verbetering van `fraude_detectie_agent.yml`

## Kernkennis

### Risicoscores
| Score   | Niveau  | Actie                                        |
|---------|---------|----------------------------------------------|
| 0–30    | Laag    | Automatisch goedkeuren                       |
| 31–74   | Medium  | Extra validatie of handmatige review         |
| 75+     | Hoog    | Automatisch blokkeren, alert naar fraud-team |

Score is een gewogen som van alle actieve risicofactoren.

### Red flags en gewichten
| Factor                              | Gewicht | Beschrijving                               |
|-------------------------------------|---------|--------------------------------------------|
| VPN / Tor gebruik                   | +35     | IP gematched met VPN/Tor exitnode-lijst    |
| Nieuw account + hoog bedrag         | +30     | Account < 7 dagen + order > 150 EUR        |
| Meerdere chargebacks (>2)           | +40     | In laatste 90 dagen                        |
| Land-mismatch billing/IP            | +25     | Facturatieadres ≠ IP-land                  |
| Hoge velocity (> 3 orders/uur)      | +45     | Zelfde IP of device fingerprint            |
| Wegwerp e-maildomein                | +20     | mailinator, yopmail, tempmail, etc.        |
| Mislukte betalingen (>2 in 24u)     | +25     | Zelfde klant of IP                         |
| Eerste order > 500 EUR              | +20     | Statistisch hoger risico                   |
| Bezorgadres ≠ facturatieadres       | +10     | Licht verhoogd risico                      |

### Velocity checks
```python
VELOCITY_RULES = {
    "orders_per_hour_ip": {"threshold": 3, "weight": 45},
    "orders_per_day_customer": {"threshold": 10, "weight": 20},
    "failed_payments_24h": {"threshold": 2, "weight": 25},
    "different_cards_24h": {"threshold": 3, "weight": 30},
}

async def check_velocity(ip: str, customer_id: str, window_hours: int = 1) -> int:
    count = await redis.zcount(f"orders:ip:{ip}", now - window_hours*3600, now)
    if count > VELOCITY_RULES["orders_per_hour_ip"]["threshold"]:
        return VELOCITY_RULES["orders_per_hour_ip"]["weight"]
    return 0
```

### Device fingerprinting indicatoren
Verdachte combinaties:
- User-agent inconsistent met OS (bv. iOS UA op Windows device)
- Canvas fingerprint overeenkomst met eerder geblokkeerde sessie
- WebRTC IP verschilt van HTTP IP (VPN-indicatie)
- Headless browser kenmerken (Selenium/Puppeteer signaturen)
- Timezone mismatch met IP-locatie (> 2u verschil)

### Beslisboom score berekening
```python
def calculate_risk_score(order: Order, context: FraudContext) -> int:
    score = 0
    if context.is_vpn:
        score += 35
    if context.account_age_days < 7 and order.total > 150:
        score += 30
    if context.chargeback_count > 2:
        score += 40
    if context.country_mismatch:
        score += 25
    velocity_score = check_velocity(context.ip, order.customer_id)
    score += velocity_score
    return min(score, 100)  # cap op 100

def make_decision(score: int) -> FraudDecision:
    if score >= 75:
        return FraudDecision.BLOCK
    if score >= 31:
        return FraudDecision.REVIEW
    return FraudDecision.APPROVE
```

### GDPR beperkingen
- **IP-adressen**: maximaal 24u in operationele logs, daarna hashen of verwijderen
- **Device fingerprints**: maximaal 90 dagen bewaren, geen koppeling aan persoon
- **Fraud signals**: geanonimiseerd bewaren voor model-training
- **Geblokkeerde klanten**: aparte database, apart retentiebeleid (max 3 jaar)
- Geen raw IP-adressen in analytics-exports

## Voorbeelden

### Volledige fraud check in order flow
```python
async def process_new_order(order: Order, request: Request) -> OrderResult:
    context = FraudContext(
        ip=request.client.host,
        user_agent=request.headers.get("user-agent"),
        account_age_days=(datetime.now() - order.customer.created_at).days,
        chargeback_count=await repo.get_chargeback_count(order.customer_id),
        country_mismatch=order.billing_country != geoip.country(request.client.host),
        is_vpn=await vpn_checker.check(request.client.host),
    )
    score = calculate_risk_score(order, context)
    decision = make_decision(score)

    await fraud_log.record(order.id, score, decision, context)  # GDPR-safe

    if decision == FraudDecision.BLOCK:
        raise FraudBlockedException(f"Order geblokkeerd, risicoscore: {score}")
    if decision == FraudDecision.REVIEW:
        await notify_fraud_team(order.id, score)

    return await continue_order_processing(order)
```

### Fraud event
```python
@dataclass
class FraudDetected:
    order_id: str
    risk_score: int
    triggered_rules: list[str]
    decision: str  # BLOCK | REVIEW
    timestamp: datetime = field(default_factory=datetime.now)
```

## Fase 4: GDPR-conforme Logging

```python
@dataclass
class FraudAuditLog:
    """GDPR-safe: geen raw PII in fraud logs."""
    order_id: str
    risk_score: int
    decision: str           # APPROVE | REVIEW | BLOCK
    triggered_rules: list[str]
    ip_hash: str            # SHA-256(IP) — niet het raw IP!
    device_fingerprint_hash: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    # NIET opslaan: email, naam, kaartnummer, raw IP

async def log_fraud_decision(
    order_id: str, score: int, decision: str,
    context: FraudContext, repo: FraudLogRepository
) -> None:
    log = FraudAuditLog(
        order_id=order_id,
        risk_score=score,
        decision=decision,
        triggered_rules=context.triggered_rules,
        ip_hash=hashlib.sha256(context.ip.encode()).hexdigest(),
        device_fingerprint_hash=hashlib.sha256(
            context.fingerprint.encode()
        ).hexdigest(),
    )
    await repo.save(log)
```

**GDPR beperkingen:**
- **IP-adressen**: maximaal 24u in operationele logs, daarna hashen of verwijderen
- **Device fingerprints**: maximaal 90 dagen bewaren, geen koppeling aan persoon
- **Fraud signals**: geanonimiseerd bewaren voor model-training
- **Geblokkeerde klanten**: aparte database, apart retentiebeleid (max 3 jaar)

## Voorbeeld Gebruik

### Input: Nieuwe order met verdacht profiel
```python
# Order: 320 EUR, account aangemaakt 3 dagen geleden, IP uit VPN
context = FraudContext(
    ip="185.220.101.45",      # Tor exit node
    user_agent="Mozilla/5.0",
    account_age_days=3,
    chargeback_count=0,
    country_mismatch=True,    # IP = NL, billing = BE
    is_vpn=True,
)
order = Order(total=Decimal("320.00"), customer_id="cust_789")
```

### Output: Fraud pipeline resultaat
```python
score = calculate_risk_score(order, context)
# VPN: +35, nieuw account + hoog bedrag: +30, country mismatch: +25
# score = 90 → BLOCK

decision = make_decision(score)
# FraudDecision.BLOCK

# Gevolg:
# 1. Order → status FRAUD_BLOCKED
# 2. FraudDetected event gepubliceerd
# 3. Fraud team krijgt alert
# 4. Klant ziet generieke foutmelding (geen reden opgeven!)
```

### Volledige integratie in order flow
```python
async def process_new_order(order: Order, request: Request) -> OrderResult:
    context = FraudContext(
        ip=request.client.host,
        user_agent=request.headers.get("user-agent"),
        account_age_days=(datetime.now() - order.customer.created_at).days,
        chargeback_count=await repo.get_chargeback_count(order.customer_id),
        country_mismatch=order.billing_country != geoip.country(request.client.host),
        is_vpn=await vpn_checker.check(request.client.host),
    )
    score = calculate_risk_score(order, context)
    decision = make_decision(score)

    await log_fraud_decision(order.id, score, str(decision), context, fraud_repo)

    if decision == FraudDecision.BLOCK:
        transition(order, OrderStatus.FRAUD_BLOCKED)
        await repo.save(order)
        raise FraudBlockedException(f"Order geblokkeerd, risicoscore: {score}")
    if decision == FraudDecision.REVIEW:
        await notify_fraud_team(order.id, score)

    return await continue_order_processing(order)
```

### Fraud event voor event bus
```python
@dataclass
class FraudDetected:
    order_id: str
    risk_score: int
    triggered_rules: list[str]
    decision: str  # BLOCK | REVIEW
    timestamp: datetime = field(default_factory=datetime.now)
```

## Anti-patronen

| ❌ NIET | ✅ WEL |
|---------|-------|
| Raw IP opslaan in fraud log | SHA-256(IP) hash opslaan |
| Reden tonen aan klant bij blokkering | Generieke "fout" melding tonen |
| `score >= 50` als blokkeerdrempel | Score ≥ 75 = BLOCK (te veel false positives bij lager) |
| Fraud check skippen bij bekende klant | Altijd fraud check, ook bij terugkerende klanten |
| Fraud check synchroon in webhook | Asynchroon vóór betalingslink aanmaken |
| Chargeback-count uit cache | Altijd fresh uit DB (race conditions bij cache) |

## Gerelateerde skills
- order-lifecycle
- mollie-payments
- belgian-commerce
