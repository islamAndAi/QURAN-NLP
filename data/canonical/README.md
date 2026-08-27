# Canonical dataset

This directory holds the **cleaned, long-format** version of QURAN-NLP, produced by
`scripts/normalize_data.py` from the raw sources in `../` (translation, tafaseer,
quran, hadith). Every Quranic row is keyed by a stable `ayah_no_quran` (1–6236).

The large consolidated hadith files (`hadith_arabic.csv`, `hadith_thaqalayn.csv`)
are **regenerated** by the script and are not committed to git — run the script
locally to produce them.

## Files

| File | Key | Description |
|------|-----|-------------|
| `quran_meta.csv` | `ayah_no_quran` | Per-ayah backbone: Uthmani Arabic + surah/verse numbers + juz/ruku/sajdah metadata |
| `translations.csv` | `ayah_no_quran` + `translator` | English translations, long format (one row per ayah per translator) |
| `tafaseer.csv` | `ayah_no_quran` + `tafsir` | English tafaseer, long format (includes source Arabic column) |
| `footnotes.csv` | — | Yusuf Ali / Asad footnotes & commentary split from verse text |
| `translations_*_raw.csv` | — | Translations that can't be ayah-aligned (see below) |
| `hadith_arabic.csv` | `book` + `hadith_no` | 9 Arabic hadith books, tashkeel + plain paired |
| `hadith_thaqalayn.csv` | — | Consolidated thaqalayn (Shia) hadith |
| `dataset_manifest.json` | — | Machine-readable metadata, completeness, per-dataset notes |
| `validation_report.txt` | — | Human-readable summary of the last normalization run |

## Schema

### `quran_meta.csv`
```
ayah_no_quran, surah_no, ayah_no_surah, surah_name_en, surah_name_ar,
surah_name_roman, ayah_ar, juz_no, ruko_no, sajdah_no, place_of_revelation, no_of_word_ayah
```

### `translations.csv`
```
ayah_no_quran, surah_no, ayah_no_surah, translator, text, complete
```
`complete` is `1` for fully-covered translations, `0` otherwise.

`translator` slugs: `yusuf_ali`, `pickthall`, `arberry`, `tahir_ul_qadri`,
`quran_dataset`, plus (`ibrahim_walk` / `royal_aal_al_bayt` — not present here
because they are not ayah-aligned; see raw files).

### `tafaseer.csv`
```
ayah_no_quran, surah_no, ayah_no_surah, tafsir, arabic, text
```
`tafsir` slugs: `jalalayn`, `ibn_abbas` (per-ayah), `kashani`, `qushairi`
(thematic — Arabic column is not per-ayah).

### `hadith_arabic.csv`
```
book, hadith_no, text_ar_tashkeel, text_ar_plain
```

## Alignment status

| Source | Status |
|--------|--------|
| yusuf_ali, pickthall, arberry, tahir_ul_qadri, quran_dataset | ✅ complete, ayah-aligned (6,236 each) |
| royal_aal_al_bayt, ibrahim_walk | ⚠️ truncated **with internal offsets** — kept raw, needs content-based alignment |
| asad | ⚠️ own verse division (e.g. 349 vs 286 in Surah 2) — kept raw |
| lings | ⚠️ fragment compilation (not a verse-by-verse translation) — kept raw |
| jalalayn, ibn_abbas tafseer | ✅ per-ayah, positional (`ayah_no_quran`) |
| kashani, qushairi tafseer | ⚠️ thematic/grouped; Arabic field not per-ayah |

## Regenerate

```bash
python3 scripts/normalize_data.py      # rebuilds this directory
python3 scripts/validate_data.py       # checks raw + canonical invariants
```
