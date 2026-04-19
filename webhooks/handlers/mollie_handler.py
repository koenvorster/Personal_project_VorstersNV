"""
VorstersNV Mollie Webhook Handler
Verwerkt inkomende Mollie betaalstatussen (klaar voor Fase B3).

Mollie stuurt bij elke statuswijziging een POST naar /webhooks/mollie
met alleen het payment ID. De handler haalt vervolgens de volledige
betaalstatus op via de Mollie API en triggert de juiste agent pipeline.

Documentatie: https://docs.mollie.com/docs/webhooks
"""
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

MOLLIE_API_KEY = os.environ.get("MOLLIE_API_KEY", "")
MOLLIE_API_BASE = "https://api.mollie.com/v2"


async def fetch_payment_from_mollie(payment_id: str) -> dict[str, Any] | None:
    """
    Haal de betaalstatus op via de Mollie API.

    Args:
        payment_id: Het Mollie payment ID (bijv. "tr_WDqYK6vAhe")

    Returns:
        Mollie payment object als dict, of None bij fout.
    """
    if not MOLLIE_API_KEY:
        logger.error(
            "MOLLIE_API_KEY niet geconfigureerd — kan Mollie payment niet ophalen. "
            "Stel de MOLLIE_API_KEY omgevingsvariabele in."
        )
        return None

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{MOLLIE_API_BASE}/payments/{payment_id}",
                headers={"Authorization": f"Bearer {MOLLIE_API_KEY}"},
            )
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        logger.error("Fout bij ophalen Mollie payment %s: %s", payment_id, exc)
        return None


async def handle_mollie_payment_webhook(payment_id: str) -> dict[str, Any]:
    """
    Verwerk een Mollie webhook notificatie.

    Mollie stuurt enkel het payment_id. Dit is de entry point die:
    1. De volledige betaalstatus ophaalt bij Mollie
    2. De juiste handler aanroept op basis van de status
    3. De juiste agent pipeline triggert

    Args:
        payment_id: Het Mollie payment ID uit de webhook body

    Returns:
        Verwerkingsresultaat als dict
    """
    logger.info("Mollie webhook ontvangen: payment_id=%s", payment_id)

    payment = await fetch_payment_from_mollie(payment_id)
    if payment is None:
        return {
            "status": "fout",
            "payment_id": payment_id,
            "reden": "Kon betaling niet ophalen bij Mollie",
        }

    mollie_status = payment.get("status", "unknown")
    order_id = payment.get("metadata", {}).get("order_id", "")
    bedrag = payment.get("amount", {}).get("value", "0.00")
    klant_email = payment.get("billingAddress", {}).get("email", "")
    klant_naam = payment.get("billingAddress", {}).get("givenName", "Klant")
    methode = payment.get("method", "onbekend")

    logger.info(
        "Mollie payment status: id=%s status=%s order=%s bedrag=€%s",
        payment_id, mollie_status, order_id, bedrag,
    )

    if mollie_status == "paid":
        return await _handle_paid(payment_id, order_id, bedrag, klant_naam, klant_email, methode)

    if mollie_status == "failed":
        reden = payment.get("details", {}).get("failureReason", "onbekend")
        return await _handle_failed(payment_id, order_id, klant_naam, reden)

    if mollie_status == "expired":
        return await _handle_expired(payment_id, order_id, klant_naam)

    if mollie_status == "canceled":
        return await _handle_canceled(payment_id, order_id, klant_naam)

    if mollie_status in ("open", "pending", "authorized"):
        logger.info("Mollie payment in tussenliggende status '%s' — geen actie vereist", mollie_status)
        return {
            "status": "genoteerd",
            "payment_id": payment_id,
            "mollie_status": mollie_status,
            "actie": "geen",
        }

    logger.warning("Onbekende Mollie status '%s' voor payment %s", mollie_status, payment_id)
    return {
        "status": "onbekend",
        "payment_id": payment_id,
        "mollie_status": mollie_status,
    }


