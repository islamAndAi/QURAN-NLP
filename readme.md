# QURAN‑NLP

**NLP & AI on the Qur'an — open data, tools, and search for Islamic knowledge.**

[![CI](https://github.com/islamAndAi/QURAN-NLP/actions/workflows/ci.yml/badge.svg)](https://github.com/islamAndAi/QURAN-NLP/actions/workflows/ci.yml)
[![Stars](https://img.shields.io/github/stars/islamAndAi/QURAN-NLP?style=social)](https://github.com/islamAndAi/QURAN-NLP/stargazers)
[![Forks](https://img.shields.io/github/forks/islamAndAi/QURAN-NLP?style=social)](https://github.com/islamAndAi/QURAN-NLP/forks)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.MD)
[![Kaggle](https://img.shields.io/badge/dataset-Kaggle-20BEFF.svg)](https://www.kaggle.com/datasets/alizahidraja/quran-nlp)

QURAN‑NLP is an open-source dataset and toolkit for doing machine learning and
natural-language processing on the Qur'an — and, increasingly, on Hadith. It
brings together the Arabic text, a full morphological corpus, multiple English
translations and tafaseer, and hundreds of thousands of hadiths into one
**clean, versioned, well-documented** collection, then ships a zero-dependency
Python package for loading and searching it.

---

## ✨ What you can do with it

- **Search the Qur'an semantically** — in English *and* Arabic — with BM25,
  embeddings, or diacritic-insensitive lexical matching.
- **Load any ayah** with its Uthmani Arabic, every English translation, and
  multiple tafaseer side by side.
- **Analyze the corpus** — word-by-word morphology, roots, lemmas, and verbs.
- **Work with Hadith** — the canonical collections, Shia sources, and a
  24,000‑narrator genealogy graph for isnad analysis.

---

## 🚀 Quickstart

```bash
git clone https://github.com/islamAndAi/QURAN-NLP.git
cd QURAN-NLP
pip install -e .

# Search (English BM25)
quran-nlp search "mercy" --k 5

# Show an ayah with all translations + tafaseer
quran-nlp ayah 2:255
```

**Semantic search** (optional):

```bash
pip install -e ".[semantic]"
python scripts/build_embeddings.py          # precompute embeddings (offline, ~1 min)
quran-nlp search "forgiveness" --semantic   # English, auto-detected
quran-nlp search "الصبر" --semantic         # Arabic, auto-detected
```

---

## 📚 Dataset

The repository ships a **canonical, long-format** layer in
[`data/canonical/`](data/canonical/README.md) — every Quranic row keyed by a
stable `ayah_no_quran` (1–6236) — produced from the raw sources by
`scripts/normalize_data.py` and checked by `scripts/validate_data.py`.

| Area | Contents |
|------|----------|
| **Qur'an** | 6,236 ayahs (Uthmani Arabic + word list) |
| **Corpus** | morphology (128k), dictionary (54k), lemmas (3.7k), verbs (1.5k) |
| **Translations** | 9 English (5 complete & ayah-aligned; 4 flagged) |
| **Tafaseer** | 4 English (Jalalayn, Ibn Abbas, Kashani, Qushairi) |
| **Hadith** | 700,000+ (Sanadset 650k, kaggle 34k, arabic 62k, thaqalayn 27k) |
| **Narrators** | 24,028 with teacher/student genealogy |
| **Names of Allah** | 99, richly annotated |
| **Surah info** | 114 (name, verses, rukus, revelation place) |

**Alignment status** (honest per-source): ✅ complete & verified — Yusuf Ali,
Pickthall, Arberry, Tahir‑ul‑Qadri, Quran Dataset. ⚠️ kept raw — Asad (own verse
division), Lings (fragments), Royal Aal al‑Bayt & Ibrahim Walk (internal
offsets). See [`data/canonical/README.md`](data/canonical/README.md).

---

## 🧰 Python package

```python
from quran_nlp import load_quran, load_translations, load_tafaseer
from quran_nlp import EnglishSearch, search_arabic

quran = load_quran()                  # 6,236 dicts
EnglishSearch().search("patience", k=5)
search_arabic("الرحمن الرحيم", k=5)   # diacritic-insensitive

from quran_nlp.embeddings import SemanticSearch   # needs [semantic]
SemanticSearch().search("forgiveness", k=5)
```

**Search modes**

| Mode | Method | Best for |
|------|--------|----------|
| `EnglishSearch` | Okapi BM25 | fast, exact keyword + phrase |
| `search_arabic` | normalized lexical | precise Arabic word/root lookup |
| `SemanticSearch` | multilingual embeddings | meaning-based queries, both languages |

---

## 🔬 Research & notebooks

The `notebooks/` folder contains the original explorations (word frequency,
sentiment, summarization, the original USE-based search engine) and
`webscrapers/` holds the scrapers for Altafsir, QuranCorpus, and Thaqalayn.

## 🗺️ Roadmap

See [`REVIVAL_PLAN.md`](REVIVAL_PLAN.md) for the full plan. Highlights:

- [x] Clean, versioned dataset + validation
- [x] Zero-dependency Python package + search
- [x] Semantic search (Arabic + English)
- [ ] Knowledge graph (ayah ↔ root ↔ lemma ↔ hadith ↔ narrator)
- [ ] Quranic Arabic language model (fine-tuned)
- [ ] Hadith authentication (isnad-graph analysis)
- [ ] Hosted search API + demo

## 🤝 Contributing

Contributions are **highly welcome** — code, data, fact-checking, and
scholarly review. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) and the
[Code of Conduct](CODE_OF_CONDUCT.md). Newcomers should start with
[`GOOD_FIRST_ISSUES.md`](GOOD_FIRST_ISSUES.md).

## 📄 License & sources

- **Code:** [Apache 2.0](LICENSE.MD)
- **Data:** individual translations and tafaseer retain their own copyrights —
  see [`sources.md`](sources.md) and the per-file attribution in
  `data/canonical/dataset_manifest.json`. Always clear rights before
  redistributing beyond research use.

## 🔗 Community

- Dataset on [Kaggle](https://www.kaggle.com/datasets/alizahidraja/quran-nlp)
- Website: [islamandai.com](https://islamandai.com)

## 📖 Citation

```bibtex
@misc{quran_nlp,
  title        = {QURAN-NLP: NLP \& AI on the Qur'an},
  author       = {{Islam \& AI}},
  year         = {2023},
  howpublished = {\url{https://github.com/islamAndAi/QURAN-NLP}},
}
```

---

*Project started March 1, 2023.*
