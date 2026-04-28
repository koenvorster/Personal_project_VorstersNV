"""
VorstersNV RAG Engine — W7-01
Retrieval-Augmented Generation pipeline voor de consultancy analyse pipeline.

Architectuur:
    CodeChunk (adaptive_chunker)
        └─► EmbeddingEngine.embed()      → list[float]  (384-dim vector)
                └─► VectorStore.add_document()           (in-memory dict)
                        └─► VectorStore.search()         (cosine similarity)
                                └─► RAGEngine.get_context() → prompt string

Embedding strategie (auto-detect):
    1. SentenceTransformerEngine  — all-MiniLM-L6-v2 (384 dim), semantisch correct
       Vereist: `pip install sentence-transformers`  → lazy-geladen bij eerste gebruik
    2. HashEmbeddingEngine        — sha256-gebaseerd, deterministisch, GEEN ML
       Fallback als sentence-transformers niet beschikbaar is.
       Geschikt voor testen en ontwikkeling; NIET voor productie semantic search.

Tenant-isolatie:
    Alle opslag is gesegmenteerd op project_id.  Een tenant kan nooit documenten
    van een andere tenant opvragen of verwijderen.

Toekomstige DB-integratie (Wave 8+):
    VectorStore wordt vervangen door een PostgreSQL-backend (vector_documents tabel).
    De migration c3d4e5f6g7h8 en VectorDocumentModel zijn reeds voorzien.

Gebruik:
    engine = get_rag_engine()
    await engine.index_chunks(project_id, chunks)
    context = await engine.get_context(project_id, "Hoe werkt de authenticatie?")
"""
from __future__ import annotations

import hashlib
import logging
import struct
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ─── Optionele import: sentence-transformers ──────────────────────────────────

try:
    from sentence_transformers import (
        SentenceTransformer as _SentenceTransformer,  # type: ignore[import-untyped]
    )
    _SENTENCE_TRANSFORMERS_AVAILABLE = True
    logger.debug("sentence-transformers beschikbaar — gebruik SentenceTransformerEngine")
except ImportError:
    _SentenceTransformer = None  # type: ignore[assignment,misc]
    _SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.info(
        "sentence-transformers niet geïnstalleerd — val terug op HashEmbeddingEngine. "
        "Installeer met: pip install sentence-transformers"
    )


# ─── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class VectorDocument:
    """
    Eén geïndexeerd code-fragment met embedding en metadata.

    Fields:
        doc_id:      UUID-string, uniek per document
        project_id:  tenant-sleutel (koppelt aan ClientProjectSpace.project_id)
        chunk_id:    verwijzing naar CodeChunk.chunk_id
        bestand:     relatief bestandspad als string
        inhoud:      de eigenlijke codetekst
        embedding:   384-dim float vector (all-MiniLM-L6-v2 of hash-fallback)
        metadata:    vrij dict — standaard bevat: taal, lijn_start, lijn_eind,
                     token_schatting
        aangemaakt_op: aanmaaktijdstip (UTC)
    """

    doc_id: str
    project_id: str
    chunk_id: str
    bestand: str
    inhoud: str
    embedding: list[float]
    metadata: dict[str, Any]
    aangemaakt_op: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass
class SearchResult:
    """
    Eén zoekresultaat uit de VectorStore.

    Fields:
        document: het gevonden VectorDocument
        score:    cosine similarity 0.0–1.0 (hoger = meer relevant)
        rank:     1-based rangorde in de resultatenlijst
    """

    document: VectorDocument
    score: float
    rank: int


