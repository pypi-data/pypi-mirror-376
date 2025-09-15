import unittest
import math
from holobit_sdk.multi_level.high_level.hololang_parser import HoloLangParser
from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler


class TestConstantsAndComments(unittest.TestCase):
    def setUp(self):
        self.parser = HoloLangParser()
        self.compiler = HoloLangCompiler()

    def test_constants_in_variable_creation(self):
        res = self.parser.interpretar("CREAR C1 (PI, TAU/2)")
        self.assertIn("Variable C1", res)
        self.assertAlmostEqual(self.parser.variables["C1"][0], math.pi)
        self.assertAlmostEqual(self.parser.variables["C1"][1], math.tau / 2)

    def test_comments_are_ignored(self):
        codigo = """
        # comentario inicial
        CREAR H1 (0.1, 0.2) // comentario
        IMPRIMIR H1 # otro
        """
        resultados = self.compiler.compilar_y_ejecutar(codigo)
        self.assertIn("Variable H1 creada con valores (0.1, 0.2)", resultados)
        self.assertIn("H1 = (0.1, 0.2)", resultados)

    def test_constants_in_control_flow(self):
        self.compiler.compilar_y_ejecutar("CREAR V1 (0)")
        programa = """
PARA TAU/PI {
IMPRIMIR V1
}
"""
        resultados = self.compiler.compilar_y_ejecutar(programa)
        self.assertEqual(len(resultados), 2)


if __name__ == "__main__":
    unittest.main()
