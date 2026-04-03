from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
import chromadb

from app.core.config import get_settings

settings = get_settings()


def get_llm() -> OllamaLLM:
    """Geeft een geconfigureerde Ollama LLM-instantie terug."""
    return OllamaLLM(
        base_url=settings.ollama_base_url,
        model=settings.ollama_chat_model,
        temperature=0.1,
    )


def get_embeddings() -> OllamaEmbeddings:
    """Geeft Ollama embeddings terug voor vectorisatie."""
    return OllamaEmbeddings(
        base_url=settings.ollama_base_url,
        model=settings.ollama_embed_model,
    )


def get_chroma_client() -> chromadb.HttpClient:
    """Verbindt met de ChromaDB HTTP-server."""
    return chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
    )


def get_vector_store() -> Chroma:
    """Geeft de LangChain Chroma vector store terug."""
    return Chroma(
        client=get_chroma_client(),
        collection_name=settings.chroma_collection,
        embedding_function=get_embeddings(),
    )


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    """Geeft een tekst-splitter terug voor het opdelen van documenten."""
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
