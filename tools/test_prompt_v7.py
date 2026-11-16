"""Prompt v7 da Ana: a v7.0 comprimida, sem perder função e sem travessão (issue #25).

Dois alvos:
- `ana/plataforma/scripts/publicar-prompt.py`, que publica o prompt no agente 1 só se
  ninguém mudou o prompt vivo desde o export (o miolo puro; a plataforma não entra no teste).
- `ana/prompt/prompt-compilado.md`, o prompt que vai ao ar, conferido contra o export do
  prompt que estava no ar antes (`ana/plataforma/export-prompt-v70.md`).
"""

from __future__ import annotations

import hashlib
import importlib.util
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "ana" / "plataforma" / "scripts" / "publicar-prompt.py"

_spec = importlib.util.spec_from_file_location("publicar_prompt", SCRIPT)
pp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pp)


def agente(prompt="prompt vivo", atualizado="2026-11-16T06:28:48.248Z"):
    return {
        "id": "1",
        "updatedAt": atualizado,
        "systemPrompt": prompt,
        "settings": {"handoff": {"mode": "route"}, "toolPreconditions": {}},
    }


def sha(texto):
    return hashlib.sha256(texto.encode()).hexdigest()


# ------------------------------------------------------------ publicação


def test_publicar_manda_so_o_prompt_e_vale_sobre_o_estado_lido():
    corpo = pp.corpo_publicar(agente(), "prompt novo")
    # sem settings no corpo: o PATCH substitui o saco de settings inteiro quando ele vem
    assert corpo == {"systemPrompt": "prompt novo", "expectedUpdatedAt": "2026-11-16T06:28:48.248Z"}


def test_prompt_mudado_por_outra_sessao_desde_o_export_para_a_publicacao():
    assert pp.prompt_mudou(sha("prompt vivo"), agente("prompt vivo")) is False
    assert pp.prompt_mudou(sha("prompt vivo"), agente("prompt vivo com uma regra a mais")) is True
    # a revisão publicada por cima confere pelo começo do hash, como sai no log
    assert pp.prompt_mudou(sha("prompt vivo")[:12], agente("prompt vivo")) is False
    assert pp.prompt_mudou(sha("prompt vivo")[:12], agente("outro prompt")) is True


def test_prompt_com_travessao_fora_das_colunas_nao_sobe():
    limpo = "Mover para `EM ATENDIMENTO \u2014 ANA` e depois `ENCERRADO \u2014 RESOLVIDO`.\nSem traço."
    assert pp.travessoes_fora_das_colunas(limpo) == []
    sujo = "Cenário A \u2014 fora do horário\nCenário B \u2013 fim de semana"
    assert pp.travessoes_fora_das_colunas(sujo) == [
        "Cenário A \u2014 fora do horário",
        "Cenário B \u2013 fim de semana",
    ]


# ------------------------------------------------------------ o prompt v7

V70 = (RAIZ / "ana" / "plataforma" / "export-prompt-v70.md").read_text(encoding="utf-8")
V7 = (RAIZ / "ana" / "prompt" / "prompt-compilado.md").read_text(encoding="utf-8")

FERRAMENTAS = [
    "search_knowledge", "consultar_precos_consultas", "consultar_exames",
    "consultar_cirurgias_estimativas", "buscar_paciente_por_cpf", "buscar_paciente_por_telefone",
    "consultar_especialidades_agenda", "consultar_convenios_agenda", "consultar_planos_convenio",
    "consultar_horarios_livres", "consultar_prestadores_agenda", "registrar_ouvidoria",
    "consultar_protocolo_ouvidoria", "kanban_move_card", "update_kanban_task", "set_labels",
    "private_note", "set_custom_attribute", "handoff_to_human", "resolve_conversation",
    "get_current_time", "skip_reply",
]
ETIQUETAS = [
    "emergencia", "particular-aquecido", "agendamento-particular", "agendamento-convenio",
    "exame-resultado", "prontuario", "ouvidoria", "fora-horario",
]
COLUNAS = [
    "NOVO CONTATO", "EM ATENDIMENTO \u2014 ANA", "AGUARDANDO CONFIRMAÇÃO", "FILA COMERCIAL",
    "FILA ATENDIMENTO", "FILA OUVIDORIA", "SETOR RESPONSÁVEL", "AGENDADO",
    "ENCERRADO \u2014 RESOLVIDO", "ENCERRADO \u2014 DESISTÊNCIA",
]
ATRIBUTOS = ["nome_completo", "cpf", "convenio"]


def blocos(texto):
    return re.findall(r"```\n(.*?)```", texto, re.DOTALL)


def test_o_prompt_comprimido_fica_perto_de_40_mil_caracteres():
    assert len(V70) == 63_657
    assert len(V7) <= 45_000


def test_o_prompt_nao_tem_travessao_fora_dos_nomes_das_colunas():
    assert pp.travessoes_fora_das_colunas(V70)  # a v7.0 tinha 29
    assert pp.travessoes_fora_das_colunas(V7) == []


