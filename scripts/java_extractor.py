"""
Java Pre-Processor voor grote codebases.

Chunks grote Java-bestanden en -packages in contextvensters van max 8K tokens
zodat Ollama ze kan analyseren zonder te vervallen of te crashen.

Gebruik:
    python scripts/java_extractor.py --path /pad/naar/java/src --output /pad/naar/output
    python scripts/java_extractor.py --path . --output ./chunks --max-tokens 6000
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
from pathlib import Path
from typing import Iterator

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

TOKENS_PER_CHAR = 0.25          # conservatieve schatting: 1 token ≈ 4 tekens
DEFAULT_MAX_TOKENS = 8_000
MIN_CHUNK_TOKENS = 500          # lege of te kleine chunks overslaan


def _estimate_tokens(text: str) -> int:
    return int(len(text) * TOKENS_PER_CHAR)


def _extract_class_name(content: str, filepath: Path) -> str:
    """Haal de (publieke) klassenaam op uit Java-broncode."""
    match = re.search(r"(?:public\s+)?(?:class|interface|enum|record)\s+(\w+)", content)
    return match.group(1) if match else filepath.stem


def _split_methods(content: str) -> list[str]:
    """Splits een Java-klasse op methodeniveau voor grote bestanden."""
    # Vind methodeblokken via accolade-balans
    chunks: list[str] = []
    lines = content.splitlines(keepends=True)
    current: list[str] = []
    depth = 0
    in_method = False

    for line in lines:
        opens = line.count("{")
        closes = line.count("}")
        depth += opens - closes

        current.append(line)

        # Methode-afsluiter: terugkeer naar diepte 1 (klasse-niveau) of 0
        if in_method and depth <= 1:
            chunks.append("".join(current))
            current = []
            in_method = False
        elif depth == 2 and not in_method:
            in_method = True

    if current:
        chunks.append("".join(current))
    return chunks or [content]


def chunk_java_file(filepath: Path, max_tokens: int = DEFAULT_MAX_TOKENS) -> Iterator[dict]:
    """
    Genereer chunks voor één Java-bestand.

    Yields dicts met: file, class_name, chunk_index, total_chunks, content, tokens
    """
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        logger.warning("Kan %s niet lezen: %s", filepath, e)
        return

    total_tokens = _estimate_tokens(content)
    class_name = _extract_class_name(content, filepath)

    if total_tokens <= max_tokens:
        yield {
            "file": str(filepath),
            "class_name": class_name,
            "chunk_index": 0,
            "total_chunks": 1,
            "content": content,
            "tokens": total_tokens,
        }
        return

    # Bestand te groot: splits op methoden
    logger.info("Groot bestand (%d tokens) — splits op methoden: %s", total_tokens, filepath.name)
    method_chunks = _split_methods(content)
    buffer: list[str] = []
    buffer_tokens = 0
    chunk_idx = 0

    def _flush(parts: list[str], idx: int) -> dict:
        joined = "".join(parts)
        return {
            "file": str(filepath),
            "class_name": class_name,
            "chunk_index": idx,
            "total_chunks": -1,        # wordt achteraf ingevuld
            "content": joined,
            "tokens": _estimate_tokens(joined),
        }

    results: list[dict] = []
    for part in method_chunks:
        part_tokens = _estimate_tokens(part)
        if buffer_tokens + part_tokens > max_tokens and buffer:
            results.append(_flush(buffer, chunk_idx))
            chunk_idx += 1
            buffer = [part]
            buffer_tokens = part_tokens
        else:
            buffer.append(part)
            buffer_tokens += part_tokens

    if buffer:
        results.append(_flush(buffer, chunk_idx))

    for r in results:
        r["total_chunks"] = len(results)
        yield r


def extract_repository(
    root: Path,
    output_dir: Path,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    pattern: str = "**/*.java",
) -> list[Path]:
    """
    Verwerk alle Java-bestanden onder `root` en schrijf chunks als JSON naar `output_dir`.

    Returns: lijst van aangemaakt output-bestanden.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    java_files = sorted(root.glob(pattern))
    logger.info("Gevonden: %d Java-bestanden in %s", len(java_files), root)

    output_files: list[Path] = []
    total_chunks = 0

    for java_file in java_files:
        relative = java_file.relative_to(root)
        safe_name = str(relative).replace(os.sep, "__").replace("/", "__")
        out_file = output_dir / f"{safe_name}.chunks.json"

        chunks = list(chunk_java_file(java_file, max_tokens))
        if not chunks:
            continue

        # Filter te kleine chunks (bijv. lege interfaces)
        chunks = [c for c in chunks if c["tokens"] >= MIN_CHUNK_TOKENS]
        if not chunks:
            logger.debug("Overgeslagen (te klein): %s", java_file.name)
            continue

        out_file.write_text(
            json.dumps(chunks, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        output_files.append(out_file)
        total_chunks += len(chunks)
        logger.info("  ✓ %s → %d chunk(s)", relative, len(chunks))

    logger.info("Klaar: %d chunks in %d bestanden → %s", total_chunks, len(output_files), output_dir)
    return output_files


def build_index(output_dir: Path) -> Path:
    """Maak een index.json met overzicht van alle chunks voor de agent."""
    index: list[dict] = []
    for chunk_file in sorted(output_dir.glob("*.chunks.json")):
        chunks = json.loads(chunk_file.read_text(encoding="utf-8"))
        for chunk in chunks:
            index.append({
                "chunk_file": chunk_file.name,
                "file": chunk["file"],
                "class_name": chunk["class_name"],
                "chunk_index": chunk["chunk_index"],
                "total_chunks": chunk["total_chunks"],
                "tokens": chunk["tokens"],
            })

    index_path = output_dir / "index.json"
    index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Index aangemaakt: %s (%d entries)", index_path, len(index))
    return index_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Java repo chunker voor Ollama analyse")
    parser.add_argument("--path", required=True, help="Root van de Java repo (src-map)")
    parser.add_argument("--output", required=True, help="Output directory voor JSON chunks")
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS, help="Max tokens per chunk")
    parser.add_argument("--pattern", default="**/*.java", help="Glob patroon voor Java-bestanden")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    output_dir = Path(args.output).resolve()

    if not root.exists():
        logger.error("Pad bestaat niet: %s", root)
        raise SystemExit(1)

    extract_repository(root, output_dir, args.max_tokens, args.pattern)
    build_index(output_dir)


if __name__ == "__main__":
    main()
