from __future__ import annotations

"""Rutinas genéticas para ajustar parámetros de un fractal."""

from dataclasses import dataclass
from typing import Dict
import random


@dataclass
class GenomaFractal:
    """Representación genética de un fractal.

    Parameters
    ----------
    densidades:
        Densidades morfométricas por dimensión.
    hierarquia_superior:
        Máximo nivel jerárquico del fractal.
    """

    densidades: Dict[int, float]
    hierarquia_superior: int

    def clone(self) -> "GenomaFractal":
        """Devuelve una copia del genoma."""

        return GenomaFractal(self.densidades.copy(), self.hierarquia_superior)

    def crossover(self, other: "GenomaFractal", rng: random.Random) -> "GenomaFractal":
        """Cruza dos genomas combinando sus densidades y jerarquías.

        Las densidades se heredan escogiendo al azar el valor de uno de los
        progenitores para cada dimensión. La jerarquía se calcula como la media
        entera de ambos padres.
        """

        densidades = {
            dim: self.densidades[dim] if rng.random() < 0.5 else other.densidades.get(dim, self.densidades[dim])
            for dim in self.densidades
        }
        hierarquia = max(1, int(round((self.hierarquia_superior + other.hierarquia_superior) / 2)))
        return GenomaFractal(densidades, hierarquia)

    def mutate(self, rng: random.Random, rate_densidad: float = 0.1, max_step_hierarquia: int = 3) -> None:
        """Aplica mutaciones a densidades y jerarquía.

        Cada densidad puede variar añadiendo ruido gaussiano con una probabilidad
        ``rate_densidad``. La jerarquía se incrementa aleatoriamente en un rango
        de ``1`` a ``max_step_hierarquia`` con probabilidad ``0.5``.
        """

        for dim, valor in list(self.densidades.items()):
            if rng.random() < rate_densidad:
                self.densidades[dim] = valor + rng.gauss(0, abs(valor) * 0.1)
        if rng.random() < 0.5:
            self.hierarquia_superior += rng.randint(1, max_step_hierarquia)
