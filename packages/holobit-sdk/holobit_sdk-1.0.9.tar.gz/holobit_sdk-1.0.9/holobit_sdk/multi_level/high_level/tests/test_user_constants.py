import unittest
from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler


class TestUserDefinedConstants(unittest.TestCase):
    def setUp(self):
        self.compiler = HoloLangCompiler()

    def test_constant_in_loop_and_operation(self):
        program = """
CONSTANTE ITER = 2
CREAR H1 (0)
PARA ITER {
    SUPERPOSICION H1
}
"""
        resultados = self.compiler.compilar_y_ejecutar(program)
        self.assertEqual(self.compiler.parser.constants["ITER"], 2)
        self.assertEqual(len(resultados[2:]), 2)


if __name__ == "__main__":
    unittest.main()
