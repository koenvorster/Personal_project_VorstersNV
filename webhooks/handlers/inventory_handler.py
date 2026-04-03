"""Voorraad event handlers voor VorstersNV webhooks."""
import logging
from typing import Any

logger = logging.getLogger(__name__)

LOW_STOCK_THRESHOLD = 5


async def handle_low_stock(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Verwerk een lage-voorraad melding.

    Stappen:
    1. Registreer melding
    2. Notificeer inkoopmanager
    3. Optioneel: activeer automatische bestelling
    """
    product_id = payload.get("product_id")
    product_naam = payload.get("product_name")
    huidige_voorraad = payload.get("current_stock", 0)

    logger.warning(
        "Lage voorraad: product=%s (%s), voorraad=%d",
        product_id,
        product_naam,
        huidige_voorraad,
    )

    # TODO: Stuur notificatie naar inkoopmanager
    # TODO: Optioneel: automatische inkooporder genereren

    return {
        "status": "verwerkt",
        "product_id": product_id,
        "huidige_voorraad": huidige_voorraad,
        "actie": "inkoopmanager_genotificeerd",
    }
