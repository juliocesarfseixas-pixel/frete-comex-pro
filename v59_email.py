"""Entrega transacional opcional de relatório V5.9 pelo Resend.

Somente habilitar depois de verificar domínio remetente e testar entrega.
Não envia marketing. Aceitação da API não comprova entrega na caixa postal.
"""
from __future__ import annotations
import base64
import json
import os
import urllib.error
import urllib.request


def send_v59_pdf(recipient: str, pdf: bytes, report_id: str) -> str:
    """Retorna accepted, failed ou not_configured sem expor segredos."""
    key = os.environ.get("RESEND_API_KEY", "").strip()
    sender = os.environ.get("EMAIL_FROM", "").strip()
    if not key or not sender:
        return "not_configured"
    if not isinstance(recipient, str) or len(recipient) > 254 or not isinstance(pdf, bytes) or not pdf.startswith(b"%PDF-"):
        raise ValueError("Dados inválidos para e-mail transacional.")
    if not isinstance(report_id,str) or len(report_id)>80 or not report_id:
        raise ValueError("Identificador de envio inválido.")
    body = {
        "from": sender,
        "to": [recipient],
        "subject": "Seu diagnóstico | Raio-X do Transportador V5.9",
        "html": (
            "<p>Seu diagnóstico executivo Raio-X do Transportador está pronto.</p>"
            "<p>Segue o relatório solicitado em anexo.</p>"
            "<p>Mensagem exclusivamente operacional; sem conteúdo publicitário.</p>"
            "<p>Para dúvidas de privacidade: juliocesarfseixas@gmail.com.</p>"
        ),
        "attachments": [{
            "filename": "Raio-X-do-Transportador-V5.9.pdf",
            "content": base64.b64encode(pdf).decode("ascii"),
        }],
    }
    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(body,ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "Idempotency-Key": "raiox-v59-" + report_id,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return "accepted" if response.status in (200,201,202) else "failed"
    except (urllib.error.URLError, TimeoutError):
        return "failed"
