---
name: mollie-payments
description: >
  Use when: integrating Mollie payment flow in VorstersNV, processing incoming webhooks,
  initiating refunds, verifying HMAC webhook signatures, debugging payment failures,
  or implementing idempotent webhook processing.
  Triggers: "mollie", "betaling", "webhook", "refund", "bancontact", "payment status",
  "checkout url", "hmac", "betalingslink", "mollie webhook", "terugbetaling"
---

# SKILL: Mollie Payments — VorstersNV

Alles over de Mollie betalingsintegratie binnen het VorstersNV platform: betalingsstatussen,
webhook verwerking (inclusief HMAC verificatie), refund flow, Belgische betaalmethoden en error handling.

## Payment Flow Pipeline

```
Order aangemaakt (VALIDATED status)
        │
        ▼
┌─────────────────────────┐
│  Fase 1: Betaling       │  ← POST /payments via Mollie API
│  Aanmaken               │    Bevat metadata: order_id, customer_id
└──────────┬──────────────┘
           │ checkout_url
           ▼
┌─────────────────────────┐
│  Fase 2: Klant Betaalt  │  ← Klant gaat naar checkout_url
│  (Mollie hosted page)   │    Kiest betaalmethode (Bancontact/iDEAL/CC)
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  Fase 3: Webhook        │  ← Mollie POST /webhook/mollie
│  Verwerking             │    Bevat alleen payment_id, NIET de status!
└──────────┬──────────────┘
           │ Haal status op via API
           ▼
┌─────────────────────────┐
│  Fase 4: Order Update   │  ← PAID → mark_paid() / FAILED → mark_payment_failed()
└─────────────────────────┘
```

## Wanneer gebruiken
- Bij order verwerking en betaling verificatie
- Bij het verwerken van inkomende Mollie webhooks
- Bij refund beslissingen en initiatie
- Bij het debuggen van betalingsproblemen
- Bij integratie van nieuwe betaalmethoden

## Kernkennis

### Betalingsstatussen
| Status      | Betekenis                                      |
|-------------|------------------------------------------------|
| `open`      | Aangemaakt, klant nog niet betaald             |
| `pending`   | In behandeling (bv. bankoverschrijving)        |
| `paid`      | Betaling geslaagd — order mag verwerkt worden  |
| `failed`    | Betaling mislukt — klant kan opnieuw proberen  |
| `expired`   | Verlopen zonder betaling (standaard: 15 min)   |
| `canceled`  | Klant heeft geannuleerd                        |
| `refunded`  | Volledig terugbetaald                          |

Enkel `paid` activeert de order verwerking. Alle andere terminale statussen (`failed`,
`expired`, `canceled`) zetten de order op `PAYMENT_FAILED`.

### Webhook verwerking
Webhooks zijn idempotent — dezelfde `payment_id` kan meerdere keren binnenkomen.

```python
@router.post("/webhook/mollie")
async def mollie_webhook(request: Request, db=Depends(get_db)) -> dict:
    form = await request.form()
    payment_id = form.get("id")
    if not payment_id:
        raise HTTPException(400, "Missing payment id")

    # Altijd opnieuw ophalen bij Mollie — nooit de webhook payload vertrouwen
    payment = mollie_client.payments.get(payment_id)
    order_id = payment.metadata.get("order_id")

    if payment.status == "paid":
        await OrderService(db).mark_paid(order_id)
    elif payment.status in ("failed", "expired", "canceled"):
        await OrderService(db).mark_payment_failed(order_id)

    return {"received": True}
```

**Retry logica**: Mollie herprobeert webhooks bij niet-200 response. Gebruik idempotency
keys om dubbele verwerking te voorkomen. Sla `processed_at` op per `payment_id`.

### HMAC Webhook Verificatie (VERPLICHT in productie)

Mollie biedt webhook signing via het `WEBHOOK_SECRET`. Verifieer elke inkomende webhook
**vóór** verdere verwerking:

```python
import hmac
import hashlib
from fastapi import Request, HTTPException

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

def verify_mollie_webhook(request_body: bytes, received_signature: str) -> bool:
    """
    Verifieer Mollie webhook HMAC-SHA256 handtekening.
    Header: X-Mollie-Signature (indien geconfigureerd via Mollie dashboard).
    """
    expected = hmac.new(
        key=WEBHOOK_SECRET.encode("utf-8"),
        msg=request_body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    # constant-time vergelijking — voorkomt timing attacks
    return hmac.compare_digest(expected, received_signature)

@router.post("/webhook/mollie")
async def mollie_webhook(request: Request, db=Depends(get_db)) -> dict:
    body = await request.body()
    signature = request.headers.get("X-Mollie-Signature", "")

    # Verificatie (skip in dev als WEBHOOK_SECRET leeg is)
    if WEBHOOK_SECRET and not verify_mollie_webhook(body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    form = await request.form()
    payment_id = form.get("id")
    if not payment_id:
        raise HTTPException(400, "Missing payment id")

    # Altijd opnieuw ophalen bij Mollie — nooit de webhook payload vertrouwen
    payment = mollie_client.payments.get(payment_id)
    order_id = payment.metadata.get("order_id")

    # Idempotency check — verwerk elk payment_id slechts één keer
    if await payment_repo.is_processed(payment_id):
        return {"received": True, "skipped": "already_processed"}

    if payment.status == "paid":
        await OrderService(db).mark_paid(order_id)
    elif payment.status in ("failed", "expired", "canceled"):
        await OrderService(db).mark_payment_failed(order_id)

    await payment_repo.mark_processed(payment_id)
    return {"received": True}
```

### Refund flow
Terugbetaling initiëren via Mollie API:

