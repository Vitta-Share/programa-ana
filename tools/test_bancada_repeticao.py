"""Repetição de ferramenta no turno, lida pelo runner da bancada (issue #55).

Na 1.59 a plataforma grava no log da etapa `tool` linhas que não são chamadas:
a de etapa (`detail.phase`, como a das etiquetas do `set_labels`) e o resumo do
fim do turno quando uma ferramenta falhou em todas as chamadas
(`detail.failedCalls`). O runner contava essas linhas como chamada e acusava
`consultar_convenios_agenda` e `buscar_paciente_por_cpf` "repetidas". As linhas
abaixo são cópias (sem dado de paciente) do log da fumaça de 15/nov.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "ana" / "bancada" / "e2e.py"

_spec = importlib.util.spec_from_file_location("bancada_e2e", SCRIPT)
e2e = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e2e)

TURNO = "4ba57969-5e27-4b10-a420-ec34a1c509f6"


def linha(id_, tool, detalhe, quando, status="ok", erro=None, thread="1:1:597", turno=TURNO):
    return {"id": id_, "turnId": turno, "threadId": thread, "stage": "tool",
            "status": status, "detail": {"tool": tool, **detalhe},
            "errorMessage": erro, "createdAt": quando}


def chamada(id_, tool, args, quando, **kw):
    return linha(id_, tool, {"args": args, "outputCut": False}, quando, **kw)


# C13-1 da fumaça de 15/nov (conversa 597 do Chatwoot), turno 3, na ordem do log
TURNO_3_C13 = [
    chamada("5082", "buscar_paciente_por_cpf", {"cpf": "string(11)"}, "2026-11-15T23:41:14.358Z"),
    chamada("5083", "consultar_especialidades_agenda", {"pesquisa": "string(11)"},
            "2026-11-15T23:41:16.081Z"),
    chamada("5084", "consultar_convenios_agenda", {"idItemAgendamento": "number"},
            "2026-11-15T23:41:47.731Z", status="error",
            erro="the provider did not answer within 30s"),
    linha("5085", "set_labels", {"phase": "labels", "added": 1, "after": 2, "removed": 0,
                                 "scope": "conversation"}, "2026-11-15T23:41:49.529Z"),
    chamada("5086", "set_labels", {"add": "array(1)"}, "2026-11-15T23:41:49.538Z"),
    chamada("5087", "kanban_move_card", {"targetStep": "string(14)"}, "2026-11-15T23:41:51.310Z"),
    chamada("5088", "handoff_to_human", {"reason": "string(398)"}, "2026-11-15T23:41:54.677Z"),
    linha("5092", "consultar_convenios_agenda", {"failedCalls": 1}, "2026-11-15T23:41:59.543Z",
          status="error",
          erro="consultar_convenios_agenda failed on every call this turn (1): "
               "the provider did not answer within 30s"),
]


def log_da_plataforma(*linhas):
    """A rota /api/v1/logs devolve do mais novo para o mais velho."""
    return list(reversed(linhas))


def test_linhas_de_etapa_e_de_resumo_de_falha_nao_sao_chamadas():
    chamadas = e2e.chamadas_do_log(log_da_plataforma(*TURNO_3_C13), 597)
    assert [tool for _, tool, _, _ in chamadas] == [
        "buscar_paciente_por_cpf", "consultar_especialidades_agenda",
        "consultar_convenios_agenda", "set_labels", "kanban_move_card", "handoff_to_human"]


def test_turno_da_fumaca_com_a_gh_fora_nao_acusa_ferramenta_de_dado_repetida():
    _, pior, _ = e2e.resumir_trace(e2e.chamadas_do_log(log_da_plataforma(*TURNO_3_C13), 597))
    assert pior == 1


def test_duas_etiquetas_no_mesmo_turno_nao_sao_repeticao_de_dado():
    # C13-1 da rodada 1 da v159 (conversa 626): set_labels uma vez por etiqueta
    turno = [
        chamada("5476", "buscar_paciente_por_cpf", {"cpf": "string(11)"}, "2026-11-16T02:35:32.416Z"),
        linha("5479", "set_labels", {"phase": "labels"}, "2026-11-16T02:36:06.797Z"),
        chamada("5480", "set_labels", {"add": "array(1)"}, "2026-11-16T02:36:06.811Z"),
        linha("5481", "set_labels", {"phase": "labels"}, "2026-11-16T02:36:08.084Z"),
        chamada("5482", "set_labels", {"add": "array(1)"}, "2026-11-16T02:36:08.086Z"),
    ]
    _, pior, _ = e2e.resumir_trace(e2e.chamadas_do_log(log_da_plataforma(*turno), 597))
    assert pior == 1


def test_ferramenta_de_dado_chamada_duas_vezes_de_verdade_segue_acusada():
    # C10-2 da v159 (conversa 642): consultar_exames sem filtro e depois com o exame
    turno = [
        chamada("5604", "consultar_exames", {}, "2026-11-16T02:49:37.489Z", thread="1:1:642"),
        chamada("5605", "consultar_exames", {"exame": "string(26)"}, "2026-11-16T02:49:38.982Z",
                thread="1:1:642"),
    ]
    _, pior, _ = e2e.resumir_trace(e2e.chamadas_do_log(log_da_plataforma(*turno), 642))
    assert pior == 2


def test_aviso_de_repeticao_nao_aponta_o_truncamento_como_causa():
    aviso = e2e.aviso_de_repeticao(2)
    assert "repetida 2x" in aviso
    assert "truncamento" not in aviso and "4.000" not in aviso
    assert "trace do turno" in aviso


def test_sem_repeticao_nao_ha_aviso():
    assert e2e.aviso_de_repeticao(1) is None
    assert e2e.aviso_de_repeticao(None) is None
