"""Semantic (embedding-based) search over the canonical dataset.

This module is **optional**: it requires the ``[semantic]`` extra
(``sentence-transformers`` + ``numpy``). Imports are done lazily so the rest of
``quran_nlp`` keeps working with zero dependencies.

Design: embeddings are precomputed **offline** (see ``scripts/build_embeddings.py``)
and stored as ``.npy`` matrices + a ``meta.json``. At query time only the query is
encoded — making serving cheap (no per-request model pass over 6,236 ayahs).

Two matrices are stored per model:

* ``emb_ar.npy`` — Arabic ayah text (the primary, Uthmani text)
* ``emb_en.npy`` — concatenated English translations + tafaseer per ayah

The query language is auto-detected (Arabic vs English) and the matching matrix
is used. A single multilingual encoder handles both, so Arabic queries match the
Arabic text and English queries match the English translations/tafaseer.
"""

import json
import os
from pathlib import Path

from .data import DATA_DIR, load_quran, load_translations, load_tafaseer
from .search import SearchResult

DEFAULT_MODEL = "intfloat/multilingual-e5-small"
EMBEDDINGS_DIR = Path(DATA_DIR).parent / "embeddings"  # data/embeddings

# Model -> (query_prefix, passage_prefix). e5-style models need the prefixes;
# the plain sentence-transformers multilingual models do not.
MODEL_CONFIG = {
    "intfloat/multilingual-e5-small": ("query: ", "passage: "),
    "intfloat/multilingual-e5-base": ("query: ", "passage: "),
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": ("", ""),
    "sentence-transformers/LaBSE": ("", ""),
}


def _prefixes(model_name):
    return MODEL_CONFIG.get(model_name, ("", ""))


def detect_arabic(text):
    """Return True if *text* contains Arabic-script characters."""
    return any("\u0600" <= ch <= "\u06FF" or "\u0750" <= ch <= "\u077F" for ch in text)


def model_slug(model_name):
    return model_name.replace("/", "__").replace(":", "_")


def _load_embeddings(model_name, embeddings_dir=None):
    """Return (emb_ar, emb_en, meta). Raises if not built yet."""
    import numpy as np

    base = Path(embeddings_dir or EMBEDDINGS_DIR) / model_slug(model_name)
    meta_path = base / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(
            f"No embeddings for {model_name!r} under {base}. "
            "Run `python scripts/build_embeddings.py` first."
        )
    with open(meta_path, encoding="utf-8") as fh:
        meta = json.load(fh)
    emb_ar = np.load(base / "emb_ar.npy")
    emb_en = np.load(base / "emb_en.npy")
    return emb_ar, emb_en, meta


def build_index(model_name=DEFAULT_MODEL, batch_size=32, out_dir=None):
    """Precompute and save Arabic + English embeddings for all 6,236 ayahs."""
    import numpy as np
    from sentence_transformers import SentenceTransformer

    ayahs = sorted(load_quran(), key=lambda r: int(r["ayah_no_quran"]))

    # English text per ayah = all complete translations + all tafaseer.
    trans = {}
    for r in load_translations():
        trans.setdefault(int(r["ayah_no_quran"]), []).append(r["text"])
    tafs = {}
    for r in load_tafaseer():
        tafs.setdefault(int(r["ayah_no_quran"]), []).append(r["text"])

    ar_texts = [r["ayah_ar"] for r in ayahs]
    en_texts = [" ".join(trans.get(int(r["ayah_no_quran"]), []) + tafs.get(int(r["ayah_no_quran"]), []))
                for r in ayahs]

    print(f"Loading model {model_name} ...")
    model = SentenceTransformer(model_name)
    q_prefix, p_prefix = _prefixes(model_name)
    print(f"Encoding {len(ar_texts)} Arabic ayahs ...")
    emb_ar = model.encode([p_prefix + t for t in ar_texts], batch_size=batch_size,
                          show_progress_bar=True, normalize_embeddings=True, convert_to_numpy=True)
    print("Encoding English (translations + tafaseer) ...")
    emb_en = model.encode([p_prefix + t for t in en_texts], batch_size=batch_size,
                          show_progress_bar=True, normalize_embeddings=True, convert_to_numpy=True)

    base = Path(out_dir or EMBEDDINGS_DIR) / model_slug(model_name)
    base.mkdir(parents=True, exist_ok=True)
    np.save(base / "emb_ar.npy", emb_ar)
    np.save(base / "emb_en.npy", emb_en)
    meta = {
        "model": model_name,
        "dim": int(emb_ar.shape[1]),
        "n_ayahs": len(ayahs),
        "ayah_no_quran": [int(r["ayah_no_quran"]) for r in ayahs],
        "normalized": True,
        "query_prefix": _prefixes(model_name)[0],
        "passage_prefix": _prefixes(model_name)[1],
    }
    with open(base / "meta.json", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
    print(f"Saved embeddings to {base}")
    return base


class SemanticSearch:
    """Cosine-similarity search over precomputed embeddings."""

    def __init__(self, model_name=None, embeddings_dir=None):
        import numpy as np
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name or DEFAULT_MODEL
        self.model = SentenceTransformer(self.model_name)
        self.emb_ar, self.emb_en, self.meta = _load_embeddings(self.model_name, embeddings_dir)

        # metadata for result construction
        self._quran = {int(r["ayah_no_quran"]): r for r in load_quran()}
        self._translations = {}
        for r in load_translations():
            self._translations.setdefault(int(r["ayah_no_quran"]), {})[r["translator"]] = r["text"]
        self._tafseer = {}
        for r in load_tafaseer():
            self._tafseer.setdefault(int(r["ayah_no_quran"]), {})[r["tafsir"]] = r["text"]

    def search(self, query, k=10):
        import numpy as np

        q = self.model.encode([self.meta.get("query_prefix", "") + query],
                              normalize_embeddings=True, convert_to_numpy=True)[0]
        mat = self.emb_ar if detect_arabic(query) else self.emb_en
        sims = mat @ q
        top = np.argsort(-sims)[:k]

        results = []
        for idx in top:
            ay = self.meta["ayah_no_quran"][int(idx)]
            meta = self._quran[ay]
            results.append(SearchResult(
                ayah_no_quran=ay,
                surah_no=int(meta["surah_no"]),
                ayah_no_surah=int(meta["ayah_no_surah"]),
                score=round(float(sims[idx]), 4),
                arabic=meta["ayah_ar"],
                translations=dict(self._translations.get(ay, {})),
                tafseer=dict(self._tafseer.get(ay, {})),
            ))
        return results


def has_semantic():
    """Return True if the optional semantic dependencies are installed."""
    try:
        import sentence_transformers  # noqa: F401
        import numpy  # noqa: F401
        return True
    except ImportError:
        return False
