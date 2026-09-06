# Knowledge Graph — Design & Acceptance Criteria

Status: **approved with corrections — see [`knowledge-graph-decision.md`](knowledge-graph-decision.md) for the authoritative spec.** (Key changes: QAC transliteration not standard Buckwalter, narrator `grade`→`generation`, aggregated edges exposed as derived queries, `unittest` not pytest, generated dump gitignored, no manifest timestamp.)

## Goal

Build a queryable knowledge graph linking the two big domains of QURAN-NLP:

```
(Ayah) ──HAS_WORD──▶ (Word) ──HAS_LEMMA──▶ (Lemma) ──HAS_ROOT──▶ (Root)
   │                    └───HAS_ROOT────────────────────▶ (Root)
   ├── HAS_LEMMA ──────────────────────────▶ (Lemma)
   ├── IN_SURAH ▶ (Surah)
   │
(Hadith) ──NARRATED_BY──▶ (Narrator)
                              │
                              ├── TAUGHT ────────▶ (Narrator)
                              └── STUDIED_FROM ──▶ (Narrator)
```

Deliverables: a set of node/edge CSVs, a Neo4j Cypher export, a manifest, a
stdlib-only Python API (`quran_nlp.graph`), a CLI subcommand, and tests.

---

## Data sources (all verified against the committed data)

| Source | Records | Used for |
|--------|---------|----------|
| `data/canonical/quran_meta.csv` | 6,236 | Ayah + Surah nodes (backbone) |
| `data/surah/surah_info.csv` | 114 | Surah node metadata |
| `data/quran/corpus/quran_morphology.csv` | 128,219 | Word nodes + word→root/lemma edges (`LOCATION`, `FEATURES`) |
| `data/quran/corpus/quran_lemmas.csv` | 3,357 | Lemma Arabic names / freq / POS enrichment |
| `data/hadith/kaggle_hadiths_clean.csv` | 34,441 | Hadith nodes + `chain_indx` → narrator edges |
| `data/hadith/kaggle_rawis.csv` | 24,326 | Narrator nodes + teacher/student genealogy |

Verification facts (from inventory):

- morphology `LOCATION` = `(surah:ayah:word:segment)`; **100%** (128,219/128,219)
  map to `ayah_no_quran` via `(surah_no, ayah_no_surah)`.
- 77,429 unique `(surah, ayah, word)` tokens → Word nodes.
- `FEATURES` carries `LEM:` (Buckwalter lemma) and `ROOT:` (Buckwalter root):
  - 1,642 unique roots, 4,832 unique lemmas.
  - every `ROOT:` word also has `LEM:` (0 roots missing lemma).
- `chain_indx` (hadith) → `scholar_indx` (narrator): 175,695 chain entries,
  **173,636 (98.8%)** resolve; 103 unique unresolved ids.
- `teachers_inds`: 36,018 resolved edges; `students_inds`: 29,230 resolved edges.
- Lemma Arabic display: 3,357/4,832 (69.5%) lemmas have Arabic in
  `quran_lemmas.csv`; the rest fall back to a Buckwalter→Arabic transliteration.

---

## Schema

### Canonical IDs

| Node | ID pattern | Count (expected) |
|------|-----------|------------------|
| Surah | `surah:<n>` | 114 |
| Ayah | `ayah:<ayah_no_quran>` | 6,236 |
| Word | `word:<s>:<a>:<w>` | 77,429 |
| Root | `root:<buckwalter>` | 1,642 |
| Lemma | `lemma:<buckwalter>` | 4,832 |
| Hadith | `hadith:kaggle:<id>` | 34,441 |
| Narrator | `narrator:<scholar_indx>` | 24,326 |

Roots and lemmas are keyed by **Buckwalter** (the corpus's native encoding, and the
only field present on every morphology word). Arabic display names are attached as
`name_ar` properties (from `quran_lemmas.csv` where available, else transliterated).

### Nodes & properties

- **Surah**: `no`, `name_en`, `name_ar`, `name_roman`, `verses`, `rukus`, `place`.
- **Ayah**: `no` (ayah_no_quran), `surah_no`, `ayah_no_surah`, `surah_name_en`,
  `surah_name_ar`, `text_ar`, `juz_no`, `ruko_no`, `sajdah_no`, `place`, `word_count`.
