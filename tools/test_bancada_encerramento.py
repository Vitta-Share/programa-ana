"""O runner da bancada prova o encerramento (issue #26).

Desde 13/out/2026 a inbox de API "Ana E2E" está no funil do Chatwoot (board 2):
cada conversa de teste ganha card. O runner lê a raia do card (o detalhe da
conversa traz só o id do card; a raia vem de GET /kanban/tasks/<id>), confere
`resolved` quando o cenário pede `confere.resolvida` e, no fim, resolve a
conversa que ficou aberta. A leitura pelo trace vira plano B, com aviso, só
quando a conversa vem sem card. O Chatwoot e a plataforma de verdade não entram
no teste: o Canal e o Trace são falsos, o `rodar_cenario` é o de verdade.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "ana" / "bancada" / "e2e.py"

_spec = importlib.util.spec_from_file_location("bancada_e2e", SCRIPT)
e2e = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e2e)

# o board 2 como o Chatwoot devolve em GET /kanban/tasks/<id> (16/nov/2026)
PASSOS = [{"id": 2, "name": "Novo Contato"}, {"id": 3, "name": "Em Atendimento — Ana"},
          {"id": 9, "name": "Agendado"}, {"id": 10, "name": "Encerrado — Resolvido"}]


def chatwoot(conversa_status="pending", card=137, passo=10):
    """As respostas da API admin do Chatwoot para a conversa 691 e o card dela."""
    respostas = {
        "/conversations/691": (200, {"id": 691, "status": conversa_status,
                                     "kanban_task": {"id": card} if card else None}),
    }
    if card:
        respostas[f"/kanban/tasks/{card}"] = (200, {"id": card, "board_step_id": passo,
                                                    "board": {"id": 2, "steps": PASSOS}})
    return respostas


def canal_de_api(respostas):
    """Um Canal de verdade com a rede trocada por um dicionário de respostas."""
    canal = e2e.Canal.__new__(e2e.Canal)
    canal.chamadas = []

    def admin(caminho, metodo="GET", corpo=None):
        canal.chamadas.append((metodo, caminho, corpo))
        return respostas.get(caminho, (404, "nao achei"))

    canal._admin = admin
    return canal


def test_a_raia_vem_do_card_do_kanban_da_conversa():
    canal = canal_de_api(chatwoot(conversa_status="resolved", card=137, passo=10))
    raia, status, card = canal.estado(691)
    assert raia == "Encerrado — Resolvido"
    assert status == "resolved"
    assert card == 137
