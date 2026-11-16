#!/usr/bin/env python3
"""Regrava o body das ferramentas 7 e 11 da Ana em `mode: kv` (issue #52).

Body em mapa simples, sem `mode`, é o formato legado da plataforma: ela ignora
o template e monta o JSON com os nomes do `input_schema`. Em `kv` o template
vale, e a ferramenta 11 passa a mandar o número da conversa (`conversa_id`).

    python3 ana/plataforma/scripts/body_kv.py            # mostra o body novo
    python3 ana/plataforma/scripts/body_kv.py --aplicar  # grava na plataforma

Antes de gravar, confere que ninguém mexeu na ferramenta desde o export
(`ana/plataforma/export-ferramentas-7-11-pre-kv.json`), que é também o caminho
de volta: PATCH com o body de lá.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
EXPORT = RAIZ / "ana" / "plataforma" / "export-ferramentas-7-11-pre-kv.json"
PLATAFORMA = "https://agents.hospitalsaomatheus.cloud/api/v1/tools"

# Linhas que cada ferramenta ganha além das que já tinha no body legado.
EXTRAS = {
    "11": {"conversa_id": "{{conversation_id}}"},
}


class MexidaDesdeOExport(Exception):
    """A ferramenta mudou na plataforma depois do export: regravar apagaria a mudança."""


def body_novo(ferramenta: dict) -> dict:
    """O body em `kv` com as mesmas chaves do legado, mais os extras da ferramenta."""
    linhas = {**ferramenta["body"], **EXTRAS.get(ferramenta["id"], {})}
    return {"mode": "kv", "rows": [{"key": k, "value": v} for k, v in linhas.items()]}


def conferir_intocada(antes: dict, atual: dict) -> None:
    if atual["updatedAt"] != antes["updatedAt"] or atual["body"] != antes["body"]:
        raise MexidaDesdeOExport(
            f"ferramenta {antes['id']} mudou desde o export "
            f"({antes['updatedAt']} -> {atual['updatedAt']}): exporte de novo antes de regravar"
        )


def _token() -> str:
    for linha in (RAIZ / ".env").read_text(encoding="utf-8").splitlines():
        chave, _, valor = linha.partition("=")
        if chave.strip() == "AGENTS_API_TOKEN":
            return valor.strip().strip("\"'")
    sys.exit("ERRO: AGENTS_API_TOKEN ausente no .env")


def _chamar(metodo: str, tool_id: str, corpo: dict | None = None) -> dict:
    pedido = urllib.request.Request(
        f"{PLATAFORMA}/{tool_id}",
        method=metodo,
        data=json.dumps(corpo).encode() if corpo is not None else None,
        headers={"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(pedido, timeout=30) as resposta:
        return json.load(resposta)["tool"]


def main(argv: list[str]) -> int:
    aplicar = "--aplicar" in argv
    for tool_id, antes in json.loads(EXPORT.read_text(encoding="utf-8"))["ferramentas"].items():
        novo = body_novo(antes)
        print(f"ferramenta {tool_id} ({antes['name']}): {json.dumps(novo, ensure_ascii=False)}")
        if not aplicar:
            continue
        conferir_intocada(antes, _chamar("GET", tool_id))
        _chamar("PATCH", tool_id, {"body": novo})
        depois = _chamar("GET", tool_id)
        if depois["body"] != novo:
            sys.exit(f"ERRO: ferramenta {tool_id} voltou com outro body: {depois['body']}")
        print(f"  gravada em {depois['updatedAt']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
