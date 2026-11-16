#!/usr/bin/env python3
"""Regrava o body das ferramentas 7 e 11 da Ana em `mode: kv` (issue #52).

Body em mapa simples, sem `mode`, é o formato legado da plataforma: ela ignora
o template e monta o JSON com os nomes do `input_schema`. Em `kv` o template
vale, e a ferramenta 11 passa a mandar o número da conversa (`conversa_id`).
"""

from __future__ import annotations

# Linhas que cada ferramenta ganha além das que já tinha no body legado.
EXTRAS = {
    "11": {"conversa_id": "{{conversation_id}}"},
}


def body_novo(ferramenta: dict) -> dict:
    """O body em `kv` com as mesmas chaves do legado, mais os extras da ferramenta."""
    linhas = {**ferramenta["body"], **EXTRAS.get(ferramenta["id"], {})}
    return {"mode": "kv", "rows": [{"key": k, "value": v} for k, v in linhas.items()]}
