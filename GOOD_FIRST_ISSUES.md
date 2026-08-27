# Good first issues

A curated backlog of small, well-scoped tasks to get started. Each entry lists
the **label**, the **skills** needed, **where to look**, and a **definition of
done**. Open any of these as a GitHub issue (or just start a PR) — and if you're
a maintainer, these are ready to copy into issues with the suggested label.

---

### 1. `quran-nlp search --surah N` filter
- **Label:** `good first issue` · **Skills:** Python (beginner)
- **Where:** `src/quran_nlp/cli.py`, `src/quran_nlp/search.py`
- **Task:** Add `--surah` (and optional `--ayah`) filters to the `search` and
  `ayah` subcommands so results can be restricted to a surah.
- **Done when:** `quran-nlp search "mercy" --surah 2` returns only Surah 2 results; a test is added.

### 2. `similar_ayahs()` helper
- **Label:** `good first issue` · **Skills:** Python (beginner), numpy
- **Where:** `src/quran_nlp/embeddings.py`
- **Task:** Add `SemanticSearch.similar(ayah_no_quran, k=10)` that returns the
  ayahs most similar to a given ayah's embedding (Arabic + English).
- **Done when:** `similar(6236)` returns sensible neighbours; test added.

### 3. Root-based Arabic search
- **Label:** `enhancement` · `arabic-nlp` · **Skills:** Python, basic Arabic
- **Where:** `data/quran/corpus/quran_lemmas.csv`, `quran_roots`, `src/quran_nlp/search.py`
- **Task:** Add a `search_arabic` mode that expands a query to its triliteral
  root/lemma using the corpus and matches related forms (e.g. صبر → يصبر/صابرين).
- **Done when:** querying "صبر" also surfaces verses with "صابرين" and "يصبروا".

### 4. More Arabic-normalization tests
- **Label:** `good first issue` · **Skills:** Python, Arabic
- **Where:** `tests/test_arabic.py`, `src/quran_nlp/arabic.py`
- **Task:** Add edge-case tests (hamza variants, tatweel, teh marbuta, madda,
  superscript alef) and fix any normalization bugs they reveal.
- **Done when:** the suite grows with real Uthmani-vs-Imla'i pairs.

### 5. Document the corpus schema
- **Label:** `documentation` · **Skills:** writing, none
- **Where:** `data/quran/corpus/`, `data/canonical/README.md`
- **Task:** Write a `data/canonical/CORPUS.md` explaining `quran_morphology.csv`,
  `quran_dictionary.csv`, `quran_lemmas.csv`, `quran_verbs.csv` — every column,
  with examples and how to join them to `quran_meta.csv`.
- **Done when:** the doc lets a newcomer load and interpret the corpus without
  reading the scraper notebook.

### 6. English stopword/stemming improvements
- **Label:** `good first issue` · **Skills:** Python
- **Where:** `src/quran_nlp/search.py`
- **Task:** Improve `tokenize()` with a light stemmer (optional) and a better
  stopword list; measure BM25 quality change on a few queries.
- **Done when:** tokenizer is improved and documented, tests still pass.

### 7. Hadith search MVP
- **Label:** `enhancement` · `hadith` · **Skills:** Python
- **Where:** `data/canonical/hadith_arabic.csv` (generated), `src/quran_nlp/`
- **Task:** Add a `hadith_search()` that searches the Arabic hadith (normalized)
  and/or the English thaqalayn/kaggle text, returning book + hadith number.
- **Done when:** a `quran-nlp hadith-search "..."` command returns ranked results.

### 8. Streamlit demo app
- **Label:** `help wanted` · **Skills:** Python, Streamlit
- **Where:** new `demo/` folder
- **Task:** A small Streamlit app (search box → ranked ayahs with Arabic +
  translations, plus an "ayah viewer") using the package.
- **Done when:** `pip install streamlit && streamlit run demo/app.py` works and
  is documented in the README.

### 9. Export to Parquet + HuggingFace Datasets
- **Label:** `enhancement` · **Skills:** Python, data
- **Where:** `scripts/`, `data/canonical/`
- **Task:** Add a `scripts/export_parquet.py` that writes the canonical CSVs to
  Parquet (pandas/pyarrow) and generates a HuggingFace `Dataset` + Dataset Card.
- **Done when:** exports are reproducible and documented.

### 10. Asad content-based alignment
- **Label:** `research` · `scholarly-review` · **Skills:** Python, some Arabic
- **Where:** `data/translation/english/Muhammad_Asad_translation.csv`
- **Task:** Build a content-alignment for Asad's divergent verse division
  (e.g. 349 vs 286 in Surah 2) so it can be mapped to `ayah_no_quran`.
- **Done when:** an alignment table maps Asad verses to standard ayahs with
  documented confidence; validation updated.

### 11. Add Urdu (or another language) translations
- **Label:** `data` · `scholarly-review` · **Skills:** research, sourcing
- **Where:** `data/translation/`, `sources.md`
- **Task:** Add a well-sourced, licensed translation (e.g. Urdu), following the
  schema in `data/canonical/README.md`.
- **Done when:** source + license recorded, normalize/validate pass, and the
  translation is complete (6,236) or correctly flagged.

### 12. Fill the truncated translations (Royal Aal al-Bayt / Ibrahim Walk)
- **Label:** `data` · `scholarly-review` · **Skills:** research, scraping
- **Where:** `data/translation/english/`, `webscrapers/`
- **Task:** Re-scrape or source the missing verses (internal offsets) and
  re-align them to the canonical 6,236.
- **Done when:** the translation becomes complete and ayah-aligned.

---

Want to propose your own? Open a **feature request** or **data contribution**
issue using the templates — we'd love to help scope it.
