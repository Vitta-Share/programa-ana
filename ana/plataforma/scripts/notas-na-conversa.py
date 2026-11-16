#!/usr/bin/env python3
"""Notas da Ana no Chatwoot: ferramentas e erros de cada turno (issue #57).

Liga no agente 1 da fazer.ai agents as notas privadas de ferramentas usadas e de
erros contornados (`settings.conversationNotes`, versão 1.55) e a guarda do
detalhe completo do turno por N dias (`settings.observability.
fullDetailRetentionDays`, versão 1.59).
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

NOTAS = {"toolsUsed": "note", "errors": "note"}
# A plataforma aceita de 1 a 90 dias, mas a linha de log em que o detalhe se
# pendura some com FLOWLOG_RETENTION_DAYS (30 por padrão): mais que isso é promessa vazia.
DIAS_MAX = 30


def corpo_da_escrita(agente: dict, dias: int) -> dict:
    """O corpo do PATCH /api/v1/agents/:id que liga as notas.

    O PATCH substitui o saco de settings inteiro, então o corpo leva todos os
    blocos lidos, e `expectedUpdatedAt` faz a plataforma recusar (409) se outra
    sessão gravou o agente depois da leitura.
    """
    if not 1 <= dias <= DIAS_MAX:
        raise ValueError(f"dias de guarda fora de 1 a {DIAS_MAX}: {dias}")
    settings = copy.deepcopy(agente["settings"])
    settings["conversationNotes"] = dict(NOTAS)
    settings["observability"] = {**settings.get("observability", {}), "fullDetailRetentionDays": dias}
    return {"settings": settings, "expectedUpdatedAt": agente["updatedAt"]}


def mudou_desde_o_export(export: dict, atual: dict) -> list[str]:
    """Blocos de settings que outra sessão mudou desde o export, em ordem.

    Só as settings contam: o prompt publicado por outra sessão não é a mesma coisa.
    """
    antes, agora = export["settings"], atual["settings"]
    return sorted(k for k in set(antes) | set(agora) if antes.get(k) != agora.get(k))


# CPF inteiro, com ou sem máscara; os 11 dígitos não podem estar colados a outro dígito
# (o trecho final do UUID do turno, no link de Logs, tem 12).
CPF = re.compile(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)")


def dados_de_paciente(texto: str, proibidos: list[str] = ()) -> list[str]:
    """O que a nota mostra de dado de paciente: CPF inteiro e o que a conversa de teste disse."""
    achados = ["CPF"] if CPF.search(texto) else []
    baixo = texto.casefold()
    achados += [f"dado da conversa: {p}" for p in proibidos if p.casefold() in baixo]
    return achados


def notas_do_agente(mensagens: list[dict]) -> list[dict]:
    """As notas privadas que a plataforma escreveu (marca `fazer_ai_activity`), na ordem."""
    return [
        m for m in mensagens
        if m.get("private")
        and (m.get("content_attributes") or {}).get("fazer_ai_activity") in ("tools", "errors")
    ]


# ---------------------------------------------------------------- casca (rede)

RAIZ = Path(__file__).resolve().parents[3]
EXPORT = RAIZ / "ana" / "plataforma" / "export-ana-pre-notas-na-conversa.json"
AGENTS = "https://agents.hospitalsaomatheus.cloud/api/v1"


def ler_env() -> dict:
    """O .env da raiz (num worktree em .claude/worktrees/, o do checkout principal acima)."""
    arquivo = next(p / ".env" for p in (RAIZ, *RAIZ.parents) if (p / ".env").is_file())
    env = {}
    for linha in arquivo.read_text().splitlines():
        if "=" in linha and not linha.lstrip().startswith("#"):
            k, v = linha.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def pedir(url: str, headers: dict, metodo: str = "GET", corpo: dict | None = None) -> dict:
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo, headers={
        **headers, "Content-Type": "application/json", "User-Agent": "ana-notas/1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b"{}")


def ler_agente(env: dict) -> dict:
    auth = {"Authorization": f"Bearer {env['AGENTS_API_TOKEN']}"}
    return pedir(f"{AGENTS}/agents/1", auth)["agent"]


def sem_prompt(agente: dict) -> dict:
    """O agente sem o prompt (a fonte dele é ana/prompt/), com o hash para conferir."""
    a = dict(agente)
    prompt = a.pop("systemPrompt", "")
    a["systemPromptSha256"] = hashlib.sha256(prompt.encode()).hexdigest()
    a["systemPromptChars"] = len(prompt)
    return a


def exportar(env: dict) -> None:
    EXPORT.write_text(json.dumps(sem_prompt(ler_agente(env)), indent=2, ensure_ascii=False) + "\n")
    print(f"export gravado em {EXPORT.relative_to(RAIZ)}")


def aplicar(env: dict, dias: int) -> int:
    export = json.loads(EXPORT.read_text())
    atual = ler_agente(env)
    mudou = mudou_desde_o_export(export, atual)
    if mudou:
        print(f"PARADO: outra sessão mudou {', '.join(mudou)} desde o export. Refaça o export e confira.")
        return 1
    auth = {"Authorization": f"Bearer {env['AGENTS_API_TOKEN']}"}
    pedir(f"{AGENTS}/agents/1", auth, "PATCH", corpo_da_escrita(atual, dias))
    depois = ler_agente(env)["settings"]
    print("conversationNotes:", depois.get("conversationNotes"))
    print("observability:", depois.get("observability"))
    ok = depois.get("conversationNotes") == NOTAS and \
        (depois.get("observability") or {}).get("fullDetailRetentionDays") == dias
    return 0 if ok else 1


def conferir(env: dict, conversa: int, proibidos: list[str]) -> int:
    url = f"{env['CHATWOOT_URL']}/api/v1/accounts/{env['CHATWOOT_ACCOUNT_ID']}" \
          f"/conversations/{conversa}/messages"
    mensagens = pedir(url, {"api_access_token": env["CHATWOOT_API_TOKEN"]})["payload"]
    notas = notas_do_agente(mensagens)
    if not notas:
        print("nenhuma nota da plataforma nesta conversa")
        return 1
    falhou = False
    for n in notas:
        achados = dados_de_paciente(n.get("content") or "", proibidos)
        falhou |= bool(achados)
        print(f"--- nota {n['id']} ({n['content_attributes']['fazer_ai_activity']})"
              f" {'ACHOU: ' + ', '.join(achados) if achados else 'sem dado de paciente'}")
        print(n.get("content"))
    return 1 if falhou else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("exportar", help="guarda o estado do agente 1 antes de mudar")
    a = sub.add_parser("aplicar", help="liga as notas, se ninguém mudou as settings desde o export")
    a.add_argument("--dias", type=int, required=True, help=f"dias de guarda do detalhe do turno (1 a {DIAS_MAX})")
    c = sub.add_parser("conferir", help="lê as notas de uma conversa do Chatwoot e varre dado de paciente")
    c.add_argument("--conversa", type=int, required=True, help="id da conversa no Chatwoot")
    c.add_argument("--proibido", action="append", default=[], help="texto que o paciente de teste disse")
    args = p.parse_args()
    env = ler_env()
    if args.cmd == "exportar":
        exportar(env)
        return 0
    if args.cmd == "aplicar":
        return aplicar(env, args.dias)
    return conferir(env, args.conversa, args.proibido)


if __name__ == "__main__":
    sys.exit(main())
