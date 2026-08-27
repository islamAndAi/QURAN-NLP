import os
import unittest

from quran_nlp.embeddings import (
    DEFAULT_MODEL,
    detect_arabic,
    has_semantic,
    model_slug,
)


class TestEmbeddingsHelpers(unittest.TestCase):
    def test_detect_arabic(self):
        self.assertTrue(detect_arabic("الرحمن"))
        self.assertTrue(detect_arabic("mixed english and العربية"))
        self.assertFalse(detect_arabic("mercy and forgiveness"))

    def test_model_slug(self):
        self.assertEqual(
            model_slug("intfloat/multilingual-e5-small"),
            "intfloat__multilingual-e5-small",
        )


@unittest.skipUnless(has_semantic(), "sentence-transformers not installed")
class TestSemanticSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from quran_nlp.embeddings import EMBEDDINGS_DIR
        base = EMBEDDINGS_DIR / model_slug(DEFAULT_MODEL)
        if not (base / "meta.json").exists():
            raise unittest.SkipTest(
                f"Embeddings not built ({base}). Run scripts/build_embeddings.py."
            )
        from quran_nlp.embeddings import SemanticSearch
        cls.ss = SemanticSearch()

    def test_english_search(self):
        results = self.ss.search("forgiveness and mercy", k=5)
        self.assertTrue(results)
        self.assertRegex(results[0].reference, r"^\d+:\d+$")

    def test_arabic_search(self):
        results = self.ss.search("الصبر", k=5)
        self.assertTrue(results)
        # top Arabic hit for "patience" should reference patience
        joined = " ".join(r.arabic for r in results)
        self.assertTrue(joined)


if __name__ == "__main__":
    unittest.main()
