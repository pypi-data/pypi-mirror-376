import matplotlib.pyplot as plt
import pytest

from holobit_sdk.core.holobit import Holobit
from holobit_sdk.core.quark import Quark
from holobit_sdk.quantum_holocron.core.holocron import Holocron
from holobit_sdk.multi_level.high_level.hololang_parser import HoloLangParser
from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler


def _crear_holobit(indice: int) -> Holobit:
    quarks = [Quark(0, 0, 0) for _ in range(6)]
    antiquarks = [Quark(0, 0, 0) for _ in range(6)]
    return Holobit(quarks, antiquarks, spin=indice)


def _holocron_valido() -> Holocron:
    holo = Holocron()
    for i in range(10):
        holo.add_holobit(f"hb{i}", _crear_holobit(i))
    return holo


def test_parser_fractal():
    parser = HoloLangParser()
    parser.holocron = _holocron_valido()

    res = parser.interpretar("CREAR_FRACTAL F1 (densidad_max=20)")
    assert "Fractal F1 creado" in res
    assert parser.fractals["F1"].hierarquia_superior == 20

    fig, axes = parser.interpretar("GRAFICAR_FRACTAL F1")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)

    fig2, axes2 = parser.interpretar("FRACTAL_ALT F1 5")
    assert isinstance(fig2, plt.Figure)
    plt.close(fig2)


def test_compiler_fractal():
    compiler = HoloLangCompiler()
    compiler.parser.holocron = _holocron_valido()

    res = compiler.compilar_y_ejecutar("CREAR_FRACTAL F2 (densidad_max=18)")
    assert "Fractal F2 creado" in res
    fig, axes = compiler.compilar_y_ejecutar("GRAFICAR_FRACTAL F2")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)
    fig2, axes2 = compiler.compilar_y_ejecutar("FRACTAL_ALT F2 7")
    assert isinstance(fig2, plt.Figure)
    plt.close(fig2)


def test_dinamica_y_densidad_fractal():
    parser = HoloLangParser()
    parser.holocron = _holocron_valido()

    parser.interpretar("CREAR_FRACTAL F3 (densidad_max=15)")
    densidad_inicial = parser.interpretar("DENSIDAD_MORFO F3 2")

    parser.interpretar("DINAMICA_FRACTAL F3 (pasos=3, dt=0.1)")
    densidad_final = parser.interpretar("DENSIDAD_MORFO F3 2")

    assert densidad_final == pytest.approx(densidad_inicial + 2 * 0.1 * 3)

