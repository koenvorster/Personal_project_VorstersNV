import logging
from pathlib import Path
import tempfile

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.services.ingest import ingest_document, verwijder_document
from app.core.dependencies import get_vector_store
from app.models.schemas import IngestResponse, CollectionStats

router = APIRouter(prefix="/documenten", tags=["Documenten"])
logger = logging.getLogger(__name__)

TOEGESTANE_EXTENSIES = {".pdf", ".txt", ".docx", ".csv"}
MAX_BESTANDSGROOTTE = 50 * 1024 * 1024  # 50 MB


@router.post("/upload", response_model=IngestResponse)
async def upload_documenten(bestanden: list[UploadFile] = File(...)):
    """
    Upload en verwerk één of meerdere bedrijfsdocumenten.
    Ondersteunde formaten: PDF, TXT, DOCX, CSV.
    """
    if not bestanden:
        raise HTTPException(status_code=400, detail="Geen bestanden ontvangen.")

    verwerkte_docs = []

    for bestand in bestanden:
        extensie = Path(bestand.filename).suffix.lower()
        if extensie not in TOEGESTANE_EXTENSIES:
            raise HTTPException(
                status_code=415,
                detail=f"Bestandstype '{extensie}' niet ondersteund. "
                       f"Gebruik: {sorted(TOEGESTANE_EXTENSIES)}",
            )

        inhoud = await bestand.read()
        if len(inhoud) > MAX_BESTANDSGROOTTE:
            raise HTTPException(
                status_code=413,
                detail=f"'{bestand.filename}' overschrijdt de maximale bestandsgrootte van 50 MB.",
            )

        with tempfile.NamedTemporaryFile(suffix=extensie, delete=False) as tmp:
            tmp.write(inhoud)
            tmp_pad = Path(tmp.name)

        try:
            doc_info = ingest_document(tmp_pad, bron_label=bestand.filename)
            verwerkte_docs.append(doc_info)
        finally:
            tmp_pad.unlink(missing_ok=True)

    geslaagd = sum(1 for d in verwerkte_docs if not d.status.startswith("fout"))
    return IngestResponse(
        bericht=f"{geslaagd}/{len(bestanden)} document(en) succesvol verwerkt.",
        documenten=verwerkte_docs,
    )


@router.delete("/{bestandsnaam}")
async def verwijder_document_endpoint(bestandsnaam: str):
    """Verwijdert alle chunks van een document uit de vector store."""
    verwijderd = verwijder_document(bestandsnaam)
    if verwijderd == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Geen chunks gevonden voor '{bestandsnaam}'.",
        )
    return {"bericht": f"{verwijderd} chunks verwijderd voor '{bestandsnaam}'."}


@router.get("/statistieken", response_model=CollectionStats)
async def haal_statistieken_op():
    """Geeft statistieken over de vector store collectie."""
    try:
        vector_store = get_vector_store()
        collectie = vector_store._collection
        data = collectie.get(include=["metadatas"])
        metadatas = data.get("metadatas") or []
        bronnen = sorted({
            m.get("bestandsnaam", "onbekend")
            for m in metadatas
            if m
        })
        return CollectionStats(
            collectie_naam=collectie.name,
            aantal_documenten=len(metadatas),
            unieke_bronnen=bronnen,
        )
    except Exception as exc:
        logger.error("Fout bij ophalen statistieken: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
