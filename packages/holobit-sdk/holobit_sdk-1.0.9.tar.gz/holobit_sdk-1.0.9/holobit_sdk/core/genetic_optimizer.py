"""Algoritmo genético sencillo para optimizar atributos de un :class:`Holobit`.

Este módulo define dos clases principales:

``HolobitGenome``
    Representa un conjunto de genes (atributos del ``Holobit``) y su
    correspondiente valor de aptitud.

``GeneticOptimizer``
    Implementa un ciclo evolutivo básico compuesto por generación de la
    población inicial, selección, cruce, mutación y evaluación de aptitud.

El objetivo es didáctico; las implementaciones están pensadas para ser
sencillas y fáciles de extender.
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Tuple


GeneBounds = Dict[str, Tuple[float, float]]
FitnessFunc = Callable[["Holobit"], float]


@dataclass
class HolobitGenome:
    """Representa un conjunto de genes de un ``Holobit``.

    Attributes
    ----------
    genes:
        Diccionario con los atributos del ``Holobit`` que se optimizan y su
        valor.
    fitness:
        Resultado de la evaluación de aptitud. Se maximiza durante la
        optimización.
    """

    genes: Dict[str, float]
    fitness: float | None = None

    def mutate(self, mutation_rate: float, bounds: GeneBounds) -> None:
        """Aplica una mutación aleatoria a los genes.

        Cada gen se perturba con probabilidad ``mutation_rate``.
        """

        for name, value in self.genes.items():
            if random.random() < mutation_rate:
                low, high = bounds[name]
                span = high - low
                perturb = random.uniform(-0.1, 0.1) * span
                new_val = max(low, min(high, value + perturb))
                self.genes[name] = new_val

    @staticmethod
    def crossover(parent1: "HolobitGenome", parent2: "HolobitGenome") -> "HolobitGenome":
        """Crea un nuevo genoma mezclando genes de dos padres."""

        child_genes = {
            name: random.choice([parent1.genes[name], parent2.genes[name]])
            for name in parent1.genes
        }
        return HolobitGenome(child_genes)


class GeneticOptimizer:
    """Optimizador genético básico para ``Holobit``.

    Parameters
    ----------
    holobit:
        Instancia sobre la que se aplica la optimización. Se utiliza como
        plantilla para evaluar la aptitud de cada genoma.
    gene_bounds:
        Diccionario con los nombres de los atributos a optimizar y los límites
        (mínimo, máximo) de cada uno.
    fitness_func:
        Función que recibe un ``Holobit`` y devuelve su aptitud. El algoritmo
        maximiza este valor.
    population_size:
        Número de individuos en cada generación.
    generations:
        Número total de generaciones que se ejecutarán.
    mutation_rate:
        Probabilidad de mutar cada gen.
    """

    def __init__(
        self,
        holobit: "Holobit",
        gene_bounds: GeneBounds,
        fitness_func: FitnessFunc,
        population_size: int = 20,
        generations: int = 10,
        mutation_rate: float = 0.1,
    ) -> None:
        self.holobit = holobit
        self.gene_bounds = gene_bounds
        self.fitness_func = fitness_func
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate

    # ------------------------------------------------------------------
    # Fases del algoritmo genético
    # ------------------------------------------------------------------
    def _create_initial_population(self) -> Iterable[HolobitGenome]:
        population = []
        for _ in range(self.population_size):
            genes = {name: random.uniform(*self.gene_bounds[name]) for name in self.gene_bounds}
            population.append(HolobitGenome(genes))
        return population

    def _evaluate(self, genome: HolobitGenome) -> None:
        candidate = copy.deepcopy(self.holobit)
        for attr, value in genome.genes.items():
            setattr(candidate, attr, value)
        genome.fitness = self.fitness_func(candidate)

    def _select(self, population: Iterable[HolobitGenome]) -> list[HolobitGenome]:
        return sorted(population, key=lambda g: g.fitness or float("-inf"), reverse=True)[: self.population_size // 2]

    def _crossover_and_mutate(self, parents: list[HolobitGenome]) -> list[HolobitGenome]:
        offspring: list[HolobitGenome] = []
        while len(offspring) + len(parents) < self.population_size:
            p1, p2 = random.sample(parents, 2)
            child = HolobitGenome.crossover(p1, p2)
            child.mutate(self.mutation_rate, self.gene_bounds)
            offspring.append(child)
        return offspring

    # ------------------------------------------------------------------
    def run(self) -> HolobitGenome:
        """Ejecuta el ciclo generacional completo.

        Returns
        -------
        HolobitGenome
            Mejor individuo encontrado. Además, actualiza los atributos del
            ``Holobit`` original con los genes de dicho individuo.
        """

        population = list(self._create_initial_population())
        for _ in range(self.generations):
            for genome in population:
                self._evaluate(genome)
            parents = self._select(population)
            offspring = self._crossover_and_mutate(parents)
            population = parents + offspring

        best = max(population, key=lambda g: g.fitness or float("-inf"))
        for attr, value in best.genes.items():
            setattr(self.holobit, attr, value)
        return best


__all__ = ["HolobitGenome", "GeneticOptimizer"]
