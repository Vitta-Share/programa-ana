#!/usr/bin/env python3
"""Mapa da Global Health (HOMOLOGACAO): o que o contrato promete e o que responde hoje.

Uso (saida sempre em JSON):
  python3 ana/api-mv/scripts/mapa-gh.py mapa                  # catalogo + ultimo estado + Historico
  python3 ana/api-mv/scripts/mapa-gh.py testar <capacidade>   # uma leitura ao vivo, resumida
  python3 ana/api-mv/scripts/mapa-gh.py rodada [--quem botao]  # todas as leituras, grava uma Execucao

O catalogo curado mora em ana/api-mv/mapa-gh.json. O Historico mora no estado local do
PedroOS (${PEDROOS_GLOBAL_HEALTH:-~/.pedroos/global-health/ana.jsonl}), uma Execucao por linha.
Le GH_TOKEN_HOMOLOG do .env da raiz do repo, como o smoke-gh.py. Escrita (agendar, reagendar,
cancelar, cadastrar, carteiras) nunca roda daqui. Producao e recusada.
"""
import json
import os
import sys
from pathlib import Path

CATALOGO = Path(__file__).resolve().parent.parent / "mapa-gh.json"

CORES = {"ok": "verde", "vazio": "amarelo", "erro": "vermelho", "fora_do_ar": "vermelho",
         "bloqueado": "cinza", "sem_registro": "cinza"}


def emitir(dados, codigo=0):
    print(json.dumps(dados, ensure_ascii=False, indent=2))
    sys.exit(codigo)


def catalogo():
    return json.loads(CATALOGO.read_text(encoding="utf-8"))


def arquivo_historico():
    padrao = Path.home() / ".pedroos" / "global-health" / "ana.jsonl"
    return Path(os.environ.get("PEDROOS_GLOBAL_HEALTH") or padrao)


def ler_historico(cat):
    arq = arquivo_historico()
    if not arq.is_file() or not arq.read_text(encoding="utf-8").strip():
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in cat["semente"]),
                       encoding="utf-8")
    return [json.loads(l) for l in arq.read_text(encoding="utf-8").splitlines() if l.strip()]


def ultimo_estado(cap_id, historico):
    for execucao in reversed(historico):
        res = execucao.get("resultados", {}).get(cap_id)
        if res:
            return {**res, "cor": CORES.get(res["estado"], "cinza"), "data": res.get("data") or execucao["data"],
                    "execucao": execucao["id"], "quem": execucao["quem"],
                    "registro_de_sessao": execucao.get("registro_de_sessao", False)}
    return {"estado": "sem_registro", "cor": "cinza", "data": None}


def cmd_mapa():
    cat = catalogo()
    historico = ler_historico(cat)
    caminhos = []
    for caminho in cat["caminhos"]:
        caps = sorted((c for c in cat["capacidades"] if c["caminho"] == caminho["id"]), key=lambda c: c["ordem"])
        caminhos.append({**caminho, "capacidades": [{**c, "ultimo_estado": ultimo_estado(c["id"], historico)}
                                                    for c in caps]})
    emitir({"versao_contrato": cat["versao_contrato"], "ambiente": "homologacao",
            "caminhos": caminhos})


def main(argv):
    if not argv:
        emitir({"erro": "uso: mapa | testar <capacidade> | rodada [--quem botao|sessao]"}, 2)
    if argv[0] == "mapa":
        cmd_mapa()
    emitir({"erro": f"uso desconhecido: {argv[0]}"}, 2)


if __name__ == "__main__":
    main(sys.argv[1:])
