import math

import numpy as np
import pytest

import math
import random
import numpy as np
import pytest

from holobit_sdk.core.quark import Quark
from holobit_sdk.core.holobit import Holobit
from holobit_sdk.quantum_holocron.core.holocron import Holocron
from holobit_sdk.quantum_holocron.fractal import Fractal
from holobit_sdk.quantum_holocron.fractal_dynamics import iterar_fractal
from holobit_sdk.quantum_holocron.fractal_evolution import GenomaFractal


def crear_holobit(indice: int) -> Holobit:
    quarks = [Quark(0, 0, 0) for _ in range(6)]
    antiquarks = [Quark(0, 0, 0) for _ in range(6)]
    return Holobit(quarks, antiquarks, spin=indice)


def construir_holocron_valido() -> Holocron:
    holocron = Holocron()
    for i in range(10):
        holocron.add_holobit(f"hb{i}", crear_holobit(i))
    return holocron


def test_fractal_generacion_y_jerarquia():
    holocron = construir_holocron_valido()
    fractal = Fractal(holocron)
    fractal.generar()

    total_quarks = sum(len(h.quarks) + len(h.antiquarks) for h in holocron.holobits.values())
    assert total_quarks == 120

    assert fractal.hierarquia_superior == 36
    assert fractal.densidad(36) == max(fractal.densidades.values())
    assert fractal.densidad(36) > fractal.densidad(1)


def test_escalado_por_phi():
    holocron = construir_holocron_valido()
    fractal = Fractal(holocron)
    fractal.generar()

    phi = (1 + math.sqrt(5)) / 2
    distancia_1 = np.linalg.norm(fractal.subniveles[1].posicion)
    distancia_2 = np.linalg.norm(fractal.subniveles[2].posicion)

    assert distancia_2 == pytest.approx(distancia_1 * phi, rel=1e-6)


def test_fractal_holocron_invalido():
    holocron = Holocron()
    for i in range(9):  # un holobit menos de los requeridos
        holocron.add_holobit(f"hb{i}", crear_holobit(i))

    with pytest.raises(ValueError):
        Fractal(holocron)


def test_simulacion_dinamica_actualiza_subniveles_y_densidades():
    holocron = construir_holocron_valido()
    fractal = Fractal(holocron, dimension=4)
    fractal.generar()

    estado_inicial = fractal.subniveles[1].posicion.copy()
    densidad_inicial = fractal.densidad(1)

    list(iterar_fractal(fractal, pasos=2, dt=0.1))

    assert not np.allclose(fractal.subniveles[1].posicion, estado_inicial)
    assert fractal.densidad(1) > densidad_inicial


def test_genoma_crossover_y_mutacion():
    rng = random.Random(1)
    g1 = GenomaFractal({1: 1.0, 2: 2.0}, 5)
    g2 = GenomaFractal({1: 3.0, 2: 4.0}, 7)
    hijo = g1.crossover(g2, rng)
    assert set(hijo.densidades.values()).issubset({1.0, 2.0, 3.0, 4.0})
    hijo.mutate(rng, rate_densidad=1.0, max_step_hierarquia=2)
    assert hijo.hierarquia_superior >= 6


def test_optimizar_geneticamente_incrementa_jerarquia():
    holocron = construir_holocron_valido()
    fractal = Fractal(holocron)
    fractal.hierarquia_superior = 1
    fractal.generar()

    def fitness(f: Fractal) -> float:
        return f.hierarquia_superior

    fractal.optimizar_geneticamente(fitness, generations=2)
    assert fractal.hierarquia_superior > 1
