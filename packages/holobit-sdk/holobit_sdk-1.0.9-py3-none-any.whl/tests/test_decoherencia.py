import random
import unittest

from holobit_sdk.multi_level.high_level.hololang_parser import HoloLangParser
from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler
from holobit_sdk.quantum_holocron.instructions import AVAILABLE_OPERATIONS


class TestDecoherenciaParser(unittest.TestCase):
    def setUp(self):
        self.parser = HoloLangParser()
        self.parser.holocron.add_holobit("H1", 0)
        self.parser.holocron.create_group("G1", ["H1"])

    def test_decoherencia_directa(self):
        random.seed(0)
        resultado = self.parser.interpretar("DECOHERENCIA G1")
        self.assertEqual(resultado, [1])
        self.assertEqual(self.parser.measurements["G1"], [1])

    def test_canalizar_decoherencia(self):
        self.parser.holocron.groups["G1"] = [1]
        random.seed(1)
        resultado = self.parser.interpretar("CANALIZAR {DECOHERENCIA} G1")
        self.assertEqual(resultado, [0])
        self.assertEqual(self.parser.holocron.groups["G1"], [0])

    def test_disponible_en_operaciones(self):
        self.assertIn("DECOHERENCIA", AVAILABLE_OPERATIONS)


class TestDecoherenciaCompiler(unittest.TestCase):
    def setUp(self):
        self.compiler = HoloLangCompiler()
        self.compiler.parser.holocron.add_holobit("H1", 0)
        self.compiler.parser.holocron.create_group("G1", ["H1"])

    def test_compiler_decoherencia(self):
        random.seed(0)
        resultado = self.compiler.compilar_y_ejecutar("DECOHERENCIA G1")
        self.assertEqual(resultado, [1])


if __name__ == "__main__":
    unittest.main()
