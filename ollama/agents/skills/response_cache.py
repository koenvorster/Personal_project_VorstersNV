"""
VorstersNV Agent Response Cache
Redis-gebaseerde cache voor identieke agent-aanroepen.

Identieke combinaties van (agent_naam, prompt_hash) worden gecached om
Ollama-latentie te reduceren bij veelgevraagde responses (bijv. productteksten,
aanbevelingen, SEO-tags).

Gebruik:
    cache = AgentResponseCache()
    cached = await cache.get("seo_agent", user_input, context)
    if cached:
        return cached, "cached"
    response, interaction_id = await agent.run(user_input, context)
    await cache.set("seo_agent", user_input, context, response)
"""
import hashlib
import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

# TTL per agent in seconden (0 = niet cachen)
DEFAULT_TTL: dict[str, int] = {
    "seo_agent": 3600,              # SEO-teksten veranderen zelden
    "product_beschrijving_agent": 1800,
    "aanbeveling_agent": 300,       # 5 minuten — snel verouderd
    "content_moderatie_agent": 86400,  # 24 uur — zelfde tekst = zelfde beslissing
    "loyaliteit_agent": 0,          # Niet cachen — altijd actueel puntensaldo
    "klantenservice_agent": 0,      # Niet cachen — conversaties zijn uniek
    "fraude_detectie_agent": 0,     # Nooit cachen — security-kritisch
    "_default": 0,
}


def _make_cache_key(agent_name: str, user_input: str, context: dict[str, Any] | None) -> str:
    """Genereer een deterministische cache key op basis van input."""
    payload = json.dumps(
        {"agent": agent_name, "input": user_input, "ctx": context or {}},
        sort_keys=True,
        ensure_ascii=False,
    )
    digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return f"ac:{agent_name}:{digest}"


class AgentResponseCache:
    """
    Cache voor agent responses.

    Redis indien beschikbaar, anders geen caching (veilige fallback).
    Cache alleen voor agents met TTL > 0 in DEFAULT_TTL.
    """

    def __init__(self, ttl_overrides: dict[str, int] | None = None):
        self._ttl = {**DEFAULT_TTL, **(ttl_overrides or {})}
        self._redis: object | None = None
        self._available = False
        self._init_redis()

    def _init_redis(self) -> None:
        try:
            import redis.asyncio as aioredis  # type: ignore[import]
            self._redis = aioredis.from_url(REDIS_URL, decode_responses=True)
            self._available = True
            logger.info("AgentResponseCache: Redis beschikbaar op %s", REDIS_URL)
        except ImportError:
            logger.warning(
                "AgentResponseCache: redis pakket niet geïnstalleerd — caching uitgeschakeld."
            )

    def _get_ttl(self, agent_name: str) -> int:
        return self._ttl.get(agent_name, self._ttl["_default"])

    async def get(
        self,
        agent_name: str,
        user_input: str,
        context: dict[str, Any] | None = None,
    ) -> str | None:
        """
        Zoek een gecachede response op.

        Returns:
            De gecachede response string, of None bij cache miss.
        """
        if not self._available or self._get_ttl(agent_name) == 0:
            return None

        key = _make_cache_key(agent_name, user_input, context)
        try:
            value = await self._redis.get(key)  # type: ignore[union-attr]
            if value:
                logger.debug("Cache HIT voor agent '%s' (key: %s)", agent_name, key)
                return value
            logger.debug("Cache MISS voor agent '%s'", agent_name)
            return None
        except Exception as exc:
            logger.warning("Cache GET fout voor agent '%s': %s", agent_name, exc)
            return None

    async def set(
        self,
        agent_name: str,
        user_input: str,
        context: dict[str, Any] | None,
        response: str,
    ) -> None:
        """
        Sla een response op in de cache.

        Args:
            agent_name: Naam van de agent
            user_input: Originele input (voor key generatie)
            context: Context dict (voor key generatie)
            response: Te cachen response string
        """
        ttl = self._get_ttl(agent_name)
        if not self._available or ttl == 0:
            return

        key = _make_cache_key(agent_name, user_input, context)
        try:
            await self._redis.set(key, response, ex=ttl)  # type: ignore[union-attr]
            logger.debug(
                "Cache SET voor agent '%s' (TTL: %ds, key: %s)", agent_name, ttl, key
            )
        except Exception as exc:
            logger.warning("Cache SET fout voor agent '%s': %s", agent_name, exc)

    async def invalidate(self, agent_name: str, pattern: str = "*") -> int:
        """
        Verwijder gecachede responses voor een agent.

        Args:
            agent_name: Agent waarvoor de cache geleegd moet worden
            pattern: Extra patroon (standaard alle keys voor de agent)

        Returns:
            Aantal verwijderde keys
        """
        if not self._available:
            return 0
        search_pattern = f"ac:{agent_name}:{pattern}"
        try:
            keys = await self._redis.keys(search_pattern)  # type: ignore[union-attr]
            if keys:
                count = await self._redis.delete(*keys)  # type: ignore[union-attr]
                logger.info(
                    "Cache geïnvalideerd voor agent '%s': %d keys verwijderd", agent_name, count
                )
                return count
            return 0
        except Exception as exc:
            logger.warning("Cache invalidate fout: %s", exc)
            return 0


# Singleton cache
_cache: AgentResponseCache | None = None


def get_response_cache() -> AgentResponseCache:
    """Geef de singleton AgentResponseCache terug."""
    global _cache
    if _cache is None:
        _cache = AgentResponseCache()
    return _cache
