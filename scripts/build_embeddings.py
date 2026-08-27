#!/usr/bin/env python3
"""Precompute semantic-search embeddings for the canonical dataset.

Requires the ``[semantic]`` extra:  pip install -e ".[semantic]"

Usage:
    python scripts/build_embeddings.py [--model NAME] [--batch-size 32]

Embeddings are saved under ``data/embeddings/<model-slug>/`` and are consumed by
``quran_nlp.embeddings.SemanticSearch``.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from quran_nlp.embeddings import DEFAULT_MODEL, build_index  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Build QURAN-NLP embeddings")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"multilingual sentence-transformers model (default: {DEFAULT_MODEL})")
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    build_index(model_name=args.model, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
