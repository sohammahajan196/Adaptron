"""Minimal plain-Python pipeline — no framework extras required.

Matches the README quickstart: ``wrap`` + ``>>``, with the default
``str → dict`` adapter inserted automatically between mismatched ports.

Run from the repo root (after ``pip install -e .``)::

    python examples/plain_python_pipeline.py

Or with verbose stage logs::

    python examples/plain_python_pipeline.py --verbose
"""

from __future__ import annotations

import argparse
import logging
import sys

from adaptron import Pipeline, wrap


def to_upper(text: str) -> str:
    """Uppercase the input string."""
    return text.upper()


def word_count(payload: dict) -> dict:
    """Count words in ``payload["text"]`` (expects a dict from the adapter)."""
    return {"words": len(payload["text"].split())}


def build_pipeline() -> Pipeline:
    """Build the demo pipeline (``str`` → adapter → ``dict``)."""
    # Default str -> dict adapter inserts automatically (exact type match only).
    return wrap(to_upper) >> wrap(word_count)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "text",
        nargs="?",
        default="hello adaptron",
        help="Input string (default: %(default)r)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Log each agent and adapter stage",
    )
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    pipeline = build_pipeline()
    result = pipeline.run(args.text, verbose=args.verbose)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
