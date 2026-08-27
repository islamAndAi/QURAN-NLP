# QURAN-NLP — Revival Plan

> Study + roadmap to bring **QURAN-NLP** (143 ⭐ / 28 🍴, started March 2023, last commit April 2024)
> back to life and take it much further — in the same way islamandai.com was revived.

---

## 1. Executive summary

QURAN-NLP is a **dataset + research** repository with a huge amount of already-collected,
highly valuable Islamic data (Quran, corpus, translations, tafaseer, hadith, narrator networks).
Its current weak point is not the data — it is **engineering and packaging**:

- The analysis lives in monolithic, half-broken Jupyter notebooks.
- The datasets are inconsistent, partly malformed, and lack a shared schema or licensing manifest.
- The "search engine" is a demo (Google USE + `linear_kernel`) that can't run in production
  and doesn't work on Arabic.

**The revival thesis:** turn QURAN-NLP from "a pile of CSVs + notebooks" into
**(1) a clean, versioned, licensed dataset + (2) a modern Python package + (3) a real semantic
search engine/API for Quran & Hadith + (4) a knowledge graph**, then wire the search engine into
the already-revived islamandai.com frontend/Vercel backend.

---

## 2. What exists today (audit)

### 2.1 Data inventory (verified locally)

| Area | Files | Records | Health |
|------|-------|---------|--------|
| Quran (Arabic) | `data/quran/quran.csv` | 6,236 | ✅ good (Uthmani + word list) |
| Combined | `data/main_df.csv` | 6,236 | ⚠️ only 3 translations + 2 tafseer embedded |
| Surah info | `data/surah/surah_info.csv` | 114 | ✅ good |
| Names of Allah | `data/names_of_Allah/Asma_ul_Husna.csv` | 99 | ✅ rich |
| Corpus: dictionary | `quran_dictionary.csv` | 53,924 | ✅ good |
| Corpus: morphology | `quran_morphology.csv` | 128,219 | ✅ good |
| Corpus: lemmas / grouped | 2 files | 3,680 / 3,357 | ✅ good |
| Corpus: verbs | `quran_verbs.csv` | 1,475 | ✅ good |
| Translations (English) | 9 files | varies | ❌ see 2.3 |
| Tafaseer (English) | 4 files | 6,236 each | ⚠️ no surah/ayah columns |
| Hadith (kaggle clean) | `kaggle_hadiths_clean.csv` | 34,410 | ✅ good (ar+en+isnad) |
| Hadith narrators | `kaggle_rawis.csv` | 24,028 | ✅ rich (genealogy graph) |
| Hadith (arabic_hadith) | 9 books × 2 | ~62k | ❌ malformed (single column) |
| Hadith (thaqalayn) | 26 books | 26,975 | ✅ good (ar+en+isnad) |
| Sanadset 650K | samples only | 650k (Kaggle) | ⚠️ exceeds GitHub limits |

### 2.2 Code / analysis inventory

- `notebooks/Preprocessing.ipynb` — builds `main_df.csv` from translations + tafaseer.
- `notebooks/Quran_NLP_eng.ipynb` — main work: word frequency, wordclouds, VADER sentiment,
  extractive summarization, **USE-based search engine**, TF-IDF similarity index.
- `notebooks/assessment.ipynb` — partial tafseer comparison (unfinished).
- `notebooks/datavisualizing.ipynb` — hadith narrator graph prep (unfinished).
- `webscrapers/` — 3 scrapers (Altafsir, QuranCorpus, Thaqalayn).
- `requirements.txt` — only 4 packages (`bs4`, `streamlit-analytics`, `deep_translator`, `nltk`),
  **does not list** tensorflow, tensorflow-hub, sklearn, matplotlib, seaborn, wordcloud, etc.
- License: **Apache 2.0** (code) — but there is **no per-dataset license/attribution**.

### 2.3 Confirmed data-quality issues (blockers)

