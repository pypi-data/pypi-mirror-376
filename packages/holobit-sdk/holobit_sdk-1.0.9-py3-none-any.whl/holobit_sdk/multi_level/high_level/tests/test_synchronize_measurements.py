import unittest
import random

from holobit_sdk.multi_level.high_level.hololang_parser import HoloLangParser
from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler


class TestSynchronizeMeasurementsHighLevel(unittest.TestCase):
    def setUp(self):
        self.parser = HoloLangParser()
        for idx in range(1, 5):
            self.parser.interpretar(f"CREAR H{idx} (0.1, 0.2, 0.3)")
        self.parser.interpretar("CREAR_GRUPO G1 (H1, H2)")
        self.parser.interpretar("CREAR_GRUPO G2 (H3, H4)")

    def test_parser_synchronize(self):
        random.seed(0)
        resultados = self.parser.interpretar("SINCRONIZAR G1 G2")
        self.assertEqual(resultados["G1"], resultados["G2"])

    def test_compiler_synchronize(self):
        compiler = HoloLangCompiler()
        for idx in range(1, 5):
            compiler.compilar_y_ejecutar(f"CREAR H{idx} (0.1, 0.2, 0.3)")
        compiler.compilar_y_ejecutar("CREAR_GRUPO G1 (H1, H2)")
        compiler.compilar_y_ejecutar("CREAR_GRUPO G2 (H3, H4)")
        random.seed(1)
        resultados = compiler.compilar_y_ejecutar("SINCRONIZAR G1 G2")
        self.assertEqual(resultados["G1"], resultados["G2"])
        self.assertEqual(
            compiler.parser.measurements["G1"], compiler.parser.measurements["G2"]
        )


if __name__ == "__main__":
    unittest.main()