def test_a_ana_e_proibida_de_usar_travessao_na_resposta():
    assert "Nunca use travessão nem meia-risca" in V7


def test_toda_ferramenta_etiqueta_coluna_e_atributo_seguem_com_o_mesmo_nome():
    for nome in FERRAMENTAS:
        assert re.search(rf"\b{nome}\b", V70.replace("assign_label", "set_labels")), nome
        assert f"`{nome}`" in V7, nome
    for nome in ATRIBUTOS:
        assert f"`{nome}`" in V70, nome
        assert f"`{nome}`" in V7, nome
    for etiqueta in ETIQUETAS:
        assert f"| {etiqueta} |" in V7, etiqueta
    for coluna in COLUNAS:
        assert f"| {coluna} |" in V7, coluna
    # a 1.59 trocou o nome da ferramenta nativa de etiqueta
    assert "assign_label" not in V7


def test_toda_mensagem_modelo_da_v70_vai_igual_na_v7():
    modelos = [b for b in blocos(V70) if "PASSO 1 →" not in b]  # o único bloco que não é fala
    assert len(modelos) == 31
    faltando = [m for m in modelos if f"```\n{m}```" not in V7]
    assert faltando == []


def test_oferta_de_encaminhar_espera_o_sim_do_paciente():
    # diagnóstico da v159, proposta 1: C08-2, C10-1 e C10-2 escalavam antes do sim
    assert V7.count("Só depois do sim do paciente") >= 1
    assert "nem fora do horário comercial" in V7


def test_exame_particular_sem_valor_vai_ao_setor_responsavel_depois_do_sim():
    # revisão do PR #69: a 2.4A é o fluxo da consulta (agenda, FILA COMERCIAL); o exame
    # particular segue a 5.B, SETOR RESPONSÁVEL, como na v7.0
    oferta = re.search(r"\*\*Oferta de encaminhar:\*\*.*", V7).group(0)
    assert "exame: Seção 5.B" in oferta
    assert "consulta: Seção 2.4A" in oferta
    assert "exame: Seção 2.4A" not in oferta
    secao_5b = V7.split("#### 5.B Exame Particular", 1)[1].split("####", 1)[0]
    assert "`SETOR RESPONSÁVEL`" in secao_5b


def test_mensagem_de_fora_do_horario_nunca_antecipa_a_escalada():
    # diagnóstico da v159, proposta 2: C13-1 pedia o nome e já escalava pelo fora de horário
    assert "nunca antecipa uma escalada" in V7


def test_prontuario_pergunta_a_finalidade_antes_de_orientar():
    # decisão do Pedro na issue (13/out): processo judicial, falecido e menor mudam o caminho
    assert "perguntar a finalidade antes de orientar" in V7


def test_toda_regra_da_v69_tem_endereco_na_v7():
    checklist = (RAIZ / "ana" / "prompt" / "regras-v69.md").read_text(encoding="utf-8")
    linhas = [l for l in checklist.splitlines() if re.match(r"\| \d+ \|", l)]
    assert len(linhas) >= 170
    celulas = [[c.strip() for c in l.strip()[1:-1].split("|")] for l in linhas]
    sem_endereco = [c for c in celulas if len(c) != 4 or not all(c)]
    assert sem_endereco == []


def test_caso_3_do_convenio_manda_o_portal_sem_narrar_a_verificacao():
    # bateria v71, rodada 1: C09-1 e C10-3 disseram "não consegui confirmar" e "agenda online"
    assert "não pôde ser confirmada, e sem citar a agenda" in V7
    assert "Proibido em todos os casos: narrar a verificação" in V7


def test_turno_da_oferta_de_encaminhar_termina_na_pergunta():
    # bateria v71, rodada 1: no C10-2 a Ana fez a oferta certa, mas chamou
    # `get_current_time`, pôs `fora-horario` e escalou no mesmo turno
    oferta = re.search(r"\*\*Oferta de encaminhar:\*\*.*", V7).group(0)
    assert "O turno da oferta termina na pergunta" in oferta
    assert "sem `get_current_time`" in oferta
    assert "sem `fora-horario`" in oferta
    secao_6b = V7.split("#### 6.B Valor de Exame Particular", 1)[1].split("####", 1)[0]
    assert "o turno termina na pergunta" in secao_6b
    # e a etiqueta do fora do horário não puxa a oferta para uma escalada
    secao_10 = V7.split("### 10. Fora do Horário Comercial", 1)[1].split("###", 1)[0]
    assert "no turno de uma oferta de encaminhar" in secao_10


def test_oferta_de_encaminhar_nao_cita_a_tabela():
    # bateria v71: "Não encontrei o valor ... na tabela oficial" é termo interno
    oferta = re.search(r"\*\*Oferta de encaminhar:\*\*.*", V7).group(0)
    assert "sem citar tabela" in oferta
