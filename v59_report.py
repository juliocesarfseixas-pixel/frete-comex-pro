"""Relatório executivo do Raio-X V5.9, usando as 35 perguntas originais.

Recebe a saída já validada de v59_api.validate_submission().
O PDF é produzido em memória, sem persistência e sem transmissão externa.
"""
from __future__ import annotations

import base64
from html import escape
from io import BytesIO
import json
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / 'v59_catalog.json'
COVER = ROOT / 'v59_preview' / 'index.html'
NAVY = colors.HexColor('#0A213A')
BLUE = colors.HexColor('#166394')
GOLD = colors.HexColor('#F4B74F')
INK = colors.HexColor('#27374A')
MUTED = colors.HexColor('#65788D')
LIGHT = colors.HexColor('#E9F1F7')
GREEN = colors.HexColor('#158167')
PAGE_W, PAGE_H = A4


def _cover_photo():
    """Reaproveita a fotografia da capa já versionada no HTML da V5.9."""
    try:
        text = COVER.read_text(encoding='utf-8')
        image = re.search(r'data:image/(?:webp|jpeg|png);base64,([A-Za-z0-9+/=]{800,})', text)
        if image:
            return ImageReader(BytesIO(base64.b64decode(image.group(1), validate=True)))
    except (OSError, ValueError, TypeError):
        pass
    return None


def _styles():
    st = getSampleStyleSheet()
    st.add(ParagraphStyle(
        name='RXMain', parent=st['Heading1'], fontName='Helvetica-Bold',
        fontSize=19, leading=23, textColor=NAVY, spaceAfter=11,
    ))
    st.add(ParagraphStyle(
        name='RXSection', parent=st['Heading2'], fontName='Helvetica-Bold',
        fontSize=13, leading=17, textColor=BLUE, spaceBefore=9, spaceAfter=9,
    ))
    st.add(ParagraphStyle(
        name='RXBody', parent=st['Normal'], fontName='Helvetica',
        fontSize=9, leading=13.5, textColor=INK, spaceAfter=7,
    ))
    st.add(ParagraphStyle(
        name='RXSmall', parent=st['Normal'], fontName='Helvetica',
        fontSize=8, leading=11, textColor=INK,
    ))
    st.add(ParagraphStyle(
        name='RXMuted', parent=st['RXSmall'], textColor=MUTED,
    ))
    st.add(ParagraphStyle(
        name='RXCell', parent=st['RXSmall'], fontSize=8, leading=11.2,
    ))
    st.add(ParagraphStyle(
        name='RXCellHeader', parent=st['RXCell'], fontName='Helvetica-Bold',
        textColor=colors.white,
    ))
    return st


def _p(s, style):
    return Paragraph(escape(str(s)), style)


def _table(rows, widths, header=True):
    tab = Table(rows, colWidths=widths, repeatRows=1 if header else 0, hAlign='LEFT')
    cmds = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 9),
        ('RIGHTPADDING', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1 if header else 0), (-1, -1),
         (colors.white, LIGHT)),
        ('LINEBELOW', (0, 0), (-1, -1), .35, colors.HexColor('#D2DFE9')),
    ]
    if header:
        cmds += [('BACKGROUND', (0, 0), (-1, 0), NAVY)]
    tab.setStyle(TableStyle(cmds))
    return tab


def _grade(score):
    if score is None:
        return 'N/D'
    return f'{score:.1f}%'.replace('.', ',')