1. **Translation row counts are inconsistent:**
   - `Abdullah_Yusuf_Ali` = 12,482 records (≈2× — duplicated)
   - `Muhammad_Asad` = 11,714 records (≈2× — duplicated/extra)
   - `Martin_Lings` = 4,303 (missing ~1,933 ayahs)
   - `Recitations_of_Ibrahim` = 5,896 (missing ~340)
   - `Royal_Aal_al-Bayt` = 6,186 (missing ~50)
   - Complete: Arberry, Pickthall, Tahir-ul-Qadri, "The Quran Dataset" (all 6,236)
2. **`arabic_hadith/*.csv` are malformed** — single column, with the *book name as the header*
   (e.g. header row literally says `Sahih Bukhari`). These are raw text lines needing parsing
   into structured `{book, hadith_no, matn_ar, isnad, grade}`.
3. **Tafaseer CSVs have only 2 columns** (`Arabic`, `Tafseer`) — no `surah`/`ayah` keys;
   they rely on row order = ayah order. Fragile and error-prone.
4. **Translation CSVs have 4 columns** (`Name`, `Surah`, `Ayat`, `Verse`) — no global ayah
   number and no Arabic text; can't join reliably without position.
5. `main_df.csv` freezes only 3 translations + 2 tafseer, even though 9 + 4 exist.

### 2.4 Code-level issues (from reading the notebooks)

- `requirements.txt` is missing most dependencies → repo doesn't reproduce.
- USE model is loaded from a `model/` dir that is **gitignored** → search engine can't run for anyone else.
- Bugs: `punctuations` list overwritten by `re.sub(...)`; undefined `exported_m` in the model-export cell;
  `linear_similarities.sort()` mutates before indexing; hard-coded column names `Translation1..3`, `Tafaseer1..2`.
- Search is **English-only** (translations/tafseer) — ignores the Arabic Quran, which is the core text.
- No tests, no CI, no data validation, no schema/versioning, no evaluation benchmark for search.

---

## 3. Vision & positioning

Make QURAN-NLP the **authoritative open data + tooling layer for Quran/Hadith NLP**, and the
**engine behind islamandai.com's Quran search**.

Long-term north star (from the original "Future Goals", restated for 2026):

1. A single, clean, versioned, **fully-attributed** dataset (Quran + tafseer + translations + hadith + narrators).
2. A **semantic search that works in Arabic *and* English** (and more languages).
3. A **knowledge graph** linking ayahs ↔ roots/lemmas ↔ themes ↔ hadith ↔ narrators.
4. An **Arabic Quran language model** (Quranic understanding) built on modern Arabic NLP.
5. A **hadith authentication (isnad analysis) tool** using the narrator graph.
6. A **hosted, end-to-end product** on islamandai.com.

---

## 4. Guiding principles

- **Authenticity first.** No LLM-generated tafsir/hadith text presented as authoritative; always
  cite source + translator + grade. Religious text errors are unacceptable — build a fact-check/review loop.
- **Arabic-first, multilingual-second.** The Quran is Arabic; search must natively handle diacritics,
  roots, and Uthmani/Imla'i variants.
- **Licensing transparency.** Every dataset gets a license + attribution manifest. Translations
  (Yusuf Ali, Pickthall, Arberry, Asad, Lings, etc.) carry their own copyrights — this must be explicit.
- **No-hallucination RAG.** LLM answers are grounded in retrieved ayahs with citations, never free-form tafsir.
- **Reproducibility.** Anyone can `pip install` and rebuild artifacts via a Makefile/DVC, not by re-running
  fragile notebooks.

---

## 5. Phased roadmap

### Phase 0 — Foundation & hygiene (Week 1–2) ⭐ highest leverage

**Goal:** make the repo trustworthy, reproducible, and contributor-ready.

- [ ] **Fix data** (see §2.3): dedupe Yusuf Ali & Asad; fill/fix Lings, Ibrahim, Royal Aal al-Bayt;
      parse `arabic_hadith` into structured CSVs; add `surah`/`ayah_no_quran` to tafaseer files.
