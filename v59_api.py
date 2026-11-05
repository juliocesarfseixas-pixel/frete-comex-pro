"""Contrato HTTP versionado V5.9, sem persistência e sem envio de e-mail.

Este módulo NÃO é registrado no server.py de produção. A integração
deve ocorrer somente depois de testes end-to-end e aprovação do deploy.
"""
from __future__ import annotations

from io import BytesIO
from html import escape
from typing import Any
import json
import re

from v59_scoring import evaluate, TOTAL_QUESTIONS

MAX_BODY_BYTES = 100_000
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def validate_submission(payload: Any) -> dict:
    """Valida entrada para futura rota POST /api/v59/diagnosticos.

    Não confunde cadastro validado com verificação da posse do e-mail.
    """
    if not isinstance(payload, dict):
        raise ValueError("Envie um objeto JSON.")
    company = payload.get("company")
    if not isinstance(company, dict):
        raise ValueError("Identificação da transportadora obrigatória.")
    name = company.get("name")
    email = company.get("email")
    responsible = company.get("responsible", "")
    if not isinstance(name, str) or not 2 <= len(name.strip()) <= 120:
        raise ValueError("Informe o nome da transportadora (2 a 120 caracteres).")
    if not isinstance(email, str) or len(email) > 254 or not EMAIL_PATTERN.fullmatch(email.strip()):
        raise ValueError("Informe um e-mail válido.")
    if not isinstance(responsible, str) or len(responsible) > 100:
        raise ValueError("Nome do responsável inválido.")
    if "cnpj" in company or "whatsapp" in company or "marketingOptIn" in payload:
        raise ValueError("O cadastro V5.9 não coleta CNPJ, WhatsApp ou marketing.")
    responses = payload.get("responses")
    result = evaluate(responses)
    return {
        "company": {
            "name": name.strip(),
            "email": email.strip().lower(),
            "responsible": responsible.strip(),
        },
        "responses": responses,
        "result": result,
    }


def make_summary_pdf(submission: dict) -> bytes:
    """PDF preliminar: pontuações reais; não afirma certificação ou auditoria.

    O relatório visual completo e a listagem das 35 perguntas dependem
    da integração do catálogo de questões e do design V5.9.
    """
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.pagesizes import A4

    validated = validate_submission(submission)
    result = validated["result"]
    company = validated["company"]
    stream = BytesIO()
    document = SimpleDocTemplate(stream, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitleV59", parent=styles["Title"], alignment=TA_CENTER, textColor=colors.HexColor("#0A203B")))
    story = [
        Paragraph("RAIO-X DO TRANSPORTADOR", styles["ReportTitleV59"]),
        Spacer(1, 12),
        Paragraph("Diagnóstico gerencial — resultado preliminar", styles["Heading2"]),
        Paragraph("Transportadora: " + escape(company["name"]), styles["Normal"]),
        Spacer(1, 16),
    ]
    overall = "Insuficiência de respostas válidas" if result["overall_score"] is None else f'{result["overall_score"]:.1f} / 100'
    story.append(Paragraph("Índice geral: " + overall, styles["Heading2"]))
    rows = [["Dimensão", "Respostas válidas", "Nota / 100"]]
    for dimension in result["dimensions"]:
        score = "Não calculada" if dimension["score"] is None else f'{dimension["score"]:.1f}'
        rows.append([dimension["name"], f'{dimension["valid"]}/{dimension["total"]}', score])
    table = Table(rows, colWidths=[230, 110, 110], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0A203B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EAF3F9")]),
        ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#D8E3EB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
    ]))
    story += [Spacer(1, 12), table, Spacer(1, 20)]
    story.append(Paragraph(
        "Método: respostas de 0 a 4. 'Não sei informar' não pontua. "
        "Cada dimensão exige 80% de respostas válidas. A nota geral só aparece "
        "quando todas as dimensões atingem esse mínimo. "
        "Autoavaliação gerencial, não auditoria, certificação ou verificação legal.",
        styles["BodyText"],
    ))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#637B91"))
        canvas.drawString(42, 28, "Raio-X do Transportador | " + company["name"][:55])
        canvas.drawRightString(A4[0] - 42, 28, str(doc.page))
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return stream.getvalue()


def process_json(raw: bytes) -> tuple[dict, bytes]:
    """Futura função de serviço; não armazena nem envia dados."""
    if not raw or len(raw) > MAX_BODY_BYTES:
        raise ValueError("Tamanho de requisição inválido.")
    payload = json.loads(raw.decode("utf-8"))
    validated = validate_submission(payload)
    return validated["result"], make_summary_pdf(payload)
