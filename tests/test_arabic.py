import unittest

from quran_nlp.arabic import normalize_arabic


class TestNormalizeArabic(unittest.TestCase):
    def test_strips_tashkeel_and_wasla(self):
        # harakat + shadda + alef-wasla all collapse
        self.assertEqual(normalize_arabic("بِسْمِ ٱللَّهِ"), "بسم الله")

    def test_alef_variants_collapse(self):
        self.assertEqual(normalize_arabic("آدم أدم إدم ادم"), "ادم ادم ادم ادم")

    def test_teh_marbuta_and_maqsura(self):
        self.assertEqual(normalize_arabic("موسى صلاه"), normalize_arabic("موسي صلاة"))

    def test_maqsura_superscript_alef(self):
        # Uthmani "مُوسَىٰ" (alef-maqsura + superscript alef) == Imla'i "موسى"
        self.assertEqual(normalize_arabic("مُوسَىٰ"), normalize_arabic("موسى"))

    def test_strips_tashkeel(self):
        self.assertEqual(normalize_arabic("مُحَمَّدٌ"), "محمد")


if __name__ == "__main__":
    unittest.main()