- [ ] **Single canonical schema** (tidy/long format) + a `data/dataset_manifest.json` listing every
      file, its source, license, language, record count, and checksum.
- [ ] **`pyproject.toml`** + proper dependency groups; make `requirements.txt` obsolete.
- [ ] **README overhaul**: quickstart, data dictionary, badges, Kaggle/HF links.
- [ ] **CI (GitHub Actions)**: run a data-validation script on every PR (row counts, schema, nulls,
      ayah alignment 1..6236).
- [ ] **CONTRIBUTING.md**, issue templates, `good first issue` labels.
- [ ] Add a **per-file license notice** (code = Apache-2.0; data = individual licenses).

### Phase 1 — Data unification & expansion (Week 2–4)

- [ ] Build **`data/parquet/`** outputs: `quran.parquet`, `translations.parquet` (one row per
      (ayah, translator)), `tafaseer.parquet`, `hadith.parquet`, `narrators.parquet` — all keyed by
      a stable `ayah_id` / `hadith_id`.
- [ ] Add **Arabic tafaseer** (Ibn Kathir, al-Tabari, al-Qurtubi, al-Sa'di) and **more languages**
      (Urdu, Farsi, Turkish, Indonesian, French, etc.).
- [ ] Normalize Arabic: store **both Uthmani and Imla'i** + `buckwalter` transliteration (corpus already
      has this) for search/ML.
- [ ] Enrich metadata: juz, hizb, ruku, sajdah, place of revelation, thematic tags (from a Tafsir
      topic model), root→lemma→word mapping.
- [ ] **Knowledge graph (Neo4j)**: `(:Ayah)-[:HAS_ROOT]->(:Root)`, `(:Ayah)-[:HAS_LEMMA]->(:Lemma)`,
      `(:Hadith)-[:NARRATED_BY]->(:Narrator)`, `(:Narrator)-[:TEACHER_OF]->(:Narrator)`, theme clusters.
      Export as Cypher + a queryable dump.

### Phase 2 — ML/NLP modernization (Week 3–6)

- [ ] Replace **USE** with **sentence-transformers** embeddings; precompute offline and store as
      `.npy`/Parquet/vector DB (Faiss / Qdrant / Chroma). No heavy model at request time.
- [ ] **Bilingual retrieval**: Arabic embeddings (e.g. `intfloat/multilingual-e5-*`, `CAMeL-BERT`,
      or an Arabic-tuned model) + English; store dual vectors or use a single multilingual space.
- [ ] **Hybrid search**: BM25 (Elasticsearch/Vespa or `rank_bm25`) + semantic + optional cross-encoder
      re-ranker. Add **Arabic normalization** (strip tashkeel, normalize hamza/alef/teh marbuta) so
      "موسى" matches "مُوسَىٰ".
