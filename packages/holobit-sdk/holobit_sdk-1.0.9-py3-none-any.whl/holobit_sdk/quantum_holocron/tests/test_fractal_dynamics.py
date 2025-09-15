import numpy as np
import pytest

from holobit_sdk.core.quark import Quark
from holobit_sdk.core.holobit import Holobit
from holobit_sdk.quantum_holocron.core.holocron import Holocron
from holobit_sdk.quantum_holocron.fractal import Fractal
from holobit_sdk.quantum_holocron.fractal_dynamics import iterar_fractal


def _crear_holobit(indice: int) -> Holobit:
    quarks = [Quark(0, 0, 0) for _ in range(6)]
    antiquarks = [Quark(0, 0, 0) for _ in range(6)]
    return Holobit(quarks, antiquarks, spin=indice)


def _holocron_valido() -> Holocron:
    holo = Holocron()
    for i in range(10):
        holo.add_holobit(f"hb{i}", _crear_holobit(i))
    return holo


def test_iteracion_actualiza_posiciones_y_densidades():
    holocron = _holocron_valido()
    fractal = Fractal(holocron, dimension=3)
    fractal.generar()

    estado_inicial = {n: q.posicion.copy() for n, q in fractal.subniveles.items()}
    densidad_inicial = fractal.densidad(3)

    pasos = list(iterar_fractal(fractal, pasos=3, dt=0.2))

    assert len(pasos) == 3
    assert any(
        not np.allclose(fractal.subniveles[n].posicion, estado_inicial[n])
        for n in fractal.subniveles
    )
    assert fractal.densidad(3) == pytest.approx(densidad_inicial + 3 * 0.2 * 3)
    for step in pasos:
        assert set(step.keys()) == set(fractal.subniveles.keys())
