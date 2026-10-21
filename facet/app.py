"""Command-line entry point."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .bootstrap import build_services


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv if argv is None else argv
    parser = argparse.ArgumentParser(prog="facet", description="A light 3D model viewer.")
    parser.add_argument("file", nargs="?", type=Path,
                        help="a model to open (.stl, .obj, .ply, .3mf)")
    parser.add_argument("--demo", action="store_true", help="open a sample model")
    args, qt_args = parser.parse_known_args(argv[1:])

    services = build_services()
    # Imported late so `--help` works without a display.
    from .presentation.qt_app import run

    return run(services, [argv[0], *qt_args], file=args.file, demo=args.demo)
