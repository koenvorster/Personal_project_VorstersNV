from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Ollama
    ollama_base_url: str = "http://ollama:11434"
    ollama_chat_model: str = "llama3:8b"
    ollama_embed_model: str = "nomic-embed-text"

    # ChromaDB
    chroma_host: str = "chromadb"
    chroma_port: int = 8000
    chroma_collection: str = "bedrijfsdocumenten"

    # RAG
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retriever_top_k: int = 5

    # API
    api_title: str = "VorstersNV AI Backend"
    api_version: str = "1.0.0"
    cors_origins: list[str] = ["http://localhost:8501", "http://frontend:8501"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
