"""Prompt v7 da Ana: a v7.0 comprimida, sem perder função e sem travessão (issue #25).

Dois alvos:
- `ana/plataforma/scripts/publicar-prompt.py`, que publica o prompt no agente 1 só se
  ninguém mudou o prompt vivo desde o export (o miolo puro; a plataforma não entra no teste).
- `ana/prompt/prompt-compilado.md`, o prompt que vai ao ar, conferido contra o export do
  prompt que estava no ar antes (`ana/plataforma/export-prompt-v70.md`).
"""

from __future__ import annotations

import hashlib
import importlib.util
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "ana" / "plataforma" / "scripts" / "publicar-prompt.py"

_spec = importlib.util.spec_from_file_location("publicar_prompt", SCRIPT)
pp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pp)


def agente(prompt="prompt vivo", atualizado="2026-11-16T06:28:48.248Z"):
    return {
        "id": "1",
        "updatedAt": atualizado,
        "systemPrompt": prompt,
        "settings": {"handoff": {"mode": "route"}, "toolPreconditions": {}},
    }


def sha(texto):
    return hashlib.sha256(texto.encode()).hexdigest()


# ------------------------------------------------------------ publicação


def test_publicar_manda_so_o_prompt_e_vale_sobre_o_estado_lido():
    corpo = pp.corpo_publicar(agente(), "prompt novo")
    # sem settings no corpo: o PATCH substitui o saco de settings inteiro quando ele vem
    assert corpo == {"systemPrompt": "prompt novo", "expectedUpdatedAt": "2026-11-16T06:28:48.248Z"}


def test_prompt_mudado_por_outra_sessao_desde_o_export_para_a_publicacao():
    assert pp.prompt_mudou(sha("prompt vivo"), agente("prompt vivo")) is False
    assert pp.prompt_mudou(sha("prompt vivo"), agente("prompt vivo com uma regra a mais")) is True


def test_prompt_com_travessao_fora_das_colunas_nao_sobe():
    limpo = "Mover para `EM ATENDIMENTO — ANA` e depois `ENCERRADO — RESOLVIDO`.\nSem traço."
    assert pp.travessoes_fora_das_colunas(limpo) == []
    sujo = "Cenário A — fora do horário\nCenário B – fim de semana"
    assert pp.travessoes_fora_das_colunas(sujo) == [
        "Cenário A — fora do horário",
        "Cenário B – fim de semana",
    ]
