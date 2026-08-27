# Contributing to QURAN-NLP

Thank you for wanting to help! This project is **data-first**: the most valuable
contributions are often not code but clean, authentic, well-sourced data and
careful fact-checking of what already exists.

Please read this guide, and remember the [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to contribute

1. **Fix or add data** — translations, tafaseer, hadith, corpus annotations
   (with sources).
2. **Fact-check / scholarly review** — verify translations and search results.
3. **Code** — the Python package, scripts, notebooks, CI.
4. **Documentation** — README, docs, dataset manifests.
5. **Research** — new analyses on the data; publish and link back.

New here? Look for issues labeled **`good first issue`** — or see
[`GOOD_FIRST_ISSUES.md`](GOOD_FIRST_ISSUES.md) for a curated, ready-to-start backlog.

---

## Getting started

```bash
git clone https://github.com/islamAndAi/QURAN-NLP.git
cd QURAN-NLP
pip install -e .                 # core (zero deps)
pip install -e ".[semantic]"     # + sentence-transformers (for embeddings)
```

Run the checks before you open a PR:

```bash
python scripts/validate_data.py       # dataset invariants
python -m unittest discover -s tests  # unit tests
python scripts/normalize_data.py      # rebuild data/canonical/ (if you changed raw data)
```

## Project layout

```
data/            raw sources (quran, translation, tafaseer, hadith, corpus, ...)
data/canonical/  generated clean long-format dataset + manifest + report
scripts/         normalize_data.py, validate_data.py, build_embeddings.py, arabic_norm.py
src/quran_nlp/   the Python package (loaders, search, embeddings, CLI)
tests/           unit tests
notebooks/       original research notebooks
webscrapers/     scrapers for altafsir.com, corpus.quran.com, thaqalayn.net
```

## Contributing data (the most important part)

Islamic source data carries real responsibility. Follow these rules:

- **Source everything.** Every new dataset must record its origin (URL, book,
  translator, edition) in `sources.md` and in the `dataset_manifest.json`.
- **Authenticity first.** Prefer established, citable sources (Tanzil,
  QuranEnc, corpus.quran.com, al‑tafsir, the six canonical hadith collections,
  etc.). Do not add machine-generated tafseer or "translations" produced by LLMs.
- **License transparency.** Record the license/copyright of each text. Many
  translations (e.g. Yusuf Ali, Pickthall, Arberry, Asad) are still under
  copyright — flag them; do not silently relicense.
- **No fabricated alignment.** If a translation's verse numbering differs from
  the standard 6236-ayah division, mark it `raw`/`needs-alignment` rather than
  forcing a wrong mapping. See `data/canonical/README.md`.
- **Preserve diacritics.** Keep Uthmani vs Imla'i text as-is; normalization is
  a matching step, never a replacement for the source text.
- **Scholarly review.** Translation/tafsir changes should be reviewed by someone
  with the relevant knowledge. Label such PRs `scholarly-review`.

### Data PR checklist

- [ ] Source URL(s) added to `sources.md`
- [ ] License/attribution recorded
- [ ] `scripts/normalize_data.py` re-run (if raw data changed)
- [ ] `scripts/validate_data.py` passes
- [ ] Row counts / schema documented in `data/canonical/README.md`

## Code style

- Python 3.8+; the package core is **stdlib-only** (no hard dependencies).
- Add tests in `tests/` for new behavior; run `python -m unittest discover -s tests`.
- Keep optional heavy dependencies (e.g. sentence-transformers) behind an
  extra and behind lazy imports.

## Pull request process

1. Open an issue first for anything non-trivial, so we can agree on scope.
2. Branch, implement, test, push.
3. Open a PR using the template. Link the issue.
4. A maintainer will review. CI must pass (`validate_data.py` + tests).
5. Data changes get an extra **scholarly review** pass before merge.

## Getting help

Open an issue with the `question` label, or reach out via the repository
discussions. We're friendly — don't be shy.
