import numpy as np
import numpy.testing as npt

from holobit_sdk.quantum_holocron.simulation.matrix_simulator import (
    apply_gate,
    pauli_x,
    hadamard,
    tensor,
)


def test_pauli_x_on_zero():
    state = np.array([1, 0], dtype=complex)
    expected = np.array([0, 1], dtype=complex)
    result = apply_gate(state, pauli_x())
    npt.assert_allclose(result, expected)


def test_hadamard_on_zero():
    state = np.array([1, 0], dtype=complex)
    expected = 1 / np.sqrt(2) * np.array([1, 1], dtype=complex)
    result = apply_gate(state, hadamard())
    npt.assert_allclose(result, expected)


def test_tensor_two_qubit_operation():
    state = np.array([1, 0, 0, 0], dtype=complex)  # |00>
    gate = tensor(hadamard(), pauli_x())  # H en qubit 0, X en qubit 1
    result = apply_gate(state, gate)
    expected = 1 / np.sqrt(2) * np.array([0, 1, 0, 1], dtype=complex)
    npt.assert_allclose(result, expected)
