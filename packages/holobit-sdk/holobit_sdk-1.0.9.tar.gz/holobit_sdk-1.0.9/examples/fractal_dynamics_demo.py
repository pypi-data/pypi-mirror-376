"""Demostración de creación, simulación y graficado de un fractal multidimensional.

El flujo básico consiste en:

1. Generar un fractal ``N``-dimensional de forma aleatoria.
2. Simular su dinámica aplicando pequeñas perturbaciones.
3. (Opcional) Optimizar genéticamente los parámetros de un fractal
   morfométrico utilizando :meth:`holobit_sdk.quantum_holocron.fractal.Fractal.optimizar_geneticamente`.
"""

from __future__ import annotations

import numpy as np
from holobit_sdk.visualization.fractal_plot import visualizar_fractal, visualizar_dinamica


def generar_fractal_multidimensional(seed: int | None = None, size: int = 25, dims: int = 4) -> np.ndarray:
    """Genera un fractal aleatorio en ``dims`` dimensiones."""
    rng = np.random.default_rng(seed)
    shape = (size,) * dims
    return rng.random(shape)


def simular_dinamica(fractal: np.ndarray, pasos: int = 20):
    """Genera una secuencia de fractales aplicando pequeñas perturbaciones."""
    data = np.asarray(fractal, dtype=float)
    rng = np.random.default_rng(0)
    for _ in range(pasos):
        data = np.clip(data + rng.normal(scale=0.05, size=data.shape), 0, 1)
        yield data


if __name__ == "__main__":
    fractal = generar_fractal_multidimensional(seed=42, size=30, dims=4)

    # Visualizar una proyección 3D del fractal multidimensional
    visualizar_fractal(fractal, modo="3D", cortes={0: 0})

    # Animar la dinámica usando cortes para reducir a 2D
    visualizar_dinamica(simular_dinamica(fractal), cortes={0: 0, 1: 0})

    import matplotlib.pyplot as plt

    plt.show()

    # Paso opcional: optimizar un fractal morfométrico utilizando el
    # algoritmo genético definido en ``Fractal.optimizar_geneticamente``.
    # El siguiente fragmento ilustra el uso básico del método:
    #
    # from holobit_sdk.quantum_holocron.fractal import Fractal
    # from holobit_sdk.quantum_holocron.core.holocron import Holocron
    # from holobit_sdk.core.holobit import Holobit
    # from holobit_sdk.core.quark import Quark
    #
    # holocron = Holocron()
    # for i in range(10):
    #     quarks = [Quark(0, 0, 0) for _ in range(6)]
    #     antiquarks = [Quark(0, 0, 0) for _ in range(6)]
    #     holocron.add_holobit(f"hb{i}", Holobit(quarks, antiquarks, spin=i))
    # fractal_model = Fractal(holocron)
    # fractal_model.generar()
    # def fitness(f: Fractal) -> float:
    #     return f.hierarquia_superior
    # fractal_model.optimizar_geneticamente(fitness, generations=5)
    # print("Jerarquía optimizada:", fractal_model.hierarquia_superior)
