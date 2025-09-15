import pytest
import numpy as np

from holobit_sdk.multi_level.medium_level.vector_quantization import encode_vector
from holobit_sdk.multi_level.medium_level.vector_processor import VectorProcessor


def test_encode_vector_pca():
    vec = [1, 2, 3]
    amps = encode_vector(vec, reduction="pca")
    assert len(amps) == 2
    np.testing.assert_allclose(np.linalg.norm(amps), 1.0)


def test_to_quantum_state_amplitudes():
    vec = [1, 2, 3, 4]
    amps = VectorProcessor.to_quantum_state(vec, reduction="svd")
    assert len(amps) == 4
    np.testing.assert_allclose(np.linalg.norm(amps), 1.0)


def test_to_quantum_state_qiskit():
    pytest.importorskip("qiskit")
    vec = [1, 2, 3]
    circuit = VectorProcessor.to_quantum_state(vec, backend="qiskit")
    assert circuit.num_qubits == 1
    assert len(circuit.data) > 0


def test_to_quantum_state_cirq():
    pytest.importorskip("cirq")
    vec = [1, 2, 3]
    circuit = VectorProcessor.to_quantum_state(vec, backend="cirq")
    assert len(circuit.all_qubits()) == 1
