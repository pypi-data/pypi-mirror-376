import unittest

from holobit_sdk.assembler.parser import AssemblerParser
from holobit_sdk.quantum_holocron.quantum_algorithm import (
    TELETRANSPORTAR,
    COLAPSAR,
    FUSIONAR,
)


class TestNewQuantumOperations(unittest.TestCase):
    def setUp(self):
        self.parser = AssemblerParser()
        self.holocron = self.parser.holocron
        self.holocron.add_holobit("H1", 1)
        self.holocron.add_holobit("H2", 0)
        self.holocron.create_group("G1", ["H1"])
        self.holocron.create_group("G2", ["H2"])
        self.holocron.create_group("G12", ["H1", "H2"])

    def test_teletransportar(self):
        resultado = self.holocron.execute_quantum_operation(TELETRANSPORTAR, "G1")
        self.assertEqual(resultado, [1])

    def test_colapsar(self):
        resultado = self.holocron.execute_quantum_operation(COLAPSAR, "G1")
        self.assertEqual(resultado, [0])

    def test_fusionar(self):
        resultado = self.holocron.execute_quantum_operation(FUSIONAR, "G12")
        self.assertEqual(resultado, [1])

    def test_canalizar_teletransportar(self):
        resultado = self.parser.parse_line("CANALIZAR TELETRANSPORTAR G1")
        self.assertEqual(resultado, [1])

    def test_canalizar_colapsar(self):
        resultado = self.parser.parse_line("CANALIZAR COLAPSAR G1")
        self.assertEqual(resultado, [0])

    def test_canalizar_fusionar(self):
        resultado = self.parser.parse_line("CANALIZAR FUSIONAR G1 G2")
        self.assertEqual(resultado, [1])


if __name__ == "__main__":
    unittest.main()
