import numpy as np


def entrelazar(quark1, quark2):
    """
    Entrelaza dos quarks usando el producto tensorial.

    Args:
        quark1, quark2: Objetos Quark.
    """
    return np.kron(quark1.estado, quark2.estado)
