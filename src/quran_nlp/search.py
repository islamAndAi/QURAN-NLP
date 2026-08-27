"""Search over the canonical QURAN-NLP dataset.

Two search modes, both stdlib-only:

* :class:`EnglishSearch` — Okapi BM25 over the English translations + tafaseer.
* :func:`search_arabic` — diacritic-insensitive Arabic token/phrase matching.

Both return :class:`SearchResult` objects keyed by ``ayah_no_quran``.
"""

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field

from .arabic import normalize_arabic
from .data import load_quran, load_translations, load_tafaseer

_STOPWORDS = frozenset(
    """a an and are as at be but by for from had has have he her his i if in is
    it its of on or she so that the their them they this to was we were what
    when which who will with you your not no do does did all any been being can
    could may might shall should would there then thus also upon unto whom whose""".split()
)

_WORD_RE = re.compile(r"[a-z0-9']+")


def tokenize(text):
    return [t for t in _WORD_RE.findall(text.lower()) if t not in _STOPWORDS and len(t) > 1]


@dataclass
class SearchResult:
    ayah_no_quran: int
    surah_no: int
    ayah_no_surah: int
    score: float
    arabic: str = ""
    translations: dict = field(default_factory=dict)
    tafseer: dict = field(default_factory=dict)

    @property
    def reference(self):
        return f"{self.surah_no}:{self.ayah_no_surah}"

    def preview(self, translator="quran_dataset", limit=160):
        text = self.translations.get(translator) or next(iter(self.translations.values()), "")
        text = " ".join(text.split())
        return text[:limit] + ("…" if len(text) > limit else "")


class BM25:
    """Minimal Okapi BM25 (k1=1.5, b=0.75)."""

    def __init__(self, corpus, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.n_docs = len(corpus)
        self.doc_len = []
        self.doc_freq = defaultdict(int)   # term -> number of docs containing it
        self.term_freqs = []               # per doc: term -> count
        for text in corpus:
            tokens = tokenize(text)
            tf = defaultdict(int)
            for t in tokens:
                tf[t] += 1
            self.term_freqs.append(tf)
            self.doc_len.append(len(tokens))
            for t in tf:
                self.doc_freq[t] += 1
        self.avgdl = sum(self.doc_len) / max(1, self.n_docs)

    def _idf(self, term):
        n = self.doc_freq.get(term, 0)
        return math.log((self.n_docs - n + 0.5) / (n + 0.5) + 1.0)

    def score(self, query, doc_idx):
        tf = self.term_freqs[doc_idx]
        dl = self.doc_len[doc_idx]
        score = 0.0
        for t in tokenize(query):
            f = tf.get(t, 0)
            if f == 0:
                continue
            idf = self._idf(t)
            denom = f + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
            score += idf * f * (self.k1 + 1) / denom
        return score

    def search(self, query, k=10):
        scored = [(self.score(query, i), i) for i in range(self.n_docs)]
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [(s, i) for s, i in scored[:k] if s > 0]


class EnglishSearch:
    """BM25 search over English translations and tafaseer, one document per ayah."""

    def __init__(self):
        quran = {int(r["ayah_no_quran"]): r for r in load_quran()}
        self._ayah = {}   # ayah_no_quran -> SearchResult meta
        corpus = []
        self._order = []

        per_ayah_text = defaultdict(list)

        for r in load_translations():
            ay = int(r["ayah_no_quran"])
            per_ayah_text[ay].append(r["text"])

        for r in load_tafaseer():
            ay = int(r["ayah_no_quran"])
            per_ayah_text[ay].append(r["text"])

        # Build documents in ayah order.
        for ay in range(1, 6237):
            meta = quran.get(ay)
            if meta is None:
                continue
            texts = per_ayah_text.get(ay, [])
            self._ayah[ay] = SearchResult(
                ayah_no_quran=ay,
                surah_no=int(meta["surah_no"]),
                ayah_no_surah=int(meta["ayah_no_surah"]),
                score=0.0,
                arabic=meta["ayah_ar"],
            )
            self._order.append(ay)
            corpus.append(" ".join(texts))

        self._bm25 = BM25(corpus)
        self._translations = defaultdict(dict)
        self._tafseer = defaultdict(dict)
        for r in load_translations():
            self._translations[int(r["ayah_no_quran"])][r["translator"]] = r["text"]
        for r in load_tafaseer():
            self._tafseer[int(r["ayah_no_quran"])][r["tafsir"]] = r["text"]

    def search(self, query, k=10):
        results = []
        for score, idx in self._bm25.search(query, k):
            ay = self._order[idx]
            r = self._ayah[ay]
            r.score = round(score, 4)
            r.translations = dict(self._translations.get(ay, {}))
            r.tafseer = dict(self._tafseer.get(ay, {}))
            results.append(r)
        return results


def search_arabic(query, k=10, quran=None):
    """Diacritic-insensitive Arabic search returning ayahs ranked by overlap."""
    if quran is None:
        quran = load_quran()
    qn = normalize_arabic(query)
    qtokens = [t for t in qn.split() if len(t) > 1]

    scored = []
    for r in quran:
        an = normalize_arabic(r["ayah_ar"])
        atokens = set(an.split())
        overlap = sum(1 for t in qtokens if t in atokens)
        phrase = 1.0 if qn and len(qn) > 3 and qn in an else 0.0
        score = overlap + phrase * len(qtokens)
        if score <= 0:
            continue
        scored.append((score, r))

    scored.sort(key=lambda x: -x[0])
    out = []
    for score, r in scored[:k]:
        out.append(SearchResult(
            ayah_no_quran=int(r["ayah_no_quran"]),
            surah_no=int(r["surah_no"]),
            ayah_no_surah=int(r["ayah_no_surah"]),
            score=round(score, 4),
            arabic=r["ayah_ar"],
        ))
    return out


def search(query, k=10, arabic=False):
    """Convenience wrapper: English BM25 by default, Arabic if ``arabic=True``."""
    if arabic:
        return search_arabic(query, k)
    return EnglishSearch().search(query, k)
