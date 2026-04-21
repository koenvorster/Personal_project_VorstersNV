---
name: mollie-checkout-validator
description: >
  Use when: validating Mollie checkout flows in VorstersNV, verifying HMAC webhook signatures,
  auditing payment security, checking idempotency handling, or debugging checkout issues.
  Triggers: "mollie checkout", "hmac verificatie", "webhook signature", "checkout valideren",
  "mollie security", "idempotency", "betalingsflow audit"
---

# SKILL: Mollie Checkout Validator — VorstersNV

Security- en correctheidsvalidatie voor de Mollie checkout flow in VorstersNV.
Gebruik deze skill om bestaande implementaties te auditen of nieuwe flows te reviewen.

## Validatie Pipeline

```
Mollie Checkout Flow
        │
        ▼
┌──────────────────────────┐
│  Fase 1: Betaling        │  ← Controleer aanmaakvelden, metadata, webhookUrl
│  Aanmaken (POST)         │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Fase 2: Webhook         │  ← HMAC verificatie, body parsing, idempotency
│  Ontvangst               │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Fase 3: Status Ophalen  │  ← Nooit uit body, altijd fresh via Mollie API
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Fase 4: Order Update    │  ← Atomaire status-update + event publishing
└──────────────────────────┘
```

## Security Audit Checklist

### ✅ HMAC Verificatie

```python
import hmac
import hashlib
import os

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

class MollieWebhookVerifier:
    """HMAC-SHA256 verificatie voor inkomende Mollie webhooks."""

    @staticmethod
    def verify(request_body: bytes, received_signature: str) -> bool:
        if not WEBHOOK_SECRET:
            return True  # Skip in dev (WEBHOOK_SECRET leeg)
        expected = hmac.new(
            key=WEBHOOK_SECRET.encode("utf-8"),
            msg=request_body,
            digestmod=hashlib.sha256,
        ).hexdigest()
        # constant-time vergelijking — voorkomt timing attacks!
        return hmac.compare_digest(expected, received_signature)
```

**Controleer:**
- [ ] `hmac.compare_digest()` gebruikt (NIET `==`)
- [ ] `WEBHOOK_SECRET` via environment variable (nooit hardcoded)
- [ ] Body gelezen VÓÓR form-parsing (body is anders leeg)
- [ ] HTTP 401 bij ongeldige signature

### ✅ Idempotency Check

```python
import redis.asyncio as redis

class PaymentIdempotencyChecker:
    """Voorkom dubbele verwerking van hetzelfde payment_id."""

    def __init__(self, redis_client):
        self._redis = redis_client

    async def is_processed(self, payment_id: str) -> bool:
        return await self._redis.exists(f"processed_payment:{payment_id}") == 1

    async def mark_processed(self, payment_id: str, ttl_seconds: int = 86400) -> None:
        # 24u bewaren — Mollie herprobeert max 24u
        await self._redis.setex(f"processed_payment:{payment_id}", ttl_seconds, "1")
```

**Controleer:**
- [ ] Idempotency check VOOR `mark_paid()` / `mark_failed()`
- [ ] Redis TTL ingesteld (24u = 86400s)
- [ ] Return `200 OK` ook als al verwerkt (anders blijft Mollie herprobeeren)

### ✅ Checkout URL Aanmaken

```python
# GOED — alle verplichte velden aanwezig
payment = mollie_client.payments.create({
    "amount": {
        "currency": "EUR",
        "value": f"{order.total:.2f}",   # ← 2 decimalen verplicht! "49.99" niet "49.9"
    },
    "description": f"Order #{order.id} - VorstersNV",
    "redirectUrl": f"{settings.BASE_URL}/orders/{order.id}/bevestiging",
    "webhookUrl": f"{settings.BASE_URL}/api/webhook/mollie",
    "method": "bancontact",              # ← optioneel; weglaten = klant kiest zelf
    "metadata": {
        "order_id": str(order.id),       # ← ALTIJD meesturen voor koppeling
        "customer_id": str(order.customer_id),
    },
    "locale": "nl_BE",                   # ← Belgisch (nl_BE / fr_BE)
})
```

**Controleer:**
- [ ] `amount.value` exact 2 decimalen (Mollie vereist dit)
- [ ] `metadata.order_id` aanwezig (koppeling bij webhook)
- [ ] `webhookUrl` verwijst naar interne API, niet frontend
- [ ] `redirectUrl` verwijst naar bevestigingspagina (na betaling)
- [ ] `locale` ingesteld op `nl_BE` of `fr_BE`

### ✅ Webhook Handler

