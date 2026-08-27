"""quran_nlp — clean data loaders and search for the QURAN-NLP dataset.

Zero runtime dependencies (Python stdlib only). Loads the canonical long-format
dataset produced by ``scripts/normalize_data.py`` and exposes a fast BM25 search
over English translations/tafaseer plus a diacritic-insensitive Arabic search.
"""

from .data import (
    DATA_DIR,
    load_quran,
    load_translations,
    load_tafaseer,
    load_footnotes,
)
from .search import EnglishSearch, search_arabic, search, SearchResult

__version__ = "0.1.0"

__all__ = [
    "DATA_DIR",
    "load_quran",
    "load_translations",
    "load_tafaseer",
    "load_footnotes",
    "EnglishSearch",
    "search_arabic",
    "search",
    "SearchResult",
    "__version__",
]
