from __future__ import annotations

"""Algoritmo cuántico básico para el Holocron.

Este módulo define una operación sencilla que coloca cada Holobit en
superposición uniforme y luego realiza una medición. La medición se modela
como una elección aleatoria entre ``0`` y ``1`` para cada Holobit.
"""

from typing import Iterable, List
import random

from .instructions.assembler_instructions import QuantumInstruction
from .core.holocron import Holocron

Holobit = int  # Alias tipado para los identificadores de Holobits


def superposicion_y_medicion(holobits: Iterable[Holobit]) -> List[int]:
    """Aplica una superposición y mide los Holobits dados.

    Cada Holobit se representa como un bit clásico que adopta ``0`` o ``1`` con
    la misma probabilidad tras la medición.
    """

    resultados: List[int] = []
    for _ in holobits:
        resultados.append(random.choice([0, 1]))
    return resultados


SUPERPOSICION_MEDICION = QuantumInstruction(
    "SUPERPOSICION_MEDICION", superposicion_y_medicion
)


def superposicion(holobits: Iterable[Holobit]) -> List[int]:
    """Coloca los Holobits en superposición y devuelve un resultado simbólico.

    En esta implementación simplificada, la superposición se modela como una
    medición inmediata del estado, reutilizando ``superposicion_y_medicion``.
    """

    return superposicion_y_medicion(holobits)


def medir(holobits: Iterable[Holobit]) -> List[int]:
    """Mide los Holobits dados.

    Para efectos del SDK, la medición produce un valor clásico "0" o "1" con la
    misma probabilidad para cada Holobit.
    """

    return superposicion_y_medicion(holobits)


SUPERPOSICION = QuantumInstruction("SUPERPOSICION", superposicion)
MEDIR = QuantumInstruction("MEDIR", medir)


def decoherencia(holobits: Iterable[Holobit]) -> List[int]:
    """Simula la decoherencia retornando estados clásicos aleatorios.

    Cada Holobit pierde coherencia y se transforma en un valor clásico
    ``0`` o ``1`` con la misma probabilidad.
    """

    return [random.choice([0, 1]) for _ in holobits]


DECOHERENCIA = QuantumInstruction("DECOHERENCIA", decoherencia)


def teletransportar(holobits: Iterable[Holobit]) -> List[Holobit]:
    """Simula un teletransporte cuántico básico.

    En esta versión simplificada, el teletransporte se modela como una copia
    directa del estado de entrada, retornando los mismos valores recibidos.
    """

    return list(holobits)


def colapsar(holobits: Iterable[Holobit]) -> List[int]:
    """Fuerza el colapso de los Holobits a ``0``.

    Cada Holobit de entrada produce un ``0`` determinista, representando la
    pérdida de superposición.
    """

    return [0 for _ in holobits]


def fusionar(holobits: Iterable[Holobit]) -> List[int]:
    """Fusiona múltiples Holobits en un único valor agregado.

    La fusión se modela sumando los valores numéricos de los Holobits
    proporcionados y devolviendo una lista con un solo elemento que contiene
    dicho total. Si un Holobit no es numérico, se contabiliza como ``1``.
    """

    total = 0
    for hb in holobits:
        try:
            total += hb
        except TypeError:
            total += 1
    return [total]


TELETRANSPORTAR = QuantumInstruction("TELETRANSPORTAR", teletransportar)
COLAPSAR = QuantumInstruction("COLAPSAR", colapsar)
FUSIONAR = QuantumInstruction("FUSIONAR", fusionar)


def ejecutar_superposicion_medicion(holocron: Holocron, group_id) -> List[int]:
    """Ejecuta la operación de superposición y medición sobre un grupo.

    Parameters
    ----------
    holocron:
        Instancia de :class:`Holocron` que contiene los Holobits.
    group_id:
        Identificador del grupo sobre el que se aplicará la operación.
    """

    return holocron.execute_quantum_operation(SUPERPOSICION_MEDICION, group_id)


__all__ = [
    "superposicion_y_medicion",
    "superposicion",
    "medir",
    "decoherencia",
    "SUPERPOSICION_MEDICION",
    "SUPERPOSICION",
    "MEDIR",
    "DECOHERENCIA",
    "teletransportar",
    "colapsar",
    "fusionar",
    "TELETRANSPORTAR",
    "COLAPSAR",
    "FUSIONAR",
    "ejecutar_superposicion_medicion",
]
