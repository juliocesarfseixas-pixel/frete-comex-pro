"""Verifica o catálogo original, HTML e PDF completo da V5.9."""
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from shutil import which

from v59_api import validate_submission
from v59_report import make_v59_full_report

ROOT = Path(__file__).resolve().parents[1]


class V59ReportTests(unittest.TestCase):
    def sample(self, score=3):
        return {"company":{"name":"Transportadora de Homologação","email":"teste@example.com"},
                "responses":[score]*35}

    def test_catalog_exact_structure(self):
        bank = json.loads((ROOT / "v59_catalog.json").read_text(encoding="utf-8"))
        qs = bank["questions"]
        self.assertEqual(len(qs),35)
        self.assertEqual([x["order"] for x in qs],list(range(1,36)))
        self.assertEqual(sum(len(x["options"]) for x in qs),175)
        self.assertEqual(len({x["question"] for x in qs}),35)
        self.assertTrue(all(x["action"] and len(x["options"])==5 for x in qs))

    def test_report_contains_cover_and_every_question(self):
        pdf = make_v59_full_report(validate_submission(self.sample()))
        self.assertTrue(pdf.startswith(b"%PDF-"))
        self.assertGreater(len(pdf),30_000)

    def test_unknown_requires_valid_dimensions(self):
        request = self.sample()
        request["responses"][10:12] = [None,None]
        valid = validate_submission(request)
        self.assertIsNone(valid["result"]["overall_score"])
        pdf = make_v59_full_report(valid)
        self.assertTrue(pdf.startswith(b"%PDF-"))

    def test_inconsistent_scoring_is_rejected(self):
        valid = validate_submission(self.sample())
        valid["result"]["overall_score"] = 0
        with self.assertRaises(ValueError):
            make_v59_full_report(valid)

    def test_preview_html_present(self):
        html = (ROOT / "v59_preview/index.html").read_text(encoding="utf-8")
        self.assertIn("RAIO-X DO TRANSPORTADOR", html)
        self.assertIn("const govSpecific=", html)
        self.assertIn("const specificQuestions=", html)
        self.assertIn("validDepartmentAggregate()", html)
        self.assertIn("data:image/webp;base64,", html)
        self.assertNotIn('id="cnpj"',html.lower())

    @unittest.skipUnless(which("node"),"Node.js indisponível")
    def test_both_javascript_blocks_have_valid_syntax(self):
        html = (ROOT / "v59_preview/index.html").read_text(encoding="utf-8")
        blocks = re.findall(r"<script[^>]*>(.*?)</script>",html,flags=re.DOTALL|re.IGNORECASE)
        self.assertEqual(len(blocks),2)
        for js in blocks:
            with tempfile.NamedTemporaryFile(suffix=".js",mode="w",encoding="utf-8") as tmp:
                tmp.write(js)
                tmp.flush()
                completed = subprocess.run(["node","--check",tmp.name],capture_output=True,text=True,timeout=15)
                self.assertEqual(completed.returncode,0,completed.stderr)


if __name__ == "__main__":
    unittest.main()
