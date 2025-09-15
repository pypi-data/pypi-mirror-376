import random
import unittest

from holobit_sdk.multi_level.high_level.hololang_parser import HoloLangParser
from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler


class TestGroupOperations(unittest.TestCase):
    """Validación de creación y uso de grupos cuánticos."""

    def setUp(self):
        self.parser = HoloLangParser()
        self.compiler = HoloLangCompiler()
        # Recursos para el parser
        self.parser.interpretar("CREAR H1 (0.1, 0.2, 0.3)")
        self.parser.interpretar("CREAR H2 (0.4, 0.5, 0.6)")
        self.parser.interpretar("CREAR H3 (0.7, 0.8, 0.9)")
        self.parser.interpretar("CREAR H4 (1.0, 1.1, 1.2)")
        self.parser.interpretar("CREAR_GRUPO G1 (H1, H2)")
        self.parser.interpretar("CREAR_GRUPO G2 (H3, H4)")
        # Recursos para el compilador
        self.compiler.compilar_y_ejecutar("CREAR H1 (0.1, 0.2, 0.3)")
        self.compiler.compilar_y_ejecutar("CREAR H2 (0.4, 0.5, 0.6)")
        self.compiler.compilar_y_ejecutar("CREAR_GRUPO G1 (H1, H2)")
        self.compiler.compilar_y_ejecutar("CREAR H3 (0.7, 0.8, 0.9)")
        self.compiler.compilar_y_ejecutar("CREAR H4 (1.0, 1.1, 1.2)")
        self.compiler.compilar_y_ejecutar("CREAR_GRUPO G2 (H3, H4)")

    def test_aplicar_grupo_parser(self):
        random.seed(0)
        resultado = self.parser.interpretar("APLICAR_GRUPO SUPERPOSICION G1")
        self.assertIn(resultado[0], [0, 1])
        random.seed(1)
        medicion = self.parser.interpretar("APLICAR_GRUPO MEDIR G1")
        self.assertIn(medicion[0], [0, 1])

    def test_aplicar_grupo_compiler(self):
        random.seed(0)
        resultado = self.compiler.compilar_y_ejecutar("APLICAR_GRUPO SUPERPOSICION G2")
        self.assertIn(resultado[0], [0, 1])
        random.seed(1)
        medicion = self.compiler.compilar_y_ejecutar("APLICAR_GRUPO MEDIR G2")
        self.assertIn(medicion[0], [0, 1])

    def test_fusionar_dividir_parser(self):
        self.parser.interpretar("FUSIONAR_GRUPO G3 (G1, G2)")
        random.seed(0)
        resultado = self.parser.interpretar("APLICAR_GRUPO SUPERPOSICION G3")
        self.assertEqual(len(resultado), 4)
        self.parser.interpretar("DIVIDIR_GRUPO G3 G2 (H3, H4)")
        random.seed(1)
        medicion = self.parser.interpretar("APLICAR_GRUPO MEDIR G2")
        self.assertEqual(len(medicion), 2)
        entrelazado = self.parser.interpretar("APLICAR_GRUPO ENTRELAZAR G2")
        self.assertEqual(len(entrelazado), 1)

    def test_fusionar_dividir_compiler(self):
        self.compiler.compilar_y_ejecutar("FUSIONAR_GRUPO G3 (G1, G2)")
        random.seed(0)
        resultado = self.compiler.compilar_y_ejecutar("APLICAR_GRUPO SUPERPOSICION G3")
        self.assertEqual(len(resultado), 4)
        self.compiler.compilar_y_ejecutar("DIVIDIR_GRUPO G3 G2 (H3, H4)")
        random.seed(1)
        medicion = self.compiler.compilar_y_ejecutar("APLICAR_GRUPO MEDIR G2")
        self.assertEqual(len(medicion), 2)
        entrelazado = self.compiler.compilar_y_ejecutar("APLICAR_GRUPO ENTRELAZAR G2")
        self.assertEqual(len(entrelazado), 1)


if __name__ == "__main__":
    unittest.main()
