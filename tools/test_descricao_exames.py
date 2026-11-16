"""A descrição da `consultar_exames` não empurra a escalada no turno da oferta (issue #19).

Na rodada direcionada da v7.3 (16/nov, conversa 1096) o C10-2 escalou de novo no turno
da oferta, com a pergunta "Quer que nossa equipe confirme para você?" dentro do
`customerMessage` do `handoff_to_human`. O C10-2 é o único cenário do C10 que passa pela
`consultar_exames`, e a descrição dela fecha com "ofereça encaminhar à equipe [...]
Perguntar se é convênio ou particular não substitui esse encaminhamento": o
encaminhamento como ação, no turno em que só cabe a pergunta. O script troca essa frase;
a plataforma de verdade não entra no teste.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "ana" / "plataforma" / "scripts" / "descricao-exames.py"

_spec = importlib.util.spec_from_file_location("descricao_exames", SCRIPT)
de = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(de)

# o fim da descrição como estava no ar em 16/nov/2026 (ferramenta 2, updatedAt 2026-08-19)
NO_AR = (
    "E aí NÃO É NÃO. `disponiveis` é só esta tabela, não a lista do que o hospital faz: o exame "
    "pode ser feito assim mesmo. NUNCA diga nem sugira que o hospital não faz. O certo é a Regra "
    "Global 13: diga que não achou o exame na tabela oficial e, NA MESMA mensagem, ofereça "
    "encaminhar à equipe para confirmar. Perguntar se é convênio ou particular não substitui esse "
    "encaminhamento. Nunca invente nome fora de `disponiveis`."
)


def ferramenta(descricao=NO_AR, atualizado="2026-08-19T18:32:00.578Z"):
    return {"id": "2", "name": "consultar_exames", "description": descricao, "updatedAt": atualizado}


def test_a_oferta_da_ferramenta_e_so_a_pergunta_e_o_handoff_vem_depois_do_sim():
    nova = de.descricao_nova(ferramenta())
    assert "esse encaminhamento" not in nova
    assert "pergunte, em texto, se quer que a equipe confirme" in nova
    assert "o `handoff_to_human` só vem depois do sim." in nova
    # o resto da descrição fica como estava
    assert nova.startswith("E aí NÃO É NÃO.")
    assert nova.endswith("Nunca invente nome fora de `disponiveis`.")
    assert "—" not in nova and "–" not in nova


def test_a_descricao_do_ar_trocada_cabe_no_teto_da_plataforma():
    # a primeira versão da frase deu 2.173 caracteres e a plataforma recusou com 422
    no_ar = json.loads((RAIZ / "ana" / "plataforma" / "export-ferramenta-2-pre-oferta.json").read_text())
    assert len(de.descricao_nova(no_ar)) <= 2000
    with pytest.raises(ValueError):
        de.descricao_nova(ferramenta(descricao="x" * 1990 + NO_AR))


def test_descricao_que_nao_tem_mais_a_frase_velha_nao_e_regravada():
    with pytest.raises(de.MexidaDesdeOExport):
        de.descricao_nova(ferramenta(descricao="outra descrição"))


def test_ferramenta_mexida_desde_o_export_para_a_escrita():
    antes = ferramenta()
    de.conferir_intocada(antes, ferramenta())
    with pytest.raises(de.MexidaDesdeOExport):
        de.conferir_intocada(antes, ferramenta(atualizado="2026-11-16T15:00:00.000Z"))
