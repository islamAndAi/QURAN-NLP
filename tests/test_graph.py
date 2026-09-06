import json
import tempfile
import unittest
from pathlib import Path

from quran_nlp import build_graph, buckwalter_to_arabic
from quran_nlp.graph import can_transliterate


class TestGraphBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = build_graph()

    # -- node counts ----------------------------------------------------------
    def test_node_counts(self):
        expected = {
            "Surah": 114,
            "Ayah": 6236,
            "Word": 77429,
            "Root": 1642,
            "Lemma": 4832,
            "Hadith": 34441,
            "Narrator": 24326,
        }
        stats = self.g.stats()["nodes"]
        self.assertEqual(stats, expected)

    # -- edge counts ----------------------------------------------------------
    def test_edge_counts(self):
        expected = {
            "IN_SURAH": 6236,
            "HAS_WORD": 77429,
            "HAS_LEMMA": 74608,
            "HAS_ROOT": 49968,
            "NARRATED_BY": 173636,
            "TAUGHT": 29230,
            "STUDIED_FROM": 36018,
        }
        stats = self.g.stats()["edges"]
        self.assertEqual(stats, expected)

    # -- coverage surfaced honestly -------------------------------------------
    def test_coverage_metrics(self):
        self.assertEqual(self.g.stats()["unresolved_chain_ids"], 103)
        self.assertEqual(self.g.stats()["chainless_hadiths"], 123)

    # -- structural invariants -------------------------------------------------
    def test_no_dangling_edges(self):
        for e in self.g.edges:
            self.assertIn(e["source"], self.g.nodes, e)
            self.assertIn(e["target"], self.g.nodes, e)

    def test_every_ayah_has_words_and_every_word_one_ayah(self):
        has_word_src = {e["source"] for e in self.g.edges if e["type"] == "HAS_WORD"}
        has_word_tgt = {e["target"] for e in self.g.edges if e["type"] == "HAS_WORD"}
        ayah_ids = {nid for nid, n in self.g.nodes.items() if n["label"] == "Ayah"}
        word_ids = {nid for nid, n in self.g.nodes.items() if n["label"] == "Word"}
        self.assertEqual(has_word_src, ayah_ids)          # every ayah has >= 1 word
        self.assertEqual(has_word_tgt, word_ids)          # every word linked exactly once
        self.assertEqual(len(has_word_tgt), len(word_ids))

    def test_narrator_edges_endpoints(self):
        for e in self.g.edges:
            if e["type"] == "NARRATED_BY":
                self.assertEqual(self.g.nodes[e["source"]]["label"], "Hadith")
                self.assertEqual(self.g.nodes[e["target"]]["label"], "Narrator")
            elif e["type"] in ("TAUGHT", "STUDIED_FROM"):
                self.assertEqual(self.g.nodes[e["source"]]["label"], "Narrator")
                self.assertEqual(self.g.nodes[e["target"]]["label"], "Narrator")

    def test_narrated_by_position_preserves_isnad_order(self):
        pos = {}
        for e in self.g.edges:
            if e["type"] == "NARRATED_BY":
                self.assertIsNotNone(e["position"])
                self.assertGreaterEqual(e["position"], 1)
                pos.setdefault(e["source"], []).append(e["position"])
        for hadith_id, positions in pos.items():
            # isnad order is preserved; gaps are expected (unresolved narrators)
            self.assertEqual(positions, sorted(positions), hadith_id)
    def test_narrator_uses_generation_not_grade(self):
        for nid, n in self.g.nodes.items():
            if n["label"] == "Narrator":
                self.assertIn("generation", n["props"])
                self.assertNotIn("grade", n["props"])

    # -- encoding / transliteration -------------------------------------------
    def test_buckwalter_transliteration(self):
        self.assertEqual(buckwalter_to_arabic("rHm"), "\u0631\u062d\u0645")  # رحم
        self.assertEqual(buckwalter_to_arabic("smw"), "\u0633\u0645\u0648")   # سمو
        self.assertTrue(can_transliterate("rHm"))
        self.assertFalse(can_transliterate("rHm^"))  # QAC-only symbol

    def test_root_and_lemma_arabic_names(self):
        self.assertEqual(self.g.nodes["root:rHm"]["props"]["name_ar"],
                         "\u0631\u062d\u0645")
        # lemma:{ll~ah is one of the 69.5% with a verified Arabic name in lemmas.csv
        self.assertTrue(self.g.nodes["lemma:{ll~ah"]["props"]["name_ar"])

    # -- derived projections ---------------------------------------------------
    def test_derive_ayah_roots(self):
        roots = {t for (s, t) in self.g.derive_ayah_roots() if s == "ayah:1"}
        self.assertEqual(roots, {"root:Alh", "root:rHm", "root:smw"})

    def test_derive_lemma_roots_consistent_with_word_edges(self):
        # every derived (lemma, root) pair must be attested by a word with both.
        lemma_words = {}
        root_words = {}
        for e in self.g.edges:
            if e["type"] == "HAS_LEMMA":
                lemma_words.setdefault(e["target"], set()).add(e["source"])
            elif e["type"] == "HAS_ROOT":
                root_words.setdefault(e["target"], set()).add(e["source"])
        for lemma, root in self.g.derive_lemma_roots():
            self.assertTrue(
                lemma_words.get(lemma, set()) & root_words.get(root, set()),
                (lemma, root),
            )

    # -- determinism -----------------------------------------------------------
    def test_deterministic_build(self):
        g2 = build_graph()
        self.assertEqual(self.g.stats(), g2.stats())

    # -- export ----------------------------------------------------------------
    def test_export_writes_expected_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.g.export(tmp)
            out = Path(tmp)
            for label in ("surah", "ayah", "word", "root", "lemma", "hadith", "narrator"):
                self.assertTrue((out / "nodes" / f"{label}.csv").exists(), label)
            self.assertTrue((out / "edges.csv").exists())
            self.assertTrue((out / "graph.cypher").exists())
            self.assertTrue((out / "graph_manifest.json").exists())

            # manifest counts must match in-memory stats
            manifest = json.loads((out / "graph_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["node_counts"], self.g.stats()["nodes"])
            self.assertEqual(manifest["edge_counts"], self.g.stats()["edges"])
            self.assertEqual(manifest["total_nodes"],
                             sum(self.g.stats()["nodes"].values()))
            self.assertEqual(manifest["total_edges"],
                             sum(self.g.stats()["edges"].values()))
            # no timestamp -> deterministic manifest
            self.assertNotIn("timestamp", manifest)

            # edges.csv: header + one row per edge
            edges_lines = (out / "edges.csv").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(edges_lines), 1 + len(self.g.edges))


if __name__ == "__main__":
    unittest.main()
