"""Pruebas para fractales de dimensión variable en HoloLang."""

import pytest

from holobit_sdk.core.holobit import Holobit
from holobit_sdk.core.quark import Quark
from holobit_sdk.quantum_holocron.core.holocron import Holocron
from holobit_sdk.multi_level.high_level.hololang_parser import HoloLangParser


def _crear_holobit(indice: int) -> Holobit:
    quarks = [Quark(0, 0, 0) for _ in range(6)]
    antiquarks = [Quark(0, 0, 0) for _ in range(6)]
    return Holobit(quarks, antiquarks, spin=indice)


def _holocron_valido() -> Holocron:
    holo = Holocron()
    for i in range(10):
        holo.add_holobit(f"hb{i}", _crear_holobit(i))
    return holo


def test_crear_y_dinamica_fractal_nd():
    parser = HoloLangParser()
    parser.holocron = _holocron_valido()

    res = parser.interpretar("CREAR_FRACTAL_ND F4 (dimension=4, densidad_max=12)")
    assert "dimension=4" in res

    densidad_inicial = parser.interpretar("DENSIDAD_MORFO F4 3")
    assert densidad_inicial == pytest.approx(360)

    parser.interpretar("DINAMICA_FRACTAL F4 (pasos=2, dt=0.5)")

    densidad_final = parser.interpretar("DENSIDAD_MORFO F4 3")
    assert densidad_final == pytest.approx(densidad_inicial + 3 * 0.5 * 2)

