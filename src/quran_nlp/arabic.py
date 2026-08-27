"""Arabic text normalization for matching.

Brings Uthmani (quran.csv / Tanzil-style) and Imla'i (altafsir-style)
orthographies onto a common, diacritic-free surface form. Lossy and meant for
matching only — never for display or recitation.
"""

import re

# Alef variants -> plain alef (U+0627)
_ALEF_VARIANTS = "\u0670\u0671\u0622\u0623\u0625"

# Combining marks to strip: harakat, madda/hamza/subscript marks and the
# Quranic annotation marks.
_STRIP_RE = re.compile("[\u064B-\u065F\u0610-\u061A\u06D6-\u06ED\u08D3-\u08FF]")


def normalize_arabic(text):
    """Return a diacritic-free, alef-normalized form of *text* for matching."""
    if not text:
        return ""
    s = text
    s = s.replace("\u0640", "")              # tatweel / kashida
    s = s.replace("\u0649\u0670", "\u0649")  # alef-maqsura + superscript-alef -> alef-maqsura
    for ch in _ALEF_VARIANTS:
        s = s.replace(ch, "\u0627")          # alef variants -> plain alef
    s = _STRIP_RE.sub("", s)                 # harakat + annotation marks
    s = s.replace("\u0629", "\u0647")        # teh marbuta -> heh
    s = s.replace("\u0649", "\u064A")        # alef maqsura -> yeh
    s = s.replace("\u0621", "")              # standalone hamza
    s = re.sub(r"\s+", " ", s).strip()
    return s
