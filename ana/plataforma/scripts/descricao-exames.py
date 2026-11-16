#!/usr/bin/env python3
"""Troca, na descrição da `consultar_exames` (ferramenta 2), a frase que empurra a escalada (issue #19).

A descrição fechava com "ofereça encaminhar à equipe [...] Perguntar se é convênio ou
particular não substitui esse encaminhamento": o encaminhamento como ação, no turno em
que só cabe a pergunta da oferta (Seção 6 do prompt). No C10-2 a Ana escalava ali.

    python3 ana/plataforma/scripts/descricao-exames.py exportar   # guarda a ferramenta antes
    python3 ana/plataforma/scripts/descricao-exames.py            # prévia: a descrição nova, sem gravar
    python3 ana/plataforma/scripts/descricao-exames.py --aplicar  # grava, se ninguém mexeu desde o export
    python3 ana/plataforma/scripts/descricao-exames.py voltar     # devolve a descrição do export
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

VELHA = (
    "ofereça encaminhar à equipe para confirmar. Perguntar se é convênio ou particular não "
    "substitui esse encaminhamento."
)
NOVA = (
    "pergunte, em texto, se quer que a equipe confirme (perguntar convênio ou particular não "
    "substitui); o `handoff_to_human` só vem depois do sim."
)
# a plataforma recusa (422) descrição acima de 2.000 caracteres: medido em 16/nov/2026
TETO_DESCRICAO = 2000


class MexidaDesdeOExport(Exception):
    """A ferramenta mudou na plataforma depois do export: regravar apagaria a mudança."""


def descricao_nova(ferramenta: dict) -> str:
    """A descrição com a frase da oferta trocada; o resto fica igual."""
    descricao = ferramenta["description"]
    if VELHA not in descricao:
        raise MexidaDesdeOExport("a frase da oferta não está na descrição: exporte de novo e confira")
    nova = descricao.replace(VELHA, NOVA, 1)
    if len(nova) > TETO_DESCRICAO:
        raise ValueError(f"descrição com {len(nova)} caracteres passa do teto de {TETO_DESCRICAO}")
    return nova


def conferir_intocada(antes: dict, atual: dict) -> None:
    if atual["updatedAt"] != antes["updatedAt"] or atual["description"] != antes["description"]:
        raise MexidaDesdeOExport(
            f"ferramenta {antes['id']} mudou desde o export "
            f"({antes['updatedAt']} -> {atual['updatedAt']}): exporte de novo antes de regravar"
        )


# ---------------------------------------------------------------- casca (rede)

RAIZ = Path(__file__).resolve().parents[3]
EXPORT = RAIZ / "ana" / "plataforma" / "export-ferramenta-2-pre-oferta.json"
FERRAMENTA = "https://agents.hospitalsaomatheus.cloud/api/v1/tools/2"


def _token() -> str:
    arquivo = next(p / ".env" for p in (RAIZ, *RAIZ.parents) if (p / ".env").is_file())
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        chave, _, valor = linha.partition("=")
        if chave.strip() == "AGENTS_API_TOKEN":
            return valor.strip().strip("\"'")
    sys.exit("ERRO: AGENTS_API_TOKEN ausente no .env")


def _chamar(metodo: str = "GET", corpo: dict | None = None) -> dict:
    pedido = urllib.request.Request(
        FERRAMENTA,
        method=metodo,
        data=json.dumps(corpo).encode() if corpo is not None else None,
        headers={"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(pedido, timeout=30) as resposta:
        return json.load(resposta)["tool"]


def _gravar(descricao: str) -> int:
    _chamar("PATCH", {"description": descricao})
    depois = _chamar()
    print(f"gravada em {depois['updatedAt']}")
    return 0 if depois["description"] == descricao else 1


def main(argv: list[str]) -> int:
    if argv[:1] == ["exportar"]:
        EXPORT.write_text(json.dumps(_chamar(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"export gravado em {EXPORT.relative_to(RAIZ)}")
        return 0
    antes = json.loads(EXPORT.read_text(encoding="utf-8"))
    if argv[:1] == ["voltar"]:
        return _gravar(antes["description"])
    nova = descricao_nova(antes)
    print(nova)
    if "--aplicar" not in argv:
        return 0
    conferir_intocada(antes, _chamar())
    return _gravar(nova)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
