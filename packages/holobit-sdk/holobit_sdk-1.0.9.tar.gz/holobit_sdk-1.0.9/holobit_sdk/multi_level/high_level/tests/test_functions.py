import unittest
import random
from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler


class TestHoloLangFunctions(unittest.TestCase):
    def setUp(self):
        self.compiler = HoloLangCompiler()

    def test_definir_y_llamar_funcion(self):
        self.compiler.compilar_y_ejecutar("CREAR H1 (0.1, 0.2, 0.3)")
        self.compiler.compilar_y_ejecutar("CREAR_ESTRUCTURA G1 {H1}")
        codigo = """
FUNCION aplicar(h) {
    SUPERPOSICION h
    MEDIR h
}
"""
        self.compiler.compilar_y_ejecutar(codigo)
        self.assertIn("aplicar", self.compiler.parser.functions)
        random.seed(0)
        resultado = self.compiler.compilar_y_ejecutar("LLAMAR aplicar(G1)")
        self.assertEqual(len(resultado), 2)
        for r in resultado:
            self.assertIn(r, [0, 1])


if __name__ == "__main__":
    unittest.main()
