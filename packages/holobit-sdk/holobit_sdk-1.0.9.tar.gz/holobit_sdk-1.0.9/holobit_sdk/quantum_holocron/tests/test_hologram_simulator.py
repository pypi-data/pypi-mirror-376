import matplotlib
matplotlib.use("Agg")

from holobit_sdk.core.quark import Quark
from holobit_sdk.core.holobit import Holobit
from holobit_sdk.quantum_holocron.core.hologram_simulator import HologramSimulator


def test_animate_creates_file(tmp_path):
    quarks = [Quark(0.1 * i, 0.1 * i, 0.1 * i) for i in range(6)]
    antiquarks = [Quark(-q.posicion[0], -q.posicion[1], -q.posicion[2]) for q in quarks]
    holobit = Holobit(quarks, antiquarks)

    simulator = HologramSimulator()
    pasos = [{"traslacion": (0.1, 0.0, 0.0), "rotacion": ("z", 15)}]

    output_file = tmp_path / "anim.gif"
    simulator.animate(holobit, pasos, interval=10, output_path=str(output_file))

    assert output_file.exists()
