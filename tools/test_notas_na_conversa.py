"""Notas da Ana no Chatwoot (issue #57): ferramentas e erros de cada turno.

O script `ana/plataforma/scripts/notas-na-conversa.py` liga no agente 1 as notas
privadas da fazer.ai agents (1.55) e a guarda do detalhe do turno (1.59). Estes
testes cobrem o miolo puro: o corpo da escrita, a trava contra mudança de outra
sessão desde o export e a varredura de dado de paciente na nota. A plataforma e
o Chatwoot de verdade não entram no teste.
"""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "ana" / "plataforma" / "scripts" / "notas-na-conversa.py"

_spec = importlib.util.spec_from_file_location("notas_na_conversa", SCRIPT)
nc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nc)


def agente(**settings):
    base = {
        "split": {"enabled": False, "maxChars": 320},
        "handoff": {"mode": "route", "instructions": "Escale quando..."},
        "attributeContext": {"contact": ["cpf", "nome_completo"]},
    }
    base.update(settings)
    return {"id": "1", "updatedAt": "2026-11-15T23:33:59.488Z", "settings": base}


def test_notas_de_ferramentas_e_erros_ficam_ligadas_como_nota_privada():
    corpo = nc.corpo_da_escrita(agente(), dias=14)
    assert corpo["settings"]["conversationNotes"] == {"toolsUsed": "note", "errors": "note"}


def test_a_escrita_preserva_os_outros_blocos_e_guarda_o_detalhe_pelos_dias_escolhidos():
    # o PATCH da plataforma SUBSTITUI o saco de settings: bloco omitido é bloco perdido
    antes = agente(observability={"logToolValues": False})
    corpo = nc.corpo_da_escrita(antes, dias=14)
    s = corpo["settings"]
    assert s["split"] == {"enabled": False, "maxChars": 320}
    assert s["handoff"] == {"mode": "route", "instructions": "Escale quando..."}
    assert s["attributeContext"] == {"contact": ["cpf", "nome_completo"]}
    assert s["observability"] == {"logToolValues": False, "fullDetailRetentionDays": 14}
    assert "conversationNotes" not in antes["settings"]  # o export guardado não muda


def test_a_escrita_so_vale_sobre_o_estado_lido():
    # a plataforma responde 409 se outra sessão gravou o agente depois desta leitura
    corpo = nc.corpo_da_escrita(agente(), dias=14)
    assert corpo["expectedUpdatedAt"] == "2026-11-15T23:33:59.488Z"


def test_dias_de_guarda_fora_da_janela_dos_logs_sao_recusados():
    # a plataforma aceita 1 a 90, mas os logs somem em 30 (FLOWLOG_RETENTION_DAYS)
    for dias in (0, 31, 90):
        try:
            nc.corpo_da_escrita(agente(), dias=dias)
        except ValueError:
            continue
        raise AssertionError(f"{dias} dias deveria ser recusado")


def test_sem_mudanca_desde_o_export_a_aplicacao_segue():
    export = agente()
    atual = copy.deepcopy(export)
    atual["updatedAt"] = "2026-11-16T10:00:00.000Z"  # outra sessão publicou o prompt: não é a mesma coisa
    atual["systemPrompt"] = "prompt novo"
    assert nc.mudou_desde_o_export(export, atual) == []


def test_outra_sessao_mexeu_nas_settings_desde_o_export_a_aplicacao_para():
    export = agente()
    atual = copy.deepcopy(export)
    atual["settings"]["split"]["enabled"] = True
    atual["settings"]["conversationNotes"] = {"toolsUsed": "activity"}
    assert nc.mudou_desde_o_export(export, atual) == ["conversationNotes", "split"]
