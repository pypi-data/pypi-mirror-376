class QuantumInstruction:
    """
    Representa una instrucción cuántica genérica.
    """

    def __init__(self, name, func):
        self.name = name
        self.func = func

    def apply(self, holobits):
        """
        Aplica la instrucción a un conjunto de Holobits.
        """
        return self.func(holobits)


# Ejemplo de instrucciones
def quantum_flip(holobits):
    """
    Ejemplo de operación cuántica: invierte el estado de los Holobits.
    """
    return [~holobit for holobit in holobits]

FLIP = QuantumInstruction("FLIP", quantum_flip)


def quantum_swap(holobits):
    """Intercambia el estado de dos Holobits."""
    if len(holobits) != 2:
        raise ValueError("SWAP requiere exactamente dos Holobits")
    h1, h2 = holobits
    return [h2, h1]


SWAP = QuantumInstruction("SWAP", quantum_swap)
