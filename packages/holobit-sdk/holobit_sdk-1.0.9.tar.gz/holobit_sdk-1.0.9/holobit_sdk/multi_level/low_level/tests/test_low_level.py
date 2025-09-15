import unittest
from holobit_sdk.multi_level.low_level.memory_manager import MemoryManager
from holobit_sdk.multi_level.low_level.low_level_api import LowLevelAPI
from holobit_sdk.multi_level.low_level.execution_unit import ExecutionUnit


class TestLowLevel(unittest.TestCase):
    """
    Pruebas unitarias para el Nivel Bajo del SDK Holobit.
    """

    def setUp(self):
        self.memory = MemoryManager()
        self.api = LowLevelAPI()
        self.executor = ExecutionUnit()

    def test_allocate_holobit(self):
        """ Prueba la asignación de un Holobit en la memoria. """
        resultado = self.api.ejecutar_comando("ALLOCATE", "H1", 0.1, 0.2, 0.3)
        self.assertEqual(resultado, "Holobit H1 asignado en (0.1, 0.2, 0.3).")

    def test_get_position_holobit(self):
        """ Prueba la obtención de la posición de un Holobit. """
        self.api.ejecutar_comando("ALLOCATE", "H1", 0.1, 0.2, 0.3)
        resultado = self.api.ejecutar_comando("GET_POSITION", "H1")
        self.assertEqual(resultado, "Posición de H1: (0.1, 0.2, 0.3)")

    def test_deallocate_holobit(self):
        """ Prueba la liberación de un Holobit en la memoria. """
        self.api.ejecutar_comando("ALLOCATE", "H1", 0.1, 0.2, 0.3)
        resultado = self.api.ejecutar_comando("DEALLOCATE", "H1")
        self.assertEqual(resultado, "Holobit H1 liberado.")

    def test_execute_instruction_allocate(self):
        """ Prueba la ejecución de una instrucción ensamblador para asignar un Holobit. """
        resultado = self.executor.ejecutar_instruccion("ALLOCATE H2 0.4 0.5 0.6")
        self.assertEqual(resultado, "Holobit H2 asignado en (0.4, 0.5, 0.6).")

    def test_execute_instruction_get_position(self):
        """ Prueba la ejecución de una instrucción ensamblador para obtener la posición de un Holobit. """
        self.executor.ejecutar_instruccion("ALLOCATE H3 0.7 0.8 0.9")
        resultado = self.executor.ejecutar_instruccion("GET_POSITION H3")
        self.assertEqual(resultado, "Posición de H3: (0.7, 0.8, 0.9)")

    def test_execute_instruction_deallocate(self):
        """ Prueba la ejecución de una instrucción ensamblador para liberar un Holobit. """
        self.executor.ejecutar_instruccion("ALLOCATE H4 1.0 1.1 1.2")
        resultado = self.executor.ejecutar_instruccion("DEALLOCATE H4")
        self.assertEqual(resultado, "Holobit H4 liberado.")

    def test_fractal_memory_allocation(self):
        """Verifica la asignación y consulta directa en el árbol fractal."""
        mm = MemoryManager()
        mm.allocate("X1", (0.1, 0.1, 0.1))
        mm.allocate("X2", (0.9, 0.9, 0.9))
        self.assertEqual(mm.get_position("X1"), (0.1, 0.1, 0.1))
        self.assertEqual(mm.get_position("X2"), (0.9, 0.9, 0.9))
        mm.deallocate("X1")
        with self.assertRaises(KeyError):
            mm.get_position("X1")


if __name__ == "__main__":
    unittest.main()
