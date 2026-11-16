"""Checagem de fatos da plataforma em modo só registrar (issue #54).

O script `ana/plataforma/scripts/checagem-fatos.py` liga no agente 1 a checagem
factual da fazer.ai agents (`guardrails.factualGrounding`, 1.57 a 1.59) no modo
`observe` e mede, nos logs da plataforma, o que ela marcaria numa bateria. Estes
testes cobrem o miolo puro: o corpo da escrita e a conta da tabela. A plataforma
de verdade não entra no teste.
"""

from __future__ import annotations

import importlib.util
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
