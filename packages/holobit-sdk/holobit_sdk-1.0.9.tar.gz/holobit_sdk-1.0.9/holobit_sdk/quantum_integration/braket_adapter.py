import numpy as np
from braket.circuits import Circuit
from braket.devices import LocalSimulator

from .base import QuantumAdapter


class BraketAdapter(QuantumAdapter):
    """Adaptador para ejecutar Holobits usando AWS Braket."""

    def holobit_to_native(self, holobit):
        """Convierte un ``Holobit`` en un ``braket.circuits.Circuit``."""
        quarks = holobit.quarks + holobit.antiquarks
        circuit = Circuit()
        for index, quark in enumerate(quarks):
            state = np.asarray(quark.estado, dtype=complex)
            norm = np.linalg.norm(state)
            if not np.isclose(norm, 1.0):
                state = state / norm
            circuit.prepare_state(state, [index])
        return circuit

    def execute(self, circuit):
        """Ejecuta el circuito y devuelve el estado resultante."""
        device = LocalSimulator()
        result = device.run(circuit).result()
        return result.state_vector