```python
@router.post("/webhook/mollie")
async def mollie_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    idempotency: PaymentIdempotencyChecker = Depends(get_idempotency),
) -> dict:
    # 1. Lees body EERST (vóór form-parsing)
    body = await request.body()

    # 2. HMAC verificatie
    signature = request.headers.get("X-Mollie-Signature", "")
    if not MollieWebhookVerifier.verify(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 3. Payment ID ophalen
    form = await request.form()
    payment_id = form.get("id")
    if not payment_id:
        return {"received": True}  # Lege webhook — negeer

    # 4. Idempotency check
    if await idempotency.is_processed(payment_id):
        return {"received": True, "skipped": "already_processed"}

    # 5. Status ophalen via Mollie API (NOOIT uit webhook body)
    payment = mollie_client.payments.get(payment_id)
    order_id = payment.metadata.get("order_id")

    # 6. Order updaten
    if payment.status == "paid":
        await OrderService(db).mark_paid(order_id)
    elif payment.status in ("failed", "expired", "canceled"):
        await OrderService(db).mark_payment_failed(order_id)

    # 7. Markeer als verwerkt
    await idempotency.mark_processed(payment_id)

    # 8. Altijd 200 OK terugsturen (ook bij interne fouten — zie anti-patronen)
    return {"received": True}
```

## Security Audit Checklist (15 punten)

| # | Check | Resultaat |
|---|-------|-----------|
| 1 | `hmac.compare_digest()` gebruikt | ✅ / ❌ |
| 2 | `WEBHOOK_SECRET` via `os.getenv()` | ✅ / ❌ |
| 3 | Body gelezen vóór form-parsing | ✅ / ❌ |
| 4 | HTTP 401 bij ongeldige signature | ✅ / ❌ |
| 5 | Idempotency check aanwezig | ✅ / ❌ |
| 6 | Redis TTL ingesteld op idempotency key | ✅ / ❌ |
| 7 | Status opgehaald via Mollie API (niet webhook body) | ✅ / ❌ |
| 8 | `metadata.order_id` aanwezig bij betaling aanmaken | ✅ / ❌ |
| 9 | `amount.value` met exact 2 decimalen | ✅ / ❌ |
| 10 | `webhookUrl` verwijst naar `/api/webhook/mollie` | ✅ / ❌ |
| 11 | HTTP 200 teruggestuurd bij interne fout | ✅ / ❌ |
| 12 | Live API key nooit in `.env.example` of git | ✅ / ❌ |
| 13 | `locale` ingesteld (`nl_BE` / `fr_BE`) | ✅ / ❌ |
| 14 | Lege `payment_id` webhook wordt genegeerd (geen error) | ✅ / ❌ |
| 15 | Order status atomair bijgewerkt (geen race condition) | ✅ / ❌ |

## Voorbeeld Gebruik

### Input: Audit een bestaande webhook handler
```
"Controleer onze Mollie webhook implementatie op security-risico's"
"Klopt onze HMAC verificatie?"
"Hoe voorkomen we dubbele verwerking van webhooks?"
```

### Output: Audit rapport
```
🔍 Mollie Checkout Audit — VorstersNV
═══════════════════════════════════════

✅ HMAC verificatie aanwezig (hmac.compare_digest)
✅ WEBHOOK_SECRET via os.getenv()
❌ Body gelezen NADAT form-parsing — signature kan niet geverifieerd worden!
   Fix: `body = await request.body()` VOOR `await request.form()`
✅ Idempotency Redis check aanwezig
❌ TTL ontbreekt op idempotency key — Redis geheugen lekt!
   Fix: gebruik `setex` met 86400 seconden
⚠️  locale niet ingesteld — klant krijgt Engelse Mollie pagina

Score: 12/15 checks geslaagd
Kritieke issues: 1 (body parsing volgorde)
Aanbevelingen: 2
```

## Troubleshooting

| Symptoom | Oorzaak | Oplossing |
|----------|---------|-----------|
| HMAC verificatie faalt altijd | Body is leeg door vroege form-parsing | Lees `body = await request.body()` VOOR `await request.form()` |
| Webhook wordt meerdere keren verwerkt | Geen idempotency check | Voeg Redis-gebaseerde idempotency toe |
| Mollie blijft webhooks sturen | Webhook geeft HTTP 500 | Altijd HTTP 200 terugsturen, ook bij interne fout |
| `payment.metadata` is leeg | `metadata` niet meegegeven bij aanmaken | Voeg `metadata: {"order_id": str(order.id)}` toe aan payments.create() |
| Betaling aangemaakt maar order niet gevonden | Race condition bij snelle webhook | Gebruik `SELECT FOR UPDATE` of retry mechanisme |

## Gerelateerde skills
- mollie-payments
- order-lifecycle
- fraud-patterns
