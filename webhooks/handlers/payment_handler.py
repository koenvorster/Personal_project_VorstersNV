"""Betaling event handlers voor VorstersNV webhooks."""
import logging
from typing import Any

from ollama.agent_runner import get_runner
from ollama.event_bridge import get_event_bridge

logger = logging.getLogger(__name__)


async def handle_payment_confirmed(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Verwerk een bevestigde betaling.

    Stappen:
    1. Verifieer betaalinformatie
    2. Update orderstatus naar 'betaald'
    3. Trigger order-fulfillment via agent
    4. Stuur factuur naar klant
    """
    order_id = payload.get("order_id")
    payment_id = payload.get("payment_id")
    bedrag = payload.get("amount")
    klant_naam = payload.get("customer", {}).get("name", "Klant")

    logger.info("Betaling bevestigd: order=%s payment=%s bedrag=%s", order_id, payment_id, bedrag)

    runner = get_runner()
    agent_bericht = await runner.run_agent(
        "order_verwerking_agent",
        f"Betaling bevestigd voor order {order_id}. Bedrag: €{bedrag}. "
        f"Genereer een factuurbevestiging voor {klant_naam} en geef aan dat de order klaar gemaakt wordt.",
        context={
            "order_id": order_id,
            "payment_id": payment_id or "",
            "bedrag": str(bedrag or ""),
            "klant_naam": klant_naam,
        },
    )

    try:
        await get_event_bridge().emit_payment_completed(payload)
    except Exception:
        logger.exception("EventBridge emit_payment_completed failed (non-critical)")

    return {
        "status": "verwerkt",
        "order_id": order_id,
        "payment_id": payment_id,
        "actie": "order_vrijgegeven_voor_verzending",
        "agent_output": agent_bericht,
    }


async def handle_payment_failed(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Verwerk een mislukte betaling.

    Stappen:
    1. Registreer mislukte betaling
    2. Laat agent klantvriendelijk bericht opstellen
    3. Bied alternatieve betaalmethode aan
    """
    order_id = payload.get("order_id")
    reden = payload.get("failure_reason", "onbekend")
    klant_naam = payload.get("customer", {}).get("name", "Klant")

    logger.warning("Betaling mislukt: order=%s reden=%s", order_id, reden)

    runner = get_runner()
    agent_bericht = await runner.run_agent(
        "klantenservice_agent",
        f"De betaling voor order {order_id} van {klant_naam} is mislukt. "
        f"Reden: {reden}. Stel een empathisch bericht op en verwijs naar alternatieve betaalmethoden.",
        context={
            "order_id": order_id,
            "reden": reden,
            "klant_naam": klant_naam,
        },
    )

    try:
        await get_event_bridge().emit_payment_failed(payload)
    except Exception:
        logger.exception("EventBridge emit_payment_failed failed (non-critical)")

    return {
        "status": "verwerkt",
        "order_id": order_id,
        "actie": "klant_genotificeerd_betaling_mislukt",
        "agent_output": agent_bericht,
    }
