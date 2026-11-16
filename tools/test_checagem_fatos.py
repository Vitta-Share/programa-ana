"""Checagem de fatos da plataforma em modo só registrar (issue #54).

O script `ana/plataforma/scripts/checagem-fatos.py` liga no agente 1 a checagem
factual da fazer.ai agents (`guardrails.factualGrounding`, 1.57 a 1.59) no modo
`observe` e mede, nos logs da plataforma, o que ela marcaria numa bateria. Estes
testes cobrem o miolo puro: o corpo da escrita e a conta da tabela. A plataforma
de verdade não entra no teste.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "ana" / "plataforma" / "scripts" / "checagem-fatos.py"

_spec = importlib.util.spec_from_file_location("checagem_fatos", SCRIPT)
cf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cf)


def agente():
    return {
        "id": "1",
        "updatedAt": "2026-11-16T02:18:36.493Z",
        "modelConfig": {"model": "gpt-6-luna", "provider": "openai",
                        "credentialRef": "vault:2", "reasoningEffort": "none"},
        "settings": {
            "split": {"enabled": False, "maxChars": 320},
            "conversationNotes": {"toolsUsed": "note", "errors": "note"},
            "guardrails": {
                "enabled": False, "provider": "openai", "model": "", "credentialRef": None,
                "input": {"enabled": True, "action": "template",
                          "checks": {"toxicity": True, "unsafeContent": True}},
                "output": {"enabled": True, "action": "template",
                           "checks": {"toxicity": True, "promptAdherence": True}},
            },
        },
    }


# ------------------------------------------------- critério 1: ligada em Só registrar

def test_a_checagem_liga_so_registrando_com_as_fontes_de_preco_exame_agenda_protocolo_e_base():
    fg = cf.corpo_da_escrita(agente())["settings"]["guardrails"]["factualGrounding"]
    assert fg["enabled"] is True
    assert fg["action"] == "observe"  # "Só registrar" no console: nada é bloqueado nem reescrito
    for fonte in ("consultar_precos_consultas", "consultar_cirurgias_estimativas",
                  "consultar_exames", "consultar_horarios_livres",
                  "consultar_especialidades_agenda", "consultar_prestadores_agenda",
                  "consultar_convenios_agenda", "consultar_planos_convenio",
                  "registrar_ouvidoria", "consultar_protocolo_ouvidoria",
                  "search_knowledge"):
        assert fonte in fg["sourceTools"], fonte
    assert fg["referenceKnowledgeBaseIds"] == ["1"]  # Base Hospital São Matheus


def test_ligar_a_checagem_nao_liga_a_moderacao_que_troca_a_resposta_por_template():
    # guardrails.enabled é a chave geral; com ela, entrada e saída já salvas ligadas
    # trocariam respostas por "Desculpe, não consigo ajudar com isso."
    gr = cf.corpo_da_escrita(agente())["settings"]["guardrails"]
    assert gr["enabled"] is True
    assert gr["input"]["enabled"] is False
    assert gr["output"]["enabled"] is False
    assert gr["output"]["checks"] == {"toxicity": True, "promptAdherence": True}


def test_o_revisor_usa_o_modelo_e_a_chave_da_propria_ana():
    # a chave dos guardrails está vazia: sem credencial própria o revisor não roda
    fg = cf.corpo_da_escrita(agente())["settings"]["guardrails"]["factualGrounding"]
    assert (fg["provider"], fg["model"], fg["credentialRef"]) == ("openai", "gpt-6-luna", "vault:2")


def test_a_escrita_preserva_os_outros_blocos_e_trava_contra_escrita_de_outra_sessao():
    a = agente()
    corpo = cf.corpo_da_escrita(a)
    assert corpo["settings"]["split"] == {"enabled": False, "maxChars": 320}
    assert corpo["settings"]["conversationNotes"] == {"toolsUsed": "note", "errors": "note"}
    assert corpo["expectedUpdatedAt"] == "2026-11-16T02:18:36.493Z"
    assert a["settings"]["guardrails"]["enabled"] is False  # não mexe no lido


def test_o_aplicar_para_se_outra_sessao_mudou_as_settings_desde_o_export():
    export, atual = agente(), agente()
    atual["settings"]["split"]["maxChars"] = 400
    assert cf.mudou_desde_o_export(export, atual) == ["split"]
    assert cf.mudou_desde_o_export(export, agente()) == []


# ------------------------------- critério 2: marcadas, falsos alarmes e custo extra

PRECOS = {"cambio_brl_por_usd": 5.0,
          "openai": {"gpt-6-luna": {"entrada": 0.10, "cache": 0.01, "saida": 0.50}}}


def revisao(conversa, veredito="clean", fonte=True, entrada=10000, cache=4000, saida=300,
            turno="t", status="ok"):
    detail = {"direction": "output", "check": "factual_grounding"}
    if status == "ok":
        detail.update(verdict=veredito, claimCount=0 if veredito == "clean" else 2,
                      sourced=fonte, inputTokens=entrada, cachedInputTokens=cache,
                      outputTokens=saida)
    else:
        detail.update(outcome="analysis_failed", unchecked=True)
    return {"turnId": turno, "threadId": f"1:1:{conversa}", "stage": "guardrail",
            "status": status, "detail": detail, "createdAt": "2026-11-16T05:00:00Z"}


def test_a_tabela_conta_respostas_marcadas_so_das_conversas_da_bateria():
    linhas = [revisao(700), revisao(700, "violated", turno="a"), revisao(701, "violated", fonte=False),
              revisao(999, "violated"),  # conversa de outra sessão na mesma janela
              {"threadId": "1:1:700", "stage": "guardrail", "status": "ok",
               "detail": {"direction": "output", "action": "template"}}]  # moderação, não checagem
    t = cf.tabela(linhas, conversas={700, 701, 702}, precos=PRECOS, modelo="gpt-6-luna")
    assert (t["conversas"], t["revisoes"], t["marcadas"]) == (3, 3, 2)
    assert (t["marcadas_com_fonte"], t["marcadas_sem_fonte"]) == (1, 1)


def test_a_tabela_soma_o_custo_do_revisor_e_divide_pelas_conversas_da_bateria():
    # 6.000 sem cache x 0,10 + 4.000 em cache x 0,01 + 300 de saída x 0,50 = US$ 0,00079 por revisão
    linhas = [revisao(700), revisao(701), revisao(700, status="error")]
    t = cf.tabela(linhas, conversas={700, 701, 702, 703}, precos=PRECOS, modelo="gpt-6-luna")
    assert t["falhas"] == 1
    assert t["usd"] == 0.00158
    assert t["usd_por_conversa"] == 0.000395
    assert t["brl_por_conversa"] == 0.001975


def test_as_marcadas_saem_em_lista_para_julgar_o_falso_alarme_uma_a_uma():
    linhas = [revisao(700), revisao(701, "violated", turno="b"), revisao(700, "violated", turno="a")]
    m = cf.marcadas(linhas, conversas={700, 701})
    assert [(x["conversa"], x["turno"], x["afirmacoes"]) for x in m] == [(700, "a", 2), (701, "b", 2)]


def test_a_bateria_conta_so_as_conversas_que_comecaram_dentro_da_janela_da_rodada(tmp_path):
    # o e2e.py copia a pasta conversas/ inteira: cenário que não rodou (C22-1 sem
    # --com-escrita, ou fora do --so) entra na cópia com o conversa_id de uma rodada antiga
    (tmp_path / "janelas-b.txt").write_text(
        "b rodada1 inicio 2026-11-16T05:00:00Z\n"
        "b rodada1 fim 2026-11-16T06:00:00Z placar 1/1\n"
        "b rodada2 inicio 2026-11-16T07:00:00Z\n"
        "b rodada2 fim 2026-11-16T08:00:00Z placar 1/1\n")
    pastas = {"rodada1": {"C01-1": (700, "2026-11-16T05:10:00+00:00"),
                          "C22-1": (606, "2026-11-16T02:17:56+00:00")},  # de outra bateria
              "rodada2": {"C01-1": (710, "2026-11-16T07:10:00+00:00"),
                          "C02-1": (701, "2026-11-16T05:20:00+00:00")}}  # não rodou na 2
    for rodada, conversas in pastas.items():
        pasta = tmp_path / f"conversas-b-{rodada}"
        pasta.mkdir()
        for nome, (cid, inicio) in conversas.items():
            (pasta / f"{nome}.json").write_text(json.dumps({"conversa_id": cid, "inicio": inicio}))
    conversas, desde = cf.conversas_da_bateria("b", tmp_path)
    assert conversas == {700, 710}
    assert desde == "2026-11-16T05:00:00Z"
