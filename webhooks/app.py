"""
VorstersNV Webhook Handlers
FastAPI applicatie voor het ontvangen en verwerken van webhooks.
"""
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from .handlers import order_handler, payment_handler, inventory_handler, mollie_handler

logger = logging.getLogger(__name__)

app = FastAPI(
    title="VorstersNV Webhook Service",
    description="Webhook handlers voor VorstersNV webshop events",
    version="1.0.0",
)

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verifieer de HMAC-SHA256 handtekening van een webhook."""
    if not secret:
        return True
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# ── Order webhooks ──────────────────────────────────────────────────────────

@app.post("/webhooks/order-created")
async def webhook_order_created(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
):
    """Verwerk een 'order aangemaakt' event."""
    body = await request.body()
    if x_webhook_signature and not verify_signature(body, x_webhook_signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Ongeldige handtekening")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Ongeldige JSON payload")
    logger.info("Order aangemaakt: %s", payload.get("order_id"))
    result = await order_handler.handle_order_created(payload)
    return JSONResponse(content=result, status_code=200)


@app.post("/webhooks/order-paid")
async def webhook_order_paid(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
):
    """Verwerk een 'order betaald' event."""
    body = await request.body()
    if x_webhook_signature and not verify_signature(body, x_webhook_signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Ongeldige handtekening")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Ongeldige JSON payload")
    logger.info("Order betaald: %s", payload.get("order_id"))
    result = await payment_handler.handle_payment_confirmed(payload)
    return JSONResponse(content=result, status_code=200)


@app.post("/webhooks/order-shipped")
async def webhook_order_shipped(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
):
    """Verwerk een 'order verzonden' event."""
    body = await request.body()
    if x_webhook_signature and not verify_signature(body, x_webhook_signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Ongeldige handtekening")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Ongeldige JSON payload")
    logger.info("Order verzonden: %s", payload.get("order_id"))
    result = await order_handler.handle_order_shipped(payload)
    return JSONResponse(content=result, status_code=200)


@app.post("/webhooks/order-returned")
async def webhook_order_returned(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
):
    """Verwerk een 'retour ontvangen' event."""
    body = await request.body()
    if x_webhook_signature and not verify_signature(body, x_webhook_signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Ongeldige handtekening")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Ongeldige JSON payload")
    logger.info("Retour ontvangen: %s", payload.get("order_id"))
    result = await order_handler.handle_order_returned(payload)
    return JSONResponse(content=result, status_code=200)


# ── Voorraad webhooks ───────────────────────────────────────────────────────

@app.post("/webhooks/stock-low")
async def webhook_stock_low(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
):
    """Verwerk een 'lage voorraad' melding."""
    body = await request.body()
    if x_webhook_signature and not verify_signature(body, x_webhook_signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Ongeldige handtekening")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Ongeldige JSON payload")
    logger.warning("Lage voorraad: product %s", payload.get("product_id"))
    result = await inventory_handler.handle_low_stock(payload)
    return JSONResponse(content=result, status_code=200)


# ── Agent feedback webhooks ─────────────────────────────────────────────────

@app.post("/webhooks/agent-feedback")
async def webhook_agent_feedback(request: Request):
    """
    Ontvang feedback op agent-output en sla op via PromptIterator.

    Verwachte payload:
        agent: naam van de agent (bv. klantenservice_agent)
        interaction_id: ID teruggegeven door de agent run
        rating: beoordeling 1-5
        feedback: optionele tekst
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Ongeldige JSON payload")

    agent_name = payload.get("agent")
    interaction_id = payload.get("interaction_id")
    rating = payload.get("rating")
    feedback_tekst = payload.get("feedback", "")

    if not agent_name:
        raise HTTPException(status_code=400, detail="'agent' veld is verplicht")
    if rating is None or not (1 <= int(rating) <= 5):
        raise HTTPException(status_code=400, detail="'rating' moet een getal tussen 1 en 5 zijn")

    logger.info("Agent feedback ontvangen: agent=%s rating=%s", agent_name, rating)

    # Koppel feedback aan de interactie via PromptIterator
    from ollama.prompt_iterator import PromptIterator
    iterator = PromptIterator(agent_name)

    saved = False
    if interaction_id:
        saved = iterator.add_feedback(
            interaction_id=interaction_id,
            rating=int(rating),
            notes=feedback_tekst,
        )

    # Analyseer feedback en log eventuele verbeterpunten
    analyse = iterator.analyse_feedback()
    if analyse.get("gemiddelde_score", 5) < 3.0:
        logger.warning(
            "Lage gemiddelde score voor agent '%s': %.2f – prompt-iteratie aanbevolen.",
            agent_name,
            analyse["gemiddelde_score"],
        )

    return JSONResponse(content={
        "status": "ontvangen",
        "agent": agent_name,
        "rating": rating,
        "feedback_opgeslagen": saved,
        "huidige_analyse": analyse,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ── Mollie betalingen (B3) ──────────────────────────────────────────────────

@app.post("/webhooks/mollie")
async def webhook_mollie(request: Request):
    """
    Verwerk Mollie betaal-statuswijziging webhooks.

    Mollie POST-t enkel het payment ID (form-encoded: id=tr_xxxxx).
    Authenticatie via Mollie API zelf (we halen de status op met API key).
    Zie: https://docs.mollie.com/docs/webhooks
    """
    try:
        form = await request.form()
        payment_id = form.get("id", "")
    except Exception:
        # Fallback: probeer JSON body
        try:
            body = await request.json()
            payment_id = body.get("id", "")
        except Exception:
            raise HTTPException(status_code=400, detail="Ongeldige Mollie webhook payload")

    if not payment_id:
        raise HTTPException(status_code=400, detail="Mollie payment ID ontbreekt in webhook")

    logger.info("Mollie webhook ontvangen: payment_id=%s", payment_id)
    result = await mollie_handler.handle_mollie_payment_webhook(payment_id)
    return JSONResponse(content=result, status_code=200)
