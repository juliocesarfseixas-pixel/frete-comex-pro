"""Testes do contrato V5.9; execute python -m unittest discover -s tests -v."""
import unittest
from v59_api import validate_submission, make_summary_pdf, process_json


def sample():
    return {
        "company": {"name": "Transportadora Exemplo", "email": "teste@example.com"},
        "responses": [4] * 35,
    }


class V59ApiTests(unittest.TestCase):
    def test_valid_registration_and_score(self):
        validated = validate_submission(sample())
        self.assertEqual(validated["result"]["overall_score"], 100.0)
        self.assertEqual(validated["company"]["email"], "teste@example.com")

    def test_required_company(self):
        data = sample()
        data["company"]["name"] = ""
        with self.assertRaises(ValueError):
            validate_submission(data)

    def test_required_email(self):
        data = sample()
        data["company"]["email"] = ""
        with self.assertRaises(ValueError):
            validate_submission(data)

    def test_forbidden_fields(self):
        for key, value in [("cnpj", "123"), ("whatsapp", "123")]:
            data = sample()
            data["company"][key] = value
            with self.assertRaises(ValueError):
                validate_submission(data)

    def test_pdf_generated(self):
        pdf = make_summary_pdf(sample())
        self.assertTrue(pdf.startswith(b"%PDF-"))
        self.assertGreater(len(pdf), 1000)

    def test_unknown_reduces_valid_count(self):
        data = sample()
        data["responses"][10:12] = [None, None]
        validated = validate_submission(data)
        self.assertIsNone(validated["result"]["overall_score"])


if __name__ == "__main__":
    unittest.main()
