import numpy as np
import qutip as qt

from .base import QuantumAdapter


class QutipAdapter(QuantumAdapter):
    """Adaptador para ejecutar Holobits usando QuTiP."""

    def holobit_to_native(self, holobit):
        """Convierte un ``Holobit`` en un estado ``qutip.Qobj``."""
        quarks = holobit.quarks + holobit.antiquarks
        states = []
        for quark in quarks:
            state = np.asarray(quark.estado, dtype=complex)
            norm = np.linalg.norm(state)
            if not np.isclose(norm, 1.0):
                state = state / norm
            states.append(qt.Qobj(state, dims=[[2], [1]]))
        return qt.tensor(states)

    def execute(self, state):
        """Devuelve directamente el estado ``Qobj`` recibido."""
        return state
