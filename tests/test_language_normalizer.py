"""
Regression test Text Normalizer + kejujuran verify_examples.

Memakai unittest (jalan di bawah `python -m unittest` maupun `python -m pytest`),
sehingga tidak menambah dependensi. Semua nomor identitas di sini adalah DUMMY.
"""
import ast
import pathlib
import unittest

from app.language import normalizer as normalizer_module
from app.language.intent import EXAMPLES_MINIMUM, classify_intent, verify_examples
from app.language.normalizer import TextNormalizer, normalize_text
from app.language.schemas import NormalizationResult, NormalizeResult


class NormalizerRegressionTest(unittest.TestCase):
    def assertNormalized(self, text, expected):
        self.assertEqual(normalize_text(text).normalized, expected, msg=f"input={text!r}")

    def test_workflow_cases(self):
        cases = [
            ("singkat", "singkat"),
            ("gk bisa cek KTP", "tidak bisa cek KTP"),
            ("saya jg mau cek KK", "saya juga mau cek KK"),
            ("jgn dihapus", "jangan dihapus"),
            ("gak bisa login", "tidak bisa login"),
            ("nggak bisa", "tidak bisa"),
            ("gw mau cek KTP", "saya mau cek KTP"),
            ("lu sudah cek?", "kamu sudah cek?"),
            ("NIK saya 367xxxxxxxxxxxxx", "NIK saya 367xxxxxxxxxxxxx"),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertNormalized(text, expected)

    def test_words_containing_abbreviations_are_untouched(self):
        for word in ["singkat", "bagaimana", "tidak", "sudah", "simpan", "tempat", "kartu keluarga", "agar", "pagi", "jangan", "juga"]:
            with self.subTest(word=word):
                self.assertNormalized(word, word)

    def test_meaning_preserving(self):
        self.assertNormalized("buat KTP baru", "buat KTP baru")
        self.assertNormalized("halo, loh kok begitu", "halo, loh kok begitu")

    def test_digits_and_emails_protected(self):
        self.assertNormalized("NIK 3670000000000001", "NIK 3670000000000001")
        self.assertNormalized("hp 081200000000", "hp 081200000000")
        self.assertNormalized("cek di budi.sy@mail.test", "cek di budi.sy@mail.test")

    def test_no_double_spaces_and_edges(self):
        self.assertNormalized("gw  lo", "saya kamu")
        self.assertNormalized("  gw mau cek KTP  ", "saya mau cek KTP")
        self.assertNormalized("gw", "saya")
        self.assertNormalized("lu", "kamu")

    def test_domain_tokens_uppercased_as_tokens(self):
        self.assertNormalized("ktp kk nik npwp sim nib kia stnk skck", "KTP KK NIK NPWP SIM NIB KIA STNK SKCK")

    def test_changes_are_reported(self):
        r = normalize_text("gk bisa")
        self.assertIn("abbr: 'gk' -> 'tidak' (x1)", r.changes)

    def test_empty_and_custom_dict(self):
        self.assertEqual(normalize_text("   ").normalized, "")
        n = TextNormalizer(abbreviations={" xy ": "ganti"}, typo_fixes={"zz": "ZZ"})
        self.assertEqual(n.normalize("xy zz xyz").normalized, "ganti ZZ xyz")

    def test_result_contract_alias(self):
        self.assertIs(NormalizeResult, NormalizationResult)
        self.assertIsInstance(normalize_text("halo"), NormalizationResult)


class DictionaryHygieneTest(unittest.TestCase):
    """Cek statis: tidak ada key dobel dan tidak ada rule berbahaya."""

    @staticmethod
    def _dict_keys(name):
        src = pathlib.Path(normalizer_module.__file__).read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(src)):
            target = None
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                target = node.target.id
            if target == name and isinstance(node.value, ast.Dict):
                return [k.value for k in node.value.keys]
        raise AssertionError(f"{name} tidak ditemukan")

    def test_no_duplicate_keys(self):
        for name in ("_ABBREVIATIONS", "_TYPO_FIXES"):
            keys = self._dict_keys(name)
            self.assertEqual(len(keys), len(set(keys)), msg=f"duplikat di {name}")

    def test_dangerous_rules_removed(self):
        keys = self._dict_keys("_ABBREVIATIONS")
        for bad in ("g", "buat"):
            self.assertNotIn(bad, keys)
        self.assertEqual(normalizer_module._ABBREVIATIONS["gk"], "tidak")
        self.assertEqual(normalizer_module._ABBREVIATIONS["jg"], "juga")
        self.assertEqual(normalizer_module._ABBREVIATIONS["jgn"], "jangan")


class IntentReportingTest(unittest.TestCase):
    def test_verify_examples_is_honest(self):
        r = verify_examples()
        self.assertEqual(r["total"], len(EXAMPLES_MINIMUM))
        self.assertEqual(r["total"], len(r["results"]))
        self.assertEqual(r["passed"], sum(1 for x in r["results"] if x["ok"]))
        self.assertEqual(r["passed"] + r["failed"], r["total"])

    def test_trailing_punctuation_does_not_break_intent(self):
        self.assertEqual(classify_intent("halo?").intent, "greeting")
        self.assertEqual(classify_intent("cek status?").intent, "ask_document_status")


class EngineIntegrationTest(unittest.TestCase):
    def test_engine_does_not_corrupt_text(self):
        from app.language.engine import create_language_engine

        engine = create_language_engine()
        self.assertEqual(engine.process("singkat").output.text, "singkat")
        self.assertEqual(engine.process("Saya gk bisa cek KTP").output.text, "saya tidak bisa cek KTP")


if __name__ == "__main__":
    unittest.main()
