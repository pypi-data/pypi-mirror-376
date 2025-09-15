"""Rutinas de iteración para fractales de dimensiones arbitrarias."""

from __future__ import annotations

from typing import Dict, Iterator

from holobit_sdk.core.quark import Quark
from .fractal import Fractal


def iterar_fractal(fractal: Fractal, pasos: int, dt: float) -> Iterator[Dict[int, Quark]]:
    """Itera la dinámica de un fractal en ``n`` dimensiones.

    Parameters
    ----------
    fractal:
        Instancia de :class:`~holobit_sdk.quantum_holocron.fractal.Fractal` a
        evolucionar.
    pasos:
        Número de iteraciones a realizar.
    dt:
        Paso temporal aplicado en cada iteración.

    Yields
    ------
    Dict[int, Quark]
        Copia del diccionario de subniveles tras cada paso de simulación.
    """

    for _ in range(pasos):
        fractal.simular_dinamica(1, dt)
        yield {nivel: Quark(*q.posicion) for nivel, q in fractal.subniveles.items()}
