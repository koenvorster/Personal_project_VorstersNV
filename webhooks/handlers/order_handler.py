"""Order event handlers voor VorstersNV webhooks."""
import logging
from typing import Any

from ollama.agent_runner import get_runner
from ollama.event_bridge import get_event_bridge

logger = logging.getLogger(__name__)


async def handle_order_created(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Verwerk een nieuw aangemaakte order.

    Stappen:
    1. Valideer ordergegevens
    2. Activeer de order_verwerking_agent via Ollama
    3. Stuur bevestigingsmail (via agent output)
    4. Update dashboard
    """
    order_id = payload.get("order_id")
    klant_naam = payload.get("customer", {}).get("name", "Klant")
    klant_email = payload.get("customer", {}).get("email")
    producten = payload.get("items", [])

    logger.info("Verwerk nieuwe order: %s voor %s", order_id, klant_email)

    runner = get_runner()
    agent_bericht = await runner.run_agent(
        "order_verwerking_agent",
        f"Verwerk nieuwe order {order_id} voor klant {klant_naam}. "
        f"Producten: {producten}. Email: {klant_email}.",
        context={
            "order_id": order_id,
            "klant_naam": klant_naam,
            "klant_email": klant_email or "",
        },
    )

    logger.info("Order %s verwerkt. Agent response: %d tekens", order_id, len(agent_bericht))

    try:
        await get_event_bridge().emit_order_created(payload)
    except Exception:
        logger.exception("EventBridge emit_order_created failed (non-critical)")

    return {
        "status": "verwerkt",
        "order_id": order_id,
        "actie": "bevestigingsmail_verzonden",
        "agent_output": agent_bericht,
        "message": f"Order {order_id} succesvol ontvangen en bevestigd.",
    }


async def handle_order_shipped(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Verwerk een verzonden order.

    Stappen:
    1. Update orderstatus naar 'verzonden'
    2. Laat agent verzendbericht opstellen
    3. Stuur verzendinformatie naar klant
    """
    order_id = payload.get("order_id")
    tracking_code = payload.get("tracking_code")
    klant_naam = payload.get("customer", {}).get("name", "Klant")

    logger.info("Order verzonden: %s (tracking: %s)", order_id, tracking_code)

    runner = get_runner()
    agent_bericht = await runner.run_agent(
        "order_verwerking_agent",
        f"Order {order_id} is verzonden met trackingcode {tracking_code}. "
        f"Stel een verzendbericht op voor klant {klant_naam}.",
        context={
            "order_id": order_id,
            "tracking_code": tracking_code or "",
            "klant_naam": klant_naam,
        },
    )

    try:
        await get_event_bridge().emit_order_shipped(payload)
    except Exception:
        logger.exception("EventBridge emit_order_shipped failed (non-critical)")

    return {
        "status": "verwerkt",
        "order_id": order_id,
        "tracking_code": tracking_code,
        "actie": "verzendbevestiging_verstuurd",
        "agent_output": agent_bericht,
    }


async def handle_order_returned(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Verwerk een retour-aanvraag.

    Stappen:
    1. Registreer retour in systeem
    2. Laat klantenservice_agent retourinstructies opstellen
    3. Plan terugbetaling
    """
    order_id = payload.get("order_id")
    retour_reden = payload.get("return_reason", "niet opgegeven")
    klant_naam = payload.get("customer", {}).get("name", "Klant")

    logger.info("Retour voor order: %s, reden: %s", order_id, retour_reden)

    runner = get_runner()
    agent_bericht = await runner.run_agent(
        "klantenservice_agent",
        f"Klant {klant_naam} wil order {order_id} retourneren. "
        f"Reden: {retour_reden}. Verwerk de retour met empathie en geef duidelijke instructies.",
        context={
            "order_id": order_id,
            "retour_reden": retour_reden,
            "klant_naam": klant_naam,
        },
    )

    try:
        await get_event_bridge().emit_order_returned(payload)
    except Exception:
        logger.exception("EventBridge emit_order_returned failed (non-critical)")

    return {
        "status": "verwerkt",
        "order_id": order_id,
        "actie": "retour_geregistreerd",
        "agent_output": agent_bericht,
        "message": f"Retour voor order {order_id} geregistreerd.",
    }