async def _handle_paid(
    payment_id: str,
    order_id: str,
    bedrag: str,
    klant_naam: str,
    klant_email: str,
    methode: str,
) -> dict[str, Any]:
    """Verwerk een geslaagde Mollie betaling."""
    from ollama.agent_runner import get_runner
    runner = get_runner()

    response, _ = await runner.run_agent_with_retry(
        agent_name="order_verwerking_agent",
        user_input=(
            f"Betaling geslaagd via Mollie voor order {order_id}. "
            f"Payment ID: {payment_id}. Bedrag: €{bedrag}. "
            f"Betaalmethode: {methode}. "
            f"Genereer bevestiging voor {klant_naam} en geef vrijgave voor verzending aan."
        ),
        context={
            "order_id": order_id,
            "payment_id": payment_id,
            "bedrag": bedrag,
            "klant_naam": klant_naam,
            "klant_email": klant_email,
            "betaalmethode": methode,
        },
    )

    logger.info("Order %s vrijgegeven voor verzending na Mollie betaling %s", order_id, payment_id)

    return {
        "status": "verwerkt",
        "payment_id": payment_id,
        "order_id": order_id,
        "mollie_status": "paid",
        "actie": "order_vrijgegeven_voor_verzending",
        "agent_output": response,
    }


async def _handle_failed(
    payment_id: str,
    order_id: str,
    klant_naam: str,
    reden: str,
) -> dict[str, Any]:
    """Verwerk een mislukte Mollie betaling."""
    from ollama.agent_runner import get_runner
    runner = get_runner()

    response, _ = await runner.run_agent_with_retry(
        agent_name="betaling_status_agent",
        user_input=(
            f"Mollie betaling mislukt voor order {order_id}. "
            f"Payment ID: {payment_id}. Reden: {reden}. "
            f"Genereer een klantvriendelijk bericht voor {klant_naam} "
            f"met alternatieve betaalmogelijkheden."
        ),
        context={
            "order_id": order_id,
            "payment_id": payment_id,
            "klant_naam": klant_naam,
            "reden": reden,
        },
    )

    return {
        "status": "verwerkt",
        "payment_id": payment_id,
        "order_id": order_id,
        "mollie_status": "failed",
        "actie": "klant_genotificeerd_betaling_mislukt",
        "agent_output": response,
    }


async def _handle_expired(
    payment_id: str,
    order_id: str,
    klant_naam: str,
) -> dict[str, Any]:
    """Verwerk een verlopen Mollie betaling (klant deed te lang over betalen)."""
    from ollama.agent_runner import get_runner
    runner = get_runner()

    response, _ = await runner.run_agent_with_retry(
        agent_name="klantenservice_agent",
        user_input=(
            f"Mollie betaling verlopen voor order {order_id} van {klant_naam}. "
            f"Payment ID: {payment_id}. "
            f"Stel een vriendelijk bericht op met uitleg en een nieuwe betaallink aanbieding."
        ),
        context={
            "order_id": order_id,
            "payment_id": payment_id,
            "klant_naam": klant_naam,
        },
    )

    return {
        "status": "verwerkt",
        "payment_id": payment_id,
        "order_id": order_id,
        "mollie_status": "expired",
        "actie": "klant_genotificeerd_betaling_verlopen",
        "agent_output": response,
    }


async def _handle_canceled(
    payment_id: str,
    order_id: str,
    klant_naam: str,
) -> dict[str, Any]:
    """Verwerk een geannuleerde Mollie betaling (klant annuleerde zelf)."""
    logger.info(
        "Mollie betaling geannuleerd door klant: order=%s payment=%s", order_id, payment_id
    )

    return {
        "status": "genoteerd",
        "payment_id": payment_id,
        "order_id": order_id,
        "mollie_status": "canceled",
        "actie": "order_in_afwachting_nieuwe_betaling",
    }
