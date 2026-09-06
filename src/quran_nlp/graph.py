"""Knowledge-graph builder for QURAN-NLP.

Builds a typed property graph linking the two big domains of the dataset:

* Quranic corpus:  ``Ayah -HAS_WORD-> Word -HAS_LEMMA-> Lemma`` and
  ``Word -HAS_ROOT-> Root`` (roots/lemmas come from the corpus morphology
  ``FEATURES`` column).
* Hadith corpus:   ``Hadith -NARRATED_BY-> Narrator`` (with isnad ``position``)
  and ``Narrator -TAUGHT/STUDIED_FROM-> Narrator`` genealogy.

The graph is exported as per-label node CSVs, a single typed ``edges.csv``, an
idempotent Neo4j ``graph.cypher`` script, and a ``graph_manifest.json``. The
build is stdlib-only and deterministic (no timestamps, stable sort order).

Encoding note: the corpus morphology stores roots/lemmas in the Quranic Arabic
Corpus (QAC) ASCII transliteration — not standard Buckwalter. Roots are clean
standard Buckwalter; lemmas may carry QAC-only symbols. Arabic display names are
taken from ``quran_lemmas.csv`` where available and transliterated only when
every character is in the standard Buckwalter table (never emitting a corrupted
glyph); otherwise ``name_ar`` is left empty.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

__all__ = [
    "KnowledgeGraph",
    "build_graph",
    "buckwalter_to_arabic",
    "can_transliterate",
]

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATA = _REPO_ROOT / "data"

# --- source paths ------------------------------------------------------------
QURAN_META = _DATA / "canonical" / "quran_meta.csv"
SURAH_INFO = _DATA / "surah" / "surah_info.csv"
MORPHOLOGY = _DATA / "quran" / "corpus" / "quran_morphology.csv"
LEMMAS = _DATA / "quran" / "corpus" / "quran_lemmas.csv"
HADITHS = _DATA / "hadith" / "kaggle_hadiths_clean.csv"
RAWIS = _DATA / "hadith" / "kaggle_rawis.csv"

_LOC_RE = re.compile(r"\((\d+):(\d+):(\d+):(\d+)\)")

# Standard Buckwalter -> Arabic. ASCII->Arabic is the unambiguous direction.
_BW2AR = {
    "'": "\u0621",  # hamza
    "|": "\u0622",  # alef madda
    ">": "\u0623",  # alef + hamza above
    "&": "\u0624",  # waw + hamza
    "<": "\u0625",  # alef + hamza below
    "}": "\u0626",  # ya + hamza
    "A": "\u0627",  # alef
    "b": "\u0628", "t": "\u062A", "v": "\u062B", "j": "\u062C",
    "H": "\u062D", "x": "\u062E", "d": "\u062F", "*": "\u0630",
    "r": "\u0631", "z": "\u0632", "s": "\u0633", "$": "\u0634",
    "S": "\u0635", "D": "\u0636", "T": "\u0637", "Z": "\u0638",
    "E": "\u0639", "g": "\u063A", "f": "\u0641", "q": "\u0642",
    "k": "\u0643", "l": "\u0644", "m": "\u0645", "n": "\u0646",
    "h": "\u0647", "w": "\u0648", "Y": "\u0649",  # alef maqsura
    "y": "\u064A",
    "F": "\u064B", "N": "\u064C", "K": "\u064D",  # tanwin
    "a": "\u064E", "u": "\u064F", "i": "\u0650",  # short vowels
    "~": "\u0651",  # shadda
    "o": "\u0652",  # sukun
    "`": "\u0670",  # superscript (dagger) alef
    "{": "\u0671",  # alef wasla
}


def can_transliterate(s: str) -> bool:
    """True if every character in *s* maps through the standard table."""
    return all(ch in _BW2AR for ch in s)


def buckwalter_to_arabic(s: str) -> str:
    """Transliterate a Buckwalter string to Arabic, or return "" if unmappable."""
    if not s or not can_transliterate(s):
        return ""
    return "".join(_BW2AR[ch] for ch in s)


def _read_rows(path: Path):
    """Yield dict rows from a CSV path."""
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            yield row


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _int(v, default=None):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


class KnowledgeGraph:
    """In-memory property graph: ``nodes`` (id -> {label, props}) and ``edges``."""

    def __init__(self):
        self.nodes = {}   # id -> {"label": str, "props": dict}
        self.edges = []   # {"source": id, "type": str, "target": id, "position": int|None}
        self.unresolved_chain_ids = set()
        self.chainless_hadiths = 0

    # -- mutation helpers ------------------------------------------------------
    def add_node(self, node_id, label, **props):
        self.nodes[node_id] = {"label": label, "props": props}

    def add_edge(self, source, type_, target, position=None):
        self.edges.append(
            {"source": source, "type": type_, "target": target, "position": position}
        )

    # -- queries ---------------------------------------------------------------
    def node_count(self, label):
        return sum(1 for n in self.nodes.values() if n["label"] == label)

    def edge_count(self, type_):
        return sum(1 for e in self.edges if e["type"] == type_)

    def stats(self):
        node_counts = {}
        for n in self.nodes.values():
            node_counts[n["label"]] = node_counts.get(n["label"], 0) + 1
        edge_counts = {}
        for e in self.edges:
            edge_counts[e["type"]] = edge_counts.get(e["type"], 0) + 1
        return {"nodes": node_counts, "edges": edge_counts,
                "unresolved_chain_ids": len(self.unresolved_chain_ids),
                "chainless_hadiths": self.chainless_hadiths}

    def neighbors(self, node_id):
        """Outgoing edges grouped by type (sorted target lists)."""
        out = {}
        for e in self.edges:
            if e["source"] == node_id:
                out.setdefault(e["type"], []).append(e["target"])
        return {t: sorted(set(ts)) for t, ts in out.items()}

    # -- derived (single-source-of-truth) projections -------------------------
    def _word_to_ayah(self):
        return {e["target"]: e["source"]
                for e in self.edges if e["type"] == "HAS_WORD"}

    def derive_ayah_roots(self):
        w2a = self._word_to_ayah()
        out = set()
        for e in self.edges:
            if e["type"] == "HAS_ROOT" and e["source"] in w2a:
                out.add((w2a[e["source"]], e["target"]))
        return sorted(out)

    def derive_ayah_lemmas(self):
        w2a = self._word_to_ayah()
        out = set()
        for e in self.edges:
            if e["type"] == "HAS_LEMMA" and e["source"] in w2a:
                out.add((w2a[e["source"]], e["target"]))
        return sorted(out)

    def derive_lemma_roots(self):
        lem = {}
        root = {}
        for e in self.edges:
            if e["type"] == "HAS_LEMMA":
                lem.setdefault(e["source"], set()).add(e["target"])
            elif e["type"] == "HAS_ROOT":
                root.setdefault(e["source"], set()).add(e["target"])
        out = set()
        for word, lemmas in lem.items():
            for r in root.get(word, ()):
                for l in lemmas:
                    out.add((l, r))
        return sorted(out)

    # -- export ----------------------------------------------------------------
    def export(self, output_dir):
        """Write node CSVs, edges.csv, graph.cypher and graph_manifest.json."""
        out = Path(output_dir)
        nodes_dir = out / "nodes"
        nodes_dir.mkdir(parents=True, exist_ok=True)

        label_cols = {
            "Surah": ["id", "no", "name_en", "name_ar", "name_roman",
                      "verses", "rukus", "place"],
            "Ayah": ["id", "no", "surah_no", "ayah_no_surah", "surah_name_en",
                     "surah_name_ar", "text_ar", "juz_no", "ruko_no",
                     "sajdah_no", "place", "word_count"],
            "Word": ["id", "surah", "ayah", "word_no", "form", "tag", "pos"],
            "Root": ["id", "name", "name_ar"],
            "Lemma": ["id", "name", "name_ar", "pos", "frequency"],
            "Hadith": ["id", "hadith_id", "source", "chapter", "hadith_no",
                       "text_ar", "text_en"],
            "Narrator": ["id", "name", "generation", "birth_date_gregorian",
                         "death_date_gregorian", "area_of_interest"],
        }

        by_label = {}
        for node_id, node in self.nodes.items():
            by_label.setdefault(node["label"], []).append((node_id, node))

        for label, cols in label_cols.items():
            rows = by_label.get(label, [])
            path = nodes_dir / f"{label.lower()}.csv"
            with open(path, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
                w.writeheader()
                for node_id, node in sorted(rows):
                    row = {"id": node_id}
                    row.update(node["props"])
                    w.writerow(row)

        # edges.csv — single typed file; `position` only on NARRATED_BY.
        edge_path = out / "edges.csv"
        with open(edge_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["source", "type", "target", "position"])
            key = lambda e: (e["source"], e["type"], e["target"],
                             e["position"] if e["position"] is not None else -1)
            for e in sorted(self.edges, key=key):
                w.writerow([e["source"], e["type"], e["target"],
                            e["position"] if e["position"] is not None else ""])

        self._write_cypher(out / "graph.cypher")
        self._write_manifest(out / "graph_manifest.json")

    def _write_cypher(self, path):
        lines = []

        def esc(s):
            return s.replace("\\", "\\\\").replace("'", "\\'")

        def prop(v):
            if v is None or v == "":
                return None
            return f"'{esc(str(v))}'"

        for label in ("Surah", "Ayah", "Word", "Root", "Lemma", "Hadith", "Narrator"):
            lines.append(
                f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.id IS UNIQUE;"
            )

        for node_id, node in sorted(self.nodes.items()):
            label = node["label"]
            sets = [f"n.id = '{esc(node_id)}'"]
            for k, v in sorted(node["props"].items()):
                p = prop(v)
                if p is not None:
                    sets.append(f"n.{k} = {p}")
            lines.append(f"MERGE (n:{label} {{id: '{esc(node_id)}'}})")
            if len(sets) > 1:
                lines.append(f"  SET {', '.join(sets[1:])}")
            lines.append(";")

        for e in sorted(self.edges, key=lambda x: (x["source"], x["type"], x["target"])):
            lines.append(
                f"MATCH (a {{id: '{esc(e['source'])}'}}), "
                f"(b {{id: '{esc(e['target'])}'}}) "
                f"MERGE (a)-[:{e['type']}]->(b);"
            )

        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

    def _write_manifest(self, path):
        st = self.stats()
        manifest = {
            "generated_by": "scripts/build_graph.py",
            "node_counts": st["nodes"],
            "edge_counts": st["edges"],
            "total_nodes": sum(st["nodes"].values()),
            "total_edges": sum(st["edges"].values()),
            "unresolved_chain_ids": sorted(self.unresolved_chain_ids),
            "unresolved_chain_id_count": len(self.unresolved_chain_ids),
            "chainless_hadiths": self.chainless_hadiths,
            "input_checksums": {
                str(p.relative_to(_REPO_ROOT)): _sha256(p)
                for p in (QURAN_META, SURAH_INFO, MORPHOLOGY, LEMMAS,
                          HADITHS, RAWIS)
            },
            "disclaimer": (
                "No graph field is an authentication ruling. Narrator 'generation' "
                "is a generational tier (Companion/Follower/etc.), NOT a jarh/"
                "ta'deel reliability grade. Isnad structure is provided as-is with "
                "documented coverage gaps (see unresolved_chain_ids and "
                "chainless_hadiths)."
            ),
            "license_note": (
                "Code is Apache-2.0. The Quranic subgraph (ayah/word/root/lemma) "
                "derives from the Quranic Arabic Corpus and is safe to redistribute "
                "under its attribution terms. The hadith/narrator subgraph re-"
                "publishes third-party data (modern English translations and a "
                "modern narrator database) whose licenses are NOT yet cleared: "
                "treat it as research-use-only and do not redistribute until "
                "licenses are confirmed. See sources.md."
            ),
            "schema": {
                "node_id_patterns": {
                    "Surah": "surah:<n>",
                    "Ayah": "ayah:<ayah_no_quran>",
                    "Word": "word:<s>:<a>:<w>",
                    "Root": "root:<buckwalter>",
                    "Lemma": "lemma:<qac-ascii>",
                    "Hadith": "hadith:kaggle:<row_ind>",
                    "Narrator": "narrator:<scholar_indx>",
                },
                "edge_semantics": {
                    "IN_SURAH": "Ayah -> Surah",
                    "HAS_WORD": "Ayah -> Word",
                    "HAS_LEMMA": "Word -> Lemma",
                    "HAS_ROOT": "Word -> Root",
                    "NARRATED_BY": "Hadith -> Narrator (position = 1-based isnad order; 1 = nearest the compiler, last = Companion/source)",
                    "TAUGHT": "Narrator -> Narrator (from students_inds)",
                    "STUDIED_FROM": "Narrator -> Narrator (from teachers_inds)",
                },
            },
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, sort_keys=True, indent=2)
            fh.write("\n")


# --- build phases -------------------------------------------------------------

def _build_quran_subgraph(g: KnowledgeGraph, morphology_rows):
    # Surah nodes
    for r in _read_rows(SURAH_INFO):
        no = _int(r["SurahNumber"])
        g.add_node(
            f"surah:{no}", "Surah",
            no=no,
            name_en=r["EnglishTitle"],
            name_ar=r["ArabicTitle"],
            name_roman=r["RomanTitle"],
            verses=_int(r["NumberOfVerses"]),
            rukus=_int(r["NumberOfRukus"]),
            place=r["PlaceOfRevelation"],
        )

    # Ayah nodes + (surah, ayah) -> ayah_no_quran map
    surah_ayah_to_id = {}
    for r in _read_rows(QURAN_META):
        ayah_no = _int(r["ayah_no_quran"])
        surah_no = _int(r["surah_no"])
        ayah_no_surah = _int(r["ayah_no_surah"])
        surah_ayah_to_id[(surah_no, ayah_no_surah)] = ayah_no
        g.add_node(
            f"ayah:{ayah_no}", "Ayah",
            no=ayah_no,
            surah_no=surah_no,
            ayah_no_surah=ayah_no_surah,
            surah_name_en=r["surah_name_en"],
            surah_name_ar=r["surah_name_ar"],
            text_ar=r["ayah_ar"],
            juz_no=_int(r["juz_no"]),
            ruko_no=_int(r["ruko_no"]),
            sajdah_no=r["sajdah_no"],
            place=r["place_of_revelation"],
            word_count=_int(r["no_of_word_ayah"]),
        )
        g.add_edge(f"ayah:{ayah_no}", "IN_SURAH", f"surah:{surah_no}")

    # Lemma enrichment: QAC-ascii -> (arabic, pos, frequency)
    lemma_ar = {}
    lemma_meta = {}
    for r in _read_rows(LEMMAS):
        bw = (r["buckwalter"] or "").strip()
        ar = (r["lemma"] or "").strip()
        if not bw:
            continue
        lemma_ar[bw] = ar
        lemma_meta[bw] = {
            "pos": r["part_of_speech"] or "",
            "frequency": _int(r["frequency"], 0),
        }

    # Word nodes + Word->Root/Lemma edges (group morphology segments by word)
    words = {}  # (s, a, w) -> {"form": [], "tag": None, "pos": None, "lemmas": set, "roots": set}
    for r in morphology_rows:
        m = _LOC_RE.match(r["LOCATION"] or "")
        if not m:
            continue
        s, a, w = (int(m.group(i)) for i in (1, 2, 3))
        form = r["FORM"] or ""
        tag = r["TAG"] or ""
        feats = r["FEATURES"] or ""

        parts = feats.split("|")
        seg_type = parts[0] if parts else ""
        pos = lem = root = None
        for part in parts[1:]:
            if part.startswith("POS:"):
                pos = part[4:]
            elif part.startswith("LEM:"):
                lem = part[4:]
            elif part.startswith("ROOT:"):
                root = part[5:]

        key = (s, a, w)
        entry = words.setdefault(key, {
            "form": [], "tag": None, "pos": None, "lemmas": set(), "roots": set(),
        })
        entry["form"].append(form)
        if seg_type == "STEM":
            if entry["tag"] is None:
                entry["tag"] = tag
                entry["pos"] = pos or ""
            if lem:
                entry["lemmas"].add(lem)
            if root:
                entry["roots"].add(root)

    for (s, a, w), entry in words.items():
        word_id = f"word:{s}:{a}:{w}"
        g.add_node(
            word_id, "Word",
            surah=s, ayah=a, word_no=w,
            form="".join(entry["form"]),
            tag=entry["tag"] or "",
            pos=entry["pos"] or "",
        )
        ayah_no = surah_ayah_to_id.get((s, a))
        if ayah_no is not None:
            g.add_edge(f"ayah:{ayah_no}", "HAS_WORD", word_id)
        for lem in entry["lemmas"]:
            g.add_node(
                f"lemma:{lem}", "Lemma",
                name=lem,
                name_ar=lemma_ar.get(lem, ""),
                pos=lemma_meta.get(lem, {}).get("pos", ""),
                frequency=lemma_meta.get(lem, {}).get("frequency", 0),
            )
            g.add_edge(word_id, "HAS_LEMMA", f"lemma:{lem}")
        for root in entry["roots"]:
            g.add_node(
                f"root:{root}", "Root",
                name=root,
                name_ar=buckwalter_to_arabic(root),
            )
            g.add_edge(word_id, "HAS_ROOT", f"root:{root}")


def _build_hadith_subgraph(g: KnowledgeGraph, hadith_rows, rawis_rows):
    # Narrator nodes
    narrator_ids = set()
    for r in rawis_rows:
        idx = (r["scholar_indx"] or "").strip()
        if not idx:
            continue
        narrator_ids.add(idx)
        g.add_node(
            f"narrator:{idx}", "Narrator",
            name=r["name"] or "",
            generation=r["grade"] or "",
            birth_date_gregorian=r["birth_date_gregorian"] or "",
            death_date_gregorian=r["death_date_gregorian"] or "",
            area_of_interest=r["area_of_interest"] or "",
        )

    # Genealogy edges
    for r in rawis_rows:
        src = (r["scholar_indx"] or "").strip()
        if not src:
            continue
        for tok in (r["teachers_inds"] or "").split(","):
            tok = tok.strip()
            if tok and tok in narrator_ids:
                g.add_edge(f"narrator:{src}", "STUDIED_FROM", f"narrator:{tok}")
        for tok in (r["students_inds"] or "").split(","):
            tok = tok.strip()
            if tok and tok in narrator_ids:
                g.add_edge(f"narrator:{src}", "TAUGHT", f"narrator:{tok}")

    # Hadith nodes + NARRATED_BY edges (position = 1-based chain order).
    # The source CSV has no globally-unique key (both `id` and `hadith_id`
    # reset/duplicate across books), so the stable node key is the 0-based
    # row index of the committed file.
    for i, r in enumerate(hadith_rows):
        hadith_id = f"hadith:kaggle:{i}"
        g.add_node(
            hadith_id, "Hadith",
            hadith_id=_int(r["hadith_id"]),
            source=(r["source"] or "").strip(),
            chapter=r["chapter"] or "",
            hadith_no=(r["hadith_no"] or "").strip(),
            text_ar=r["text_ar"] or "",
            text_en=r["text_en"] or "",
        )
        chain = (r["chain_indx"] or "").strip()
        if not chain or chain.lower() in ("na", "none"):
            g.chainless_hadiths += 1
            continue
        position = 0
        for tok in chain.split(","):
            tok = tok.strip()
            if not tok:
                continue
            position += 1
            if tok in narrator_ids:
                g.add_edge(hadith_id, "NARRATED_BY", f"narrator:{tok}", position=position)
            else:
                g.unresolved_chain_ids.add(tok)


def build_graph():
    """Build the full knowledge graph from committed source CSVs."""
    g = KnowledgeGraph()

    # Preload the two large hadith/narrator tables once (shared across phases).
    hadith_rows = list(_read_rows(HADITHS))
    rawis_rows = list(_read_rows(RAWIS))

    # Stream morphology without holding all segments (the phase groups per word).
    def morphology_rows():
        for row in _read_rows(MORPHOLOGY):
            yield row

    _build_quran_subgraph(g, morphology_rows())
    _build_hadith_subgraph(g, hadith_rows, rawis_rows)
    return g
