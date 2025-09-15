"""Módulo de utilidades para entrelazar Holobits.

Proporciona funciones que permiten entrelazar estados de múltiples
Holobits o grupos completos de Holobits. El entrelazamiento se modela
como la creación de pares ordenados que representan la correlación entre
los Holobits involucrados.
"""

from __future__ import annotations

from typing import Iterable, List, Tuple

from .instructions.assembler_instructions import QuantumInstruction

Holobit = int  # Alias simple para claridad tipada


def entangle_holobits(holobits: Iterable[Holobit]) -> List[Tuple[Holobit, Holobit]]:
    """Crea un estado entrelazado a partir de una colección de Holobits.

    Cada Holobit se correlaciona con todos los demás generando pares
    ordenados. El resultado es una lista que representa las correlaciones
    entre todos los Holobits de la colección.
    """

    holobits = list(holobits)
    entangled: List[Tuple[Holobit, Holobit]] = []
    for i in range(len(holobits)):
        for j in range(i + 1, len(holobits)):
            entangled.append((holobits[i], holobits[j]))
    return entangled


def entangle_groups(groups: Iterable[Iterable[Holobit]]) -> List[Tuple[Holobit, Holobit]]:
    """Entrelaza los Holobits pertenecientes a múltiples grupos.

    Los Holobits de todos los grupos se combinan y se aplica
    :func:`entangle_holobits` sobre el conjunto resultante.
    """

    combined: List[Holobit] = []
    for group in groups:
        combined.extend(list(group))
    return entangle_holobits(combined)


def desentangle_holobits(
    entangled: Iterable[Tuple[Holobit, Holobit]],
    pairs_to_remove: Iterable[Tuple[Holobit, Holobit]] | None = None,
) -> List[Tuple[Holobit, Holobit]]:
    """Elimina correlaciones de un estado entrelazado.

    Parameters
    ----------
    entangled:
        Colección de pares que representan el estado entrelazado.
    pairs_to_remove:
        Pares específicos a eliminar. Si es ``None`` se eliminan todas las
        correlaciones.

    Returns
    -------
    list of tuple
        Nuevo estado entrelazado tras eliminar los pares indicados.
    """

    entangled = list(entangled)
    if pairs_to_remove is None:
        return []
    normalized = {tuple(sorted(p)) for p in pairs_to_remove}
    return [pair for pair in entangled if tuple(sorted(pair)) not in normalized]


# Instrucción cuántica reutilizable que aplica el entrelazamiento
# sobre un conjunto de Holobits.
ENTANGLE = QuantumInstruction("ENTANGLE", entangle_holobits)
DESENTANGLE = QuantumInstruction("DESENTANGLE", desentangle_holobits)

__all__ = [
    "entangle_holobits",
    "entangle_groups",
    "desentangle_holobits",
    "ENTANGLE",
    "DESENTANGLE",
]
