"""Janela de robustez da bancada: E1, E3 e D4 (issue #6).

O script `ana/plataforma/scripts/janela-robustez.py` quebra de propósito, um
cenário por vez, a credencial `vault:6` (E1 e E3) ou a ferramenta 11 (D4) no
agente da Ana, e restaura logo depois, conferindo contra o export guardado antes.
Os testes cobrem o miolo puro (a quebra, a restauração, a conferência e a trava
do prompt); a plataforma de verdade não entra no teste.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "ana" / "plataforma" / "scripts" / "janela-robustez.py"

_spec = importlib.util.spec_from_file_location("janela_robustez", SCRIPT)
jr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(jr)

URL_11 = "https://api.hospitalsaomatheus.cloud/api/ana/ouvidoria/protocolos"


def ferramenta(id_="11", url=URL_11, atualizada="2026-11-16T02:17:38.628Z", **extra):
    return {
        "id": id_,
        "name": "registrar_ouvidoria",
        "urlTemplate": url,
        "allowedHosts": ["api.hospitalsaomatheus.cloud"],
        "credentialRef": "vault:6",
        "updatedAt": atualizada,
        **extra,
    }


def test_d4_aponta_a_gravacao_para_uma_rota_inexistente_da_mesma_api():
    corpo = jr.corpo_quebrar_d4(ferramenta())
    url = corpo["urlTemplate"]
    assert url.startswith("https://api.hospitalsaomatheus.cloud/api/ana/")
    assert url != URL_11
    assert set(corpo) == {"urlTemplate"}


def test_d4_restaurada_volta_a_url_do_export_e_a_conferencia_fica_limpa():
    export = ferramenta()
    quebrada = ferramenta(url=URL_11 + "-inexistente-bancada-d4", atualizada="2026-11-16T20:00:00.000Z")
    assert jr.diferencas(export, quebrada) == ["urlTemplate"]
    corpo = jr.corpo_restaurar(export, quebrada)
    assert corpo == {"urlTemplate": URL_11}
    restaurada = {**quebrada, **corpo, "updatedAt": "2026-11-16T20:05:00.000Z"}
    assert jr.diferencas(export, restaurada) == []


def test_e3_a_chave_girada_no_vault_nao_toca_definicao_de_ferramenta_nenhuma():
    export = [ferramenta("1", url="https://x/consultas"), ferramenta()]
    assert jr.ferramentas_tocadas(export, [dict(f) for f in export]) == []
    editada = [export[0], ferramenta(atualizada="2026-11-16T20:00:00.000Z")]
    assert jr.ferramentas_tocadas(export, editada) == ["11"]


def test_nada_se_quebra_com_outro_prompt_no_ar_ou_ferramenta_mexida_desde_o_export():
    export = [ferramenta()]
    assert jr.motivo_para_parar(jr.PROMPT_V72, export, export) is None
    assert "prompt" in jr.motivo_para_parar("abc123", export, export)
    mexida = [ferramenta(url="https://api.hospitalsaomatheus.cloud/api/ana/outra")]
    assert "11" in jr.motivo_para_parar(jr.PROMPT_V72, export, mexida)


def _rodar_quebrar_e1(monkeypatch, chave, status):
    """Roda `quebrar-e1` com a rede trocada; devolve (saída, pedidos à plataforma)."""
    pedidos = []
    monkeypatch.setattr(jr, "_trava", lambda: None)
    monkeypatch.setattr(jr, "_chave_de_volta", lambda: chave)
    monkeypatch.setattr(jr, "_status_chave", lambda _chave: status)
    monkeypatch.setattr(jr, "_pedir", lambda caminho, metodo="GET", corpo=None: pedidos.append((metodo, caminho)) or {})
    monkeypatch.setattr("sys.argv", ["janela-robustez.py", "quebrar-e1"])
    try:
        saida = jr.main()
    except SystemExit as fim:
        saida = fim.code
    return saida, pedidos


def test_e1_nao_quebra_o_vault_sem_a_chave_de_volta(monkeypatch):
    saida, pedidos = _rodar_quebrar_e1(monkeypatch, chave=None, status=None)
    assert ("PUT", "/vault/6") not in pedidos
    assert "Nada foi quebrado" in str(saida)


def test_e1_nao_quebra_o_vault_se_a_api_do_hospital_recusa_a_chave_de_volta(monkeypatch):
    saida, pedidos = _rodar_quebrar_e1(monkeypatch, chave="chave-velha", status=401)
    assert ("PUT", "/vault/6") not in pedidos
    assert "401" in str(saida)


def test_e1_quebra_o_vault_quando_a_chave_de_volta_e_aceita(monkeypatch):
    saida, pedidos = _rodar_quebrar_e1(monkeypatch, chave="chave-certa", status=200)
    assert pedidos == [("PUT", "/vault/6")]
    assert saida == 0
