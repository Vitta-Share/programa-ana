"""Trava da ouvidoria na plataforma (issue #53).

O script `ana/plataforma/scripts/precondicao-ouvidoria.py` liga no agente 1 a
pré-condição `customer_choice` (fazer.ai agents 1.54) na ferramenta 11,
`registrar_ouvidoria`: a plataforma só roda o registro depois que um juiz
confere, na conversa, que o paciente confirmou o que vai ser gravado. Os testes
cobrem o miolo puro (o corpo da escrita, a trava contra mudança de outra sessão
e o desligar); a plataforma de verdade não entra no teste.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "ana" / "plataforma" / "scripts" / "precondicao-ouvidoria.py"

_spec = importlib.util.spec_from_file_location("precondicao_ouvidoria", SCRIPT)
po = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(po)


def agente(**settings):
    base = {
        "handoff": {"mode": "route", "instructions": "Escale quando..."},
        "conversationNotes": {"toolsUsed": "note", "errors": "note"},
    }
    base.update(settings)
    return {"id": "1", "updatedAt": "2026-11-16T04:19:43.630Z", "settings": base}


def test_registro_da_ouvidoria_so_roda_com_a_confirmacao_do_paciente():
    corpo = po.corpo_ligar(agente())
    assert corpo["settings"]["toolPreconditions"] == {
        "registrar_ouvidoria": {"kind": "customer_choice"},
    }
