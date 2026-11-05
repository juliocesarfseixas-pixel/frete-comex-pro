"""Teste da persistência isolada V5.9 sem acesso ao Supabase real."""
import unittest
from unittest.mock import patch

from v59_storage import save_v59


class FakeCursor:
    def __init__(self):
        self.sql = None
        self.args = None
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def execute(self, sql, args):
        self.sql = sql
        self.args = args


class FakeConnection:
    def __init__(self): self.cur = FakeCursor()
    def cursor(self): return self.cur


class V59StorageTests(unittest.TestCase):
    def sample(self):
        return {
            "company": {"name": "Transportadora de Teste", "email": "TESTE@example.com"},
            "responses": [4] * 35,
        }

    def test_sql_is_parameterized_and_writes_only_versioned_schema(self):
        con = FakeConnection()
        identifier = save_v59(con, self.sample())
        self.assertEqual(len(identifier), 36)
        self.assertIn("INSERT INTO raiox_v59.diagnostics", con.cur.sql)
        self.assertNotIn("Transportadora de Teste", con.cur.sql)
        self.assertIn("Transportadora de Teste", con.cur.args)
        self.assertIn("teste@example.com", con.cur.args)
        self.assertEqual(con.cur.args[-1], "not_requested")
        self.assertNotIn("DELETE", con.cur.sql.upper())
        self.assertNotIn("UPDATE", con.cur.sql.upper())

    def test_invalid_payload_never_writes(self):
        con = FakeConnection()
        invalid = self.sample()
        invalid["responses"] = [4] * 34
        with self.assertRaises(ValueError):
            save_v59(con, invalid)
        self.assertIsNone(con.cur.sql)


if __name__ == "__main__":
    unittest.main()
