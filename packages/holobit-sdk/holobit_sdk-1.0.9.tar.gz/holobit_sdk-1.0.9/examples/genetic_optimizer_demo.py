"""Ejemplo de uso del optimizador genético para ajustar el ``spin`` de un Holobit."""

from holobit_sdk.core.quark import Quark
from holobit_sdk.core.holobit import Holobit


def main() -> None:
    quarks = [Quark() for _ in range(6)]
    antiquarks = [Quark() for _ in range(6)]
    holobit = Holobit(quarks, antiquarks, spin=0.1)

    # Función de aptitud: queremos que el spin se acerque a 0.8
    objetivo = 0.8

    def fitness(hb: Holobit) -> float:
        return -abs(hb.spin - objetivo)

    holobit.optimizar({"spin": (0.0, 1.0)}, fitness, generations=25, population_size=30)
    print(f"Spin optimizado: {holobit.spin:.3f}")


if __name__ == "__main__":
    main()
