"""Teste HTTP de ponta a ponta para rotas V5.9 sem persistência.

Usa servidor local temporário e não acessa Render/Supabase.
"""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class V59HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.port = free_port()
        env = os.environ.copy()
        env.pop("DATABASE_URL", None)
        env["PORT"] = str(cls.port)
        env["SQLITE_PATH"] = str(Path(cls.temp.name) / "test.sqlite3")
        cls.server = subprocess.Popen(
            [sys.executable, "server.py"],
            cwd=ROOT, env=env, stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        for _ in range(60):
            if cls.server.poll() is not None:
                raise RuntimeError("Servidor de teste encerrou inesperadamente.")
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{cls.port}/health", timeout=1
                ) as response:
                    if response.status == 200:
                        break
            except (urllib.error.URLError, TimeoutError):
                time.sleep(0.1)
        else:
            raise RuntimeError("Servidor de teste não iniciou.")

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        try:
            cls.server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cls.server.kill()
            cls.server.wait()
        cls.temp.cleanup()

    def request(self, path, payload):
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=body, headers={"Content-Type": "application/json"},
            method="POST",
        )
        return urllib.request.urlopen(request, timeout=5)

    def sample(self):
        return {
            "company": {
                "name": "Transportadora Teste",
                "email": "teste@example.com",
            },
            "responses": [4] * 35,
        }

    def test_preview_returns_actual_score(self):
        with self.request("/api/v59/preview", self.sample()) as response:
            self.assertEqual(response.status, 200)
            result = json.load(response)
        self.assertEqual(result["result"]["overall_score"], 100.0)
        self.assertFalse(result["stored"])
        self.assertFalse(result["emailSent"])

    def test_pdf_returns_valid_signature(self):
        with self.request("/api/v59/relatorio", self.sample()) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers.get_content_type(), "application/pdf")
            self.assertTrue(response.read(8).startswith(b"%PDF-"))

    def test_missing_email_is_rejected(self):
        payload = self.sample()
        payload["company"]["email"] = ""
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request("/api/v59/preview", payload)
        self.assertEqual(error.exception.code, 400)

    def test_legacy_health_still_works(self):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/health") as response:
            self.assertEqual(response.read(), b"OK")


if __name__ == "__main__":
    unittest.main()
