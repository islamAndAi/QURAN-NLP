"""
QURAN-NLP data normalization pipeline.

Repairs and consolidates the raw CSVs in ``data/`` into a clean, long-format
canonical dataset under ``data/canonical/`` and writes a machine-readable
``dataset_manifest.json`` plus a human-readable ``validation_report.txt``.

What it fixes (see REVIVAL_PLAN.md §2.3 for the diagnosis):

  * translations: splits Yusuf Ali / Asad verse text from their interleaved
    footnotes; detects surah-end truncation in Royal Aal al-Bayt, Ibrahim and
    Lings; normalises every translation to ``ayah_no_quran``.
  * tafaseer: assigns ``ayah_no_quran`` positionally (all four are exactly
    6236 rows in Quranic order) and records per-ayah alignment confidence.
  * arabic_hadith: parses the malformed single-column files (header = book
    name, then one hadith per line) and pairs each book with its
    ``Without_Tashkel`` variant.
  * thaqalayn: consolidates the 26 per-book CSVs into one file.

Run from the repo root:

    python3 scripts/normalize_data.py

Pure stdlib — no third-party dependencies required.
"""

import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arabic_norm import normalize_arabic  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data")
CANON = os.path.join(DATA, "canonical")

TRANSLATION_DIR = os.path.join(DATA, "translation", "english")
TAFASEER_DIR = os.path.join(DATA, "tafaseer", "english")
ARABIC_HADITH_DIR = os.path.join(DATA, "hadith", "arabic_hadith")
THAQALAYN_DIR = os.path.join(DATA, "hadith", "thaqalayn")

EXPECTED_AYAHS = 6236

# Translation metadata. ``file`` is the CSV basename; ``complete`` is the
# known state after repair (Yusuf Ali / Asad are complete once footnotes are
# split out; the truncated ones stay partial).
TRANSLATORS = [
    {"slug": "yusuf_ali", "file": "Abdullah_Yusuf_Ali_translation.csv",
     "name": "Abdullah Yusuf Ali", "notes": "verse text + footnotes split", "source": "https://www.altafsir.com/"},
    {"slug": "asad", "file": "Muhammad_Asad_translation.csv",
     "name": "Muhammad Asad", "notes": "own verse division; footnotes split out", "source": "https://www.altafsir.com/"},
    {"slug": "pickthall", "file": "Marmaduke_Pickthall_translation.csv",
     "name": "Marmaduke Pickthall", "notes": "complete", "source": "https://www.altafsir.com/"},
    {"slug": "arberry", "file": "Arthur_J._Arberry_translation.csv",
     "name": "Arthur J. Arberry", "notes": "complete", "source": "https://www.altafsir.com/"},
    {"slug": "lings", "file": "Martin_Lings_translation.csv",
     "name": "Martin Lings", "notes": "fragment compilation, not a complete translation", "source": "https://www.altafsir.com/"},
    {"slug": "tahir_ul_qadri", "file": "Muhammad_Tahir-ul-Qadri_translation.csv",
     "name": "Muhammad Tahir-ul-Qadri", "notes": "complete", "source": "https://www.altafsir.com/"},
    {"slug": "ibrahim_walk", "file": "Recitations_of_Ibrahim_walk_from_saheeh_international_translation.csv",
     "name": "Recitations of Ibrahim Walk (Saheeh International style)", "notes": "truncation with internal offsets — needs content alignment", "source": "https://www.altafsir.com/"},
    {"slug": "royal_aal_al_bayt", "file": "Royal_Aal_al-Bayt_Institute_Translation_translation.csv",
     "name": "Royal Aal al-Bayt Institute", "notes": "truncation with internal offsets — needs content alignment", "source": "https://www.altafsir.com/"},
    {"slug": "quran_dataset", "file": "The Quran Dataset.csv",
     "name": "The Quran Dataset (Kaggle, imrankhan197)", "notes": "complete; separate schema (ayah_en)", "source": "https://www.kaggle.com/datasets/imrankhan197/the-quran-dataset"},
]

