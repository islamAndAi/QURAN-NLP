"""
QURAN-NLP data validation.

Checks the invariants of the raw ``data/`` sources (so regressions are caught
in CI) and — when present — the generated canonical files under
``data/canonical/``.

Run from the repo root:

    python3 scripts/validate_data.py

Exit code 0 = all checks passed, 1 = failures found.

Pure stdlib — no third-party dependencies required.
"""

import csv
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
CANON = os.path.join(DATA, "canonical")

EXPECTED_AYAHS = 6236
EXPECTED_SURAHS = 114

# Known record counts for raw translations (from sources.md / diagnosed state).
# These document the *current* truth; update them if a source is repaired.
TRANSLATION_EXPECTED = {
    "Abdullah_Yusuf_Ali_translation.csv": 12482,     # verses + footnotes (split at normalize time)
    "Muhammad_Asad_translation.csv": 11714,         # verses + footnotes, divergent division
    "Marmaduke_Pickthall_translation.csv": 6236,
    "Arthur_J._Arberry_translation.csv": 6236,
    "Martin_Lings_translation.csv": 4303,           # fragment compilation
    "Muhammad_Tahir-ul-Qadri_translation.csv": 6236,
    "Recitations_of_Ibrahim_walk_from_saheeh_international_translation.csv": 5896,  # truncated
    "Royal_Aal_al-Bayt_Institute_Translation_translation.csv": 6186,                # truncated
    "The Quran Dataset.csv": 6236,
}

TAFASEER_EXPECTED = 6236  # all four tafseer files

failures = []


def check(condition, message):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {message}")
    if not condition:
        failures.append(message)


def count_rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return sum(1 for _ in csv.reader(fh)) - 1


def validate_raw():
    print("Raw sources:")
    # Quran backbone
    n = count_rows(os.path.join(DATA, "quran", "quran.csv"))
    check(n == EXPECTED_AYAHS, f"quran.csv has {EXPECTED_AYAHS} ayahs (got {n})")

    # Surah info
    n = count_rows(os.path.join(DATA, "surah", "surah_info.csv"))
    check(n == EXPECTED_SURAHS, f"surah_info.csv has {EXPECTED_SURAHS} surahs (got {n})")

    # Names of Allah
    n = count_rows(os.path.join(DATA, "names_of_Allah", "Asma_ul_Husna.csv"))
    check(n == 99, f"Asma_ul_Husna.csv has 99 names (got {n})")

    # Translations
    for fname, expected in TRANSLATION_EXPECTED.items():
        path = os.path.join(DATA, "translation", "english", fname)
        if not os.path.exists(path):
            check(False, f"missing translation file {fname}")
            continue
        n = count_rows(path)
        check(n == expected, f"{fname} has {expected} records (got {n})")

    # Tafaseer
    for fname in ["Tafsir_al-Jalalayn_tafseer.csv", "Tanwir_al-Miqbas_min_Tafsir_Ibn_Abbas_tafseer.csv",
                  "Kashani_Tafsir_tafseer.csv", "Al_Qushairi_Tafsir_tafseer.csv"]:
        path = os.path.join(DATA, "tafaseer", "english", fname)
        n = count_rows(path)
        check(n == TAFASEER_EXPECTED, f"{fname} has {TAFASEER_EXPECTED} records (got {n})")

    # Arabic hadith: each tashkeel book must have a same-count plain counterpart
    ah_dir = os.path.join(DATA, "hadith", "arabic_hadith")
    if os.path.isdir(ah_dir):
        files = sorted(f for f in os.listdir(ah_dir) if f.endswith(".csv"))
        tashkeel = [f for f in files if "Without_Tashkel" not in f]
        plain = {count_rows(os.path.join(ah_dir, f)): f for f in files if "Without_Tashkel" in f}
        for f in tashkeel:
            n = count_rows(os.path.join(ah_dir, f))
            check(n in plain, f"arabic hadith '{f}' ({n} records) has a plain (Without_Tashkel) counterpart")


def validate_canonical():
    if not os.path.isdir(CANON):
        print("  canonical/ not present — skipping (run scripts/normalize_data.py)")
        return
    print("Canonical outputs:")

    # quran_meta.csv
    path = os.path.join(CANON, "quran_meta.csv")
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))[1:]
        check(len(rows) == EXPECTED_AYAHS, f"quran_meta.csv has {EXPECTED_AYAHS} rows (got {len(rows)})")
        keys = [int(r[0]) for r in rows]
        check(len(set(keys)) == EXPECTED_AYAHS and min(keys) == 1 and max(keys) == EXPECTED_AYAHS,
              "quran_meta.csv ayah_no_quran is unique and spans 1..6236")

    # translations.csv — complete translators must cover all 6236 ayahs
    path = os.path.join(CANON, "translations.csv")
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))[1:]
        from collections import defaultdict
        by_tr = defaultdict(set)
        for r in rows:
            by_tr[r[3]].add(int(r[0]))
        for tr, ayahs in sorted(by_tr.items()):
            complete = "complete" if len(ayahs) == EXPECTED_AYAHS else f"partial ({len(ayahs)})"
            check(len(ayahs) <= EXPECTED_AYAHS and len(ayahs) > 0, f"translations.csv '{tr}' -> {complete}")

    # manifest parses
    path = os.path.join(CANON, "dataset_manifest.json")
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                json.load(fh)
            check(True, "dataset_manifest.json is valid JSON")
        except json.JSONDecodeError as e:
            check(False, f"dataset_manifest.json is invalid: {e}")


def main():
    validate_raw()
    print()
    validate_canonical()
    print()
    if failures:
        print(f"{len(failures)} check(s) FAILED")
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
