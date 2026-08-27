import unittest

from quran_nlp import load_quran, load_translations, load_tafaseer, load_footnotes


class TestLoaders(unittest.TestCase):
    def test_quran_has_6236_ayahs(self):
        rows = load_quran()
        self.assertEqual(len(rows), 6236)
        self.assertIsInstance(rows[0]["ayah_no_quran"], int)

    def test_translations_long_format(self):
        rows = load_translations()
        self.assertGreater(len(rows), 0)
        self.assertIn("translator", rows[0])

    def test_tafaseer_nonempty(self):
        rows = load_tafaseer()
        self.assertGreater(len(rows), 0)

    def test_footnotes_nonempty(self):
        rows = load_footnotes()
        self.assertGreater(len(rows), 0)


if __name__ == "__main__":
    unittest.main()
