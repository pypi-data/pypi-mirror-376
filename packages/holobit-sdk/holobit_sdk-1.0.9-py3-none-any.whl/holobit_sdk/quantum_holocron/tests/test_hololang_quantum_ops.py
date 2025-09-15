import random
import unittest

from holobit_sdk.assembler.parser import AssemblerParser


class TestHololangQuantumOps(unittest.TestCase):
    """Pruebas de superposición, medición y entrelazamiento desde Hololang."""

    def setUp(self):
        self.parser = AssemblerParser()
        # Crear quarks y dos Holobits de ejemplo
        for i in range(1, 13):
            self.parser.parse_line(
                f"CREAR Q{i} ({i * 0.1}, {i * 0.2}, {i * 0.3})"
            )
        self.parser.parse_line("CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}")
        self.parser.parse_line("CREAR H2 {Q7, Q8, Q9, Q10, Q11, Q12}")

    def test_superposicion(self):
        random.seed(0)
        self.parser.parse_line("SUPERPOS H1 H2")
        self.assertIn(self.parser.measurements["H1"], [0, 1])
        self.assertIn(self.parser.measurements["H2"], [0, 1])

    def test_medicion(self):
        random.seed(1)
        self.parser.parse_line("MEDIR H1 H2")
        self.assertIn(self.parser.measurements["H1"], [0, 1])
        self.assertIn(self.parser.measurements["H2"], [0, 1])

    def test_entangle(self):
        resultado = self.parser.parse_line("ENTANGLE H1 H2")
        self.assertIn((self.parser.holobits["H1"], self.parser.holobits["H2"]), resultado)

    def test_desentangle(self):
        self.parser.parse_line("ENTANGLE H1 H2")
        resultado = self.parser.parse_line("DESENTANGLE H1 H2")
        self.assertEqual(resultado, [])


if __name__ == "__main__":
    unittest.main()

