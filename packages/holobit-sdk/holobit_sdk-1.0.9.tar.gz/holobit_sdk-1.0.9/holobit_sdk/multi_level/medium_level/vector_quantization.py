import numpy as np
from math import log2, floor
from typing import Sequence

try:
    from sklearn.decomposition import PCA
except Exception:  # pragma: no cover - sklearn optional
    PCA = None


def _reduce_vector(vec: np.ndarray, target_dim: int, reduction: str) -> np.ndarray:
    """Aplica reducción de dimensionalidad por PCA o SVD.

    Si la reducción no es posible (por ejemplo, por falta de dependencias),
    se toma un truncamiento simple del vector.
    """
    if vec.size <= target_dim:
        padded = np.zeros(target_dim)
        padded[: vec.size] = vec
        return padded

    if reduction == "pca" and PCA is not None and target_dim > 0:
        try:
            # PCA requiere al menos tantas características como componentes.
            # Usamos el vector como una única muestra.
            pca = PCA(n_components=target_dim)
            data = vec.reshape(1, -1)
            reduced = pca.fit_transform(data).flatten()
            return reduced
        except Exception:
            pass
    elif reduction == "svd":
        try:
            u, s, vh = np.linalg.svd(vec.reshape(1, -1), full_matrices=False)
            m = min(target_dim, vh.shape[0])
            reduced = (u[:, :m] * s[:m]) @ vh[:m, :]
            return reduced.flatten()[:target_dim]
        except Exception:
            pass
    # Fallback: truncamiento
    return vec[:target_dim]


def encode_vector(vector: Sequence[float], reduction: str = "pca") -> np.ndarray:
    """Reduce y normaliza un vector para su codificación cuántica.

    Parameters
    ----------
    vector: Sequence[float]
        Vector de entrada.
    reduction: str
        Método de reducción de dimensionalidad: ``'pca'`` o ``'svd'``.

    Returns
    -------
    numpy.ndarray
        Vector de amplitudes normalizado cuya longitud es la mayor potencia de
        dos no mayor que la longitud del vector original.
    """
    vec = np.asarray(vector, dtype=float)
    if vec.ndim != 1:
        raise ValueError("El vector debe ser unidimensional.")
    if vec.size == 0:
        raise ValueError("El vector no puede estar vacío.")

    target_dim = 1 if vec.size == 1 else 2 ** int(floor(log2(vec.size)))
    reduced = _reduce_vector(vec, target_dim, reduction.lower())

    norm = np.linalg.norm(reduced)
    if norm == 0:
        raise ValueError("El vector de entrada no puede ser el vector cero.")
    return reduced / norm


def amplitudes_to_circuit(amplitudes: Sequence[complex], backend: str = "qiskit"):
    """Genera un circuito cuántico a partir de amplitudes.

    Parameters
    ----------
    amplitudes: Sequence[complex]
        Amplitudes del estado cuántico.
    backend: str
        Backend a utilizar: ``'qiskit'`` o ``'cirq'``.

    Returns
    -------
    Objeto circuito del backend seleccionado.
    """
    amplitudes = np.asarray(amplitudes, dtype=complex)
    nqubits = int(log2(len(amplitudes)))
    if backend == "qiskit":
        from qiskit import QuantumCircuit

        circuit = QuantumCircuit(nqubits)
        circuit.initialize(amplitudes, range(nqubits))
        return circuit
    elif backend == "cirq":
        import cirq

        qubits = cirq.LineQubit.range(nqubits)
        circuit = cirq.Circuit(cirq.StatePreparationChannel(amplitudes)(*qubits))
        return circuit
    else:
        raise ValueError(f"Backend no soportado: {backend}")