- **Word**: `surah`, `ayah`, `word_no`, `form`, `tag`, `pos`.
- **Root**: `name` (buckwalter), `name_ar`.
- **Lemma**: `name` (buckwalter), `name_ar`, `pos`, `frequency` (when known).
- **Hadith**: `id`, `source`, `chapter`, `hadith_no`, `text_ar`, `text_en`.
- **Narrator**: `id`, `name`, `grade`, `birth_date_gregorian`,
  `death_date_gregorian`, `area_of_interest`.

### Edges

| Type | From → To | Source | Property |
|------|-----------|--------|----------|
| `IN_SURAH` | Ayah → Surah | quran_meta | — |
| `HAS_WORD` | Ayah → Word | morphology | — |
| `HAS_LEMMA` | Word → Lemma | morphology `LEM:` | — |
| `HAS_ROOT` | Word → Root | morphology `ROOT:` | — |
| `HAS_LEMMA` | Ayah → Lemma | aggregate | — |
| `HAS_ROOT` | Ayah → Root | aggregate | — |
| `HAS_ROOT` | Lemma → Root | aggregate (word has both) | — |
| `NARRATED_BY` | Hadith → Narrator | chain_indx | `position` (1-based isnad order) |
| `TAUGHT` | Narrator → Narrator | students_inds | — |
| `STUDIED_FROM` | Narrator → Narrator | teachers_inds | — |

`TAUGHT` and `STUDIED_FROM` are kept as separate faithful mirrors of the two source
fields (they are not perfectly symmetric in the source data).

### Output artifacts (`data/graph/`)

```
nodes/surah.csv  nodes/ayah.csv  nodes/word.csv  nodes/root.csv
nodes/lemma.csv  nodes/hadith.csv nodes/narrator.csv
edges.csv        # source,type,target,props(JSON)
graph.cypher     # idempotent MERGE statements
graph_manifest.json  # counts, schema, unresolved ids, sources, timestamp
```

### API / CLI

- `quran_nlp.graph.build_graph()` → `KnowledgeGraph` (nodes + edges in memory).
- `KnowledgeGraph.export(output_dir)` → CSVs + Cypher + manifest.
- `KnowledgeGraph.neighbors(id)` / `.stats()` for querying.
- CLI: `quran-nlp graph build [--out data/graph]`, `quran-nlp graph stats`.
- Script: `scripts/build_graph.py` (stdlib-only, mirrors `build_embeddings.py`).

---

## Acceptance criteria (testable)

1. Exactly **6,236 Ayah** and **114 Surah** nodes; every ayah has exactly one
   `IN_SURAH` edge.
2. **77,429 Word** nodes; each `HAS_WORD`-linked from exactly one ayah; every ayah
   has ≥ 1 word; no orphan words.
3. Root/Lemma counts == morphology-derived counts (1,642 / 4,832); every Word with
   a stem has `HAS_ROOT`/`HAS_LEMMA`; aggregated Ayah→Root, Ayah→Lemma, Lemma→Root
   edges exist and are consistent.
4. **34,441 Hadith** nodes; **173,636** resolved `NARRATED_BY` edges; 103 unresolved
   chain ids recorded in the manifest; **zero** dangling narrator edges.
5. **24,326 Narrator** nodes; `TAUGHT`/`STUDIED_FROM` edges emitted only for resolved
   pairs (36,018 / 29,230); zero dangling edges.
6. `export()` writes all files; `graph.cypher` statement count == node+edge count;
   `graph_manifest.json` matches the in-memory counts.
7. `python -m quran_nlp graph build` runs with stdlib only and reproduces the same
   counts (deterministic); `pytest` passes.

## Out of scope (v1)

- Isnad/chain parsing for `arabic_hadith` (62k) and `thaqalayn` (27k) — these have no
  structured chain, so they are not added as Hadith nodes yet.
- Sanadset 650k full corpus (only samples are in-repo).
- Hadith authentication / narrator-grade classification (built *on top of* this graph).
- Translation/Tafsir nodes.
