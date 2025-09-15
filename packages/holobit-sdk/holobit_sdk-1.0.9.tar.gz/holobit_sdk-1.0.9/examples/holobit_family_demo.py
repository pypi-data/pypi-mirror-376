"""Ejemplo de visualización de una familia de holobits con spins."""

from holobit_sdk.core.quark import Quark
from holobit_sdk.core.holobit import Holobit
from holobit_sdk.visualization.projector import visualizar_familia_3d


def crear_holobit(desplazamiento: float, spin: float) -> Holobit:
    """Crea un holobit simple con un desplazamiento en sus coordenadas."""
    quarks = [Quark(desplazamiento + i, desplazamiento + i + 0.1, desplazamiento + i + 0.2) for i in range(6)]
    antiquarks = list(reversed(quarks))
    return Holobit(quarks, antiquarks, spin=spin)


def main():
    familia = [
        crear_holobit(0, 0.5),
        crear_holobit(1, 1.0),
    ]
    visualizar_familia_3d(familia)


if __name__ == "__main__":
    main()

