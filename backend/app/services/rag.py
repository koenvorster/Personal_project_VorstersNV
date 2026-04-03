import logging
from typing import AsyncIterator

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document

from app.core.dependencies import get_llm, get_vector_store
from app.core.config import get_settings
from app.models.schemas import ChatResponse

logger = logging.getLogger(__name__)
settings = get_settings()

PROMPT_TEMPLATE = """Je bent een behulpzame zakelijke assistent voor VorstersNV.
Gebruik uitsluitend de onderstaande context om de vraag te beantwoorden.
Als het antwoord niet in de context staat, zeg dan eerlijk dat je het niet weet.
Antwoord altijd in het Nederlands.

Context:
{context}

Vraag: {question}

Antwoord:"""

RAG_PROMPT = PromptTemplate(
    template=PROMPT_TEMPLATE,
    input_variables=["context", "question"],
)


def _haal_bronnen_op(documenten: list[Document]) -> list[str]:
    """Extraheert unieke bronvermeldingen uit opgehaalde documenten."""
    gezien: set[str] = set()
    bronnen: list[str] = []
    for doc in documenten:
        bron = doc.metadata.get("bron") or doc.metadata.get("bestandsnaam", "onbekend")
        pagina = doc.metadata.get("page")
        label = f"{bron} (p. {pagina + 1})" if pagina is not None else bron
        if label not in gezien:
            gezien.add(label)
            bronnen.append(label)
    return bronnen


def beantwoord_vraag(vraag: str, model_override: str | None = None) -> ChatResponse:
    """
    Beantwoordt een vraag op basis van de ingested bedrijfsdocumenten (RAG).

    Args:
        vraag: De gebruikersvraag in natuurlijke taal.
        model_override: Optioneel: gebruik een ander Ollama-model.

    Returns:
        ChatResponse met antwoord en bronnen.
    """
    llm = get_llm()
    if model_override:
        llm.model = model_override

    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.retriever_top_k},
    )

    keten = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": RAG_PROMPT},
    )

    logger.info("RAG-vraag verwerken: %s", vraag)
    resultaat = keten.invoke({"query": vraag})

    antwoord = resultaat.get("result", "Geen antwoord gegenereerd.")
    bronnen = _haal_bronnen_op(resultaat.get("source_documents", []))

    return ChatResponse(
        antwoord=antwoord,
        bronnen=bronnen,
        model_gebruikt=llm.model,
    )


def beantwoord_vraag_direct(vraag: str, model_override: str | None = None) -> ChatResponse:
    """
    Beantwoordt een vraag zonder RAG (directe LLM-aanroep).

    Args:
        vraag: De gebruikersvraag.
        model_override: Optioneel: gebruik een ander Ollama-model.

    Returns:
        ChatResponse zonder bronvermeldingen.
    """
    llm = get_llm()
    if model_override:
        llm.model = model_override

    logger.info("Directe LLM-vraag: %s", vraag)
    antwoord = llm.invoke(vraag)

    return ChatResponse(
        antwoord=str(antwoord),
        bronnen=[],
        model_gebruikt=llm.model,
    )
