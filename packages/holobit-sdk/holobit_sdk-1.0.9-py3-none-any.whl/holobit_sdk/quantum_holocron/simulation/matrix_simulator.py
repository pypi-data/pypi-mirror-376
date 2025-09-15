import numpy as np


def apply_gate(state, gate):
    """Aplica una puerta cuántica representada por una matriz."""
    state = np.asarray(state, dtype=complex)
    gate = np.asarray(gate, dtype=complex)
    return gate @ state


def pauli_x():
    """Devuelve la matriz de Pauli-X."""
    return np.array([[0, 1], [1, 0]], dtype=complex)


def hadamard():
    """Devuelve la matriz de Hadamard."""
    return 1 / np.sqrt(2) * np.array([[1, 1], [1, -1]], dtype=complex)


def tensor(*matrices):
    """Calcula el producto de Kronecker de varias matrices."""
    if not matrices:
        raise ValueError("Se requiere al menos una matriz")
    result = np.array(matrices[0], dtype=complex)
    for m in matrices[1:]:
        result = np.kron(result, np.array(m, dtype=complex))
    return result
