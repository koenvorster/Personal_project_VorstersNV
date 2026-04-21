"""
scripts/analyse_project.py

VorstersNV IT/AI Consultancy — Codebase Analyse Tool

Gebruik:
    python scripts/analyse_project.py --pad <codebase_pad> --klant <naam> [opties]

Voorbeelden:
    # Analyseer lpb_unified_master (loonberekening)
    python scripts/analyse_project.py \\
        --pad "C:/Users/kvo/Desktop/lpbunified-master/spring/lima/lima-server/src/main/java/be/schaubroeck/lpb/rkm/rekenmotor" \\
        --klant "LPB Unified" \\
        --taal java \\
        --doelgroep it_team

    # Droge run (toont bestanden zonder Ollama aan te roepen)
    python scripts/analyse_project.py --pad <pad> --klant <naam> --dry-run

    # Analyseer slechts bepaalde bestanden
    python scripts/analyse_project.py --pad <pad> --klant <naam> --filter "Reken*.java"
"""
from __future__ import annotations

import argparse
import asyncio
import fnmatch
import logging
import sys
from datetime import date
from pathlib import Path

# Voeg project root toe aan PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("analyse_project")

# Maximum tekens per code-chunk die naar de agent gestuurd wordt
MAX_CHUNK_CHARS = 1_500
# Maximum bestanden voor volledige analyse (anders: sampling)
MAX_FILES_FULL = 20
# Bestanden die als eerste geanalyseerd worden (entry points)
PRIORITY_PATTERNS = [
    "*RekenChainFactory*.java",
    "*AbstractReken*.java",
    "*RekenCommand*.java",
    "*Service*.java",
    "*Main*.java",
    "*Application*.java",
    "index.py",
    "main.py",
    "app.py",
]


def ontdek_bestanden(
    pad: Path,
    extensies: list[str],
    filter_patroon: str | None = None,
) -> list[Path]:
    """Ontdek alle broncode bestanden in een map."""
    bestanden: list[Path] = []
    for ext in extensies:
        bestanden.extend(pad.rglob(f"*{ext}"))

    if filter_patroon:
        bestanden = [b for b in bestanden if fnmatch.fnmatch(b.name, filter_patroon)]

    # Sorteer: priority patterns eerst, dan op grootte (groot = meer logica)
    def prioriteit(bestand: Path) -> tuple[int, int]:
        is_prio = any(fnmatch.fnmatch(bestand.name, p) for p in PRIORITY_PATTERNS)
        return (0 if is_prio else 1, -bestand.stat().st_size)

    return sorted(bestanden, key=prioriteit)