```python
refund = mollie_client.payment_refunds.with_parent_id(payment_id).create({
    "amount": {"currency": "EUR", "value": "29.99"},
    "description": "Retour order #1234"
})
```

Wanneer terugbetaling initiëren:
- Klant heeft herroepingsrecht ingeroepen binnen 14 dagen
- Product niet op voorraad na betaling
- Fraude bevestigd na betaling
- Dubbele betaling gedetecteerd

Refund statussen: `queued` → `pending` → `refunded` (of `failed`)

### Mollie API endpoints
| Endpoint                          | Gebruik                            |
|-----------------------------------|------------------------------------|
| `POST /payments`                  | Nieuwe betaling aanmaken           |
| `GET /payments/{id}`              | Status ophalen                     |
| `POST /payments/{id}/refunds`     | Terugbetaling initiëren            |
| `GET /payments/{id}/refunds`      | Terugbetalingen ophalen            |
| `POST /orders`                    | Mollie Orders API (alternatief)    |

### Belgische specifics
| Betaalmethode | Regio           | Opmerkingen                         |
|---------------|-----------------|-------------------------------------|
| Bancontact    | België          | Meest gebruikte methode in BE       |
| iDEAL         | Nederland       | Voor NL-klanten                     |
| Creditcard    | Internationaal  | Visa, Mastercard, Amex              |
| SEPA transfer | EU              | Langzaam (2-3 dagen), status pending|
| Klarna        | BE/NL           | Buy now, pay later                  |

### Error handling
| Fout                        | Aanpak                                                    |
|-----------------------------|-----------------------------------------------------------|
| Netwerk timeout             | Exponential backoff, max 3 pogingen                       |
| Dubbele webhook             | Check `processed_at` — skip indien al verwerkt           |
| `payment_id` niet gevonden  | Log warning, return 200 (Mollie stopt anders met retries) |
| Ongeldige API key           | Alert naar ops-team, order in HOLD zetten                 |
| Bedrag mismatch             | Fraud alert + manual review                               |

**Belangrijk**: Altijd HTTP 200 terugsturen naar Mollie, ook bij interne fouten —
anders blijft Mollie herprobeeren en raken webhooks uit sync.

## Voorbeelden

### Betaling aanmaken
```python
payment = mollie_client.payments.create({
    "amount": {"currency": "EUR", "value": "49.99"},
    "description": "Order #1234 - VorstersNV",
    "redirectUrl": f"{settings.BASE_URL}/orders/1234/status",
    "webhookUrl": f"{settings.BASE_URL}/webhook/mollie",
    "method": "bancontact",
    "metadata": {"order_id": "1234", "customer_id": "567"}
})
return {"checkout_url": payment.checkout_url}
```

### Status check in service
```python
async def verify_payment(self, order_id: str) -> bool:
    order = await self.repo.get(order_id)
    payment = mollie_client.payments.get(order.mollie_payment_id)
    return payment.status == "paid"
```

## Voorbeeld Gebruik

### Scenario: Klant bestelt Bancontact (€49,99)

**Stap 1 — Betaling aanmaken (in OrderService):**
```python
# api/services/payment_service.py
async def create_payment(self, order: Order) -> dict:
    payment = mollie_client.payments.create({
        "amount": {"currency": "EUR", "value": f"{order.total:.2f}"},
        "description": f"Order #{order.id} - VorstersNV",
        "redirectUrl": f"{settings.BASE_URL}/orders/{order.id}/bevestiging",
        "webhookUrl": f"{settings.BASE_URL}/webhook/mollie",
        "method": "bancontact",
        "metadata": {
            "order_id": str(order.id),
            "customer_id": str(order.customer_id),
        }
    })
    order.mollie_payment_id = payment.id
    return {"checkout_url": payment.checkout_url}
    # Voorbeeld checkout_url: https://www.mollie.com/checkout/bancontact/select/...
```

**Stap 2 — Webhook ontvangen (async, na betaling):**
```
POST /webhook/mollie
Content-Type: application/x-www-form-urlencoded
X-Mollie-Signature: abc123...

id=tr_WDqYK6vllg
```

**Stap 3 — Webhook verwerken:**
```python
# Haal betaling op via Mollie API (NIET uit de webhook body)
payment = mollie_client.payments.get("tr_WDqYK6vllg")
# payment.status = "paid"
# payment.metadata = {"order_id": "1234", "customer_id": "567"}

# Update order
await OrderService(db).mark_paid("1234")
# Order status: PAYMENT_PENDING → PAID
# Event: OrderPaid gepubliceerd
```

**Stap 4 — Refund na retour:**
```python
# Klant retourneert product binnen 14 dagen
refund = mollie_client.payment_refunds.with_parent_id("tr_WDqYK6vllg").create({
    "amount": {"currency": "EUR", "value": "49.99"},
    "description": f"Retour order #1234 — VorstersNV herroepingsrecht"
})
# refund.status: queued → pending → refunded
```

## Anti-patronen

| ❌ NIET | ✅ WEL |
|---------|-------|
| Status uitlezen uit webhook body | Status ophalen via `mollie_client.payments.get(id)` |
| HTTP 500 terugsturen bij interne fout | Altijd HTTP 200 — anders blijft Mollie herprobeeren |
| Webhook body vertrouwen zonder verificatie | HMAC handtekening verifiëren via `X-Mollie-Signature` |
| Zelfde payment_id twee keer verwerken | Idempotency check vóór verwerking |
| `live_` key in `.env.example` committen | Nooit live keys in versiecontrole |
| Kaartnummer of IBAN opslaan | Enkel `mollie_id`, `status`, `bedrag` bewaren |

## Gerelateerde skills
- order-lifecycle
- fraud-patterns
- belgian-commerce
- mollie-checkout-validator
