"""Motor de pontuação V5.9, isolado do backend v1.4.

Não altera rotas, banco ou a versão em produção.
Cada resposta: inteiro 0..4 ou null para 'Não sei informar'.
O relatório deve distinguir nota indisponível de nota zero.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEPARTMENTS = (
    "Tesouro e Pessoas",
    "Estratégia e Governança",
    "Frota e Patrimônio",
    "Transportes e Operações",
    "Comércio e Expansão",
)
GOVERNANCE_COUNT = 10
QUESTIONS_PER_DEPARTMENT = 5
TOTAL_QUESTIONS = GOVERNANCE_COUNT + len(DEPARTMENTS) * QUESTIONS_PER_DEPARTMENT
MIN_VALID_FRACTION = 0.80


@dataclass(frozen=True)
class Dimension:
    name: str
    valid: int
    total: int
    score: float | None
    sufficient: bool


def _dimension(name: str, values: list[int | None]) -> Dimension:
    known = [v for v in values if v is not None]
    sufficient = len(known) / len(values) >= MIN_VALID_FRACTION
    score = round(sum(known) / (len(known) * 4) * 100, 1) if sufficient else None
    return Dimension(name, len(known), len(values), score, sufficient)


def evaluate(responses: Any) -> dict:
    """Pontua 35 respostas na ordem: governança (10), cinco departamentos (5 cada).

    As notas departamentais são independentes. Nota global só é calculada
    quando todas as seis dimensões alcançam o mínimo de respostas válidas.
    A nota global é a média de todas as respostas válidas (sem pesos inventados).
    """
    if not isinstance(responses, list) or len(responses) != TOTAL_QUESTIONS:
        raise ValueError("São necessárias exatamente 35 respostas.")
    if any(v is not None and (type(v) is not int or not 0 <= v <= 4) for v in responses):
        raise ValueError("Cada resposta deve ser um inteiro entre 0 e 4 ou null.")

    dimensions = [_dimension("Governança corporativa", responses[:GOVERNANCE_COUNT])]
    for index, name in enumerate(DEPARTMENTS):
        start = GOVERNANCE_COUNT + index * QUESTIONS_PER_DEPARTMENT
        dimensions.append(_dimension(name, responses[start:start + QUESTIONS_PER_DEPARTMENT]))

    complete = all(d.sufficient for d in dimensions)
    known = [v for v in responses if v is not None]
    overall = round(sum(known) / (len(known) * 4) * 100, 1) if complete else None
    return {
        "methodology": "governo-360-v5.9",
        "valid_responses": len(known),
        "total_responses": TOTAL_QUESTIONS,
        "sufficient": complete,
        "overall_score": overall,
        "governance_score": dimensions[0].score,
        "departments": [
            {"name": d.name, "valid": d.valid, "total": d.total,
             "score": d.score, "sufficient": d.sufficient}
            for d in dimensions[1:]
        ],
        "dimensions": [
            {"name": d.name, "valid": d.valid, "total": d.total,
             "score": d.score, "sufficient": d.sufficient}
            for d in dimensions
        ],
    }
