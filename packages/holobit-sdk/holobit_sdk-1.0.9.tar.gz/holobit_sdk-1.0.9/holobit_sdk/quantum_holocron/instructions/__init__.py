"""Registro central de instrucciones cuánticas disponibles."""

from importlib import import_module, reload

from . import assembler_instructions
from .assembler_instructions import QuantumInstruction


AVAILABLE_OPERATIONS = {
    name: obj
    for name, obj in vars(assembler_instructions).items()
    if isinstance(obj, QuantumInstruction)
}

quantum_algorithm = reload(
    import_module("holobit_sdk.quantum_holocron.quantum_algorithm")
)

AVAILABLE_OPERATIONS.update(
    {
        name: obj
        for name, obj in vars(quantum_algorithm).items()
        if isinstance(obj, QuantumInstruction)
    }
)

# Exponer las operaciones para importación directa
globals().update(AVAILABLE_OPERATIONS)

__all__ = ["QuantumInstruction", "AVAILABLE_OPERATIONS"] + list(
    AVAILABLE_OPERATIONS.keys()
)
