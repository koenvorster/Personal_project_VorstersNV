"""
VorstersNV Agent Rate Limiter
Redis-gebaseerde rate limiting voor AI-agent endpoints.

Gebruik:
    limiter = AgentRateLimiter()
    await limiter.check("klantenservice_agent", klant_id="k123")
    # gooit RateLimitExceeded als de limiet overschreden is
"""
import logging
import os
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

# Standaard limieten per agent (aanroepen per minuut)
DEFAULT_LIMITS: dict[str, int] = {
    "klantenservice_agent": 20,
    "product_beschrijving_agent": 10,
    "seo_agent": 10,
    "aanbeveling_agent": 60,   # hogere limiet — lichte widget calls
    "content_moderatie_agent": 100,  # batch-moderatie verwacht
    "loyaliteit_agent": 30,
    "fraude_detectie_agent": 50,
    "email_template_agent": 20,
    "_default": 15,
}


class RateLimitExceeded(Exception):
    """Wordt gegooid wanneer een agent zijn rate limiet heeft overschreden."""

    def __init__(self, agent_name: str, limit: int, window_seconds: int, retry_after: int):
        self.agent_name = agent_name
        self.limit = limit
        self.window_seconds = window_seconds
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit overschreden voor agent '{agent_name}': "
            f"{limit} aanroepen per {window_seconds}s. Retry after: {retry_after}s"
        )


@dataclass
class RateLimitConfig:
    """Configuratie voor een specifieke agent of globale limiet."""
    max_calls: int = 15
    window_seconds: int = 60
    per_client: bool = True   # Limiet per klant-ID (True) of globaal (False)


@dataclass
class _InMemoryBucket:
    """Eenvoudige in-memory token bucket als Redis fallback."""
    max_calls: int
    window_seconds: int
    calls: list[float] = field(default_factory=list)

    def is_allowed(self) -> tuple[bool, int]:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        self.calls = [t for t in self.calls if t > cutoff]
        if len(self.calls) >= self.max_calls:
            oldest = self.calls[0]
            retry_after = int(oldest + self.window_seconds - now) + 1
            return False, retry_after
        self.calls.append(now)
        return True, 0


class AgentRateLimiter:
    """
    Rate limiter voor agent aanroepen.

    Gebruikt Redis indien beschikbaar; valt terug op in-memory per process.
    Redis sliding window implementatie met ZADD/ZREMRANGEBYSCORE.
    """

    def __init__(self, limits: dict[str, int] | None = None):
        self._limits = {**DEFAULT_LIMITS, **(limits or {})}
        self._redis: object | None = None
        self._fallback: dict[str, _InMemoryBucket] = {}
        self._redis_available = False
        self._init_redis()

    def _init_redis(self) -> None:
        try:
            import redis.asyncio as aioredis  # type: ignore[import]
            self._redis = aioredis.from_url(REDIS_URL, decode_responses=True)
            self._redis_available = True
            logger.info("AgentRateLimiter: Redis beschikbaar op %s", REDIS_URL)
        except ImportError:
            logger.warning(
                "AgentRateLimiter: redis pakket niet geïnstalleerd — in-memory fallback actief. "
                "Installeer met: pip install redis"
            )

    def _get_limit(self, agent_name: str) -> int:
        return self._limits.get(agent_name, self._limits["_default"])

    async def check(
        self,
        agent_name: str,
        client_id: str = "global",
        window_seconds: int = 60,
    ) -> None:
        """
        Controleer of een agent aanroep toegestaan is.

        Args:
            agent_name: Naam van de agent
            client_id: Klant- of gebruikers-ID voor per-client limiting
            window_seconds: Tijdvenster in seconden

        Raises:
            RateLimitExceeded: Als de limiet overschreden is
        """
        max_calls = self._get_limit(agent_name)
        key = f"rl:{agent_name}:{client_id}"

        if self._redis_available and self._redis is not None:
            allowed, retry_after = await self._check_redis(key, max_calls, window_seconds)
        else:
            allowed, retry_after = self._check_memory(key, max_calls, window_seconds)

        if not allowed:
            logger.warning(
                "Rate limit overschreden: agent=%s client=%s limit=%d/%ds",
                agent_name, client_id, max_calls, window_seconds,
            )
            raise RateLimitExceeded(
                agent_name=agent_name,
                limit=max_calls,
                window_seconds=window_seconds,
                retry_after=retry_after,
            )

    async def _check_redis(
        self, key: str, max_calls: int, window_seconds: int
    ) -> tuple[bool, int]:
        """Sliding window rate check via Redis sorted set."""
        try:
            import redis.asyncio as aioredis  # type: ignore[import]
            now = time.time()
            cutoff = now - window_seconds

            pipe = self._redis.pipeline()  # type: ignore[union-attr]
            pipe.zremrangebyscore(key, 0, cutoff)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, window_seconds + 1)
            results = await pipe.execute()

            count_before_add = results[1]
            if count_before_add >= max_calls:
                # Verwijder de zojuist toegevoegde call terug
                await self._redis.zrem(key, str(now))  # type: ignore[union-attr]
                oldest_score = await self._redis.zrange(key, 0, 0, withscores=True)  # type: ignore[union-attr]
                retry_after = 1
                if oldest_score:
                    retry_after = int(oldest_score[0][1] + window_seconds - now) + 1
                return False, max(retry_after, 1)

            return True, 0
        except Exception as exc:
            logger.error("Redis rate limit fout — in-memory fallback: %s", exc)
            return self._check_memory(key, max_calls, window_seconds)

    def _check_memory(
        self, key: str, max_calls: int, window_seconds: int
    ) -> tuple[bool, int]:
        """In-memory sliding window fallback."""
        if key not in self._fallback:
            self._fallback[key] = _InMemoryBucket(
                max_calls=max_calls, window_seconds=window_seconds
            )
        return self._fallback[key].is_allowed()


# Singleton limiter
_limiter: AgentRateLimiter | None = None


def get_rate_limiter() -> AgentRateLimiter:
    """Geef de singleton AgentRateLimiter terug."""
    global _limiter
    if _limiter is None:
        _limiter = AgentRateLimiter()
    return _limiter
