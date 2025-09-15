from __future__ import annotations

"""Generador de fractales cuánticos basados en un Holocron."""

from dataclasses import dataclass, field
from typing import Callable, Dict
import math
import numpy as np
import random

from holobit_sdk.core.quark import Quark
from .core.holocron import Holocron
from .fractal_evolution import GenomaFractal


phi = (1 + math.sqrt(5)) / 2


def morphometric_field(
    level: int,
    coord: int,
    dimension: int,
    density_fn: Callable[[int, int, int], float] | None = None,
) -> float:
    r"""Evalúa un campo morfométrico configurable.

    Parameters
    ----------
    level:
        Nivel jerárquico del fractal.
    coord:
        Índice de la coordenada evaluada.
    dimension:
        Número de dimensiones espaciales consideradas.
    density_fn:
        Función que define la densidad morfométrica. Si es ``None`` se
        utiliza la forma ``sin(level) * cos(coord)``.

    Returns
    -------
    float
        Magnitud del campo en el punto solicitado.
    """

    if density_fn is None:
        return math.sin(level) * math.cos(coord)
    return density_fn(level, coord, dimension)


@dataclass
class Fractal:
    """Representa un fractal generado a partir de un :class:`Holocron`.

    El fractal requiere exactamente diez Holobits. Cada Holobit debe
    contener seis quarks y seis antiquarks (doce en total) y poseer un
    valor de ``spin`` asociado.

    Parameters
    ----------
    holocron:
        Instancia de :class:`Holocron` que contiene los Holobits base del
        fractal.
    """

    holocron: Holocron
    dimension: int = 3
    density_fn: Callable[[int, int, int], float] | None = None
    densidades: Dict[int, float] = field(default_factory=lambda: {i: 0 for i in range(1, 37)})
    hierarquia_superior: int = 36

    def __post_init__(self) -> None:
        if not isinstance(self.holocron, Holocron):
            raise TypeError("Se requiere una instancia válida de Holocron.")

        if len(self.holocron.holobits) != 10:
            raise ValueError("El Holocron debe contener exactamente 10 holobits.")

        for holobit in self.holocron.holobits.values():
            if len(getattr(holobit, "quarks", [])) != 6 or len(getattr(holobit, "antiquarks", [])) != 6:
                raise ValueError(
                    "Cada Holobit debe poseer 6 quarks y 6 antiquarks."
                )

        self.spins = [getattr(hb, "spin", None) for hb in self.holocron.holobits.values()]
        if len(self.spins) != 10:
            raise ValueError("Se requieren 10 valores de spin.")

    def generar(self) -> None:
        r"""Genera las densidades y posiciones fractales.

        El valor de densidad de la dimensión :math:`d` se calcula como el
        número total de quarks (partículas y antipartículas) multiplicado por
        ``d``.  Para cada nivel ``n`` se obtiene un vector unitario mediante el
        campo morfométrico :func:`morphometric_field` y se escala por
        :math:`\phi^n`, donde ``phi`` es la proporción áurea
        :math:`(1+\sqrt{5})/2`.

        Notes
        -----
        Se asume un origen común ``(0, 0, 0)`` y se normaliza el campo para
        evitar amplificación no controlada.
        """

        total_quarks = sum(
            len(hb.quarks) + len(hb.antiquarks) for hb in self.holocron.holobits.values()
        )
        for dimension in self.densidades:
            self.densidades[dimension] = total_quarks * dimension

        # Generar quarks virtuales escalados por phi en cada subnivel
        self.subniveles: Dict[int, Quark] = {}
        for nivel in range(1, self.hierarquia_superior + 1):
            vector = np.array(
                [
                    morphometric_field(
                        nivel, c, self.dimension, self.density_fn
                    )
                    for c in range(self.dimension)
                ],
                dtype=float,
            )
            norma = np.linalg.norm(vector) or 1.0  # Evita división por cero
            direccion = vector / norma
            posicion = direccion * (phi ** nivel)
            # Se crean quarks virtuales representativos de cada subnivel
            self.subniveles[nivel] = Quark(*posicion)

    def simular_dinamica(self, pasos: int, dt: float) -> None:
        """Simula la evolución dinámica del fractal.

        Cada paso actualiza las posiciones de los subniveles siguiendo la
        dirección del campo morfométrico y ajusta las densidades en función
        del parámetro ``dt``.

        Parameters
        ----------
        pasos:
            Número de iteraciones a ejecutar.
        dt:
            Paso temporal aplicado en cada iteración.
        """

        for _ in range(pasos):
            for nivel, quark in self.subniveles.items():
                vector = np.array(
                    [
                        morphometric_field(
                            nivel, c, self.dimension, self.density_fn
                        )
                        for c in range(self.dimension)
                    ],
                    dtype=float,
                )
                norma = np.linalg.norm(vector) or 1.0
                direccion = vector / norma
                quark.posicion = quark.posicion + direccion * dt

            for dimension in self.densidades:
                self.densidades[dimension] += dimension * dt

    def densidad(self, dimension: int) -> float:
        """Devuelve la densidad registrada para la dimensión solicitada."""

        if dimension not in self.densidades:
            raise ValueError("Dimensión fuera de rango (1-36).")
        return self.densidades[dimension]

    def optimizar_geneticamente(
        self,
        fitness_fn: Callable[["Fractal"], float],
        generations: int = 10,
        poblacion: int = 4,
    ) -> None:
        """Optimiza densidades y jerarquía mediante un algoritmo genético simple.

        Parameters
        ----------
        fitness_fn:
            Función que recibe un fractal y devuelve un valor de aptitud.
        generations:
            Número de generaciones a ejecutar.
        poblacion:
            Tamaño de la población genética.
        """

        rng = random.Random(0)

        base = GenomaFractal(self.densidades.copy(), self.hierarquia_superior)
        poblacion_genomas = [base.clone()]
        for _ in range(poblacion - 1):
            g = base.clone()
            g.mutate(rng)
            poblacion_genomas.append(g)

        for _ in range(generations):
            evaluados = []
            for gen in poblacion_genomas:
                fr = Fractal(
                    self.holocron,
                    self.dimension,
                    self.density_fn,
                    densidades=gen.densidades.copy(),
                    hierarquia_superior=gen.hierarquia_superior,
                )
                fr.generar()
                fr.densidades.update(gen.densidades)
                evaluados.append((fitness_fn(fr), gen))

            evaluados.sort(key=lambda x: x[0], reverse=True)
            poblacion_genomas = [evaluados[0][1], evaluados[1][1]]

            while len(poblacion_genomas) < poblacion:
                padre1, padre2 = rng.sample(poblacion_genomas[:2], 2)
                hijo = padre1.crossover(padre2, rng)
                hijo.mutate(rng)
                poblacion_genomas.append(hijo)

        mejor_fractal: Fractal | None = None
        mejor_score: float | None = None
        mejor_genoma: GenomaFractal | None = None
        for gen in poblacion_genomas:
            fr = Fractal(
                self.holocron,
                self.dimension,
                self.density_fn,
                densidades=gen.densidades.copy(),
                hierarquia_superior=gen.hierarquia_superior,
            )
            fr.generar()
            fr.densidades.update(gen.densidades)
            score = fitness_fn(fr)
            if mejor_fractal is None or score > mejor_score:  # type: ignore[operator]
                mejor_fractal, mejor_score, mejor_genoma = fr, score, gen

        if mejor_genoma is None or mejor_fractal is None:
            return

        self.hierarquia_superior = mejor_genoma.hierarquia_superior
        self.generar()
        self.densidades.update(mejor_genoma.densidades)

