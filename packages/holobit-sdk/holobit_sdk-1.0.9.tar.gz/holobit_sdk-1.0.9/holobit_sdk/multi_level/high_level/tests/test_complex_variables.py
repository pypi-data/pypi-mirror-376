import unittest
from holobit_sdk.multi_level.high_level.hololang_parser import HoloLangParser
from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler


class TestComplexVariables(unittest.TestCase):
    def setUp(self):
        self.parser = HoloLangParser()
        self.compiler = HoloLangCompiler()

    def test_parser_crea_complex(self):
        resultado = self.parser.interpretar("CREAR Z1 (1+2i, 3-4i)")
        self.assertEqual(
            resultado,
            "Variable Z1 creada con valores ((1+2j), (3-4j))",
        )
        self.assertEqual(
            self.parser.variables["Z1"],
            (complex(1, 2), complex(3, -4)),
        )

    def test_compiler_imprime_complex(self):
        self.compiler.compilar_y_ejecutar("CREAR Z2 (5+6i)")
        resultado = self.compiler.compilar_y_ejecutar("IMPRIMIR Z2")
        self.assertEqual(resultado, "Z2 = ((5+6j),)")


if __name__ == "__main__":
    unittest.main()
