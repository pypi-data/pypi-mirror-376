import numpy as np
import pennylane as qml

from .base import QuantumAdapter


class PennyLaneAdapter(QuantumAdapter):
    """Adaptador para ejecutar Holobits usando PennyLane."""

    def holobit_to_native(self, holobit):
        """Convierte un ``Holobit`` en un ``QNode`` de PennyLane."""
        quarks = holobit.quarks + holobit.antiquarks
        num_qubits = len(quarks)
        dev = qml.device("default.qubit", wires=num_qubits)

        @qml.qnode(dev)
        def circuit():
            for index, quark in enumerate(quarks):
                state = np.asarray(quark.estado, dtype=complex)
                norm = np.linalg.norm(state)
                if not np.isclose(norm, 1.0):
                    state = state / norm
                qml.StatePrep(state, wires=index)
            return qml.state()

        return circuit

    def execute(self, qnode):
        """Ejecuta el ``QNode`` y devuelve el estado resultante."""
        return qnode()
