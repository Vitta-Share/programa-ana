"""Testes da regravação do body das ferramentas 7 e 11 em `mode: kv` (issue #52).

Body em mapa simples, sem `mode`, cai no modo legado da plataforma: ignora o
template e monta o JSON com os nomes do `input_schema`. Por isso o número da
conversa nunca entrava no protocolo da ouvidoria. Os testes leem o export do
estado anterior, versionado em `ana/plataforma/`, e conferem o body novo
contra o esperado escrito à mão.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SCRIPT = RAIZ / "ana" / "plataforma" / "scripts" / "body_kv.py"
EXPORT = RAIZ / "ana" / "plataforma" / "export-ferramentas-7-11-pre-kv.json"

_spec = importlib.util.spec_from_file_location("body_kv", SCRIPT)
body_kv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(body_kv)


def _antes(tool_id: str) -> dict:
    return json.loads(EXPORT.read_text(encoding="utf-8"))["ferramentas"][tool_id]


def test_ouvidoria_grava_o_numero_da_conversa_no_protocolo() -> None:
    assert body_kv.body_novo(_antes("11")) == {
        "mode": "kv",
        "rows": [
            {"key": "setor", "value": "{{setor}}"},
            {"key": "resumo", "value": "{{resumo}}"},
            {"key": "categoria", "value": "{{categoria}}"},
            {"key": "conversa_id", "value": "{{conversation_id}}"},
        ],
    }
