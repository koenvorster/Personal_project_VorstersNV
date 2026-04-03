import logging

import httpx
from fastapi import APIRouter

from app.core.config import get_settings
from app.models.schemas import HealthResponse

router = APIRouter(tags=["Health"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Controleert de bereikbaarheid van Ollama en ChromaDB."""
    ollama_ok = False
    chroma_ok = False
    modellen: list[str] = []

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            if resp.status_code == 200:
                ollama_ok = True
                data = resp.json()
                modellen = [m["name"] for m in data.get("models", [])]
        except Exception as exc:
            logger.warning("Ollama niet bereikbaar: %s", exc)

        try:
            resp = await client.get(
                f"http://{settings.chroma_host}:{settings.chroma_port}/api/v1/heartbeat"
            )
            chroma_ok = resp.status_code == 200
        except Exception as exc:
            logger.warning("ChromaDB niet bereikbaar: %s", exc)

    alles_ok = ollama_ok and chroma_ok
    return HealthResponse(
        status="gezond" if alles_ok else "gedeeltelijk beschikbaar",
        ollama_bereikbaar=ollama_ok,
        chroma_bereikbaar=chroma_ok,
        modellen_beschikbaar=modellen,
    )
