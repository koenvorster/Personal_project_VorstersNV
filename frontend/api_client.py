import requests
from typing import Optional
from config import API_BASE_URL


def stuur_chat_vraag(
    vraag: str,
    gebruik_documenten: bool = True,
    model: Optional[str] = None,
) -> dict:
    """Stuurt een chatvraag naar de backend en geeft het antwoord terug."""
    payload = {
        "vraag": vraag,
        "gebruik_documenten": gebruik_documenten,
    }
    if model:
        payload["model"] = model

    resp = requests.post(f"{API_BASE_URL}/chat/", json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()


def upload_documenten(bestanden: list) -> dict:
    """Upload één of meerdere bestanden naar de backend voor verwerking."""
    files = [
        ("bestanden", (b.name, b.getvalue(), b.type))
        for b in bestanden
    ]
    resp = requests.post(
        f"{API_BASE_URL}/documenten/upload",
        files=files,
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()


def haal_statistieken_op() -> dict:
    """Haalt statistieken over de vector store op."""
    resp = requests.get(f"{API_BASE_URL}/documenten/statistieken", timeout=10)
    resp.raise_for_status()
    return resp.json()


def verwijder_document(bestandsnaam: str) -> dict:
    """Verwijdert een document uit de vector store."""
    resp = requests.delete(
        f"{API_BASE_URL}/documenten/{bestandsnaam}",
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def haal_status_op() -> dict:
    """Controleert de gezondheid van de backend-services."""
    resp = requests.get(f"{API_BASE_URL}/health", timeout=10)
    resp.raise_for_status()
    return resp.json()
