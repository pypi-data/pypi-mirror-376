"""Algoritmos evolutivos para grupos de Holobits."""

from __future__ import annotations

from typing import Callable, Dict, List, Any
import random


def evolve_group_ids(
    initial_ids: List[str],
    holobits: Dict[str, Any],
    criteria_fn: Callable[[List[Any]], float],
    generations: int,
    population_size: int,
) -> List[str]:
    """Evoluciona un conjunto de identificadores de Holobits.

    Parameters
    ----------
    initial_ids:
        Lista inicial de identificadores del grupo.
    holobits:
        Mapeo con todos los Holobits disponibles.
    criteria_fn:
        Función de aptitud que recibe una lista de Holobits y devuelve un
        valor numérico. El algoritmo intenta maximizar dicho valor; para
        minimizar, se debe devolver el valor negativo.
    generations:
        Número de generaciones a simular.
    population_size:
        Número de candidatos que componen la población en cada generación.

    Returns
    -------
    list[str]
        Lista con los identificadores del mejor candidato encontrado.
    """

    available_ids = list(holobits.keys())
    group_size = len(initial_ids)

    def fitness(ids: List[str]) -> float:
        return criteria_fn([holobits[i] for i in ids])

    def mutate(ids: List[str]) -> List[str]:
        mutated = ids[:]
        index = random.randrange(group_size)
        opciones = [hid for hid in available_ids if hid not in mutated or hid == mutated[index]]
        mutated[index] = random.choice(opciones)
        return mutated

    # Población inicial
    population = [initial_ids[:]]
    for _ in range(max(population_size - 1, 0)):
        population.append(random.sample(available_ids, group_size))

    best_ids = initial_ids[:]
    best_score = fitness(best_ids)

    for _ in range(generations):
        scored = [(fitness(ids), ids) for ids in population]
        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best_ids = scored[0]
        # Seleccionar los dos mejores como padres
        parents = [ids for _, ids in scored[:2]]
        # Nueva población basada en mutaciones de los padres
        population = parents[:]
        while len(population) < population_size:
            parent = random.choice(parents)
            child = mutate(parent)
            population.append(child)

    # Evaluar última generación para asegurar mejor candidato
    scored = [(fitness(ids), ids) for ids in population]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]
