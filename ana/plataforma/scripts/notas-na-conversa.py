#!/usr/bin/env python3
"""Notas da Ana no Chatwoot: ferramentas e erros de cada turno (issue #57).

Liga no agente 1 da fazer.ai agents as notas privadas de ferramentas usadas e de
erros contornados (`settings.conversationNotes`, versão 1.55) e a guarda do
detalhe completo do turno por N dias (`settings.observability.
fullDetailRetentionDays`, versão 1.59).
"""

from __future__ import annotations

import copy

NOTAS = {"toolsUsed": "note", "errors": "note"}
# A plataforma aceita de 1 a 90 dias, mas a linha de log em que o detalhe se
# pendura some com FLOWLOG_RETENTION_DAYS (30 por padrão): mais que isso é promessa vazia.
DIAS_MAX = 30


def corpo_da_escrita(agente: dict, dias: int) -> dict:
    """O corpo do PATCH /api/v1/agents/:id que liga as notas.

    O PATCH substitui o saco de settings inteiro, então o corpo leva todos os
    blocos lidos, e `expectedUpdatedAt` faz a plataforma recusar (409) se outra
    sessão gravou o agente depois da leitura.
    """
    if not 1 <= dias <= DIAS_MAX:
        raise ValueError(f"dias de guarda fora de 1 a {DIAS_MAX}: {dias}")
    settings = copy.deepcopy(agente["settings"])
    settings["conversationNotes"] = dict(NOTAS)
    settings["observability"] = {**settings.get("observability", {}), "fullDetailRetentionDays": dias}
    return {"settings": settings, "expectedUpdatedAt": agente["updatedAt"]}
