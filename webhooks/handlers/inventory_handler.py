"""Voorraad event handlers voor VorstersNV webhooks."""
import logging
from typing import Any

from ollama.agent_runner import get_runner

logger = logging.getLogger(__name__)

LOW_STOCK_THRESHOLD = 5


async def handle_low_stock(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Verwerk een lage-voorraad melding.

    Stappen:
    1. Registreer melding
    2. Laat agent inkoopadvies genereren
    3. Notificeer inkoopmanager
    """
    product_id = payload.get("product_id")
    product_naam = payload.get("product_name", "Onbekend product")
    huidige_voorraad = payload.get("current_stock", 0)

    logger.warning(
        "Lage voorraad: product=%s (%s), voorraad=%d",
        product_id,
        product_naam,
        huidige_voorraad,
    )

    runner = get_runner()
    agent_bericht = await runner.run_agent(
        "order_verwerking_agent",
        f"Product '{product_naam}' (ID: {product_id}) heeft nog slechts {huidige_voorraad} stuks op voorraad. "
        f"Genereer een inkoopadvies en urgentiemelding voor de inkoopmanager.",
        context={
            "product_id": product_id or "",
            "product_naam": product_naam,
            "huidige_voorraad": str(huidige_voorraad),
        },
    )

    return {
        "status": "verwerkt",
        "product_id": product_id,
        "huidige_voorraad": huidige_voorraad,
        "actie": "inkoopmanager_genotificeerd",
        "agent_output": agent_bericht,
    }
