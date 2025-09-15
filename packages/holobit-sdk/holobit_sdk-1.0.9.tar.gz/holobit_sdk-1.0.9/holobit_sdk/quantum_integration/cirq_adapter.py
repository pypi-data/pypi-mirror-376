import numpy as np
import cirq

from .base import QuantumAdapter


class CirqAdapter(QuantumAdapter):
    """Adaptador para ejecutar Holobits usando Cirq."""

    def holobit_to_native(self, holobit):
        """Convierte un ``Holobit`` en un ``cirq.Circuit``."""
        quarks = holobit.quarks + holobit.antiquarks
        qubits = cirq.LineQubit.range(len(quarks))
        circuit = cirq.Circuit()
        for qubit, quark in zip(qubits, quarks):
            state = np.asarray(quark.estado, dtype=complex)
            norm = np.linalg.norm(state)
            if not np.isclose(norm, 1.0):
                state = state / norm
            circuit.append(cirq.StatePreparationChannel(state).on(qubit))
        return circuit

    def execute(self, circuit):
        """Ejecuta el ``Circuit`` y devuelve el estado resultante."""
        simulator = cirq.Simulator()
        result = simulator.simulate(circuit)
        return result.final_state_vector
