"""
Arabic text normalization helpers for QURAN-NLP.

Purpose: bring Uthmani (quran.csv / Tanzil-style) and Imla'i (altafsir-style)
orthographies onto a common, diacritic-free surface form so that verse text
from different sources can be compared and aligned.

The normalization is intentionally *lossy* and meant for matching only, not
for display or recitation. It:

  * removes tatweel (kashida)
  * maps every alef variant (long/superscript alef, alef-wasla, madda/hamza
    carriers) to a plain alef
  * strips harakat, shadda, sukun, hamza marks and the Quranic annotation
    marks (small high signs, sajdah marks, etc.)
  * maps teh marbuta -> heh and alef maqsura -> yeh
  * drops the standalone hamza glyph
  * collapses whitespace

Only Python's stdlib is required.
"""

import re

# Any alef-shaped letter -> plain alef (U+0627).
# U+0670 ARABIC LETTER SUPERSCRIPT ALEF  (Uthmani long "aa", e.g. الرَّحْمَٰنِ)
# U+0671 ARABIC LETTER ALEF WASLA       (definite article "ٱل", Bismillah)
# U+0622 ARABIC LETTER ALEF WITH MADDA ABOVE (آ)
# U+0623 ARABIC LETTER ALEF WITH HAMZA ABOVE (أ)
# U+0625 ARABIC LETTER ALEF WITH HAMZA BELOW (إ)
_ALEF_VARIANTS = "\u0670\u0671\u0622\u0623\u0625"

# Combining marks to strip: harakat (064B-0652), madda/hamza/subscript
# (0653-065F), Quranic annotation marks (0610-061A, 06D6-06ED) and the
# extended Arabic marks (08D3-08FF).
_STRIP_RE = re.compile("[\u064B-\u065F\u0610-\u061A\u06D6-\u06ED\u08D3-\u08FF]")


def normalize_arabic(text):
    """Return a diacritic-free, alef-normalized form of *text* for matching."""
    if not text:
        return ""
    s = text
    s = s.replace("\u0640", "")            # tatweel / kashida
    s = s.replace("\u0649\u0670", "\u0649")  # alef-maqsura + superscript-alef -> alef-maqsura
    for ch in _ALEF_VARIANTS:
        s = s.replace(ch, "\u0627")        # every alef variant -> plain alef
    s = _STRIP_RE.sub("", s)               # harakat + annotation marks
    s = s.replace("\u0629", "\u0647")      # teh marbuta -> heh
    s = s.replace("\u0649", "\u064A")      # alef maqsura -> yeh
    s = s.replace("\u0621", "")            # standalone hamza
    s = re.sub(r"\s+", " ", s).strip()
    return s
