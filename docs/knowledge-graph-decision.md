# Knowledge Graph — Council Decision Memo

Date: 2026-09-06 · Council: 10 read-only persona advisors (all `oracle`, forked context) · Passes: 1 (no cross-exam needed — converged).

## Question

(1) What is the best next step for QURAN-NLP? (2) Is the proposed knowledge-graph
design (`docs/knowledge-graph.md`) correct?

## Verdict

**Build the knowledge graph — with a corrected spec.** 7/10 advisors endorsed
KG-first (quranic-linguist, graph-engineer, hadith-scholar, oss-maintainer,
data-engineer, religious-accuracy, research-scientist); 3 dissented on *order*
(arabic-nlp → eval-first, backend → API-first, product → API+eval-first), not on
the KG's validity. The 3 dissenters' core point is adopted as scope guard: **the
KG is built this session; the search eval benchmark (nDCG@10) is the explicitly
scheduled next increment**, and the KG must not be treated as a serving layer.

## Corrections adopted (convergent, evidence-backed)

1. **Encoding is QAC transliteration, not "standard Buckwalter".** Roots (1,642)
   are clean standard Buckwalter; lemmas (4,832) carry QAC-only symbols
   (`^`, `` ` ``, `_`, `#`, `@`, `[`, `,`, `.`). Fix: populate `Lemma.name_ar`
   from `quran_lemmas.csv` (69.5% verified); transliterate the rest **only** when
   all chars are in the standard table, else leave `name_ar` empty (never emit a
   corrupted Arabic glyph). Roots are fully transliterable.
2. **`grade` → `generation`.** `kaggle_rawis.grade` is a generational tier
   (Comp./Tabi'/Taba' Tabi'/3rd C.), **not** a jarh/ta'deel reliability grade
   (verified: zero reliability keywords across 24,326 rows). Rename + add a
   manifest disclaimer: "no graph field is an authentication ruling."
3. **Word semantics.** `form` = concatenated segment surface (Buckwalter);
   `pos`/`tag` from the first STEM segment; `HAS_LEMMA`/`HAS_ROOT` edges come from
   **all** STEM segments (handles the 486 two-stem words). "Every stemmed word has
   HAS_ROOT" is **false** — particles/function words have LEM but no ROOT.
4. **Aggregated edges dropped from storage.** Ayah→Root, Ayah→Lemma, Lemma→Root
   are derivable from Word→Root/Word→Lemma (single source of truth). Exposed via
   `KnowledgeGraph.derive_*()` instead of stored rows.
5. **`position` is a typed column** (no JSON-in-CSV); documented semantics:
   1-based, position 1 = transmitter nearest the compiler, last = Companion/source
   (verified against `text_ar` isnad for Bukhari 1).
6. **Cypher idempotency:** uniqueness constraints per label + escaped MERGE.
7. **Determinism:** no timestamp in manifest; all CSVs sorted by stable key;
   `json.dump(sort_keys=True)`; SHA-256 input checksums in the manifest.
8. **Tests are `unittest`** (CI runs `python -m unittest discover -s tests`).
9. **Generated dump is gitignored** (`data/graph/`), regenerated in CI — commit
   only builder + tests + docs (matches `data/embeddings/` convention).
10. **Unify naming:** every node CSV uses `id`; Arabic text is `text_ar`
    everywhere (drop `ayah_ar`).
11. **Surface coverage honestly:** 103 dangling chain ids + 123 chainless hadiths
    recorded in the manifest as a measured coverage metric.
12. **Defer** `quran_dictionary.csv` / `quran_verbs.csv` merge (property
    enrichment only; Arabic→ASCII is the ambiguous direction — safe to defer).

## Owner decisions

- **Sequencing:** KG-first (7/10) stands; eval benchmark is the next increment.
- **Structure:** build the quran subgraph and hadith subgraph as separable
  functions so they can ship as two PRs (PR A: Surah/Ayah/Word/Root/Lemma;
  PR B: Hadith/Narrator).
- **Licensing:** the hadith/narrator subgraph re-publishes a modern English
  translation (`text_en`) and a modern narrator database with **uncleared**
  licenses. The Quranic subgraph is safe now. Mitigation: mark the hadith
  subgraph research-use-only in the manifest + docs, add per-source attribution,
  and **do not commit/publish the generated dump** until licenses are cleared.

## Rejected / deferred feedback

- Eval-benchmark-first (arabic-nlp) and API-first (backend, product) → deferred
  to next increment; their "search is unmeasured" point is recorded and accepted.
- Root/lemma-aware Arabic retrieval index (arabic-nlp) → separate build, out of
  scope for the graph.
- Isnad link-prediction holdout + root/lemma retrieval benchmark
  (research-scientist) → out of scope for a stdlib build; a deterministic
  root/lemma sanity test is included instead.
- Parquet/RDF export (graph-engineer/data-engineer) → CSV is correct for v1 given
  the stdlib-only constraint.

## Evidence / run ids

Pass 1 workflow `2968e430-7917-4f49-aa2a-cb2342a73709`. Advisor run ids:
quranic-linguist `e3265ca2`, graph-engineer `23eee712`, arabic-nlp `e99ff3f7`,
hadith-scholar `d48a0a88`, backend `c42dab08`, oss-maintainer `5ebd98ef`,
product `1f5967d5`, data-engineer `e351a6fa`, religious-accuracy `d11be3d4`,
research-scientist `79f95343`.
