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


def test_cadastro_do_paciente_vai_em_kv_com_as_mesmas_chaves_e_sem_extra() -> None:
    assert body_kv.body_novo(_antes("7")) == {
        "mode": "kv",
        "rows": [
            {"key": "cpf", "value": "{{cpf}}"},
            {"key": "nome", "value": "{{nome}}"},
            {"key": "telefone", "value": "{{telefone}}"},
            {"key": "dataNascimento", "value": "{{dataNascimento}}"},
        ],
    }


def test_ferramenta_mexida_por_outra_sessao_desde_o_export_nao_e_regravada() -> None:
    antes = _antes("11")
    mexida = {**antes, "updatedAt": "2026-11-15T21:00:00.000Z"}
    with pytest.raises(body_kv.MexidaDesdeOExport):
        body_kv.conferir_intocada(antes, mexida)
    body_kv.conferir_intocada(antes, dict(antes))
