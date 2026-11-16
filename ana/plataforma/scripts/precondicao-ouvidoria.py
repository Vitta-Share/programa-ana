#!/usr/bin/env python3
"""Trava da ouvidoria na plataforma: `customer_choice` na ferramenta 11 (issue #53).

Liga no agente 1 da fazer.ai agents a pré-condição `customer_choice` (versão
1.54) na `registrar_ouvidoria`: antes de cada chamada, um juiz no modelo do
próprio agente lê a conversa e só deixa o registro rodar se o paciente
confirmou o que vai ser gravado. Recusada, a chamada não acontece e o modelo
recebe a instrução de perguntar ao paciente.

    python3 ana/plataforma/scripts/precondicao-ouvidoria.py exportar   # guarda o estado antes
    python3 ana/plataforma/scripts/precondicao-ouvidoria.py ligar      # para se outra sessão mexeu
    python3 ana/plataforma/scripts/precondicao-ouvidoria.py desligar   # volta atrás
    python3 ana/plataforma/scripts/precondicao-ouvidoria.py ver        # regras vivas
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

FERRAMENTA = "registrar_ouvidoria"
REGRA = {"kind": "customer_choice"}


def corpo_ligar(agente: dict) -> dict:
    """O corpo do PATCH /api/v1/agents/:id que liga a trava.

    O PATCH substitui o saco de settings inteiro, então o corpo leva todos os
    blocos lidos (e as regras de outras ferramentas), e `expectedUpdatedAt` faz
    a plataforma recusar (409) se outra sessão gravou o agente depois da leitura.
    """
    settings = copy.deepcopy(agente["settings"])
    settings["toolPreconditions"] = {**settings.get("toolPreconditions", {}), FERRAMENTA: dict(REGRA)}
    return {"settings": settings, "expectedUpdatedAt": agente["updatedAt"]}


def corpo_desligar(agente: dict) -> dict:
    """O corpo do PATCH que tira só a trava da ouvidoria, com as mesmas garantias do ligar."""
    settings = copy.deepcopy(agente["settings"])
    settings["toolPreconditions"] = {
        k: v for k, v in settings.get("toolPreconditions", {}).items() if k != FERRAMENTA
    }
    return {"settings": settings, "expectedUpdatedAt": agente["updatedAt"]}


def mudou_desde_o_export(export: dict, atual: dict) -> list[str]:
    """Blocos de settings que outra sessão mudou desde o export, em ordem.

    Só as settings contam: o prompt publicado por outra sessão não é a mesma coisa.
    """
    antes, agora = export["settings"], atual["settings"]
    return sorted(k for k in set(antes) | set(agora) if antes.get(k) != agora.get(k))


# ---------------------------------------------------------------- casca (rede)

RAIZ = Path(__file__).resolve().parents[3]
EXPORT = RAIZ / "ana" / "plataforma" / "export-ana-pre-precondicao-ouvidoria.json"
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


def _sem_prompt(agente: dict) -> dict:
    """O agente sem o prompt (a fonte dele é ana/prompt/), com o hash para conferir."""
    a = dict(agente)
    prompt = a.pop("systemPrompt", "")
    a["systemPromptSha256"] = hashlib.sha256(prompt.encode()).hexdigest()
    a["systemPromptChars"] = len(prompt)
    return a


def _escrever(montar) -> int:
    atual = _pedir()
    mudou = mudou_desde_o_export(json.loads(EXPORT.read_text(encoding="utf-8")), atual)
    if mudou:
        print(f"PARADO: outra sessão mudou {', '.join(mudou)} desde o export. Refaça o export e confira.")
        return 1
    corpo = montar(atual)
    _pedir("PATCH", corpo)
    depois = _pedir()["settings"].get("toolPreconditions", {})
    print("toolPreconditions:", json.dumps(depois, ensure_ascii=False))
    return 0 if depois == corpo["settings"]["toolPreconditions"] else 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("cmd", choices=["exportar", "ligar", "desligar", "ver"])
    cmd = p.parse_args().cmd
    if cmd == "exportar":
        EXPORT.write_text(json.dumps(_sem_prompt(_pedir()), indent=2, ensure_ascii=False) + "\n")
        print(f"export gravado em {EXPORT.relative_to(RAIZ)}")
        return 0
    if cmd == "ver":
        print(json.dumps(_pedir()["settings"].get("toolPreconditions", {}), ensure_ascii=False))
        return 0
    return _escrever(corpo_ligar if cmd == "ligar" else corpo_desligar)


if __name__ == "__main__":
    sys.exit(main())
