"""O turno que só roda se a Ana disse uma coisa (issue #19, bateria v72).

C13-1, C14-1 e C16-1 foram escritos para a Global Health sem resposta: o turno 3
espera a escalada do PASSO A2. Na rodada 3 da v72 a GH devolveu um horário, a Ana
mostrou a lista e esperou o número (o certo), e os três cenários falharam. O cenário
passa a cobrir os dois casos: o turno 4 (o paciente escolhe o número) só é enviado se
a resposta da Ana ao turno anterior trouxe a lista numerada. O Chatwoot e a plataforma
não entram no teste: o Canal e o Trace são falsos, o `rodar_cenario` é o de verdade.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "ana" / "bancada" / "e2e.py"

_spec = importlib.util.spec_from_file_location("bancada_e2e", SCRIPT)
e2e = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e2e)

LISTA = "^\\s*1[.)]\\s"

CENARIO = {
    "id": "C14-1", "titulo": "Oferecer horários reais para escolher",
    "turnos": [
        {"envie": "meu nome é Teste Bancada Ana"},
        {"envie": "quero o 1, por favor", "so_se": LISTA},
    ],
    "confere": {"handoff": True},
}

COM_HORARIO = ("Encontrei este horário disponível para cardiologia:\n\n"
               "1. 26/11, às 9h15, com o médico de teste\n\nQuer que eu anote sua preferência?")
SEM_HORARIO = ("Prontinho, Teste! A agenda online não me retornou horários agora, então nossa "
               "equipe vai entrar em contato para confirmar o melhor horário com você.")
ANOTADO = "Perfeito, Teste! Anotei sua preferência de horário."

HANDOFF = [("t", "handoff_to_human", "2099-01-01T00:00:00Z", {})]


class CanalFalso:
    """O paciente no Chatwoot, sem rede: a Ana responde na ordem da lista."""

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.enviados = []

    def link(self, conversa_id):
        return f"chatwoot/{conversa_id}"

    def abrir_conversa(self, nome):
        return "src", 691

    def enviar(self, source_id, conversa_id, texto):
        if texto != e2e.PREFIXO_MODO_TESTE:
            self.enviados.append(texto)

    def mensagens(self, source_id, conversa_id):
        return []

    def esperar_resposta(self, source_id, conversa_id, vistos):
        return [self.respostas.pop(0)] if self.respostas else []

    def notas_privadas(self, conversa_id):
        return []

    def etiquetas(self, conversa_id):
        return []

    def estado(self, conversa_id):
        return "Fila Comercial", "open", 137

    def resolver(self, conversa_id):
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


def rodar(canal, chamadas=HANDOFF):
    return e2e.rodar_cenario(canal, TraceFalso(list(chamadas)), json.loads(json.dumps(CENARIO)),
                             "capacidades.json")


def test_com_horario_na_lista_o_paciente_escolhe_o_numero_e_a_escalada_e_conferida_no_turno_4():
    canal = CanalFalso([COM_HORARIO, ANOTADO])
    r = rodar(canal)
    assert canal.enviados == ["meu nome é Teste Bancada Ana", "quero o 1, por favor"]
    assert [t["n"] for t in r["turnos"]] == [1, 2]
    assert r["turnos_pulados"] == []
    assert r["veredito"] == "passou", r["falhas"]
    assert any(c["tipo"] == "handoff" and c["turno"] == 2 for c in r["conferencias"])


def test_com_a_gh_sem_resposta_o_turno_da_escolha_nao_e_enviado_e_a_escalada_vale_no_turno_3():
    canal = CanalFalso([SEM_HORARIO])
    r = rodar(canal)
    assert canal.enviados == ["meu nome é Teste Bancada Ana"]
    assert [t["n"] for t in r["turnos"]] == [1]
    assert r["turnos_pulados"] == [2]
    assert r["veredito"] == "passou", r["falhas"]
    assert any(c["tipo"] == "handoff" and c["turno"] == 1 for c in r["conferencias"])


def test_turno_pulado_fica_na_conversa_gravada(tmp_path, monkeypatch):
    monkeypatch.setattr(e2e, "CONVERSAS", tmp_path)
    r = rodar(CanalFalso([SEM_HORARIO]))
    gravada = json.loads(e2e.gravar_conversa(r).read_text())
    assert gravada["turnos_pulados"] == [2]


def test_sem_escalada_em_nenhum_dos_dois_casos_o_cenario_falha():
    # C14-1 da rodada 3: "Anotei sua preferência para 26/11" sem lista e sem handoff
    r = rodar(CanalFalso(["Perfeito, Teste! Anotei sua preferência para 26/11, às 9h15."]), chamadas=[])
    assert r["turnos_pulados"] == [2]
    assert r["veredito"] == "falhou"


# ------------------------------------------------------- os três cenários da bateria

CENARIOS = {c["id"]: c for c in json.loads(
    (RAIZ / "ana" / "bancada" / "cenarios" / "capacidades.json").read_text())["cenarios"]}


@pytest.mark.parametrize("cid", ["C13-1", "C14-1", "C16-1"])
def test_cenarios_da_agenda_cobrem_a_gh_sem_resposta_e_a_gh_com_horario(cid):
    turnos = CENARIOS[cid]["turnos"]
    assert len(turnos) == 4
    assert re.search(turnos[3]["so_se"], COM_HORARIO, re.MULTILINE)
    assert not re.search(turnos[3]["so_se"], SEM_HORARIO, re.MULTILINE)
    assert "so_se" not in turnos[2]
    assert CENARIOS[cid]["confere"]["handoff"] is True


def test_c14_1_reprova_a_ana_que_anota_o_horario_sem_o_numero_do_paciente():
    # rodada 3 da v72: com um horário só, a Ana anotou a preferência no turno 3
    turno_3 = CENARIOS["C14-1"]["turnos"][2]
    assert "anotei" in [f.lower() for f in turno_3["nao_contem"]]
