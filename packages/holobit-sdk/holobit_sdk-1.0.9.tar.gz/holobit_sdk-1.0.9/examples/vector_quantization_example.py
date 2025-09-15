"""Ejemplo de cuantización y codificación cuántica de vectores."""

from holobit_sdk.multi_level.medium_level.vector_processor import VectorProcessor

vector = [1, 2, 3, 4, 5]

# Obtener amplitudes normalizadas usando SVD
amplitudes = VectorProcessor.to_quantum_state(vector, reduction="svd")
print("Amplitudes normalizadas:", amplitudes)

# Generar un circuito de Qiskit si la librería está disponible
try:
    circuito = VectorProcessor.to_quantum_state(vector, reduction="svd", backend="qiskit")
    print("Circuito Qiskit:\n", circuito)
except Exception as exc:  # pragma: no cover - dependencias opcionales
    print("No se pudo generar circuito Qiskit:", exc)
