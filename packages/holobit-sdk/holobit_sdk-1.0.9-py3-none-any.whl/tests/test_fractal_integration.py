"""Prueba de integración de fractales con HoloLang."""

import matplotlib.pyplot as plt

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


def test_fractal_hololang_integration():
    parser = HoloLangParser()
    parser.holocron = _holocron_valido()

    res = parser.interpretar("CREAR_FRACTAL Fint (densidad_max=16)")
    assert "Fractal Fint creado" in res
    fractal = parser.fractals["Fint"]
    assert len(fractal.densidades) > 0

    fig, axes = parser.interpretar("GRAFICAR_FRACTAL Fint")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)