- [ ] **Quranic Arabic language model** (long-term goal #5): fine-tune CAMeL-BERT / AraBERT on the
      Quran + tafaseer for root prediction, POS, and thematic embeddings; release on HuggingFace.
- [ ] **Hadith authentication tool** (goal #7): build an **isnad graph** from Sanadset + kaggle_rawis
      (narrator grades, teacher/student edges); features → graph embeddings → classifier for
      "soundness" (sahih/hasan/da'if) as a *decision-support* tool with clear caveats, not a fatwa.
- [ ] **Evaluation benchmark**: golden query set (Arabic + English) with relevance judgments;
      report nDCG@10 / Recall@10. Ship this in CI so search never regresses.

### Phase 3 — Productization (Week 5–8)

- [ ] **Python package `quran_nlp`**: `load_quran()`, `load_translations()`, `search(query, lang=...)`,
      `get_tafseer(ayah)`, `similar_ayahs()`, CLI + docs.
- [ ] **REST API** (FastAPI, or reuse the existing **Vercel serverless** pattern from
      `vercelserver/`): `/search`, `/ayah`, `/tafseer`, `/hadith/search`, `/graph/neighbors`.
      Precomputed embeddings → cheap serverless lookups, matching how the chat backend already works.
- [ ] **Wire into islamandai.com**: add a "Quran Search" page to the React/Vite frontend
      (same stack + Firestore usage tracking as the chat feature).
- [ ] **Hosted demo**: HuggingFace Spaces / Streamlit for browsable search + tafseer + visualization.
- [ ] **Hadith authentication demo**: UI where you paste an isnad and see the narrator chain graph + grades.

### Phase 4 — Community & growth (ongoing)

- [ ] Refresh the **Kaggle dataset** and mirror to **HuggingFace Datasets** (with a Dataset Card).
- [ ] Publish a **paper/blog** on the search engine + isnad graph; cite the original repo.
- [ ] **Fact-check workflow**: a `REVIEW.md` per dataset + an open review board; label issues
      `needs-scholarly-review`.
- [ ] Recruit from the existing 28 forks: open issues for each Phase-0/1 item so contributors can
      land quick wins (this is the fastest path to momentum).
- [ ] Add a **contributor leaderboard / acknowledgments** and a CHANGELOG.

---

## 6. Target architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Data layer (versioned, Parquet + git-lfs/DVC + Kaggle/HF)      │
│   Quran · Translations · Tafaseer · Hadith · Narrators · Corpus │
└───────────────────────────────┬─────────────────────────────────┘
                                │ ETL / validation (CI)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Processing (offline, reproducible)                             │
│   normalize · dedupe · align ayah_id · embed (sentence-        │
│   transformers) · build Faiss index · Neo4j graph               │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Serving                                                         │
│   FastAPI / Vercel serverless  →  /search /ayah /tafseer        │
│   (BM25 + vector + rerank)      /hadith /graph                  │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Products                                                        │
│   islamandai.com (React+Vite+Firebase) · Streamlit/HF demo      │
│   Python package quran_nlp · CLI · Notebooks for research        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. First 3 PRs (concrete quick wins)

1. **PR 1 — Data repair + schema**: fix duplicated/incomplete translations, parse `arabic_hadith`,
   add `surah`/`ayah_no_quran` to tafaseer, emit `translations.parquet` + `dataset_manifest.json`.
2. **PR 2 — Packaging + CI**: `pyproject.toml`, data-validation script, GitHub Actions, README overhaul.
3. **PR 3 — Modern search MVP**: sentence-transformers embeddings (Arabic + English) + Faiss,
   `quran_nlp.search()`, and a 100-query eval harness with nDCG/Recall. Demo in Streamlit.

---

## 8. Risks & mitigations

| Risk | Mitigation |
|------|-----------|
| Religious accuracy of auto-generated summaries/answers | No-hallucination RAG only; always cite ayah + tafsir source; scholarly review board |
| Data licensing (translations/tafsir copyright) | Per-dataset license manifest; replace/relicense where needed; prefer open-licensed sources (Tanzil, QuranEnc, al-tafsir with permission) |
| Hadith authentication being misread as authoritative | Label as decision-support; state methodology + limitations prominently |
| Heavy models on serverless | Precompute embeddings offline; only lightweight encode/re-rank at request time |
| Contributor churn (already stalled since 2024) | Small, well-scoped `good first issue` tickets; active maintainer cadence; public roadmap |

---

## 9. Success metrics

- **Dataset**: 100% ayah alignment across all translations/tafaseer; 0 malformed CSVs; full license manifest.
- **Search**: nDCG@10 ≥ 0.8 on the golden set; Arabic queries return correct surah/ayah; p95 latency < 200ms.
- **Adoption**: 2× stars/forks within 6 months; ≥10 new contributors; Kaggle/HF downloads up.
- **Product**: Quran Search live on islamandai.com with real usage tracked in Firestore.
- **Research**: Quranic Arabic LM + isnad-graph tool released with papers/blog posts.
