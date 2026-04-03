import logging
import logging.config

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api import chat, documents, health

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=(
        "Lokale AI-backend voor VorstersNV. "
        "Gebruikt Ollama (Llama 3 / Mistral) en ChromaDB voor RAG op bedrijfsdocumenten. "
        "Alle data blijft lokaal — geen externe cloud-API's."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(documents.router)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "applicatie": settings.api_title,
        "versie": settings.api_version,
        "documentatie": "/docs",
    }