# ─── Cosine similarity (pure Python) ─────────────────────────────────────────

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    Bereken de cosine similarity tussen twee vectoren.

    Vereist geen numpy — volledig pure Python.
    Retourneert 0.0 als één van de vectoren de nulvector is.

    Args:
        a: eerste vector
        b: tweede vector (zelfde dimensie als a)

    Returns:
        Cosine similarity in het bereik [0.0, 1.0]
    """
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


# ─── VectorStore ──────────────────────────────────────────────────────────────

class VectorStore:
    """
    In-memory vector store met tenant-isolatie per project_id.

    Opslag: dict[project_id → list[VectorDocument]]
    Zoeken: brute-force cosine similarity (geschikt voor Wave 7; schaal later naar
            pgvector of ANN-index bij >10k documenten per project).

    Thread-safety: voor Wave 7 (single-threaded async) voldoende.
    """

    def __init__(self) -> None:
        self._documents: dict[str, list[VectorDocument]] = {}

    # ── Schrijven ─────────────────────────────────────────────────────────────

    def add_document(self, doc: VectorDocument) -> None:
        """
        Voeg één VectorDocument toe aan de store.

        Args:
            doc: het te indexeren document
        """
        if doc.project_id not in self._documents:
            self._documents[doc.project_id] = []
        self._documents[doc.project_id].append(doc)
        logger.debug(
            "VectorStore: doc %s toegevoegd aan project %s (totaal: %d)",
            doc.doc_id[:8],
            doc.project_id[:8],
            len(self._documents[doc.project_id]),
        )

    # ── Zoeken ────────────────────────────────────────────────────────────────

    def search(
        self,
        project_id: str,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[SearchResult]:
        """
        Zoek de meest relevante documenten via cosine similarity.

        Args:
            project_id:      tenant-sleutel
            query_embedding: embedding van de zoekvraag (384-dim)
            top_k:           maximaal aantal resultaten

        Returns:
            Gesorteerde lijst van SearchResult (best eerst), maximaal top_k items
        """
        docs = self._documents.get(project_id, [])
        if not docs:
            logger.debug(
                "VectorStore.search: geen documenten voor project %s", project_id[:8]
            )
            return []

        gescoord: list[tuple[float, VectorDocument]] = [
            (_cosine_similarity(query_embedding, doc.embedding), doc)
            for doc in docs
        ]
        gescoord.sort(key=lambda t: t[0], reverse=True)

        return [
            SearchResult(document=doc, score=score, rank=rank)
            for rank, (score, doc) in enumerate(gescoord[:top_k], start=1)
        ]

    # ── Ophalen ───────────────────────────────────────────────────────────────

    def get_by_project(self, project_id: str) -> list[VectorDocument]:
        """
        Haal alle documenten op voor één project (tenant).

        Args:
            project_id: tenant-sleutel

        Returns:
            Kopie van de documentenlijst (leeg als project onbekend)
        """
        return list(self._documents.get(project_id, []))

    # ── Verwijderen ───────────────────────────────────────────────────────────

    def delete_project(self, project_id: str) -> int:
        """
        Verwijder alle documenten voor één project.

        Args:
            project_id: tenant-sleutel

        Returns:
            Aantal verwijderde documenten (0 als project onbekend was)
        """
        docs = self._documents.pop(project_id, [])
        count = len(docs)
        if count:
            logger.info(
                "VectorStore: %d documenten verwijderd voor project %s",
                count,
                project_id[:8],
            )
        return count

    # ── Tellen ────────────────────────────────────────────────────────────────

    def count(self, project_id: str) -> int:
        """
        Geef het aantal geïndexeerde documenten voor één project.

        Args:
            project_id: tenant-sleutel

        Returns:
            Aantal documenten (0 als project onbekend)
        """
        return len(self._documents.get(project_id, []))


# ─── EmbeddingEngine implementaties ──────────────────────────────────────────

class SentenceTransformerEngine:
    """
    Embedding engine op basis van sentence-transformers all-MiniLM-L6-v2.

    - 384-dimensionele dense vector
    - Semantisch correct: synoniemen krijgen vergelijkbare embeddings
    - Model wordt lazy-geladen bij eerste gebruik (≈ 80 MB RAM)
    - Aanbevolen voor productiegebruik

    Vereist: pip install sentence-transformers
    """

    MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    _model: Optional[Any] = None  # lazy-geladen _SentenceTransformer instantie

    def _get_model(self) -> Any:
        """Lazy-laad het SentenceTransformer model (eenmalig)."""
        if SentenceTransformerEngine._model is None:
            logger.info(
                "SentenceTransformerEngine: model %s laden...", self.MODEL_NAME
            )
            SentenceTransformerEngine._model = _SentenceTransformer(self.MODEL_NAME)
            logger.info("SentenceTransformerEngine: model geladen")
        return SentenceTransformerEngine._model

    def embed(self, tekst: str) -> list[float]:
        """
        Genereer een 384-dim embedding voor één tekst.

        Args:
            tekst: willekeurige tekst (code, vraag, ...)

        Returns:
            list van 384 floats (genormaliseerd)
        """
        model = self._get_model()
        vector = model.encode(tekst, normalize_embeddings=True)
        return vector.tolist()

    def embed_batch(self, teksten: list[str]) -> list[list[float]]:
        """
        Genereer embeddings voor een lijst van teksten (batch, efficiënter).

        Args:
            teksten: lijst van tekststrings

        Returns:
            Lijst van 384-dim float lijsten
        """
        if not teksten:
            return []
        model = self._get_model()
        vectors = model.encode(teksten, normalize_embeddings=True)
        return [v.tolist() for v in vectors]


class HashEmbeddingEngine:
    """
    Deterministisch embedding-alternatief op basis van SHA-256 + struct.

    Strategie:
        1. Bereken SHA-256 van de (UTF-8 gecodeerde) tekst
        2. Herhaal de 32-byte hash tot 384 floats gevuld zijn
           (via struct.unpack_from op circulaire window)
        3. Normaliseer naar unit vector (L2-norm = 1.0)

    Eigenschappen:
        ✓ Deterministisch: zelfde tekst → zelfde vector altijd
        ✓ Geen externe afhankelijkheden
        ✓ Snel (µs per embedding)
        ✗ GEEN semantische betekenis: "auto" en "car" krijgen totaal andere vectoren
        ✗ Niet geschikt voor productie semantic search

    Gebruik: lokale ontwikkeling en tests zonder GPU/internet.
    """

    EMBEDDING_DIM: int = 384

    def embed(self, tekst: str) -> list[float]:
        """
        Genereer een 384-dim deterministisch embedding voor één tekst.

        Args:
            tekst: willekeurige tekst

        Returns:
            list van 384 floats (genormaliseerd naar unit vector)
        """
        # ── Stap 1: SHA-256 van de tekst ──────────────────────────────
        digest = hashlib.sha256(tekst.encode("utf-8", errors="replace")).digest()

        # ── Stap 2: vul 384 floats via circulaire struct.unpack ───────
        # struct.unpack_from("f", buffer, offset) leest 4 bytes als float32.
        # Digest is 32 bytes → herhaal circlair tot 384 * 4 = 1536 bytes nodig.
        source = digest * (1536 // len(digest) + 1)  # minstens 1536 bytes
        raw: list[float] = [
            struct.unpack_from("f", source, i * 4)[0]
            for i in range(self.EMBEDDING_DIM)
        ]

        # ── Stap 3: vervang NaN/Inf door 0.0 (struct float edge cases) ─
        raw = [
            v if not (v != v or v == float("inf") or v == float("-inf")) else 0.0
            for v in raw
        ]

        # ── Stap 4: normaliseer naar unit vector ──────────────────────
        norm = sum(x * x for x in raw) ** 0.5
        if norm == 0.0:
            # Nulvector is onwaarschijnlijk maar veilig afhandelen
            return [0.0] * self.EMBEDDING_DIM

        return [x / norm for x in raw]

    def embed_batch(self, teksten: list[str]) -> list[list[float]]:
        """
        Genereer embeddings voor een lijst van teksten.

        Args:
            teksten: lijst van tekststrings

        Returns:
            Lijst van 384-dim float lijsten
        """
        return [self.embed(t) for t in teksten]


# ─── Singletons embedding engines ────────────────────────────────────────────

_embedding_engine: Optional[SentenceTransformerEngine | HashEmbeddingEngine] = None


def get_embedding_engine() -> SentenceTransformerEngine | HashEmbeddingEngine:
    """
    Singleton accessor voor de embedding engine.

    Auto-detecteert sentence-transformers: geeft SentenceTransformerEngine als
    de bibliotheek geïnstalleerd is, anders HashEmbeddingEngine.

    Returns:
        De actieve embedding engine instantie
    """
    global _embedding_engine
    if _embedding_engine is None:
        if _SENTENCE_TRANSFORMERS_AVAILABLE:
            _embedding_engine = SentenceTransformerEngine()
            logger.info("get_embedding_engine: SentenceTransformerEngine actief")
        else:
            _embedding_engine = HashEmbeddingEngine()
            logger.info("get_embedding_engine: HashEmbeddingEngine actief (fallback)")
    return _embedding_engine


# ─── RAGEngine ────────────────────────────────────────────────────────────────

class RAGEngine:
    """
    Combineert EmbeddingEngine en VectorStore tot een volledige RAG-pipeline.

    Workflow:
        1. index_chunks()   — chunk embeddings genereren en opslaan
        2. search()         — vraag embedden en meest relevante chunks ophalen
        3. get_context()    — zoekresultaten formatteren als LLM-prompt context

    Tenant-isolatie: alle methoden vereisen een project_id.

    Args:
        embedding_engine: optioneel — overschrijf de standaard engine (voor tests)
        vector_store:     optioneel — overschrijf de standaard store (voor tests)
    """

    def __init__(
        self,
        embedding_engine: Optional[SentenceTransformerEngine | HashEmbeddingEngine] = None,
        vector_store: Optional[VectorStore] = None,
    ) -> None:
        self._embedding_engine = embedding_engine or get_embedding_engine()
        self._vector_store = vector_store or VectorStore()
        logger.debug(
            "RAGEngine geïnitialiseerd met %s",
            type(self._embedding_engine).__name__,
        )

    # ── Indexeren ─────────────────────────────────────────────────────────────

    async def index_chunks(self, project_id: str, chunks: list[Any]) -> int:
        """
        Indexeer een lijst van CodeChunk objecten voor één project.

        Per chunk wordt:
          1. Een embedding gegenereerd (batch voor efficiëntie)
          2. Een VectorDocument aangemaakt
          3. Opgeslagen in de VectorStore

        Args:
            project_id: tenant-sleutel
            chunks:     lijst van CodeChunk objecten (uit adaptive_chunker)

        Returns:
            Aantal succesvol geïndexeerde chunks
        """
        if not chunks:
            logger.debug("index_chunks: geen chunks voor project %s", project_id[:8])
            return 0

        # Batch embedding — efficiënter dan één voor één
        teksten = [chunk.inhoud for chunk in chunks]
        try:
            embeddings = self._embedding_engine.embed_batch(teksten)
        except Exception as exc:
            logger.error(
                "index_chunks: embedding mislukt voor project %s: %s",
                project_id[:8],
                exc,
            )
            raise

        geindexeerd = 0
        for chunk, embedding in zip(chunks, embeddings):
            doc = VectorDocument(
                doc_id=str(uuid.uuid4()),
                project_id=project_id,
                chunk_id=chunk.chunk_id,
                bestand=chunk.bestand,
                inhoud=chunk.inhoud,
                embedding=embedding,
                metadata={
                    "taal": chunk.taal,
                    "lijn_start": chunk.lijn_start,
                    "lijn_eind": chunk.lijn_eind,
                    "token_schatting": chunk.token_schatting,
                    "volgnummer": chunk.volgnummer,
                    "totaal_chunks": chunk.totaal_chunks,
                },
            )
            self._vector_store.add_document(doc)
            geindexeerd += 1

        logger.info(
            "index_chunks: %d chunks geïndexeerd voor project %s",
            geindexeerd,
            project_id[:8],
        )
        return geindexeerd

    # ── Zoeken ────────────────────────────────────────────────────────────────

    async def search(
        self,
        project_id: str,
        vraag: str,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """
        Zoek de meest relevante code-chunks voor een gegeven vraag.

        Args:
            project_id: tenant-sleutel
            vraag:      vrije tekst zoekvraag
            top_k:      maximaal aantal resultaten

        Returns:
            Gesorteerde lijst van SearchResult (best eerst)
        """
        try:
            query_embedding = self._embedding_engine.embed(vraag)
        except Exception as exc:
            logger.error(
                "search: embedding van vraag mislukt (project %s): %s",
                project_id[:8],
                exc,
            )
            raise

        resultaten = self._vector_store.search(project_id, query_embedding, top_k)
        logger.debug(
            "search: %d resultaten voor project %s (top_k=%d)",
            len(resultaten),
            project_id[:8],
            top_k,
        )
        return resultaten

    # ── Context generatie ─────────────────────────────────────────────────────

    async def get_context(
        self,
        project_id: str,
        vraag: str,
        top_k: int = 3,
    ) -> str:
        """
        Zoek relevante chunks en formatteer ze als LLM-prompt context.

        Formaat per fragment:
            ### {bestand} (lijn {start}-{eind})
            ```{taal}
            {inhoud}
            ```

        Args:
            project_id: tenant-sleutel
            vraag:      vrije tekst zoekvraag
            top_k:      maximaal aantal fragments in de context

        Returns:
            Geformatteerde Markdown string, of lege string als geen resultaten
        """
        resultaten = await self.search(project_id, vraag, top_k)
        if not resultaten:
            logger.debug(
                "get_context: geen resultaten voor project %s", project_id[:8]
            )
            return ""

        onderdelen: list[str] = ["## Relevante code\n"]
        for resultaat in resultaten:
            doc = resultaat.document
            taal = doc.metadata.get("taal", "")
            lijn_start = doc.metadata.get("lijn_start", "?")
            lijn_eind = doc.metadata.get("lijn_eind", "?")

            onderdelen.append(
                f"### {doc.bestand} (lijn {lijn_start}-{lijn_eind})\n"
                f"```{taal}\n"
                f"{doc.inhoud}\n"
                f"```\n"
            )

        return "\n".join(onderdelen)

    # ── Statistieken ──────────────────────────────────────────────────────────

    def get_statistieken(self, project_id: str) -> dict[str, Any]:
        """
        Geef statistieken over de geïndexeerde documenten voor één project.

        Returns:
            dict met:
            - project_id:        de opgevraagde tenant
            - aantal_documenten: totaal geïndexeerde documenten
            - embedding_dim:     dimensie van de embeddings (0 als leeg)
            - embedding_engine:  naam van de actieve embedding engine klasse
            - taal_verdeling:    dict[taal → aantal] op basis van metadata
        """
        docs = self._vector_store.get_by_project(project_id)

        taal_verdeling: dict[str, int] = {}
        for doc in docs:
            taal = doc.metadata.get("taal", "onbekend")
            taal_verdeling[taal] = taal_verdeling.get(taal, 0) + 1

        embedding_dim = len(docs[0].embedding) if docs else 0

        return {
            "project_id": project_id,
            "aantal_documenten": len(docs),
            "embedding_dim": embedding_dim,
            "embedding_engine": type(self._embedding_engine).__name__,
            "taal_verdeling": taal_verdeling,
        }


# ─── Singleton RAGEngine ──────────────────────────────────────────────────────

_rag_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """
    Singleton accessor voor de RAGEngine.

    De engine gebruikt automatisch de beschikbare embedding engine
    (SentenceTransformer indien geïnstalleerd, anders HashEmbeddingEngine).

    Returns:
        De globale RAGEngine instantie
    """
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
        logger.info("get_rag_engine: RAGEngine singleton aangemaakt")
    return _rag_engine
