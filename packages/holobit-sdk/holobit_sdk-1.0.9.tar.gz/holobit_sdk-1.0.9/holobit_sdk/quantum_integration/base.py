from abc import ABC, abstractmethod


class QuantumAdapter(ABC):
    """Interfaz para adaptadores de backends cuánticos."""

    @abstractmethod
    def holobit_to_native(self, holobit):
        """Convierte un ``Holobit`` al formato nativo del backend."""

    @abstractmethod
    def execute(self, native_object):
        """Ejecuta el objeto nativo y devuelve el estado resultante."""
