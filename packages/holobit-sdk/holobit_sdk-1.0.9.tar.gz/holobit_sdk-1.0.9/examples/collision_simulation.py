from holobit_sdk.core.quark import Quark
from holobit_sdk.core.holobit import Holobit
from holobit_sdk.quantum_holocron.core.hologram_simulator import HologramSimulator


def crear_holobit(offset):
    quarks = [Quark(offset + 0.01 * i, 0, 0) for i in range(6)]
    antiquarks = [Quark(offset - 0.01 * i, 0, 0) for i in range(6)]
    return Holobit(quarks, antiquarks)


def main():
    """Ejemplo de simulación de colisión entre dos Holobits."""
    h1 = crear_holobit(-0.3)
    h2 = crear_holobit(0.3)

    simulador = HologramSimulator()
    parametros = {
        "v1": [0.05, 0, 0],
        "v2": [-0.05, 0, 0],
        "pasos": 40,
        "dt": 1.0,
        "umbral": 0.02,
    }
    resultado = simulador.simulate_collision(h1, h2, parametros, interval=200)
    print(resultado)


if __name__ == "__main__":
    main()