def groepeer_in_chunks(bestanden: list[Path], max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Groepeer bestanden in chunks die niet groter zijn dan max_chars."""
    chunks: list[str] = []
    huidige_chunk = ""
    huidige_grootte = 0

    for bestand in bestanden:
        try:
            inhoud = bestand.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            logger.warning("Kan bestand niet lezen: %s — %s", bestand, e)
            continue

        bestand_header = f"\n// === BESTAND: {bestand.name} ===\n"
        toe_te_voegen = bestand_header + inhoud

        # Als een enkel bestand groter is dan max_chars, knip het af
        if len(toe_te_voegen) > max_chars:
            toe_te_voegen = toe_te_voegen[:max_chars] + "\n// ... [afgekapt]"

        if huidige_grootte + len(toe_te_voegen) > max_chars and huidige_chunk:
            chunks.append(huidige_chunk)
            huidige_chunk = toe_te_voegen
            huidige_grootte = len(toe_te_voegen)
        else:
            huidige_chunk += toe_te_voegen
            huidige_grootte += len(toe_te_voegen)

    if huidige_chunk:
        chunks.append(huidige_chunk)

    return chunks


def druk_overzicht_af(bestanden: list[Path], taal: str, klant: str) -> None:
    """Druk een overzicht af van wat geanalyseerd zou worden."""
    totale_grootte = sum(b.stat().st_size for b in bestanden)
    print(f"\n{'='*60}")
    print(f"  ANALYSE OVERZICHT — {klant}")
    print(f"{'='*60}")
    print(f"  Taal:          {taal.upper()}")
    print(f"  Bestanden:     {len(bestanden)}")
    print(f"  Totale grootte: {totale_grootte / 1024:.1f} KB")
    print(f"  Chunks:        {len(groepeer_in_chunks(bestanden))}")
    print()
    print("  Grootste bestanden (top 10):")
    for b in sorted(bestanden, key=lambda x: x.stat().st_size, reverse=True)[:10]:
        print(f"    {b.stat().st_size / 1024:6.1f} KB  {b.name}")
    print()
    print("  Priority bestanden (worden eerst geanalyseerd):")
    prio = [b for b in bestanden if any(fnmatch.fnmatch(b.name, p) for p in PRIORITY_PATTERNS)]
    for b in prio[:10]:
        print(f"    ✓ {b.name}")
    print(f"{'='*60}\n")


async def analyseer_met_agent(
    chunks: list[str],
    klant: str,
    taal: str,
    doelgroep: str,
    business_context: str,
) -> list[str]:
    """Analyseer code chunks via de code_analyse_agent."""
    from ollama.agent_runner import get_runner  # type: ignore[import]

    runner = get_runner()
    resultaten: list[str] = []

    for i, chunk in enumerate(chunks, 1):
        logger.info("Analyseer chunk %d/%d (%d tekens)...", i, len(chunks), len(chunk))
        try:
            prompt = f"""
Analyseer de volgende {taal.upper()} broncode voor klant: {klant}
Business context: {business_context}
Doelgroep: {doelgroep}
Analyse type: volledig

CODE:
{chunk}
"""
            antwoord, interaction_id, _ = await runner.run_agent(
                "code_analyse_agent",
                prompt,
                context={
                    "klant": klant,
                    "taal": taal,
                    "doelgroep": doelgroep,
                    "chunk_nr": i,
                    "totaal_chunks": len(chunks),
                },
            )
            resultaten.append(antwoord)
            logger.info("Chunk %d klaar (interaction_id: %s)", i, interaction_id)

        except Exception as exc:
            logger.error("Fout bij chunk %d: %s", i, exc)
            resultaten.append(f"[FOUT bij chunk {i}: {exc}]")

    return resultaten


async def genereer_klantrapport(
    analyse_resultaten: list[str],
    klant: str,
    doelgroep: str,
) -> str:
    """Genereer een professioneel klantrapport via de klant_rapport_agent."""
    from ollama.agent_runner import get_runner  # type: ignore[import]

    runner = get_runner()

    bevindingen = "\n\n---\n\n".join(analyse_resultaten)
    prompt = f"""
Genereer een professioneel Code Analyse Rapport voor klant: {klant}
Doelgroep: {doelgroep}
Rapport type: code_analyse_rapport

Bevindingen van de code analyse:
{bevindingen[:8000]}  # Eerste 8000 tekens van de bevindingen
"""
    antwoord, _, _ = await runner.run_agent(
        "klant_rapport_agent",
        prompt,
        context={"klant_naam": klant, "doelgroep": doelgroep},
    )
    return antwoord


def sla_rapport_op(rapport: str, klant: str, uitvoer_map: Path) -> Path:
    """Sla het rapport op als markdown bestand."""
    uitvoer_map.mkdir(parents=True, exist_ok=True)
    datum = date.today().isoformat()
    bestandsnaam = f"{klant.replace(' ', '_')}_{datum}_code_analyse.md"
    pad = uitvoer_map / bestandsnaam
    pad.write_text(rapport, encoding="utf-8")
    return pad


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="VorstersNV Codebase Analyse Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--pad", required=True, help="Pad naar de codebase map")
    parser.add_argument("--klant", required=True, help="Naam van de klant/project")
    parser.add_argument("--taal", default="java", choices=["java", "python", "csharp", "php", "javascript", "typescript"], help="Programmeertaal")
    parser.add_argument("--doelgroep", default="it_team", choices=["directie", "it_team", "business_analist"], help="Doelgroep voor het rapport")
    parser.add_argument("--context", default="", help="Business context: wat doet dit systeem?")
    parser.add_argument("--filter", default=None, help="Glob patroon om bestanden te filteren (bijv. 'Reken*.java')")
    parser.add_argument("--uitvoer", default="logs/analyse_rapporten", help="Map voor output rapporten")
    parser.add_argument("--dry-run", action="store_true", help="Toon wat geanalyseerd zou worden zonder Ollama aan te roepen")
    parser.add_argument("--max-bestanden", type=int, default=MAX_FILES_FULL, help="Maximum aantal bestanden voor volledige analyse")

    args = parser.parse_args()

    codebase_pad = Path(args.pad)
    if not codebase_pad.exists():
        logger.error("Codebase pad bestaat niet: %s", codebase_pad)
        sys.exit(1)

    # Extensies op basis van taal
    extensie_map = {
        "java": [".java"],
        "python": [".py"],
        "csharp": [".cs"],
        "php": [".php"],
        "javascript": [".js", ".jsx"],
        "typescript": [".ts", ".tsx"],
    }
    extensies = extensie_map.get(args.taal, [".java"])

    # Ontdek bestanden
    logger.info("Bestanden scannen in: %s", codebase_pad)
    bestanden = ontdek_bestanden(codebase_pad, extensies, args.filter)

    if not bestanden:
        logger.error("Geen bestanden gevonden voor taal '%s' in %s", args.taal, codebase_pad)
        sys.exit(1)

    # Beperk aantal bestanden als --max-bestanden is ingesteld
    if len(bestanden) > args.max_bestanden:
        logger.warning(
            "%d bestanden gevonden — beperkt tot %d (gebruik --max-bestanden om te wijzigen)",
            len(bestanden), args.max_bestanden,
        )
        bestanden = bestanden[:args.max_bestanden]

    druk_overzicht_af(bestanden, args.taal, args.klant)

    if args.dry_run:
        print("✓ Droge run compleet — gebruik zonder --dry-run om de analyse te starten.")
        return

    # Groepeer in chunks
    chunks = groepeer_in_chunks(bestanden)
    logger.info("%d bestanden → %d analyse-chunks", len(bestanden), len(chunks))

    # Stap 1: Code analyse via Ollama agent
    print(f"\n🔍 Start code analyse ({len(chunks)} chunks)...")
    try:
        resultaten = await analyseer_met_agent(
            chunks,
            klant=args.klant,
            taal=args.taal,
            doelgroep=args.doelgroep,
            business_context=args.context or f"Codebase analyse voor {args.klant}",
        )
    except ImportError:
        logger.error("Kan ollama module niet importeren. Zorg dat je in de project root staat.")
        sys.exit(1)

    # Stap 2: Klantrapport genereren
    print("\n📄 Rapport genereren...")
    rapport = await genereer_klantrapport(resultaten, args.klant, args.doelgroep)

    # Stap 3: Rapport opslaan
    uitvoer_map = PROJECT_ROOT / args.uitvoer
    rapport_pad = sla_rapport_op(rapport, args.klant, uitvoer_map)
    print(f"\n✅ Rapport opgeslagen: {rapport_pad}")
    print(f"   Klant:     {args.klant}")
    print(f"   Bestanden: {len(bestanden)}")
    print(f"   Chunks:    {len(chunks)}")
    print(f"   Rapport:   {rapport_pad.name}")


if __name__ == "__main__":
    asyncio.run(main())
