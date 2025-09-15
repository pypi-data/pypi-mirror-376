"""Interacciones básicas para Holobits."""
import numpy as np
from typing import Iterable

from .holobit import Holobit


def confinar_quarks(holobit: Holobit, limite: float = 1.0) -> Holobit:
    """Limita la posición de cada quark dentro de un cubo de lado ``2*limite``.

    Args:
        holobit: Holobit a modificar.
        limite: Valor absoluto máximo permitido para cada coordenada.
    """
    for quark in holobit.quarks + holobit.antiquarks:
        quark.posicion = np.clip(quark.posicion, -limite, limite)
    return holobit


def cambiar_spin(holobit: Holobit, nuevo_spin: float) -> Holobit:
    """Modifica el valor del *spin* del Holobit."""
    holobit.spin = nuevo_spin
    return holobit


def sincronizar_spin(holobits: Iterable[Holobit]) -> Iterable[Holobit]:
    """Iguala el *spin* de todos los Holobits al promedio del grupo.

    Args:
        holobits: Conjunto de Holobits a sincronizar.
    """
    holobits = list(holobits)
    if not holobits:
        return holobits
    promedio = float(np.mean([hb.spin for hb in holobits]))
    for hb in holobits:
        hb.spin = promedio
    return holobits

