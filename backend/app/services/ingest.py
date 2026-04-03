import logging
from pathlib import Path
from typing import Optional

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    CSVLoader,
)
from langchain.schema import Document

from app.core.dependencies import get_vector_store, get_text_splitter
from app.models.schemas import DocumentInfo

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".docx": Docx2txtLoader,
    ".csv": CSVLoader,
}


def _load_document(bestandspad: Path) -> list[Document]:
    """Laadt een document op basis van zijn bestandsextensie."""
    extensie = bestandspad.suffix.lower()
    loader_klasse = SUPPORTED_EXTENSIONS.get(extensie)
    if not loader_klasse:
        raise ValueError(
            f"Bestandstype '{extensie}' wordt niet ondersteund. "
            f"Ondersteunde types: {list(SUPPORTED_EXTENSIONS.keys())}"
        )
    loader = loader_klasse(str(bestandspad))
    return loader.load()


def ingest_document(bestandspad: Path, bron_label: Optional[str] = None) -> DocumentInfo:
    """
    Verwerkt één document: laden → splitsen → embedden → opslaan in ChromaDB.

    Args:
        bestandspad: Pad naar het te verwerken bestand.
        bron_label: Optioneel label om in de metadata op te slaan.

    Returns:
        DocumentInfo met verwerkinsstatus.
    """
    bestandsnaam = bestandspad.name
    label = bron_label or bestandsnaam

    try:
        logger.info("Document laden: %s", bestandsnaam)
        documenten = _load_document(bestandspad)

        # Voeg bronnaam toe aan metadata
        for doc in documenten:
            doc.metadata.setdefault("bron", label)
            doc.metadata.setdefault("bestandsnaam", bestandsnaam)

        splitter = get_text_splitter()
        chunks = splitter.split_documents(documenten)
        logger.info("%d chunks aangemaakt voor '%s'", len(chunks), bestandsnaam)

        vector_store = get_vector_store()
        vector_store.add_documents(chunks)
        logger.info("Chunks opgeslagen in ChromaDB voor '%s'", bestandsnaam)

        return DocumentInfo(
            bestandsnaam=bestandsnaam,
            aantal_chunks=len(chunks),
            status="verwerkt",
        )

    except Exception as exc:
        logger.error("Fout bij verwerken van '%s': %s", bestandsnaam, exc)
        return DocumentInfo(
            bestandsnaam=bestandsnaam,
            aantal_chunks=0,
            status=f"fout: {exc}",
        )


def verwijder_document(bestandsnaam: str) -> int:
    """
    Verwijdert alle chunks van een document op basis van bestandsnaam.

    Returns:
        Aantal verwijderde chunks.
    """
    vector_store = get_vector_store()
    collectie = vector_store._collection
    resultaten = collectie.get(where={"bestandsnaam": bestandsnaam})
    ids = resultaten.get("ids", [])
    if ids:
        collectie.delete(ids=ids)
        logger.info("%d chunks verwijderd voor '%s'", len(ids), bestandsnaam)
    return len(ids)
