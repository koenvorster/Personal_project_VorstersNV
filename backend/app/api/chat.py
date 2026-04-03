import logging

from fastapi import APIRouter, HTTPException

from app.services.rag import beantwoord_vraag, beantwoord_vraag_direct
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=ChatResponse)
async def chat(verzoek: ChatRequest):
    """
    Beantwoord een vraag met of zonder RAG op bedrijfsdocumenten.

    - **gebruik_documenten=true**: RAG op de ingested documenten.
    - **gebruik_documenten=false**: Directe LLM-aanroep zonder context.
    """
    try:
        if verzoek.gebruik_documenten:
            return beantwoord_vraag(verzoek.vraag, model_override=verzoek.model)
        return beantwoord_vraag_direct(verzoek.vraag, model_override=verzoek.model)
    except Exception as exc:
        logger.error("Chatfout: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
