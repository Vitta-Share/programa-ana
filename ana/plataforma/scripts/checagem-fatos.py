#!/usr/bin/env python3
"""Checagem de fatos da Ana em modo só registrar (issue #54).

Liga no agente 1 da fazer.ai agents a checagem factual (`guardrails.factualGrounding`,
versões 1.57 a 1.59) com a ação `observe` ("Só registrar" no console): um modelo
revisor compara cada resposta com o que as ferramentas trouxeram e anota no log o que
não bate, sem bloquear nem reescrever nada. Depois mede, nos logs, o que ela marcou
nas conversas de uma bateria da bancada.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

# As fontes que a issue pede: preço, exame, agenda e protocolo, mais a base de conhecimento.
FONTES = [
    "consultar_precos_consultas", "consultar_cirurgias_estimativas",   # preço
    "consultar_exames",                                                # exame
    "consultar_especialidades_agenda", "consultar_prestadores_agenda",  # agenda
    "consultar_convenios_agenda", "consultar_planos_convenio", "consultar_horarios_livres",
    "registrar_ouvidoria", "consultar_protocolo_ouvidoria",            # protocolo
    "search_knowledge",                                                # base de conhecimento
]
# "Base Hospital São Matheus" (5 documentos, uns 4 mil caracteres): lida inteira em toda
# revisão, para regra da casa (endereço, horário) não sair como afirmação sem fonte.
BASE_REFERENCIA = "1"


def corpo_da_escrita(agente: dict) -> dict:
    """O corpo do PATCH /api/v1/agents/:id que liga a checagem em Só registrar.

    O PATCH substitui o saco de settings inteiro, então o corpo leva todos os blocos
    lidos, e `expectedUpdatedAt` faz a plataforma recusar (409) se outra sessão gravou
    o agente depois da leitura.
    """
    settings = copy.deepcopy(agente["settings"])
    gr = settings.setdefault("guardrails", {})
    gr["enabled"] = True  # chave geral: a checagem não roda sem ela
    # a moderação de entrada e saída vem salva ligada e trocaria a resposta por template
    gr["input"] = {**gr.get("input", {}), "enabled": False}
    gr["output"] = {**gr.get("output", {}), "enabled": False}
    mc = agente["modelConfig"]
    gr["factualGrounding"] = {
        "enabled": True,
        "action": "observe",
        "sourceTools": list(FONTES),
        "referenceKnowledgeBaseIds": [BASE_REFERENCIA],
        # o revisor roda no modelo e na chave da Ana: os guardrails não têm chave própria
        "provider": mc["provider"],
        "model": mc["model"],
        "credentialRef": mc["credentialRef"],
    }
    return {"settings": settings, "expectedUpdatedAt": agente["updatedAt"]}


def mudou_desde_o_export(export: dict, atual: dict) -> list[str]:
    """Blocos de settings que outra sessão mudou desde o export, em ordem."""
    antes, agora = export["settings"], atual["settings"]
    return sorted(k for k in set(antes) | set(agora) if antes.get(k) != agora.get(k))


def _revisoes(linhas: list[dict], conversas: set[int]) -> list[dict]:
    """As linhas da checagem factual (uma por resposta revisada) das conversas dadas.

    A conversa é o fim do threadId ("1:1:<id no Chatwoot>"), como no runner da bancada:
    conversa de outra sessão na mesma janela fica de fora.
    """
    saida = []
    for linha in linhas:
        d = linha.get("detail") or {}
        if d.get("check") != "factual_grounding" or d.get("outcome") == "revision":
            continue
        conversa = str(linha.get("threadId") or "").rsplit(":", 1)[-1]
        if conversa.isdigit() and int(conversa) in conversas:
            saida.append({**linha, "conversa": int(conversa)})
    return saida


def marcadas(linhas: list[dict], conversas: set[int]) -> list[dict]:
    """As respostas que a checagem marcou, em ordem de conversa e hora, para julgar uma a uma."""
    saida = [{"conversa": r["conversa"], "turno": r.get("turnId"), "quando": r.get("createdAt"),
              "afirmacoes": r["detail"].get("claimCount"), "com_fonte": r["detail"].get("sourced"),
              "fontes": r["detail"].get("sources") or []}
             for r in _revisoes(linhas, conversas) if r["detail"].get("verdict") == "violated"]
    return sorted(saida, key=lambda x: (x["conversa"], x["quando"] or "", x["turno"] or ""))


def tabela(linhas: list[dict], conversas: set[int], precos: dict, modelo: str) -> dict:
    """Revisões, marcadas (com e sem fonte), falhas e o custo do revisor na bateria."""
    revs = _revisoes(linhas, conversas)
    ok = [r["detail"] for r in revs if r.get("status") == "ok" and "verdict" in r["detail"]]
    viol = [d for d in ok if d["verdict"] == "violated"]
    p = precos["openai"][modelo]
    usd = sum(((d.get("inputTokens", 0) - d.get("cachedInputTokens", 0)) * p["entrada"]
               + d.get("cachedInputTokens", 0) * p["cache"]
               + d.get("outputTokens", 0) * p["saida"]) / 1e6 for d in ok)
    por_conversa = usd / len(conversas) if conversas else 0.0
    return {
        "conversas": len(conversas),
        "revisoes": len(ok),
        "marcadas": len(viol),
        "marcadas_com_fonte": sum(1 for d in viol if d.get("sourced")),
        "marcadas_sem_fonte": sum(1 for d in viol if not d.get("sourced")),
        "falhas": len(revs) - len(ok),
        "usd": round(usd, 6),
        "usd_por_conversa": round(por_conversa, 6),
        "brl_por_conversa": round(por_conversa * precos["cambio_brl_por_usd"], 6),
    }


# ---------------------------------------------------------------- casca (rede)

RAIZ = Path(__file__).resolve().parents[3]
EXPORT = RAIZ / "ana" / "plataforma" / "export-ana-pre-checagem-fatos.json"
RESULTADOS = RAIZ / "ana" / "bancada" / "resultados"
PRECOS = RAIZ / "ana" / "bancada" / "precos.json"
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


def pedir(env: dict, caminho: str, metodo: str = "GET", corpo: dict | None = None) -> dict:
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(f"{AGENTS}{caminho}", data=dados, method=metodo, headers={
        "Authorization": f"Bearer {env['AGENTS_API_TOKEN']}",
        "Content-Type": "application/json", "User-Agent": "ana-checagem-fatos/1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"{}")


def sem_prompt(agente: dict) -> dict:
    """O agente sem o prompt (a fonte dele é ana/prompt/), com o tamanho para conferir."""
    a = dict(agente)
    a["systemPromptChars"] = len(a.pop("systemPrompt", ""))
    return a


def exportar(env: dict) -> None:
    agente = pedir(env, "/agents/1")["agent"]
    EXPORT.write_text(json.dumps(sem_prompt(agente), indent=2, ensure_ascii=False) + "\n")
    print(f"export gravado em {EXPORT.relative_to(RAIZ)}")


def aplicar(env: dict) -> int:
    export = json.loads(EXPORT.read_text())
    atual = pedir(env, "/agents/1")["agent"]
    mudou = mudou_desde_o_export(export, atual)
    if mudou:
        print(f"PARADO: outra sessão mudou {', '.join(mudou)} desde o export. Refaça o export e confira.")
        return 1
    pedir(env, "/agents/1", "PATCH", corpo_da_escrita(atual))
    gr = pedir(env, "/agents/1")["agent"]["settings"].get("guardrails") or {}
    fg = gr.get("factualGrounding") or {}
    print(json.dumps({"enabled": gr.get("enabled"), "input": (gr.get("input") or {}).get("enabled"),
                      "output": (gr.get("output") or {}).get("enabled"), "factualGrounding": fg},
                     ensure_ascii=False, indent=2))
    ok = gr.get("enabled") is True and fg.get("enabled") is True and fg.get("action") == "observe"
    return 0 if ok else 1


def conversas_da_bateria(bateria: str, resultados: Path = RESULTADOS) -> tuple[set[int], str]:
    """Os ids no Chatwoot das conversas que rodaram na bateria e o início dela.

    O e2e.py copia a pasta conversas/ inteira para cada rodada, com os cenários que não
    rodaram (fora do --so, ou de escrita sem --com-escrita) guardando o conversa_id de uma
    rodada antiga. Só conta a conversa que começou depois do início da sua rodada.
    """
    inicio_da_rodada = {}  # rodada repetida: a cópia é da última, então vale o último início
    for l in (resultados / f"janelas-{bateria}.txt").read_text().splitlines():
        if l.split()[2:3] == ["inicio"]:
            inicio_da_rodada[l.split()[1]] = l.split()[3]
    conversas = set()
    for arquivo in resultados.glob(f"conversas-{bateria}-rodada*/*.json"):
        rodada = arquivo.parent.name.removeprefix(f"conversas-{bateria}-")
        d = json.loads(arquivo.read_text())
        if (d.get("conversa_id") and d.get("inicio") and rodada in inicio_da_rodada
                and datetime.fromisoformat(d["inicio"]) >= datetime.fromisoformat(inicio_da_rodada[rodada])):
            conversas.add(int(d["conversa_id"]))
    return conversas, min(inicio_da_rodada.values())


def linhas_de_guardrail(env: dict, desde: str) -> list[dict]:
    linhas, cursor = [], None
    while True:
        q = {"stage": "guardrail", "source": "inbox", "since": desde, "limit": 200}
        if cursor:
            q["cursor"] = cursor
        pagina = pedir(env, f"/logs?{urllib.parse.urlencode(q)}")
        linhas += pagina.get("items") or []
        cursor = pagina.get("nextCursor")
        if not cursor:
            return linhas


def medir(env: dict, bateria: str) -> int:
    conversas, desde = conversas_da_bateria(bateria)
    linhas = linhas_de_guardrail(env, desde)
    modelo = pedir(env, "/agents/1")["agent"]["modelConfig"]["model"]
    t = tabela(linhas, conversas, json.loads(PRECOS.read_text()), modelo)
    print(json.dumps(t, ensure_ascii=False, indent=2))
    for m in marcadas(linhas, conversas):
        print(json.dumps(m, ensure_ascii=False))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("exportar", help="guarda o estado do agente 1 antes de mudar")
    sub.add_parser("aplicar", help="liga a checagem em Só registrar, se ninguém mudou as settings")
    m = sub.add_parser("medir", help="tabela da checagem nas conversas de uma bateria da bancada")
    m.add_argument("--bateria", required=True, help="nome da bateria (ex.: v159-checagem)")
    args = p.parse_args()
    env = ler_env()
    if args.cmd == "exportar":
        exportar(env)
        return 0
    if args.cmd == "aplicar":
        return aplicar(env)
    return medir(env, args.bateria)


if __name__ == "__main__":
    sys.exit(main())
