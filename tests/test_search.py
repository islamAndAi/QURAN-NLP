import unittest

from quran_nlp import EnglishSearch, search_arabic


class TestEnglishSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.es = EnglishSearch()

    def test_mercy_returns_mercy_verses(self):
        top = self.es.search("mercy", k=3)
        self.assertTrue(top)
        # the top result's preview text should be about mercy
        combined = " ".join(r.preview() for r in top).lower()
        self.assertIn("mercy", combined)

    def test_reference_format(self):
        r = self.es.search("patience", k=1)[0]
        self.assertRegex(r.reference, r"^\d+:\d+$")


class TestArabicSearch(unittest.TestCase):
    def test_bismillah_found(self):
        results = search_arabic("الرحمن الرحيم", k=5)
        refs = {r.reference for r in results}
        self.assertIn("1:1", refs)

    def test_diacritics_insensitive(self):
        a = search_arabic("موسى", k=10)
        b = search_arabic("مُوسَىٰ", k=10)
        self.assertEqual({r.reference for r in a}, {r.reference for r in b})


if __name__ == "__main__":
    unittest.main()
