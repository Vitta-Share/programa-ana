"""O comando do Mapa da Global Health (issue #77, PRD #76).

Os testes rodam o comando como o PedroOS vai rodar (processo, saída em JSON)
contra uma Global Health falsa num endereço local: lista cheia, lista vazia,
417, 500 e demora. Nada aqui fala com a Global Health de verdade.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
COMANDO = RAIZ / "ana" / "api-mv" / "scripts" / "mapa-gh.py"

TOKEN_FALSO = "tok-falso-77-abcdef"
CPF_SONDA = "66301102770"
NOME_SONDA = "TESTE SONDA ANA VITTA"
TELEFONE_SONDA = "5521999990000"

# As 23 chamadas do contrato doc_whatsapp_agendamento_1.10.pdf, lidas à mão do PDF.
CHAMADAS_DO_CONTRATO = {
    "GET /pessoas", "POST /pessoas", "GET /consultas", "GET /exames",
    "GET /convenios", "GET /convenios/{id}/planos",
    "GET /convenios/{id}/planos/{idPlano}/subPlanos",
    "GET /carteiras", "POST /carteiras", "DELETE /carteiras/{id}",
    "GET /prestadores", "GET /agendas/v2", "POST /anexos/agendamento",
    "POST /anexos/upload", "GET /consultas/tipos", "GET /exames/perguntas",
    "GET /horarios/{id}/instrucoes", "POST /horarios/agendar",
    "POST /horarios/reagendar", "GET /agendamentos", "GET /agendamentos/{id}",
    "DELETE /agendamentos/{id}", "GET /exames/instrucaoGeral",
}


class GHFalsa:
    """Global Health falsa: cada rota responde (status, corpo, demora em segundos)."""

    def __init__(self, rotas):
        self.rotas = dict(rotas)
        self.pedidos = []
        gh = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _responder(self):
                url = urllib.parse.urlparse(self.path)
                caminho = url.path.removeprefix("/rest/whatsapp")
                gh.pedidos.append((self.command, caminho, urllib.parse.parse_qs(url.query),
                                   self.headers.get("Token")))
                resposta = gh.rotas.get(f"{self.command} {caminho}", (404, {"erro": "rota"}, 0))
                status, corpo, demora = resposta
                if demora:
                    time.sleep(demora)
                dados = json.dumps(corpo).encode()
                try:
                    self.send_response(status)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(dados)))
                    self.end_headers()
                    self.wfile.write(dados)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            do_GET = _responder
            do_POST = _responder
            do_DELETE = _responder

        self.servidor = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.servidor.daemon_threads = True
        self.base = f"http://127.0.0.1:{self.servidor.server_address[1]}/rest/whatsapp"
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()

    def fechar(self):
        self.servidor.shutdown()
        self.servidor.server_close()


def lista(*itens):
    return {"conteudo": list(itens), "paginaAnterior": "", "paginaSeguinte": ""}


def rotas_cheias():
    """A homologação de 16/11/2026, com nomes de catálogo e a sonda inventada."""
    return {
        "GET /pessoas": (200, {"id": 1681, "cpf": CPF_SONDA, "nome": NOME_SONDA,
                               "dataNascimento": "1990-01-01", "telefone": TELEFONE_SONDA}, 0),
        "GET /carteiras": (200, lista(), 0),
        "GET /consultas": (200, lista({"id": 1843, "nome": "Consulta Cardiologica",
                                       "bloqueado": False, "ordem": 1}), 0),
        "GET /prestadores": (200, lista(*[{"id": i, "nome": n, "ordem": k} for k, (i, n) in enumerate(
            [(21, "Amanda"), (51, "Charles"), (140, "Norvandia"), (160, "Ricardo")], 1)]), 0),
        "GET /convenios": (200, lista({"id": 8, "nome": "Unimed Do Brasil", "particular": False, "ordem": 1},
                                      {"id": 3, "nome": "Particular", "particular": True, "ordem": 2}), 0),
        "GET /convenios/3/planos": (200, lista({"id": 2, "nome": "Particular Apartamento", "ordem": 1},
                                               {"id": 1, "nome": "Particular Enfermaria", "ordem": 2}), 0),
        "GET /convenios/3/planos/2/subPlanos": (200, lista(), 0),
        "GET /agendas/v2": (200, {"dataInicial": "2026-11-26", "dataFinal": "2026-12-09",
                                  "dataPaginaSeguinte": None, "diasPesquisados": 14, "agendas": [
                                      {"idUnidade": 1, "nomeUnidade": "Hospital", "prestadores": [
                                          {"idPrestador": 160, "nomePrestadorRecurso": "Ricardo",
                                           "horarios": [{"idHorario": 68754, "descricaoHorario": "26/Nov 09:15",
                                                         "idAgenda": 2859, "ordem": 1}]}]}]}, 0),
        "GET /consultas/tipos": (200, [{"id": 15, "nome": "CONSULTA SUBSEQUENTE", "ordem": 1},
                                       {"id": 1, "nome": "PRIMEIRA CONSULTA", "ordem": 2}], 0),
        "GET /horarios/68754/instrucoes": (500, {"mensagens": [{"tipo": "ERROR", "texto": "Erro interno"}]}, 0),
        "POST /anexos/agendamento": (200, [], 0),
        "GET /exames": (200, lista(), 0),
        "GET /agendamentos": (200, lista(), 0),
    }


@pytest.fixture
def historico(tmp_path):
    return tmp_path / "global-health" / "ana.jsonl"


def rodar(*args, base=None, historico=None, timeout=None, prazo=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GH_")}
    env["GH_TOKEN_HOMOLOG"] = TOKEN_FALSO
    if base:
        env["GH_MAPA_BASE"] = base
    if historico:
        env["PEDROOS_GLOBAL_HEALTH"] = str(historico)
    if timeout is not None:
        env["GH_MAPA_TIMEOUT"] = str(timeout)
    if prazo is not None:
        env["GH_MAPA_PRAZO"] = str(prazo)
    r = subprocess.run([sys.executable, str(COMANDO), *args], capture_output=True, text=True,
                       env=env, timeout=60)
    return r


def saida(r):
    assert r.stdout, f"sem saída (stderr: {r.stderr})"
    return json.loads(r.stdout)


def capacidades(mapa):
    return [c for caminho in mapa["caminhos"] for c in caminho["capacidades"]]


# Critério 1: o mapa


def test_mapa_traz_todas_as_capacidades_do_contrato_com_a_ficha_completa(historico):
    r = rodar("mapa", historico=historico)
    assert r.returncode == 0, r.stderr
    mapa = saida(r)

    assert [c["id"] for c in mapa["caminhos"]] == ["paciente", "consulta", "exame", "gestao"]
    caps = capacidades(mapa)
    assert {c["chamada"] for c in caps} == CHAMADAS_DO_CONTRATO

    campos = {"id", "caminho", "ordem", "chamada", "tipo", "promessa", "ferramenta_ana",
              "ligada", "chamada_pelo_prompt", "links", "card", "ultimo_estado"}
    for c in caps:
        assert campos <= set(c), (c["id"], campos - set(c))
        assert c["tipo"] in ("leitura", "escrita")
        assert c["promessa"]
        assert c["links"], c["id"]

    por_chamada = {}
    for c in caps:
        por_chamada.setdefault(c["chamada"], []).append(c)
    horarios = por_chamada["GET /agendas/v2"][0]
    assert horarios["ferramenta_ana"] == "consultar_horarios_livres"
    assert horarios["ligada"] is True and horarios["chamada_pelo_prompt"] is True
    cadastro = por_chamada["POST /pessoas"][0]
    assert cadastro["ferramenta_ana"] == "cadastrar_paciente"
    assert cadastro["ligada"] is False and cadastro["tipo"] == "escrita"
    exames = por_chamada["GET /exames"][0]
    assert exames["ferramenta_ana"] is None and exames["ligada"] is False
    assert {c["ferramenta_ana"] for c in por_chamada["GET /pessoas"]} == {
        "buscar_paciente_por_cpf", "buscar_paciente_por_telefone"}
    assert por_chamada["POST /horarios/agendar"][0]["tipo"] == "escrita"
    assert por_chamada["DELETE /agendamentos/{id}"][0]["tipo"] == "escrita"
    for caminho in mapa["caminhos"]:
        ordens = [c["ordem"] for c in caminho["capacidades"]]
        assert ordens == sorted(ordens) and len(set(ordens)) == len(ordens)


# Critério 5: a semente do Histórico


def test_historico_nasce_com_as_tres_execucoes_de_semente_marcadas_como_registro_de_sessao(historico):
    mapa = saida(rodar("mapa", historico=historico))
    saida(rodar("mapa", historico=historico))  # o segundo uso não planta de novo

    linhas = [json.loads(l) for l in historico.read_text().splitlines() if l.strip()]
    assert [l["data"][:10] for l in linhas] == ["2026-09-08", "2026-11-15", "2026-11-16"]
    assert all(l["registro_de_sessao"] is True and l["quem"] == "sessao" for l in linhas)

    assert [e["data"][:10] for e in mapa["historico"]] == ["2026-09-08", "2026-11-15", "2026-11-16"]
    set_08, nov_15, nov_16 = (e["numeros"] for e in mapa["historico"])
    assert set_08["convenios"] == 33 and set_08["horarios_14_dias"] == 3
    assert set_08["escritas"]["agendar"]["status"] == 417
    assert "convenios: fora do ar" in nov_15["erros"] and "horarios: fora do ar" in nov_15["erros"]
    assert nov_16["convenios"] == 25 and nov_16["horarios_14_dias"] == 1
    assert nov_16["ultimo_horario"] == "26/11" and nov_16["exames_publicados"] == 0
    assert nov_16["escritas"]["agendar"]["status"] == 417

    agendar = next(c for c in capacidades(mapa) if c["id"] == "agendar")
    assert agendar["ultimo_estado"]["status"] == 417
    assert agendar["ultimo_estado"]["cor"] == "vermelho"
    assert agendar["ultimo_estado"]["registro_de_sessao"] is True
    assert agendar["ultimo_estado"]["data"].startswith("2026-11-16")


@pytest.fixture
def gh():
    falsa = GHFalsa(rotas_cheias())
    yield falsa
    falsa.fechar()


# Critério 2: testar


def test_testar_uma_leitura_cheia_devolve_status_tempo_contagem_e_nomes(gh, historico):
    r = rodar("testar", "especialidades", base=gh.base, historico=historico)
    assert r.returncode == 0, r.stderr
    res = saida(r)
    assert res["capacidade"] == "especialidades"
    assert res["estado"] == "ok" and res["cor"] == "verde"
    assert res["status"] == 200
    assert isinstance(res["tempo_ms"], int)
    assert res["contagem"] == 1
    assert res["nomes"] == ["Consulta Cardiologica"]
    assert res["faltou"] is None
    assert gh.pedidos[0][3] == TOKEN_FALSO


def test_testar_mostra_no_maximo_cinco_nomes(gh, historico):
    gh.rotas["GET /consultas"] = (200, lista(*[{"id": i, "nome": f"Consulta {i}", "bloqueado": False, "ordem": i}
                                                for i in range(1, 8)]), 0)
    res = saida(rodar("testar", "especialidades", base=gh.base, historico=historico))
    assert res["contagem"] == 7
    assert res["nomes"] == ["Consulta 1", "Consulta 2", "Consulta 3", "Consulta 4", "Consulta 5"]


def test_testar_uma_lista_vazia_diz_o_que_faltou(gh, historico):
    res = saida(rodar("testar", "exames", base=gh.base, historico=historico))
    assert res["estado"] == "vazio" and res["cor"] == "amarelo"
    assert res["status"] == 200 and res["contagem"] == 0 and res["nomes"] == []
    assert res["faltou"]


def test_testar_um_500_vem_vermelho_com_a_mensagem_da_global_health(gh, historico):
    res = saida(rodar("testar", "instrucoes_horario", base=gh.base, historico=historico))
    assert res["estado"] == "erro" and res["cor"] == "vermelho"
    assert res["status"] == 500
    assert res["faltou"] == "Erro interno"


def test_testar_um_417_vem_vermelho_com_a_regra_de_negocio(gh, historico):
    gh.rotas["GET /carteiras"] = (417, {"mensagens": [{"tipo": "ERROR", "texto": "Regra de negócio recusou"}]}, 0)
    res = saida(rodar("testar", "carteiras", base=gh.base, historico=historico))
    assert res["estado"] == "erro" and res["status"] == 417
    assert res["faltou"] == "Regra de negócio recusou"


def test_testar_uma_escrita_recusa_sem_chamar_e_devolve_o_ultimo_registro(gh, historico):
    r = rodar("testar", "agendar", base=gh.base, historico=historico)
    assert r.returncode == 0, r.stderr
    res = saida(r)
    assert res["recusado"] is True
    assert res["ultimo_registro"]["status"] == 417
    assert res["ultimo_registro"]["data"].startswith("2026-11-16")
    assert res["ultimo_registro"]["registro_de_sessao"] is True
    assert gh.pedidos == []
