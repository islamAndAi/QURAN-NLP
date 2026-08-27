"""Loaders for the canonical QURAN-NLP dataset (``data/canonical/``).

All loaders are stdlib-only and return lists of dicts. The canonical directory
is located relative to the package, but can be overridden with the
``QURAN_NLP_DATA`` environment variable.
"""

import csv
import os
from pathlib import Path

# src/quran_nlp/data.py -> repo root is parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[2]


def _data_dir() -> Path:
    env = os.environ.get("QURAN_NLP_DATA")
    if env:
        return Path(env)
    return _REPO_ROOT / "data" / "canonical"


DATA_DIR = _data_dir()


def _read_csv(name):
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(
            f"Canonical file {name!r} not found under {DATA_DIR}. "
            "Run `python3 scripts/normalize_data.py` first, or set QURAN_NLP_DATA."
        )
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return [dict(row) for row in reader]


def _to_int(d, *keys):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            try:
                d[k] = int(d[k])
            except (TypeError, ValueError):
                pass
    return d


def load_quran():
    """Return the per-ayah backbone (6,236 rows), keyed by ``ayah_no_quran``."""
    rows = [_to_int(r, "ayah_no_quran", "surah_no", "ayah_no_surah",
                     "juz_no", "ruko_no", "no_of_word_ayah") for r in _read_csv("quran_meta.csv")]
    return rows


def load_translations():
    """Return English translations in long format (ayah x translator)."""
    return [_to_int(r, "ayah_no_quran", "surah_no", "ayah_no_surah", "complete")
            for r in _read_csv("translations.csv")]


def load_tafaseer():
    """Return English tafaseer in long format (ayah x tafsir)."""
    return [_to_int(r, "ayah_no_quran", "surah_no", "ayah_no_surah")
            for r in _read_csv("tafaseer.csv")]


def load_footnotes():
    """Return Yusuf Ali / Asad footnotes and commentary."""
    return [_to_int(r, "surah_no", "ref_ayah_no_surah")
            for r in _read_csv("footnotes.csv")]
