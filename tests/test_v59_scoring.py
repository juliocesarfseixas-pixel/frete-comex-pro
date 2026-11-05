"""Testes do motor V5.9. Execute: python -m unittest discover -s tests -v"""
import unittest
from v59_scoring import evaluate


class ScoringV59Tests(unittest.TestCase):
    def test_all_high(self):
        result = evaluate([4] * 35)
        self.assertEqual(result["overall_score"], 100.0)
        self.assertEqual(result["governance_score"], 100.0)
        self.assertTrue(result["sufficient"])

    def test_all_zero_is_valid(self):
        result = evaluate([0] * 35)
        self.assertEqual(result["overall_score"], 0.0)
        self.assertTrue(result["sufficient"])

    def test_unknown_is_excluded(self):
        answers = [4] * 35
        answers[0] = None
        answers[10] = None
        result = evaluate(answers)
        self.assertEqual(result["overall_score"], 100.0)
        self.assertEqual(result["valid_responses"], 33)

    def test_governance_needs_eight_of_ten(self):
        answers = [4] * 35
        answers[:3] = [None] * 3
        result = evaluate(answers)
        self.assertIsNone(result["governance_score"])
        self.assertIsNone(result["overall_score"])
        self.assertFalse(result["sufficient"])

    def test_department_needs_four_of_five(self):
        answers = [4] * 35
        answers[10:12] = [None, None]
        result = evaluate(answers)
        self.assertIsNone(result["departments"][0]["score"])
        self.assertIsNone(result["overall_score"])

    def test_invalid_scores_and_count(self):
        for bad in ([4] * 34, [4] * 34 + [5], [4] * 34 + [True], [4] * 34 + ["4"]):
            with self.assertRaises(ValueError):
                evaluate(bad)


if __name__ == "__main__":
    unittest.main()
