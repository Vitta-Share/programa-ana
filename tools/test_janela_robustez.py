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
