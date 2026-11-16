#!/usr/bin/env python3
"""Checagem de fatos da Ana em modo só registrar (issue #54).

Liga no agente 1 da fazer.ai agents a checagem factual (`guardrails.factualGrounding`,
versões 1.57 a 1.59) com a ação `observe` ("Só registrar" no console): um modelo
revisor compara cada resposta com o que as ferramentas trouxeram e anota no log o que
não bate, sem bloquear nem reescrever nada. Depois mede, nos logs, o que ela marcou
nas conversas de uma bateria da bancada.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# As fontes que a issue pede: preço, exame, agenda e protocolo, mais a base de conhecimento.
FONTES = [
    "consultar_precos_consultas", "consultar_cirurgias_estimativas",   # preço
    "consultar_exames",                                                # exame
    "consultar_especialidades_agenda", "consultar_prestadores_agenda",  # agenda
    "consultar_convenios_agenda", "consultar_planos_convenio", "consultar_horarios_livres",
    "registrar_ouvidoria", "consultar_protocolo_ouvidoria",            # protocolo
    "search_knowledge",                                                # base de conhecimento
]
# "Base Hospital São Matheus" (5 documentos, uns 4 mil caracteres): lida inteira em toda
# revisão, para regra da casa (endereço, horário) não sair como afirmação sem fonte.
BASE_REFERENCIA = "1"


def corpo_da_escrita(agente: dict) -> dict:
    """O corpo do PATCH /api/v1/agents/:id que liga a checagem em Só registrar.

    O PATCH substitui o saco de settings inteiro, então o corpo leva todos os blocos
    lidos, e `expectedUpdatedAt` faz a plataforma recusar (409) se outra sessão gravou
    o agente depois da leitura.
    """
    settings = copy.deepcopy(agente["settings"])
    gr = settings.setdefault("guardrails", {})
    gr["enabled"] = True  # chave geral: a checagem não roda sem ela
    # a moderação de entrada e saída vem salva ligada e trocaria a resposta por template
    gr["input"] = {**gr.get("input", {}), "enabled": False}
    gr["output"] = {**gr.get("output", {}), "enabled": False}
    mc = agente["modelConfig"]
    gr["factualGrounding"] = {
        "enabled": True,
        "action": "observe",
        "sourceTools": list(FONTES),
        "referenceKnowledgeBaseIds": [BASE_REFERENCIA],
        # o revisor roda no modelo e na chave da Ana: os guardrails não têm chave própria
        "provider": mc["provider"],
        "model": mc["model"],
        "credentialRef": mc["credentialRef"],
    }
    return {"settings": settings, "expectedUpdatedAt": agente["updatedAt"]}


def mudou_desde_o_export(export: dict, atual: dict) -> list[str]:
    """Blocos de settings que outra sessão mudou desde o export, em ordem."""
    antes, agora = export["settings"], atual["settings"]
    return sorted(k for k in set(antes) | set(agora) if antes.get(k) != agora.get(k))
