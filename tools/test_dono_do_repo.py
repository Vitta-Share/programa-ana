"""O repositório da Ana e o do Hospital moram na organização Vitta-Share (issue #83).

Desde 26/11/2026 os dois saíram da conta pessoal do Pedro. O endereço antigo
redireciona, mas referência fixa ao dono antigo fica errada em doc, script e
config. O login de pessoa (`pedrorezendefig` como assignee, revisor ou sócio)
não muda, e o histórico (arquivo do roadmap, ADRs, log do TODO) fica como foi
escrito.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

# Montado em partes para este arquivo não achar a si mesmo.
DONO_ANTIGO = "pedrorezendefig" + "/"
REPOS = ("programa-ana", "hospital-reunioes")

# Histórico: o que foi escrito antes da mudança e fica como estava.
# docs/documentacao.html é o retrato gerado pelo /documentacao e carrega o texto das ADRs.
HISTORICO = ("roadmap/arquivo/", "docs/adr/", "docs/documentacao.html")


def _eh_historico(arquivo: str, linha: str) -> bool:
    if arquivo.startswith(HISTORICO):
        return True
    # O log do TODO (linhas "- **dd/mmm/aaaa:** ...") é histórico; o cabeçalho não.
    return arquivo == "roadmap/TODO.md" and linha.startswith("- **")


def _referencias_ao_dono_antigo() -> list[str]:
    achados = []
    for repo in REPOS:
        saida = subprocess.run(
            ["git", "grep", "-n", "-I", "-F", DONO_ANTIGO + repo],
            cwd=RAIZ, capture_output=True, text=True,
        ).stdout
        for registro in saida.splitlines():
            arquivo, _, resto = registro.partition(":")
            _, _, linha = resto.partition(":")
            if not _eh_historico(arquivo, linha):
                achados.append(registro[:160])
    return achados


def test_referencias_aos_repositorios_da_ana_e_do_hospital_apontam_para_a_vitta_share() -> None:
    assert _referencias_ao_dono_antigo() == []
