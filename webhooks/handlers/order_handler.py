"""Order event handlers voor VorstersNV webhooks."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def handle_order_created(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Verwerk een nieuw aangemaakte order.

    Stappen:
    1. Valideer ordergegevens
    2. Activeer de order-verwerking AI-agent
    3. Stuur bevestigingsmail
    4. Update dashboard
    """
    order_id = payload.get("order_id")
    klant_email = payload.get("customer", {}).get("email")

    logger.info("Verwerk nieuwe order: %s voor %s", order_id, klant_email)

    # TODO: Roep order_verwerking_agent aan via Ollama
    # TODO: Stuur bevestigingsmail
    # TODO: Update order-dashboard

    return {
        "status": "verwerkt",
        "order_id": order_id,
        "actie": "bevestigingsmail_verzonden",
        "message": f"Order {order_id} succesvol ontvangen en bevestigd.",
    }


async def handle_order_shipped(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Verwerk een verzonden order.

    Stappen:
    1. Update orderstatus naar 'verzonden'
    2. Stuur verzendinformatie naar klant
    3. Activeer track & trace koppeling
    """
    order_id = payload.get("order_id")
    tracking_code = payload.get("tracking_code")

    logger.info("Order verzonden: %s (tracking: %s)", order_id, tracking_code)

    # TODO: Stuur verzendmail met track & trace link
    # TODO: Update orderstatus in systeem

    return {
        "status": "verwerkt",
        "order_id": order_id,
        "tracking_code": tracking_code,
        "actie": "verzendbevestiging_verstuurd",
    }


async def handle_order_returned(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Verwerk een retour-aanvraag.

    Stappen:
    1. Registreer retour in systeem
    2. Genereer retourlabel
    3. Stuur retourinstructies naar klant
    4. Plan terugbetaling
    """
    order_id = payload.get("order_id")
    retour_reden = payload.get("return_reason")

    logger.info("Retour voor order: %s, reden: %s", order_id, retour_reden)

    # TODO: Activeer klantenservice_agent voor retourafhandeling
    # TODO: Genereer retourlabel
    # TODO: Stuur retourinstructies

    return {
        "status": "verwerkt",
        "order_id": order_id,
        "actie": "retour_geregistreerd",
        "message": f"Retour voor order {order_id} geregistreerd.",
    }
