"""Betaling event handlers voor VorstersNV webhooks."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def handle_payment_confirmed(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Verwerk een bevestigde betaling.

    Stappen:
    1. Verifieer betaalinformatie
    2. Update orderstatus naar 'betaald'
    3. Trigger order-fulfillment
    4. Stuur betalingsbevestiging
    """
    order_id = payload.get("order_id")
    payment_id = payload.get("payment_id")
    bedrag = payload.get("amount")

    logger.info("Betaling bevestigd: order=%s payment=%s bedrag=%s", order_id, payment_id, bedrag)

    # TODO: Update orderstatus
    # TODO: Trigger fulfillment workflow
    # TODO: Stuur factuur naar klant

    return {
        "status": "verwerkt",
        "order_id": order_id,
        "payment_id": payment_id,
        "actie": "order_vrijgegeven_voor_verzending",
    }


async def handle_payment_failed(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Verwerk een mislukte betaling.

    Stappen:
    1. Registreer mislukte betaling
    2. Stuur notificatie naar klant
    3. Bied alternatieve betaalmethode aan
    """
    order_id = payload.get("order_id")
    reden = payload.get("failure_reason")

    logger.warning("Betaling mislukt: order=%s reden=%s", order_id, reden)

    # TODO: Stuur betaling-mislukt email
    # TODO: Bied retrypagina aan

    return {
        "status": "verwerkt",
        "order_id": order_id,
        "actie": "klant_genotificeerd_betaling_mislukt",
    }
