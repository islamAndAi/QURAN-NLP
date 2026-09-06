"""Command-line interface.

Usage:
    python -m quran_nlp search "mercy" [--arabic] [--k 10]
    python -m quran_nlp ayah 2:255
    quran-nlp search "patience"          # if installed as a package
"""

import argparse
import sys

from .data import load_quran, load_translations, load_tafaseer
from .search import EnglishSearch, search_arabic



def _cmd_search(args):
    if args.semantic:
        try:
            from .embeddings import SemanticSearch
        except ImportError as e:
            print(f"Semantic search unavailable: {e}\n"
                  "Install it with: pip install -e \".[semantic]\"", file=sys.stderr)
            return 1
        try:
            ss = SemanticSearch(model_name=args.model)
            results = ss.search(args.query, k=args.k)
        except FileNotFoundError as e:
            print(f"{e}\nRun: python scripts/build_embeddings.py", file=sys.stderr)
            return 1
    elif args.arabic:
        results = search_arabic(args.query, k=args.k)
    else:
        results = EnglishSearch().search(args.query, k=args.k)
    if not results:
        print("No results.")
        return 0
    for r in results:
        print(f"[{r.reference:>7}]  score={r.score}")
        print(f"   ar: {r.arabic}")
        print(f"   en: {r.preview()}")
        print()
    return 0


def _cmd_ayah(args):
    ref = args.ref
    if ":" not in ref:
        print("Reference must be 'surah:ayah', e.g. 2:255", file=sys.stderr)
        return 1
    surah, ayah = ref.split(":", 1)
    try:
        surah, ayah = int(surah), int(ayah)
    except ValueError:
        print("Reference must be 'surah:ayah', e.g. 2:255", file=sys.stderr)
        return 1

    quran = load_quran()
    target = None
    for r in quran:
        if int(r["surah_no"]) == surah and int(r["ayah_no_surah"]) == ayah:
            target = r
            break
    if target is None:
        print(f"Ayah {ref} not found.", file=sys.stderr)
        return 1

    ayah_no = int(target["ayah_no_quran"])
    print(f"Quran {ref}  ({target['surah_name_en']})")
    print(f"  Arabic: {target['ayah_ar']}")
    print("  Translations:")
    for r in load_translations():
        if int(r["ayah_no_quran"]) == ayah_no:
            print(f"    - {r['translator']}: {r['text']}")
    print("  Tafaseer:")
    for r in load_tafaseer():
        if int(r["ayah_no_quran"]) == ayah_no:
            print(f"    - {r['tafsir']}: {r['text'][:200]}")
    return 0


def _cmd_graph(args):
    from .graph import build_graph

    if args.graph_command == "build":
        g = build_graph()
        g.export(args.out)
        print(f"Exported knowledge graph to {args.out}")
        return 0
    if args.graph_command == "stats":
        g = build_graph()
        stats = g.stats()
        for label, n in sorted(stats["nodes"].items()):
            print(f"{label:<9} {n}")
        for type_, n in sorted(stats["edges"].items()):
            print(f"{type_:<12} {n}")
        print(f"unresolved_chain_ids: {stats['unresolved_chain_ids']}")
        print(f"chainless_hadiths:   {stats['chainless_hadiths']}")
        return 0
    return 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="quran-nlp", description="Search and explore QURAN-NLP data")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("search", help="search the Quran (BM25, semantic, or Arabic)")
    p.add_argument("query")
    p.add_argument("--arabic", action="store_true", help="Arabic search (diacritic-insensitive)")
    p.add_argument("--semantic", action="store_true", help="semantic (embedding) search")
    p.add_argument("--model", default=None, help="embedding model (semantic only)")
    p.add_argument("--k", type=int, default=10)
    p.set_defaults(func=_cmd_search)

    p = sub.add_parser("ayah", help="show an ayah with all translations and tafaseer")
    p.add_argument("ref", help="surah:ayah, e.g. 2:255")
    p.set_defaults(func=_cmd_ayah)

    p = sub.add_parser("graph", help="build and inspect the knowledge graph")
    gsub = p.add_subparsers(dest="graph_command", required=True)
    gb = gsub.add_parser("build", help="build and export the graph")
    gb.add_argument("--out", default="data/graph")
    gb.set_defaults(func=_cmd_graph)
    gs = gsub.add_parser("stats", help="print graph node/edge counts")
    gs.set_defaults(func=_cmd_graph)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
