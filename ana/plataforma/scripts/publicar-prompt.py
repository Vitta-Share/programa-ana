#!/usr/bin/env python3
"""Publica o prompt da Ana no agente 1 com trava de export (issue #25).

A fonte do prompt é `ana/prompt/` (ADR-0012); `compilar.py` gera `prompt-compilado.md`.
Este script guarda o prompt vivo antes de mudar e só publica se ninguém mexeu nele
desde o export, que é o que o `prompt_set` do console não confere.

    python3 ana/plataforma/scripts/publicar-prompt.py exportar    # guarda o prompt vivo e o hash
    python3 ana/plataforma/scripts/publicar-prompt.py conferir    # o vivo ainda é o do export?
    python3 ana/plataforma/scripts/publicar-prompt.py publicar    # sobe ana/prompt/prompt-compilado.md
    python3 ana/plataforma/scripts/publicar-prompt.py publicar --sobre <sha>   # revisão por cima da que subiu
    python3 ana/plataforma/scripts/publicar-prompt.py voltar      # devolve o prompt do export
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

# Os nomes das colunas do kanban têm travessão na plataforma e ficam como estão:
# o `kanban_move_card` move pelo nome exato.
COLUNAS_COM_TRAVESSAO = (
    "EM ATENDIMENTO \u2014 ANA",
    "ENCERRADO \u2014 RESOLVIDO",
    "ENCERRADO \u2014 DESISTÊNCIA",
)
TRACOS = ("\u2014", "\u2013")


def corpo_publicar(agente: dict, prompt: str) -> dict:
    """O corpo do PATCH /api/v1/agents/:id que troca só o prompt.

    Sem `settings` no corpo (o PATCH substitui o saco de settings inteiro quando ele vem),
    e com `expectedUpdatedAt` para a plataforma recusar (409) se outra sessão gravou o
    agente depois da leitura.
    """
    return {"systemPrompt": prompt, "expectedUpdatedAt": agente["updatedAt"]}


def _sha(texto: str) -> str:
    return hashlib.sha256(texto.encode()).hexdigest()


def prompt_mudou(sha_esperado: str, agente: dict) -> bool:
    """O prompt vivo é outro que não o esperado? Então outra sessão publicou no meio.

    `sha_esperado` pode ser o hash inteiro ou o começo dele (os 12 do log).
    """
    return not _sha(agente.get("systemPrompt", "")).startswith(sha_esperado)


def travessoes_fora_das_colunas(prompt: str) -> list[str]:
    """As linhas com travessão ou meia-risca, tirando os nomes das colunas do kanban."""
    linhas = []
    for linha in prompt.splitlines():
        resto = linha
        for coluna in COLUNAS_COM_TRAVESSAO:
            resto = resto.replace(coluna, "")
        if any(t in resto for t in TRACOS):
            linhas.append(linha)
    return linhas


# ---------------------------------------------------------------- casca (rede)

RAIZ = Path(__file__).resolve().parents[3]
EXPORT_PROMPT = RAIZ / "ana" / "plataforma" / "export-prompt-v70.md"
EXPORT_AGENTE = RAIZ / "ana" / "plataforma" / "export-ana-pre-prompt-v71.json"
COMPILADO = RAIZ / "ana" / "prompt" / "prompt-compilado.md"
AGENTE = "https://agents.hospitalsaomatheus.cloud/api/v1/agents/1"


def _token() -> str:
    arquivo = next(p / ".env" for p in (RAIZ, *RAIZ.parents) if (p / ".env").is_file())
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        chave, _, valor = linha.partition("=")
        if chave.strip() == "AGENTS_API_TOKEN":
            return valor.strip().strip("\"'")
    sys.exit("ERRO: AGENTS_API_TOKEN ausente no .env")


def _pedir(metodo: str = "GET", corpo: dict | None = None) -> dict:
    pedido = urllib.request.Request(
        AGENTE,
        method=metodo,
        data=json.dumps(corpo).encode() if corpo is not None else None,
        headers={"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(pedido, timeout=30) as resposta:
        return json.load(resposta)["agent"]


def _subir(prompt: str, sha_esperado_no_ar: str) -> int:
    atual = _pedir()
    if prompt_mudou(sha_esperado_no_ar, atual):
        print("PARADO: o prompt vivo não é o esperado (outra sessão publicou). Refaça o export e confira.")
        return 1
    _pedir("PATCH", corpo_publicar(atual, prompt))
    depois = _pedir()
    ok = _sha(depois["systemPrompt"]) == _sha(prompt)
    print(f"no ar: {len(depois['systemPrompt'])} chars, sha {_sha(depois['systemPrompt'])[:12]}")
    if depois["settings"] != atual["settings"]:
        print("ATENÇÃO: as settings mudaram junto com o prompt.")
        ok = False
    return 0 if ok else 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("cmd", choices=["exportar", "conferir", "publicar", "voltar"])
    p.add_argument("--sobre", help="publicar por cima deste prompt vivo (sha ou começo dele), e não do export")
    args = p.parse_args()
    cmd = args.cmd
    if cmd == "exportar":
        a = _pedir()
        prompt = a.pop("systemPrompt", "")
        EXPORT_PROMPT.write_text(prompt, encoding="utf-8")
        a["systemPromptSha256"] = _sha(prompt)
        a["systemPromptChars"] = len(prompt)
        EXPORT_AGENTE.write_text(json.dumps(a, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"export: {len(prompt)} chars, sha {_sha(prompt)[:12]}")
        return 0
    sha_export = json.loads(EXPORT_AGENTE.read_text(encoding="utf-8"))["systemPromptSha256"]
    if cmd == "conferir":
        mudou = prompt_mudou(sha_export, _pedir())
        print("o prompt vivo MUDOU desde o export" if mudou else "o prompt vivo é o do export")
        return 1 if mudou else 0
    if cmd == "publicar":
        prompt = COMPILADO.read_text(encoding="utf-8")
        sujas = travessoes_fora_das_colunas(prompt)
        if sujas:
            print("PARADO: travessão fora dos nomes das colunas:\n" + "\n".join(sujas))
            return 1
        return _subir(prompt, args.sobre or sha_export)
    return _subir(EXPORT_PROMPT.read_text(encoding="utf-8"), _sha(COMPILADO.read_text(encoding="utf-8")))


if __name__ == "__main__":
    sys.exit(main())
