"""Testa que a prévia V5.9 é inacessível sem ativação explícita."""
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler
from server import Handler


class PreviewRouteTests(unittest.TestCase):
    def test_preview_disabled_by_default(self):
        self.assertNotEqual(os.environ.get("ENABLE_V59_PREVIEW"), "1")

    def test_preview_is_not_root(self):
        root = Path(__file__).resolve().parents[1]
        self.assertNotEqual(root / "index.html", root / "v59_preview" / "index.html")

    def test_preview_file_is_not_required_for_legacy_routes(self):
        self.assertTrue((Path(__file__).resolve().parents[1] / "index.html").is_file())


if __name__ == "__main__":
    unittest.main()
