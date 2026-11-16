"""O runner da bancada prova o encerramento (issue #26).

Desde 13/out/2026 a inbox de API "Ana E2E" está no funil do Chatwoot (board 2):
cada conversa de teste ganha card. O runner lê a raia do card (o detalhe da
conversa traz só o id do card; a raia vem de GET /kanban/tasks/<id>), confere
`resolved` quando o cenário pede `confere.resolvida` e, no fim, resolve a
conversa que ficou aberta. A leitura pelo trace vira plano B, com aviso, só
quando a conversa vem sem card. O Chatwoot e a plataforma de verdade não entram
no teste: o Canal e o Trace são falsos, o `rodar_cenario` é o de verdade.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "ana" / "bancada" / "e2e.py"

_spec = importlib.util.spec_from_file_location("bancada_e2e", SCRIPT)
e2e = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e2e)

# o board 2 como o Chatwoot devolve em GET /kanban/tasks/<id> (16/nov/2026)
PASSOS = [{"id": 2, "name": "Novo Contato"}, {"id": 3, "name": "Em Atendimento \u2014 Ana"},
          {"id": 9, "name": "Agendado"}, {"id": 10, "name": "Encerrado \u2014 Resolvido"}]


def chatwoot(conversa_status="pending", card=137, passo=10):
    """As respostas da API admin do Chatwoot para a conversa 691 e o card dela."""
    respostas = {
        "/conversations/691": (200, {"id": 691, "status": conversa_status,
                                     "kanban_task": {"id": card} if card else None}),
    }
    if card:
        respostas[f"/kanban/tasks/{card}"] = (200, {"id": card, "board_step_id": passo,
                                                    "board": {"id": 2, "steps": PASSOS}})
    return respostas


def canal_de_api(respostas):
    """Um Canal de verdade com a rede trocada por um dicionário de respostas."""
    canal = e2e.Canal.__new__(e2e.Canal)
    canal.chamadas = []

    def admin(caminho, metodo="GET", corpo=None):
        canal.chamadas.append((metodo, caminho, corpo))
        return respostas.get(caminho, (404, "nao achei"))

    canal._admin = admin
    return canal


def test_a_raia_vem_do_card_do_kanban_da_conversa():
    canal = canal_de_api(chatwoot(conversa_status="resolved", card=137, passo=10))
    raia, status, card = canal.estado(691)
    assert raia == "Encerrado \u2014 Resolvido"
    assert status == "resolved"
    assert card == 137


# ------------------------------------------------------- o cenario inteiro, ponta a ponta

C29 = {"id": "C29-1", "titulo": "Encerramento",
       "turnos": [{"envie": "qual o endereço de vocês?"}, {"envie": "obrigado, era só isso"}],
       "confere": {"raia": "ENCERRADO RESOLVIDO", "handoff": False, "resolvida": True}}

# o log da plataforma mascara o argumento: "Encerrado, Resolvido" com travessao tem 21 caracteres
MOVE_ENCERRADO = ("t2", "kanban_move_card", "2099-01-01T00:00:00Z", {"targetStep": "string(21)"})


class CanalFalso:
    """O paciente e a API admin do Chatwoot, sem rede: grava a ordem do que o runner faz."""

    def __init__(self, raia=None, status="pending", card=None):
        self.fim = (raia, status, card)
        self.eventos = []

    def link(self, conversa_id):
        return f"chatwoot/{conversa_id}"

    def abrir_conversa(self, nome):
        return "src", 691

    def enviar(self, source_id, conversa_id, texto):
        self.eventos.append(("enviar", texto))

    def mensagens(self, source_id, conversa_id):
        return []

    def esperar_resposta(self, source_id, conversa_id, vistos):
        return ["Imagina! Até logo."]

    def notas_privadas(self, conversa_id):
        return []

    def etiquetas(self, conversa_id):
        return []

    def estado(self, conversa_id):
        self.eventos.append(("estado", conversa_id))
        return self.fim

    def resolver(self, conversa_id):
        self.eventos.append(("resolver", conversa_id))
        return True


class TraceFalso:
    ligado = True

    def __init__(self, chamadas):
        self.chamadas = chamadas

    def por_conversa(self, conversa_chatwoot, desde_iso):
        return self.chamadas

    def uso(self, desde_iso):
        return None


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    monkeypatch.setattr(e2e.time, "sleep", lambda s: None)


def rodar(canal, chamadas=(MOVE_ENCERRADO,), cenario=C29):
    return e2e.rodar_cenario(canal, TraceFalso(list(chamadas)), json.loads(json.dumps(cenario)),
                             "capacidades.json")


def test_encerramento_reprova_quando_a_conversa_nao_ficou_resolvida():
    r = rodar(CanalFalso(raia="Encerrado \u2014 Resolvido", status="pending", card=137))
    assert r["fim"]["status"] == "pending"
    assert r["veredito"] == "falhou"
    assert any("resolvida" in f for f in r["falhas"])


def test_encerramento_passa_com_o_card_encerrado_e_a_conversa_resolvida():
    r = rodar(CanalFalso(raia="Encerrado \u2014 Resolvido", status="resolved", card=137))
    assert r["veredito"] == "passou", r["falhas"]
    assert any(c["tipo"] == "resolvida" and c["ok"] for c in r["conferencias"])


@pytest.mark.parametrize("status", ["open", "pending"])
def test_no_fim_o_runner_resolve_a_conversa_que_ficou_aberta(status):
    canal = CanalFalso(raia="Em Atendimento \u2014 Ana", status=status, card=110)
    r = rodar(canal, cenario={"id": "C02-1", "turnos": [{"envie": "oi"}]})
    assert ("resolver", 691) in canal.eventos
    # o estado conferido e o que a Ana deixou, lido antes de o runner fechar a conversa
    assert canal.eventos.index(("estado", 691)) < canal.eventos.index(("resolver", 691))
    assert r["fim"]["status"] == status


def test_o_runner_nao_mexe_na_conversa_que_a_ana_ja_resolveu():
    canal = CanalFalso(raia="Encerrado \u2014 Resolvido", status="resolved", card=137)
    rodar(canal)
    assert ("resolver", 691) not in canal.eventos


def test_resolver_pede_toggle_status_resolved_ao_chatwoot():
    respostas = {"/conversations/691/toggle_status": (200, {"payload": {"current_status": "resolved"}})}
    canal = canal_de_api(respostas)
    assert canal.resolver(691) is True
    assert canal.chamadas == [("POST", "/conversations/691/toggle_status", {"status": "resolved"})]


def test_com_card_a_raia_conferida_e_a_do_card_e_nao_a_do_trace():
    # o trace diz que a Ana moveu para Encerrado, mas o card esta em Novo Contato: vale o card
    r = rodar(CanalFalso(raia="Novo Contato", status="resolved", card=137))
    assert r["fim"]["raia"] == "Novo Contato"
    assert r["fim"]["raia_pelo_trace"] is None
    assert r["veredito"] == "falhou"
    assert any(c["tipo"] == "raia" and c["veio"] == "Novo Contato" for c in r["conferencias"])


def test_sem_card_a_raia_vem_do_trace_como_plano_b_com_aviso(capsys):
    r = rodar(CanalFalso(raia=None, status="resolved", card=None))
    assert r["fim"]["raia_pelo_trace"] == ["ENCERRADO \u2014 RESOLVIDO"]
    assert r["veredito"] == "passou", r["falhas"]
    assert "sem card no kanban" in capsys.readouterr().out


def test_com_card_nao_ha_aviso_de_plano_b(capsys):
    rodar(CanalFalso(raia="Encerrado \u2014 Resolvido", status="resolved", card=137))
    assert "sem card no kanban" not in capsys.readouterr().out


def test_card_que_nao_deu_para_ler_nao_cai_no_trace():
    # o plano B e so para conversa sem card: card existe e a leitura falhou = raia None
    r = rodar(CanalFalso(raia=None, status="resolved", card=137))
    assert r["fim"]["raia_pelo_trace"] is None
    assert r["veredito"] == "falhou"


def test_o_cenario_de_encerramento_da_bateria_pede_a_conversa_resolvida():
    dados = json.loads((RAIZ / "ana" / "bancada" / "cenarios" / "capacidades.json").read_text())
    c29 = next(c for c in dados["cenarios"] if c["id"] == "C29-1")
    assert c29["confere"]["resolvida"] is True
    assert c29["confere"]["raia"] == "ENCERRADO RESOLVIDO"
