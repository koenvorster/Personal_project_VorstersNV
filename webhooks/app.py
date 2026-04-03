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
from datetime import datetime
from typing import Optional

from .handlers import order_handler, payment_handler, inventory_handler

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
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


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
    """Ontvang feedback op agent-output voor prompt-iteratie."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Ongeldige JSON payload")
    agent_name = payload.get("agent")
    rating = payload.get("rating")
    feedback = payload.get("feedback")
    logger.info("Agent feedback ontvangen: agent=%s rating=%s", agent_name, rating)
    # Sla feedback op voor prompt-iteratie analyse
    feedback_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "agent": agent_name,
        "rating": rating,
        "feedback": feedback,
        "prompt_version": payload.get("prompt_version"),
    }
    # In productie: sla op in database of analyseer direct
    return JSONResponse(content={"status": "ontvangen", "entry": feedback_entry})
