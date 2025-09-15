import unittest
from holobit_sdk.assembler.parser import AssemblerParser
from holobit_sdk.quantum_holocron.instructions import AVAILABLE_OPERATIONS, QuantumInstruction


class TestParallelChannel(unittest.TestCase):
    def setUp(self):
        self.parser = AssemblerParser()
        AVAILABLE_OPERATIONS["INCREMENTAR"] = QuantumInstruction(
            "INCREMENTAR", lambda hbs: [hb + 1 for hb in hbs]
        )
        AVAILABLE_OPERATIONS["DOBLAR"] = QuantumInstruction(
            "DOBLAR", lambda hbs: [hb * 2 for hb in hbs]
        )
        self.parser.holocron.add_holobit("A", 1)
        self.parser.holocron.add_holobit("B", 2)
        self.parser.holocron.create_group("G1", ["A"])
        self.parser.holocron.create_group("G2", ["B"])

    def tearDown(self):
        AVAILABLE_OPERATIONS.pop("INCREMENTAR", None)
        AVAILABLE_OPERATIONS.pop("DOBLAR", None)

    def test_parallel_operations(self):
        result = self.parser.parse_line(
            "CANALIZAR_PARALELO {INCREMENTAR:G1, DOBLAR:G2}"
        )
        self.assertEqual(self.parser.holocron.groups["G1"], [2])
        self.assertEqual(self.parser.holocron.groups["G2"], [4])
        self.assertEqual(result, {"G1": [2], "G2": [4]})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
