"""Notas da Ana no Chatwoot (issue #57): ferramentas e erros de cada turno.

O script `ana/plataforma/scripts/notas-na-conversa.py` liga no agente 1 as notas
privadas da fazer.ai agents (1.55) e a guarda do detalhe do turno (1.59). Estes
testes cobrem o miolo puro: o corpo da escrita, a trava contra mudança de outra
sessão desde o export e a varredura de dado de paciente na nota. A plataforma e
o Chatwoot de verdade não entram no teste.
"""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "ana" / "plataforma" / "scripts" / "notas-na-conversa.py"

_spec = importlib.util.spec_from_file_location("notas_na_conversa", SCRIPT)
nc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nc)


def agente(**settings):
    base = {
        "split": {"enabled": False, "maxChars": 320},
        "handoff": {"mode": "route", "instructions": "Escale quando..."},
        "attributeContext": {"contact": ["cpf", "nome_completo"]},
    }
    base.update(settings)
    return {"id": "1", "updatedAt": "2026-11-15T23:33:59.488Z", "settings": base}


def test_notas_de_ferramentas_e_erros_ficam_ligadas_como_nota_privada():
    corpo = nc.corpo_da_escrita(agente(), dias=14)
    assert corpo["settings"]["conversationNotes"] == {"toolsUsed": "note", "errors": "note"}
