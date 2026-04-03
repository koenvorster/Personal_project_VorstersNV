from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    vraag: str
    gebruik_documenten: bool = True
    model: Optional[str] = None


class ChatResponse(BaseModel):
    antwoord: str
    bronnen: list[str] = []
    model_gebruikt: str


class DocumentInfo(BaseModel):
    bestandsnaam: str
    aantal_chunks: int
    status: str


class IngestResponse(BaseModel):
    bericht: str
    documenten: list[DocumentInfo]


class HealthResponse(BaseModel):
    status: str
    ollama_bereikbaar: bool
    chroma_bereikbaar: bool
    modellen_beschikbaar: list[str]


class CollectionStats(BaseModel):
    collectie_naam: str
    aantal_documenten: int
    unieke_bronnen: list[str]
