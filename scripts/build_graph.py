"""Build and export the QURAN-NLP knowledge graph.

Usage:
    python scripts/build_graph.py [--out data/graph]

The graph is built from the committed source CSVs (stdlib only) and exported as
per-label node CSVs, ``edges.csv``, ``graph.cypher`` and ``graph_manifest.json``.
The generated ``data/graph/`` directory is gitignored — regenerate it in CI.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from quran_nlp.graph import build_graph


def main():
    parser = argparse.ArgumentParser(description="Build the QURAN-NLP knowledge graph")
    parser.add_argument("--out", default="data/graph",
                        help="output directory (default: data/graph)")
    args = parser.parse_args()

    print("Building knowledge graph ...")
    g = build_graph()
    stats = g.stats()
    print("Nodes:")
    for label, n in sorted(stats["nodes"].items()):
        print(f"  {label:<9} {n}")
    print("Edges:")
    for type_, n in sorted(stats["edges"].items()):
        print(f"  {type_:<12} {n}")
    print(f"  unresolved_chain_ids: {stats['unresolved_chain_ids']}")
    print(f"  chainless_hadiths:   {stats['chainless_hadiths']}")

    g.export(args.out)
    print(f"\nExported to {args.out}")


if __name__ == "__main__":
    main()
