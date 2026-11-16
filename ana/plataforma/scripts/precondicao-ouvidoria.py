#!/usr/bin/env python3
"""Trava da ouvidoria na plataforma: `customer_choice` na ferramenta 11 (issue #53).

Liga no agente 1 da fazer.ai agents a pré-condição `customer_choice` (versão
1.54) na `registrar_ouvidoria`: antes de cada chamada, um juiz no modelo do
próprio agente lê a conversa e só deixa o registro rodar se o paciente
confirmou o que vai ser gravado.
"""

from __future__ import annotations

import copy

FERRAMENTA = "registrar_ouvidoria"
REGRA = {"kind": "customer_choice"}


def corpo_ligar(agente: dict) -> dict:
    """O corpo do PATCH /api/v1/agents/:id que liga a trava.

    O PATCH substitui o saco de settings inteiro, então o corpo leva todos os
    blocos lidos (e as regras de outras ferramentas), e `expectedUpdatedAt` faz
    a plataforma recusar (409) se outra sessão gravou o agente depois da leitura.
    """
    settings = copy.deepcopy(agente["settings"])
    settings["toolPreconditions"] = {**settings.get("toolPreconditions", {}), FERRAMENTA: dict(REGRA)}
    return {"settings": settings, "expectedUpdatedAt": agente["updatedAt"]}
