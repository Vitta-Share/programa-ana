"""A rodada diz qual agente respondeu pela inbox de teste (issue #19).

A tentativa 3 da #19 roda a bateria num clone da Ana com `reasoningEffort: low`,
ligado à inbox "Ana E2E (API)" no lugar da Ana 1. Sem o agente, o modelo e o
esforço de raciocínio no log e nas janelas, um placar não diz de quem é (a v70
misturou dois modelos na mesma rodada sem que o log dissesse). A lista de agentes
é a de GET /api/v1/agents, que traz as inboxes de cada um.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "ana" / "bancada" / "e2e.py"

_spec = importlib.util.spec_from_file_location("bancada_e2e", SCRIPT)
e2e = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e2e)

# o formato de GET /api/v1/agents (plataforma 1.59.0, 16/nov/2026), só o que importa
ANA_1 = {"id": "1", "name": "Ana (Hospital São Matheus)",
         "modelConfig": {"model": "gpt-6-luna", "provider": "openai", "reasoningEffort": "none"},
         "inboxes": [{"id": "1", "name": "SaoMatheusBot"}]}
CLONE = {"id": "2", "name": "Ana clone reasoning low (#19)",
         "modelConfig": {"model": "gpt-6-luna", "provider": "openai", "reasoningEffort": "low"},
         "inboxes": [{"id": "2", "name": "Ana E2E (API)"}]}


def test_a_rodada_no_clone_diz_que_respondeu_o_clone_com_reasoning_low():
    agente = e2e.agente_da_inbox([ANA_1, CLONE], "Ana E2E (API)")
    assert agente == "agente 2 (Ana clone reasoning low (#19)), gpt-6-luna, reasoning low"


def test_inbox_sem_agente_ligado_aparece_como_sem_agente():
    assert e2e.agente_da_inbox([ANA_1], "Ana E2E (API)") == "sem agente ligado"