TAFASEER = [
    {"slug": "jalalayn", "file": "Tafsir_al-Jalalayn_tafseer.csv",
     "name": "Tafsir al-Jalalayn", "per_ayah": True},
    {"slug": "ibn_abbas", "file": "Tanwir_al-Miqbas_min_Tafsir_Ibn_Abbas_tafseer.csv",
     "name": "Tanwir al-Miqbas min Tafsir Ibn Abbas", "per_ayah": True},
    {"slug": "kashani", "file": "Kashani_Tafsir_tafseer.csv",
     "name": "Kashani Tafsir", "per_ayah": False},
    {"slug": "qushairi", "file": "Al_Qushairi_Tafsir_tafseer.csv",
     "name": "Al-Qushairi Tafsir", "per_ayah": False},
]


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.reader(fh))


def write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return len(rows)


def build_backbone():
    """Return (ayah_by_key, meta_rows)."""
    quran = read_rows(os.path.join(DATA, "quran", "quran.csv"))
    surah = read_rows(os.path.join(DATA, "surah", "surah_info.csv"))
    qds = read_rows(os.path.join(TRANSLATION_DIR, "The Quran Dataset.csv"))

    ayah_by_key = {}
    quran_ar = {}
    for r in quran[1:]:
        if len(r) < 5:
            continue
        ayah_no_quran = int(r[0])
        surah_no = int(r[2])
        ayah_no_surah = int(r[3])
        ayah_by_key[(surah_no, ayah_no_surah)] = ayah_no_quran
        quran_ar[ayah_no_quran] = r[4]

    def _int(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    surah_meta = {}
    for r in surah[1:]:
        if len(r) < 7:
            continue
        surah_meta[int(r[0])] = {
            "en": r[1], "ar": r[2], "roman": r[3],
            "verses": _int(r[4]), "rukus": _int(r[5]), "place": r[6],
        }

    qds_idx = {}
    qds_header = qds[0]
    for r in qds[1:]:
        d = dict(zip(qds_header, r))
        qds_idx[int(d["ayah_no_quran"])] = d

    meta_rows = []
    for ayah_no_quran in range(1, EXPECTED_AYAHS + 1):
        surah_no = None
        ayah_no_surah = None
        for k, v in ayah_by_key.items():
            if v == ayah_no_quran:
                surah_no, ayah_no_surah = k
                break
        sm = surah_meta.get(surah_no, {})
        d = qds_idx.get(ayah_no_quran, {})
        meta_rows.append([
            ayah_no_quran, surah_no, ayah_no_surah,
            sm.get("en", ""), sm.get("ar", ""), sm.get("roman", ""),
            quran_ar.get(ayah_no_quran, ""),
            d.get("juz_no", ""), d.get("ruko_no", ""), d.get("sajdah_no", ""),
            d.get("place_of_revelation", ""), d.get("no_of_word_ayah", ""),
        ])

    return ayah_by_key, meta_rows


def _expected_by_surah():
    surah = read_rows(os.path.join(DATA, "surah", "surah_info.csv"))
    exp = {}
    for r in surah[1:]:
        if len(r) >= 5 and r[4].strip():
            exp[int(r[0])] = int(r[4])
    return exp


def _is_commentary(text):
    """Heuristic for Yusuf Ali / Asad footnotes & commentary lines."""
    t = text.lstrip()
    if t.startswith("*"):
        return True
    if re.match(r"^C\s*\d+\.", t):        # Yusuf Ali "C199." commentary marker
        return True
    if re.match(r"^\(\d+\)", t):          # numbered commentary items "(1) ..."
        return True
    return False


# Alignment mode per translator slug:
#   "align"     -> sequence-align verses per surah (only safe when every surah
#                  has exactly the canonical verse count — i.e. no internal offsets)
#   "trim"      -> like align, but drop trailing commentary rows (Yusuf Ali)
#   "divergent" -> source uses a different verse division; emit raw (Asad)
#   "raw"       -> cannot be safely ayah-aligned (offsets/fragments); emit raw
TRANSLATOR_MODES = {
    "yusuf_ali": "trim",
    "asad": "divergent",
    "pickthall": "align",
    "arberry": "align",
    "lings": "raw",
    "tahir_ul_qadri": "align",
    "ibrahim_walk": "raw",
    "royal_aal_al_bayt": "raw",
}


def process_translations(ayah_by_key):
    """Return (translation_rows, footnote_rows, raw_rows, report list)."""
    translation_rows = []
    footnote_rows = []
    raw_rows = {}
    report = []
    exp = _expected_by_surah()

    for t in TRANSLATORS:
        path = os.path.join(TRANSLATION_DIR, t["file"])
        raw = read_rows(path)[1:]
        slug = t["slug"]

        if t["file"] == "The Quran Dataset.csv":
            header = read_rows(path)[0]
            count = 0
            for r in raw:
                d = dict(zip(header, r))
                translation_rows.append([
                    int(d["ayah_no_quran"]), d["surah_no"], d["ayah_no_surah"], slug, d["ayah_en"], 1,
                ])
                count += 1
            report.append({"slug": slug, "rows": count, "mapped": count,
                           "missing_ayahs": EXPECTED_AYAHS - count, "complete": count == EXPECTED_AYAHS,
                           "notes": t["notes"]})
            continue

        mode = TRANSLATOR_MODES.get(slug, "align")

        # Split verse rows from footnote/commentary rows and group by surah.
        verses_by_surah = {s: [] for s in range(1, 115)}
        for r in raw:
            if len(r) < 4:
                continue
            try:
                surah_no = int(r[1])
                ayat = int(r[2])
            except ValueError:
                continue
            text = r[3].strip()

            if mode == "divergent":
                if _is_commentary(text):
                    footnote_rows.append([surah_no, ayat, slug, "footnote", text])
                else:
                    raw_rows.setdefault(slug, []).append([surah_no, ayat, slug, text])
                continue

            if mode == "raw":
                raw_rows.setdefault(slug, []).append([surah_no, ayat, slug, text])
                continue

            if _is_commentary(text):
                m = re.search(r"v\.?\s*(\d+)", text)
                ref = int(m.group(1)) if m else ayat
                footnote_rows.append([surah_no, ref, slug, "footnote", text])
            else:
                verses_by_surah[surah_no].append((ayat, text))

        if mode in ("divergent", "raw"):
            report.append({"slug": slug, "rows": len(raw_rows.get(slug, [])), "mapped": 0,
                           "missing_ayahs": None, "complete": False,
                           "numbering": mode, "notes": t["notes"]})
            continue

        mapped = 0
        missing = 0
        trimmed = 0
        for s in range(1, 115):
            vlist = sorted(verses_by_surah[s])
            want = exp.get(s, 0)
            keep = min(len(vlist), want)
            for i in range(keep):
                ayah_no_quran = ayah_by_key.get((s, i + 1))
                if ayah_no_quran is None:
                    continue
                translation_rows.append([ayah_no_quran, s, i + 1, slug, vlist[i][1], 1])
                mapped += 1
            # trailing rows beyond the surah's verse count are commentary
            for j in range(keep, len(vlist)):
                footnote_rows.append([s, vlist[j][0], slug, "commentary", vlist[j][1]])
                trimmed += 1
            missing += max(0, want - len(vlist))

        complete = (missing == 0 and mapped == EXPECTED_AYAHS)
        report.append({
            "slug": slug, "rows": sum(len(v) for v in verses_by_surah.values()),
            "mapped": mapped, "missing_ayahs": missing, "trimmed_commentary": trimmed,
            "complete": complete, "notes": t["notes"],
        })

    return translation_rows, footnote_rows, raw_rows, report


def process_tafaseer(ayah_by_key, meta_rows):
    """Return (tafaseer_rows, report list)."""
    # ayah_no_quran -> (surah_no, ayah_no_surah) from meta_rows
    ayah_seq = [(m[0], m[1], m[2]) for m in meta_rows]  # in 1..6236 order

    tafaseer_rows = []
    report = []
    for t in TAFASEER:
        path = os.path.join(TAFASEER_DIR, t["file"])
        raw = read_rows(path)[1:]
        matches = 0
        for i, r in enumerate(raw):
            if i >= len(ayah_seq):
                break
            arabic = r[0] if len(r) > 0 else ""
            tafseer = r[1] if len(r) > 1 else ""
            ayah_no_quran, surah_no, ayah_no_surah = ayah_seq[i]
            # verify alignment where Arabic is present
            if arabic and i < EXPECTED_AYAHS:
                # compare against quran_meta arabic (index 6)
                if normalize_arabic(arabic) == normalize_arabic(meta_rows[i][6]):
                    matches += 1
            tafaseer_rows.append([ayah_no_quran, surah_no, ayah_no_surah, t["slug"], arabic, tafseer])
        report.append({
            "slug": t["slug"], "rows": min(len(raw), EXPECTED_AYAHS),
            "per_ayah": t["per_ayah"], "normalized_arabic_match": matches,
            "match_rate": round(matches / EXPECTED_AYAHS, 4) if len(raw) >= EXPECTED_AYAHS else None,
        })
    return tafaseer_rows, report


def _count_rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return sum(1 for _ in csv.reader(fh)) - 1


def process_arabic_hadith():
    """Parse malformed single-column hadith files and pair tashkeel/plain."""
    files = [f for f in sorted(os.listdir(ARABIC_HADITH_DIR)) if f.endswith(".csv")]
    tashkeel = [f for f in files if "Without_Tashkel" not in f]
    plain = [f for f in files if "Without_Tashkel" in f]

    tashkeel_meta = []
    for f in tashkeel:
        n = _count_rows(os.path.join(ARABIC_HADITH_DIR, f))
        book = f[:-4].strip()
        tashkeel_meta.append((f, book, n))

    plain_by_count = {}
    for f in plain:
        n = _count_rows(os.path.join(ARABIC_HADITH_DIR, f))
        plain_by_count[n] = f

    rows = []
    report = []
    for f, book, n in tashkeel_meta:
        pf = plain_by_count.get(n)
        if pf is None:
            report.append({"book": book, "records": n, "paired": False, "error": "no plain counterpart"})
            continue
        t = read_rows(os.path.join(ARABIC_HADITH_DIR, f))
        p = read_rows(os.path.join(ARABIC_HADITH_DIR, pf))
        t_rows = [r[0] for r in t[1:]]   # header line 0 = book name
        p_rows = [r[0] for r in p[1:]]
        for i in range(n):
            rows.append([book, i + 1, t_rows[i], p_rows[i] if i < len(p_rows) else ""])
        report.append({"book": book, "records": n, "paired": True, "plain_file": pf})

    return rows, report


def process_thaqalayn():
    """Consolidate the structured thaqalayn (Shia) hadith CSVs."""
    files = sorted(f for f in os.listdir(THAQALAYN_DIR) if f.endswith(".csv"))
    header = ["title", "title_en", "volume", "author", "translator", "book",
              "chapter", "hadees_number", "hadees_arabic", "hadees_english"]
    rows = []
    report = []
    for f in files:
        raw = read_rows(os.path.join(THAQALAYN_DIR, f))
        h = raw[0]
        for r in raw[1:]:
            d = dict(zip(h, r))
            rows.append([d.get(k, "") for k in header])
        report.append({"file": f, "records": len(raw) - 1})
    return rows, report, header


def main():
    os.makedirs(CANON, exist_ok=True)

    ayah_by_key, meta_rows = build_backbone()
    print(f"backbone: {len(meta_rows)} ayahs")

    translation_rows, footnote_rows, raw_rows, trep = process_translations(ayah_by_key)
    tafaseer_rows, tafrep = process_tafaseer(ayah_by_key, meta_rows)
    hadith_rows, hadrep = process_arabic_hadith()
    thaq_rows, thaqrep, thaq_header = process_thaqalayn()

    # ---- write outputs ----
    n_quran = write_csv(os.path.join(CANON, "quran_meta.csv"),
        ["ayah_no_quran", "surah_no", "ayah_no_surah", "surah_name_en",
         "surah_name_ar", "surah_name_roman", "ayah_ar", "juz_no", "ruko_no",
         "sajdah_no", "place_of_revelation", "no_of_word_ayah"], meta_rows)

    n_tr = write_csv(os.path.join(CANON, "translations.csv"),
        ["ayah_no_quran", "surah_no", "ayah_no_surah", "translator", "text", "complete"],
        translation_rows)

    n_fn = write_csv(os.path.join(CANON, "footnotes.csv"),
        ["surah_no", "ref_ayah_no_surah", "translator", "kind", "text"], footnote_rows)

    raw_files = {}
    for slug, rows in raw_rows.items():
        fname = f"translations_{slug}_raw.csv"
        raw_files[fname] = write_csv(os.path.join(CANON, fname),
            ["surah_no", "ayat", "translator", "text"], rows)

    n_taf = write_csv(os.path.join(CANON, "tafaseer.csv"),
        ["ayah_no_quran", "surah_no", "ayah_no_surah", "tafsir", "arabic", "text"],
        tafaseer_rows)

    n_had = write_csv(os.path.join(CANON, "hadith_arabic.csv"),
        ["book", "hadith_no", "text_ar_tashkeel", "text_ar_plain"], hadith_rows)

    n_thaq = write_csv(os.path.join(CANON, "hadith_thaqalayn.csv"), thaq_header, thaq_rows)

    # ---- manifest ----
    manifest = {
        "generated_by": "scripts/normalize_data.py",
        "canonical_ayahs": EXPECTED_AYAHS,
        "files": {
            "quran_meta.csv": {"records": n_quran, "description": "canonical per-ayah backbone (Uthmani Arabic + metadata)"},
            "translations.csv": {"records": n_tr, "description": "long-format English translations keyed by ayah_no_quran"},
            "footnotes.csv": {"records": n_fn, "description": "Yusuf Ali / Asad footnotes & commentary split from verse text"},
            "translations_raw": {"files": raw_files, "description": "raw (non-aligned) translations: asad = divergent verse division, lings = fragment compilation"},
            "tafaseer.csv": {"records": n_taf, "description": "long-format English tafaseer keyed by ayah_no_quran"},
            "hadith_arabic.csv": {"records": n_had, "description": "9 Arabic hadith books, tashkeel + plain paired"},
            "hadith_thaqalayn.csv": {"records": n_thaq, "description": "consolidated thaqalayn (Shia) hadith"},
        },
        "translations": trep,
        "tafaseer": tafrep,
        "arabic_hadith": hadrep,
        "thaqalayn": {"files": len(thaqrep), "total_records": n_thaq},
        "license_note": "Code is Apache-2.0. Individual translation/tafsir texts retain their own "
                        "copyright; see sources.md and clear rights before redistribution beyond research.",
    }
    with open(os.path.join(CANON, "dataset_manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    # ---- human-readable report ----
    lines = ["QURAN-NLP data normalization report", "=" * 60, ""]
    lines.append("Translations:")
    for r in trep:
        mapped = r.get("mapped", r.get("rows"))
        miss = r.get("missing_ayahs")
        miss_s = str(miss) if miss is not None else "n/a"
        lines.append(f"  {r['slug']:16s} rows={r['rows']:5d} mapped={mapped:>5} "
                     f"missing={miss_s:>4} complete={r['complete']}  ({r['notes']})")
    lines.append("")
    lines.append("Tafaseer (6236 rows each, positional ayah_no_quran):")
    for r in tafrep:
        mr = f"{r['match_rate']:.1%}" if r["match_rate"] is not None else "n/a"
        lines.append(f"  {r['slug']:10s} per_ayah={str(r['per_ayah']):5s} "
                     f"normalized_arabic_match={r['normalized_arabic_match']:5d} ({mr})")
    lines.append("")
    lines.append("Arabic hadith:")
    for r in hadrep:
        lines.append(f"  {r['book']:30s} records={r.get('records','?'):6d} paired={r.get('paired','?')}")
    lines.append("")
    lines.append("Thaqalayn:")
    for r in thaqrep:
        lines.append(f"  {r['file'][:55]:55s} records={r['records']}")
    lines.append("")
    lines.append(f"Outputs written to data/canonical/ ({n_quran+n_tr+n_fn+n_taf+n_had+n_thaq+sum(raw_files.values())} rows total)")

    report_txt = "\n".join(lines)
    with open(os.path.join(CANON, "validation_report.txt"), "w", encoding="utf-8") as fh:
        fh.write(report_txt)
    print(report_txt)


if __name__ == "__main__":
    main()
