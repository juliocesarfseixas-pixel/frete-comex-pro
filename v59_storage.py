"""Persistência opcional V5.9 — nunca chamada por endpoints de prévia.

Use somente após a migração e a configuração de DATABASE_URL em ambiente
privado. Não contém chaves de Supabase e não executa DDL.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone


def save_v59(connection, submission: dict) -> str:
    """Grava cadastro e resultado em transação gerenciada pelo chamador.

    Recebe objeto previamente validado por validate_submission().
    Usa parâmetros SQL; não interpolar valores de usuários na query.
    """
    from v59_api import validate_submission

    validated = validate_submission(submission)
    identifier = str(uuid.uuid4())
    company = validated["company"]
    with connection.cursor() as cursor:
        cursor.execute(
            """INSERT INTO raiox_v59.diagnostics (
                id, created_at, company_name, email, responsible,
                responses, result, email_status
            ) VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s)
            """,
            (
                identifier,
                datetime.now(timezone.utc),
                company["name"],
                company["email"],
                company["responsible"],
                json.dumps(validated["responses"], ensure_ascii=False),
                json.dumps(validated["result"], ensure_ascii=False),
                "not_requested",
            ),
        )
    return identifier
