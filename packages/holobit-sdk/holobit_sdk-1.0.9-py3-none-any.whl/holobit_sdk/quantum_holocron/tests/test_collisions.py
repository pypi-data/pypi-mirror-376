import numpy as np

from holobit_sdk.core.quark import Quark
from holobit_sdk.core.holobit import Holobit
from holobit_sdk.quantum_holocron.simulation import simulate_collision


def crear(offset):
    quarks = [Quark(offset, 0, 0) for _ in range(6)]
    antiquarks = [Quark(offset, 0, 0) for _ in range(6)]
    return Holobit(quarks, antiquarks)


def test_simulate_collision_detects_impact():
    h1 = crear(-0.1)
    h2 = crear(0.1)
    params = {"v1": [0.1, 0, 0], "v2": [-0.1, 0, 0], "pasos": 10, "dt": 1, "umbral": 0.05}
    result = simulate_collision(h1, h2, params)
    assert result["paso_colision"] is not None
    assert "energia" in result
