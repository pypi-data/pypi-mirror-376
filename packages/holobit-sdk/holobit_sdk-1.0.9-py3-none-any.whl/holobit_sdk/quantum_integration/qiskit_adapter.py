import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from .base import QuantumAdapter


class QiskitAdapter(QuantumAdapter):
    """Adaptador para ejecutar Holobits usando Qiskit."""

    def holobit_to_native(self, holobit):
        """Convierte un ``Holobit`` en un ``QuantumCircuit`` de Qiskit."""
        quarks = holobit.quarks + holobit.antiquarks
        circuit = QuantumCircuit(len(quarks))
        for index, quark in enumerate(quarks):
            state = np.asarray(quark.estado, dtype=complex)
            norm = np.linalg.norm(state)
            if not np.isclose(norm, 1.0):
                state = state / norm
            circuit.initialize(state, index)
        return circuit

    def execute(self, circuit):
        """Ejecuta el circuito y devuelve el ``Statevector`` resultante."""
        return Statevector.from_instruction(circuit)
