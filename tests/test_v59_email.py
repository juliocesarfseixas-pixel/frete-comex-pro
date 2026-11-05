"""Testes isolados do envio Resend V5.9 sem tráfego real."""
import json
import os
import unittest
from unittest.mock import patch

from v59_email import send_v59_pdf


class FakeHTTPResponse:
    status = 202
    def __enter__(self): return self
    def __exit__(self,*args): return False


class V59EmailTests(unittest.TestCase):
    def test_no_api_secret_never_sends(self):
        with patch.dict(os.environ,{},clear=True):
            self.assertEqual(send_v59_pdf("teste@example.com",b"%PDF-1.4", "123"),"not_configured")

    def test_transactional_payload_and_idempotency(self):
        with patch.dict(os.environ,{"RESEND_API_KEY":"test-only-key","EMAIL_FROM":"raiox@example.com"}):
            with patch("urllib.request.urlopen",return_value=FakeHTTPResponse()) as send:
                result=send_v59_pdf("teste@example.com",b"%PDF-1.4", "123")
        self.assertEqual(result,"accepted")
        req=send.call_args.args[0]
        self.assertEqual(req.get_method(),"POST")
        self.assertEqual(req.get_header("Idempotency-key"),"raiox-v59-123")
        data=json.loads(req.data)
        self.assertEqual(data["to"],["teste@example.com"])
        self.assertIn("Raio-X do Transportador",data["subject"])
        self.assertNotIn("marketing",req.data.decode().lower())
        self.assertEqual(data["attachments"][0]["filename"],"Raio-X-do-Transportador-V5.9.pdf")

    def test_invalid_pdf_rejected(self):
        with patch.dict(os.environ,{"RESEND_API_KEY":"test","EMAIL_FROM":"sender@example.com"}):
            with self.assertRaises(ValueError):
                send_v59_pdf("teste@example.com",b"NOT-PDF", "123")


if __name__ == "__main__":
    unittest.main()
