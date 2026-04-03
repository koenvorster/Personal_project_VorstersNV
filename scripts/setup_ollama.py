#!/usr/bin/env python3
"""
Ollama setup script voor VorstersNV.
Controleert Ollama-installatie en downloadt benodigde modellen.
Gebruik: python scripts/setup_ollama.py
"""
import asyncio
import sys
from pathlib import Path

# Voeg project-root toe aan path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ollama.client import OllamaClient

REQUIRED_MODELS = ["llama3", "mistral"]


async def main():
    print("=== VorstersNV Ollama Setup ===\n")
    client = OllamaClient()

    # Controleer beschikbaarheid
    print("1. Controleer Ollama beschikbaarheid...")
    if not await client.is_available():
        print("   FOUT: Ollama is niet bereikbaar op http://localhost:11434")
        print("   Installeer Ollama via: https://ollama.ai")
        print("   Of start Docker Compose: docker-compose up -d ollama")
        await client.close()
        sys.exit(1)
    print("   OK: Ollama is beschikbaar!\n")

    # Toon beschikbare modellen
    print("2. Beschikbare modellen:")
    available = await client.list_models()
    for model in available:
        print(f"   - {model}")
    print()

    # Controleer vereiste modellen
    print("3. Vereiste modellen controleren:")
    missing = []
    for model in REQUIRED_MODELS:
        base = model.split(":")[0]
        found = any(base in m for m in available)
        status = "OK" if found else "ONTBREEKT"
        print(f"   [{status}] {model}")
        if not found:
            missing.append(model)
    print()

    if missing:
        print(f"4. Ontbrekende modellen downloaden: {', '.join(missing)}")
        print("   Voer handmatig uit:")
        for model in missing:
            print(f"   ollama pull {model}")
    else:
        print("4. Alle vereiste modellen zijn beschikbaar!")

    # Test met een eenvoudige query
    print("\n5. Test met llama3...")
    try:
        response = await client.generate(
            prompt="Zeg 'Hallo VorstersNV!' in het Nederlands.",
            model="llama3",
            max_tokens=50,
        )
        print(f"   Antwoord: {response[:100]}")
        print("   OK: Ollama werkt correct!\n")
    except Exception as e:
        print(f"   Fout bij testen: {e}\n")

    await client.close()
    print("=== Setup Voltooid ===")


if __name__ == "__main__":
    asyncio.run(main())
