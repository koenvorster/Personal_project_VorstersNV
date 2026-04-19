---
mode: agent
description: Implementeer een complete Mollie checkout flow voor VorstersNV, van winkelwagen tot betalingsbevestiging.
---

# Mollie Checkout Flow Implementatie

Implementeer een complete, productieklare checkout flow met Mollie voor VorstersNV.

## Flow Overzicht

```
Winkelwagen → Klantgegevens → Betaallink → Mollie → Webhook → Bevestiging
```

## Stap 1: Checkout API Endpoint (`api/routers/checkout.py`)

```python
@router.post("/checkout", response_model=CheckoutResponse)
async def start_checkout(
    cart: CartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CheckoutResponse:
    # 1. Valideer stock voor elk cart-item
    # 2. Maak Order aan in DB (status: AANGEMAAKT)
    # 3. Fraudecheck via fraude_detectie_agent
    # 4. Maak Mollie betaling aan
    # 5. Return checkout_url
```

## Stap 2: Mollie Betaling Aanmaken

```python
from mollie.api.client import Client

def get_mollie_client() -> Client:
    client = Client()
    client.set_api_key(settings.mollie_api_key)
    return client

async def create_mollie_payment(order: Order) -> tuple[str, str]:
    """Returns (checkout_url, mollie_payment_id)"""
    client = get_mollie_client()
    payment = client.payments.create({
        "amount": {"currency": "EUR", "value": f"{order.totaal:.2f}"},
        "description": f"VorstersNV #{order.id}",
        "redirectUrl": f"{settings.base_url}/bestelling/{order.id}/bevestiging",
        "webhookUrl": f"{settings.base_url}/webhooks/mollie",
        "metadata": {"order_id": str(order.id)},
        "method": ["ideal", "creditcard", "bancontact"],  # Belgisch relevante methodes
    })
    return payment.checkout_url, payment.id
```

## Stap 3: Webhook Handler (`webhooks/handlers/payment_handler.py`)

```python
async def handle_mollie_webhook(payment_id: str, db: AsyncSession) -> None:
    client = get_mollie_client()
    payment = client.payments.get(payment_id)
    
    # Update Payment record
    await update_payment_status(db, payment.id, payment.status)
    
    if payment.is_paid():
        await update_order_status(db, payment.metadata["order_id"], "BETAALD")
        await decrease_stock_atomic(db, order_id)
        await send_confirmation_email(order_id)  # via email_template_agent
    elif payment.is_failed() or payment.is_expired():
        await update_order_status(db, payment.metadata["order_id"], "GEANNULEERD")
        await restore_reserved_stock(db, order_id)
```

## Stap 4: Frontend Checkout (`frontend/app/(shop)/afrekenen/page.tsx`)

```tsx
"use client";
export default function AfrekenenPage() {
  const cart = useCartStore((s) => s.items);
  
  async function handleCheckout(klantgegevens: KlantgegevensForm) {
    const res = await fetch("/api/checkout", {
      method: "POST",
      body: JSON.stringify({ cart, klantgegevens }),
    });
    const { checkout_url } = await res.json();
    window.location.href = checkout_url; // redirect naar Mollie
  }
  
  return <CheckoutForm onSubmit={handleCheckout} />;
}
```

## Stap 5: Bevestigingspagina

```tsx
// app/(shop)/bestelling/[id]/bevestiging/page.tsx
export default async function BevestigingPage({ params }: Props) {
  const order = await getOrder(params.id);  // Server Component
  if (order.status !== "BETAALD") redirect("/afrekenen"); // nog niet betaald
  return <OrderBevestiging order={order} />;
}
```

## Checklist
- [ ] HMAC webhook verificatie actief
- [ ] Idempotente webhook handler (dubbele calls veilig)
- [ ] Stock-verlaging atomisch (database transaction)
- [ ] Bevestigingsmail via `email_template_agent`
- [ ] Test met Mollie test-mode API key
- [ ] E2E test via `@playwright-mcp`
