#!/usr/bin/env python3
"""Janela de robustez da bancada: E1, E3 e D4 quebram e restauram a Ana (issue #6)."""

from __future__ import annotations

SUFIXO_INEXISTENTE = "-inexistente-bancada-d4"


def corpo_quebrar_d4(ferramenta: dict) -> dict:
    """O PATCH que aponta a gravação da ouvidoria para uma rota que a API não tem (404)."""
    return {"urlTemplate": ferramenta["urlTemplate"].rstrip("/") + SUFIXO_INEXISTENTE}


CARIMBOS = {"updatedAt", "createdAt"}


def diferencas(export: dict, atual: dict) -> list[str]:
    """Campos da definição que mudaram desde o export; os carimbos de data não contam."""
    campos = (set(export) | set(atual)) - CARIMBOS
    return sorted(c for c in campos if export.get(c) != atual.get(c))


def corpo_restaurar(export: dict, atual: dict) -> dict:
    """O PATCH que devolve à ferramenta os campos do export que estão diferentes agora."""
    return {c: export.get(c) for c in diferencas(export, atual)}