def _create_decorator(company, report_code, photo):
    def draw(canvas, doc):
        canvas.saveState()
        if doc.page == 1:
            canvas.setFillColor(NAVY)
            canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
            canvas.setFillColor(GOLD)
            canvas.rect(0, PAGE_H - 9, PAGE_W, 9, fill=1, stroke=0)
            canvas.setFont('Helvetica-Bold', 10)
            canvas.drawString(43, 761, 'GOVERNO EMPRESARIAL 360º  |  V5.9')
            canvas.setFillColor(colors.white)
            canvas.setFont('Helvetica-Bold', 30)
            canvas.drawString(43, 709, 'RAIO-X DO')
            canvas.drawString(43, 673, 'TRANSPORTADOR')
            canvas.setFont('Helvetica', 12)
            canvas.setFillColor(colors.HexColor('#D1E5F3'))
            canvas.drawString(43, 646, 'Diagnóstico executivo de gestão e transporte rodoviário')
            if photo:
                canvas.drawImage(photo, 42, 287, width=PAGE_W-84, height=315,
                                 preserveAspectRatio=False, mask='auto')
            else:
                canvas.setFillColor(colors.HexColor('#1A4160'))
                canvas.roundRect(42, 287, PAGE_W-84, 315, 12, stroke=0, fill=1)
            canvas.setFillColor(GOLD)
            canvas.setFont('Helvetica-Bold', 14)
            # Não deixar nome excessivamente longo ultrapassar a página.
            company_line = company[:58]
            while canvas.stringWidth(company_line, 'Helvetica-Bold', 14) > PAGE_W-92:
                company_line = company_line[:-2] + '…'
            canvas.drawString(43, 241, company_line)
            canvas.setFillColor(colors.white)
            canvas.setFont('Helvetica', 10)
            canvas.drawString(43, 217, 'Relatório gerencial individualizado | 35 perguntas')
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors.HexColor('#B8CADD'))
            canvas.drawString(43, 72, 'Autoavaliação declaratória. Não equivale a auditoria ou certificação.')
            canvas.drawString(43, 53, 'Documento: ' + report_code)
        else:
            canvas.setFillColor(NAVY)
            canvas.rect(0, PAGE_H-44, PAGE_W, 44, stroke=0, fill=1)
            canvas.setFillColor(colors.white)
            canvas.setFont('Helvetica-Bold', 9)
            canvas.drawString(42, PAGE_H-28, 'RAIO-X DO TRANSPORTADOR  |  V5.9')
            canvas.setStrokeColor(colors.HexColor('#DCE4EA'))
            canvas.line(42, 41, PAGE_W-42, 41)
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(MUTED)
            # Nome individualizado em todas as páginas.
            label = company[:62]
            canvas.drawString(42, 27, 'Transportadora: ' + label)
            canvas.drawRightString(PAGE_W-42, 27, 'Pág. ' + str(doc.page))
        canvas.restoreState()
    return draw


