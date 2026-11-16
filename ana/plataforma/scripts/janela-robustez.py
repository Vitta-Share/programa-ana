#!/usr/bin/env python3
"""Janela de robustez da bancada: E1, E3 e D4 quebram e restauram a Ana (issue #6).

Um cenário por vez, com a Ana parada para todo o resto, porque a credencial
`vault:6` serve as ferramentas 1, 2, 3, 4, 11 e 12 ao mesmo tempo.

    python3 ana/plataforma/scripts/janela-robustez.py exportar      # guarda o estado antes (sem segredo)
    python3 ana/plataforma/scripts/janela-robustez.py quebrar-e1    # chave errada no vault:6
    python3 ana/plataforma/scripts/janela-robustez.py girar-e3      # a chave certa de volta, só no vault
    python3 ana/plataforma/scripts/janela-robustez.py quebrar-d4    # ferramenta 11 numa rota que dá 404
    python3 ana/plataforma/scripts/janela-robustez.py restaurar-d4  # ferramenta 11 de volta ao export
    python3 ana/plataforma/scripts/janela-robustez.py conferir      # tudo igual ao export?

As quebras param se o prompt no ar não é a v7.2 ou se alguma ferramenta mudou
desde o export; o E1 para também se a chave de volta falta ou a API do hospital
a recusa, porque o vault não devolve o valor guardado. O segredo nunca é impresso nem gravado: a chave certa vem do
mesmo lugar que o `smoke-hospital.py` usa.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import sys
import urllib.error
import urllib.request
from pathlib import Path

PROMPT_V72 = "5331eb0a977b"
FERRAMENTAS = ["1", "2", "3", "4", "11", "12"]
VAULT = "6"
SUFIXO_INEXISTENTE = "-inexistente-bancada-d4"
CARIMBOS = {"updatedAt", "createdAt"}


def corpo_quebrar_d4(ferramenta: dict) -> dict:
    """O PATCH que aponta a gravação da ouvidoria para uma rota que a API não tem (404)."""
    return {"urlTemplate": ferramenta["urlTemplate"].rstrip("/") + SUFIXO_INEXISTENTE}


def diferencas(export: dict, atual: dict) -> list[str]:
    """Campos da definição que mudaram desde o export; os carimbos de data não contam."""
    campos = (set(export) | set(atual)) - CARIMBOS
    return sorted(c for c in campos if export.get(c) != atual.get(c))


def corpo_restaurar(export: dict, atual: dict) -> dict:
    """O PATCH que devolve à ferramenta os campos do export que estão diferentes agora."""
    return {c: export.get(c) for c in diferencas(export, atual)}


def ferramentas_tocadas(export: list[dict], atuais: list[dict]) -> list[str]:
    """Ids das ferramentas gravadas desde o export (o E3 exige lista vazia)."""
    antes = {f["id"]: f.get("updatedAt") for f in export}
    return [f["id"] for f in atuais if antes.get(f["id"]) != f.get("updatedAt")]


def motivo_para_parar(sha_prompt: str, export: list[dict], atuais: list[dict]) -> str | None:
    """Por que não quebrar nada agora, ou None quando o chão é o do export."""
    if not sha_prompt.startswith(PROMPT_V72):
        return f"o prompt no ar é {sha_prompt[:12]}, não a v7.2 ({PROMPT_V72})"
    antes = {f["id"]: f for f in export}
    mexidas = [f["id"] for f in atuais if diferencas(antes.get(f["id"], {}), f)]
    if mexidas:
        return f"ferramenta {', '.join(mexidas)} mudou desde o export"
    return None


# ---------------------------------------------------------------- casca (rede)

RAIZ = Path(__file__).resolve().parents[3]
EXPORT = RAIZ / "ana" / "plataforma" / "export-ana-pre-janela-robustez.json"
API = "https://agents.hospitalsaomatheus.cloud/api/v1"
API_HOSPITAL_PROVA = "https://api.hospitalsaomatheus.cloud/api/ana/consultas-particulares"


def _ler(arquivo: Path, nome: str) -> str | None:
    if not arquivo.is_file():
        return None
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        chave, _, valor = linha.partition("=")
        if chave.strip() == nome:
            return valor.strip().strip("\"'")
    return None


def _env() -> Path:
    return next(p / ".env" for p in (RAIZ, *RAIZ.parents) if (p / ".env").is_file())


def _chave_de_volta() -> str | None:
    return _ler(_env(), "HOSPITAL_ANA_API_KEY") or _ler(
        Path.home() / "PedroDev" / "Hospital" / "tokens" / ".env", "ANA_API_KEY"
    )


def _chave_hospital() -> str:
    chave = _chave_de_volta()
    if not chave:
        sys.exit("ERRO: chave da API do hospital ausente (a mesma do smoke-hospital.py)")
    return chave


def _status_chave(chave: str) -> int | None:
    """O HTTP que a API do hospital devolve para a chave (a mesma rota do smoke), ou None sem rede."""
    pedido = urllib.request.Request(
        API_HOSPITAL_PROVA, headers={"Accept": "application/json", "X-API-Key": chave}
    )
    try:
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            return resposta.status
    except urllib.error.HTTPError as erro:
        return erro.code
    except OSError:
        return None


def _pedir(caminho: str, metodo: str = "GET", corpo: dict | None = None) -> dict:
    pedido = urllib.request.Request(
        f"{API}{caminho}",
        method=metodo,
        data=json.dumps(corpo).encode() if corpo is not None else None,
        headers={
            "Authorization": f"Bearer {_ler(_env(), 'AGENTS_API_TOKEN')}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            return json.load(resposta)
    except urllib.error.HTTPError as erro:
        sys.exit(f"ERRO {erro.code} em {metodo} {caminho}: {erro.read()[:300]!r}")


def _ferramentas() -> list[dict]:
    return [_pedir(f"/tools/{i}")["tool"] for i in FERRAMENTAS]


def _sha_prompt() -> str:
    return hashlib.sha256(_pedir("/agents/1")["agent"].get("systemPrompt", "").encode()).hexdigest()


def _vault() -> dict:
    return next(e for e in _pedir("/vault")["entries"] if e["id"] == VAULT)


def _export() -> dict:
    return json.loads(EXPORT.read_text(encoding="utf-8"))


def _trava() -> None:
    motivo = motivo_para_parar(_sha_prompt(), _export()["ferramentas"], _ferramentas())
    if motivo:
        sys.exit(f"PARADO: {motivo}. Nada foi quebrado.")


def _trava_volta_do_vault() -> None:
    """O E1 só sobrescreve o vault:6 se a chave de volta existe e a API do hospital a aceita."""
    chave = _chave_de_volta()
    if not chave:
        sys.exit("PARADO: sem a chave de volta (HOSPITAL_ANA_API_KEY no .env). Nada foi quebrado.")
    status = _status_chave(chave)
    if status != 200:
        sys.exit(f"PARADO: a API do hospital devolveu {status} para a chave de volta. Nada foi quebrado.")


def _conferir() -> int:
    export, atuais = _export()["ferramentas"], _ferramentas()
    antes = {f["id"]: f for f in export}
    ok = True
    for f in atuais:
        dif = diferencas(antes[f["id"]], f)
        ok &= not dif
        print(f"ferramenta {f['id']} {f['name']}: {'igual ao export' if not dif else 'DIFERE em ' + ', '.join(dif)}")
    v = _vault()
    print(f"vault:{VAULT} {v['name']}: status {v['status']}")
    sha = _sha_prompt()
    print(f"prompt no ar: {sha[:12]} ({'v7.2' if sha.startswith(PROMPT_V72) else 'NÃO é a v7.2'})")
    return 0 if ok and v["status"] == "active" else 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("cmd", choices=["exportar", "quebrar-e1", "girar-e3", "quebrar-d4", "restaurar-d4", "conferir"])
    cmd = p.parse_args().cmd
    if cmd == "exportar":
        v = _vault()
        estado = {"promptSha256": _sha_prompt(), "vault": v, "ferramentas": _ferramentas()}
        EXPORT.write_text(json.dumps(estado, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"export gravado em {EXPORT.relative_to(RAIZ)}")
        return 0
    if cmd == "conferir":
        return _conferir()
    if cmd == "quebrar-e1":
        _trava()
        _trava_volta_do_vault()
        _pedir(f"/vault/{VAULT}", "PUT", {"value": f"bancada-e1-{secrets.token_hex(16)}"})
        print(f"vault:{VAULT} com chave errada. Rode o E1 e depois girar-e3.")
        return 0
    if cmd == "girar-e3":
        _pedir(f"/vault/{VAULT}", "PUT", {"value": _chave_hospital()})
        tocadas = ferramentas_tocadas(_export()["ferramentas"], _ferramentas())
        print(f"vault:{VAULT} com a chave certa. Ferramentas gravadas desde o export: {tocadas or 'nenhuma'}")
        return 0 if not tocadas else 1
    if cmd == "quebrar-d4":
        _trava()
        onze = _pedir("/tools/11")["tool"]
        depois = _pedir("/tools/11", "PATCH", corpo_quebrar_d4(onze))["tool"]
        print(f"ferramenta 11 apontada para {depois['urlTemplate']}. Rode o D4 e depois restaurar-d4.")
        return 0
    onze = next(f for f in _export()["ferramentas"] if f["id"] == "11")
    corpo = corpo_restaurar(onze, _pedir("/tools/11")["tool"])
    if corpo:
        _pedir("/tools/11", "PATCH", corpo)
    return _conferir()


if __name__ == "__main__":
    sys.exit(main())
