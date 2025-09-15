import unittest
from holobit_sdk.assembler.parser import AssemblerParser


class TestGroupPattern(unittest.TestCase):
    def setUp(self):
        self.parser = AssemblerParser()
        # Crear quarks base
        for i in range(1, 7):
            self.parser.parse_line(f"CREAR Q{i} ({i*0.1}, {i*0.2}, {i*0.3})")
        # Crear holobits
        self.parser.parse_line("CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}")
        self.parser.parse_line("CREAR H2 {Q1, Q2, Q3, Q4, Q5, Q6}")
        self.parser.parse_line("CREAR HX {Q1, Q2, Q3, Q4, Q5, Q6}")

    def test_group_by_pattern(self):
        self.parser.parse_line("AGRUPAR G /H[0-9]/")
        group = self.parser.holocron.groups["G"]
        expected = {self.parser.holobits["H1"], self.parser.holobits["H2"]}
        self.assertEqual(set(group), expected)
        self.assertNotIn(self.parser.holobits["HX"], group)


if __name__ == "__main__":
    unittest.main()