def make_v59_full_report(validated: dict) -> bytes:
    """Gera PDF com pontuação, prioridades e todas as respostas originais.

    validated: valor retornado por validate_submission (já validado na rota).
    """
    if not isinstance(validated, dict):
        raise ValueError('Diagnóstico não validado.')
    company = validated['company']['name']
    responses = validated['responses']
    result = validated['result']
    if not isinstance(company, str) or not 2 <= len(company) <= 120:
        raise ValueError('Transportadora inválida.')
    if not isinstance(responses, list) or len(responses) != 35:
        raise ValueError('35 respostas obrigatórias.')
    from v59_scoring import evaluate
    if result != evaluate(responses):
        raise ValueError('Pontuação inconsistente com respostas.')
    data = json.loads(CATALOG.read_text(encoding='utf-8'))
    questions = data['questions']
    if len(questions) != 35 or any(len(q['options']) != 5 for q in questions):
        raise RuntimeError('Catálogo de perguntas incompleto.')

    styles = _styles()
    raw = BytesIO()
    doc = SimpleDocTemplate(raw, pagesize=A4,
                            rightMargin=43, leftMargin=43,
                            topMargin=64, bottomMargin=58,
                            title=f'Raio-X do Transportador V5.9 - {company}',
                            author='Raio-X do Transportador')
    story = [Spacer(1, 690), PageBreak()]
    story += [
        _p('Resumo executivo do diagnóstico', styles['RXMain']),
        _p(f'Transportadora: {company}', styles['RXBody']),
        _p('Índice geral: ' + _grade(result['overall_score']) +
           f'  |  Respostas válidas: {result["valid_responses"]}/35', styles['RXSection']),
        _p('A pontuação utiliza respostas de 0 a 4. A opção “Não sei informar” não pontua. '
           'Para exibir uma dimensão, exige-se pelo menos 80% das respostas válidas '
           'naquela dimensão; a nota geral só aparece quando todas atingem esse mínimo.',
           styles['RXBody']),
        Spacer(1, 10),
    ]
    table_rows = [[_p('DIMENSÃO', styles['RXCellHeader']),
                   _p('RESPOSTAS', styles['RXCellHeader']),
                   _p('NOTA', styles['RXCellHeader'])]]
    for d in result['dimensions']:
        table_rows.append([_p(d['name'], styles['RXCell']),
                           _p(f'{d["valid"]}/{d["total"]}', styles['RXCell']),
                           _p(_grade(d['score']), styles['RXCell'])])
    story.append(_table(table_rows, [285, 115, 106]))
    story.append(Spacer(1, 22))
    story.append(_p('Leitura gerencial', styles['RXSection']))
    story.append(_p('As notas refletem exclusivamente as situações declaradas. '
                    'Ausência de resposta não significa ausência de controle. '
                    'Valide documentos, indicadores, registros operacionais e práticas antes de decidir investimentos.',
                    styles['RXBody']))
    story.append(Spacer(1, 10))
    story.append(_p('Plano de ação priorizado', styles['RXSection']))
    candidates = [(int(v), q) for v, q in zip(responses, questions)
                  if type(v) is int and 0 <= v <= 2]
    candidates.sort(key=lambda item:(item[0], item[1]['order']))
    if not candidates:
        story.append(_p('Não há respostas de 0 a 2 para priorização automática. '
                        'Ainda assim, valide evidências e estabeleça metas de melhoria.', styles['RXBody']))
    else:
        table_rows = [[_p('ORDEM',styles['RXCellHeader']),
                       _p('LACUNA DECLARADA', styles['RXCellHeader']),
                       _p('AÇÃO INICIAL', styles['RXCellHeader'])]]
        for i, (value, q) in enumerate(candidates[:10],1):
            table_rows.append([_p(str(i),styles['RXCell']),
                               _p(f'{q["dimension"]} (nota {value}) — {q["question"]}',styles['RXCell']),
                               _p(q['action'],styles['RXCell'])])
        story.append(_table(table_rows, [46, 218, 242]))
    story.append(Spacer(1, 20))
    story.append(_p('Detalhamento: as 35 respostas', styles['RXSection']))
    story.append(_p('A seguir estão os enunciados originais e as alternativas selecionadas, '
                    'agrupados nas seis dimensões do diagnóstico.', styles['RXBody']))

    for dim in result['dimensions']:
        story.append(PageBreak())
        story.append(_p(dim['name'], styles['RXMain']))
        story.append(_p('Pontuação: ' + _grade(dim['score']) +
                        f'  |  Respostas válidas: {dim["valid"]}/{dim["total"]}',
                        styles['RXBody']))
        table_rows = [[_p('QUESTÃO', styles['RXCellHeader']),
                       _p('SITUAÇÃO DECLARADA', styles['RXCellHeader']),
                       _p('NOTA', styles['RXCellHeader'])]]
        relevant = [(q, v) for q, v in zip(questions,responses) if q['dimension']==dim['name']]
        for q, v in relevant:
            answer = q['options'][v] if type(v) is int and 0 <= v <= 4 else 'Não sei informar'
            grade = str(v)+'/4' if type(v) is int and 0 <= v <= 4 else 'N/D'
            table_rows.append([_p(f'{q["order"]}. {q["question"]}',styles['RXCell']),
                               _p(answer,styles['RXCell']),_p(grade,styles['RXCell'])])
        story.append(_table(table_rows,[260,199,47]))
        story.append(Spacer(1,13))
        story.append(_p('Recomendações para os controles que exigem atenção',styles['RXSection']))
        low = [(q,v) for q,v in relevant if type(v) is int and v<=2]
        if not low:
            story.append(_p('Nenhuma resposta de 0 a 2 nesta dimensão. '
                            'Verifique a aderência às práticas declaradas e documente evidências.',styles['RXBody']))
        for q, v in low:
            story.append(_p(f'{q["order"]}. {q["action"]}', styles['RXBody']))
    story += [
        Spacer(1, 20),
        _p('Nota metodológica',styles['RXSection']),
        _p('Este documento é uma autoavaliação executiva. Não estabelece conformidade legal, '
           'não atesta certificação ISO/OEA e não substitui auditoria, contabilidade ou consultoria especializada.',
           styles['RXBody']),
    ]
    decorator = _create_decorator(company, 'G360-59', _cover_photo())
    doc.build(story, onFirstPage=decorator, onLaterPages=decorator)
    pdf = raw.getvalue()
    if not pdf.startswith(b'%PDF-'):
        raise RuntimeError('Relatório PDF não gerado.')
    return pdf