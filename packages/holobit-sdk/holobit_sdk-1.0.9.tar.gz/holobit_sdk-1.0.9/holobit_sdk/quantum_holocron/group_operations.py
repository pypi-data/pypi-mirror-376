"""Operaciones de gestión de grupos para el Holocron."""

from __future__ import annotations

from typing import Iterable

from .core.holocron import Holocron


def fusionar_grupo(holocron: Holocron, nuevo_grupo: str, grupos: Iterable[str]):
    """Fusiona varios grupos existentes en uno nuevo.

    Parameters
    ----------
    holocron:
        Instancia sobre la que se aplicará la operación.
    nuevo_grupo:
        Identificador para el grupo resultante.
    grupos:
        Colección con los identificadores de los grupos a fusionar.
    """
    holocron.merge_groups(nuevo_grupo, grupos)
    return holocron.groups[nuevo_grupo]


def dividir_grupo(
    holocron: Holocron,
    grupo_origen: str,
    nuevo_grupo: str,
    holobits: Iterable[str],
):
    """Divide un grupo moviendo Holobits a un nuevo grupo."""
    holocron.split_group(grupo_origen, nuevo_grupo, holobits)
    return holocron.groups[nuevo_grupo]


FUSIONAR_GRUPO = fusionar_grupo
DIVIDIR_GRUPO = dividir_grupo

__all__ = ["fusionar_grupo", "dividir_grupo", "FUSIONAR_GRUPO", "DIVIDIR_GRUPO"]
