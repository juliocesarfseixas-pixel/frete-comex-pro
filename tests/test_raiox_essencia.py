"""Contrato de originalidade e segurança da nova prévia visual Raio-X."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "experimentos" / "essencia-2026"


class EssenciaVisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.css = (ROOT / "styles.css").read_text(encoding="utf-8")
        cls.js = (ROOT / "app.js").read_text(encoding="utf-8")
        cls.catalog = json.loads((ROOT / "perguntas-v59-originais.json").read_text(encoding="utf-8"))

    def test_catalog_has_35_questions_and_175_specific_options(self):
        q = self.catalog["questions"]
        self.assertEqual(len(q), 35)
        self.assertTrue(all(len(x["options"]) == 5 for x in q))
        self.assertEqual(len({x["question"] for x in q}), 35)
        self.assertEqual(len({x["dimension"] for x in q}), 6)

    def test_embedded_catalog_matches_source_exactly(self):
        m = re.search(r'<script id="questionCatalog" type="application/json">(.*?)</script>', self.html, re.S)
        self.assertIsNotNone(m)
        self.assertEqual(json.loads(m.group(1)), self.catalog)

    def test_original_truck_and_design_tokens_preserved(self):
        self.assertTrue((ROOT / "assets/caminhao-original.webp").is_file())
        self.assertIn("#071726", self.css)
        self.assertIn("#ecc075", self.css)
        self.assertIn("caminhao-original.webp", self.css)
        self.assertIn('id="report"', self.html)

    def test_preview_has_no_hidden_collection(self):
        self.assertNotIn("fetch(", self.js)
        self.assertNotIn("localStorage.setItem(", self.js)
        self.assertNotIn("navigator.sendBeacon(", self.js)
        self.assertIn('id="email"', self.html)
        self.assertNotIn('id="cnpj"', self.html)
        self.assertNotIn('id="whatsapp"', self.html)

    def test_print_uses_same_stylesheet_as_dashboard(self):
        self.assertIn("@media print", self.css)
        self.assertIn("-webkit-print-color-adjust:exact", self.css)
        self.assertIn('id="reportScreen"', self.html)
        self.assertIn("window.print()", self.js)


if __name__ == "__main__":
    unittest.main()
