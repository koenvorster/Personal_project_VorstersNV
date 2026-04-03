#!/usr/bin/env python3
"""
Plan-mode beheer script voor VorstersNV.
Gebruik: python scripts/set_mode.py --mode <plan|build|review>
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

import yaml

MODE_FILE = Path(__file__).parent.parent / "plan" / "mode.yml"
VALID_MODES = ["plan", "build", "review"]


def read_mode() -> dict:
    """Lees het huidige mode-bestand."""
    if not MODE_FILE.exists():
        return {"mode": "plan"}
    return yaml.safe_load(MODE_FILE.read_text(encoding="utf-8"))


def write_mode(data: dict) -> None:
    """Schrijf het mode-bestand."""
    MODE_FILE.write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Beheer de plan-mode voor VorstersNV"
    )
    parser.add_argument(
        "--mode",
        choices=VALID_MODES,
        help="Stel de actieve mode in",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Toon de huidige mode",
    )
    args = parser.parse_args()

    current = read_mode()

    if args.status or (not args.mode):
        print(f"Huidige mode: {current.get('mode', 'onbekend')}")
        print(f"Beschikbare modes: {', '.join(VALID_MODES)}")
        print(f"Bijgewerkt op: {current.get('updated_at', 'onbekend')}")
        return

    if args.mode:
        old_mode = current.get("mode")
        current["mode"] = args.mode
        current["updated_at"] = datetime.now().strftime("%Y-%m-%d")
        current["updated_by"] = "gebruiker"
        write_mode(current)
        print(f"Mode gewijzigd: {old_mode} → {args.mode}")


if __name__ == "__main__":
    main()
