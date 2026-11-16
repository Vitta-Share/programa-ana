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


def corpo_da_escrita(agente: dict, dias: int) -> dict:
    """O corpo do PATCH /api/v1/agents/:id que liga as notas."""
    settings = copy.deepcopy(agente["settings"])
    settings["conversationNotes"] = dict(NOTAS)
    return {"settings": settings}
