import unittest
from holobit_sdk.quantum_holocron.core.holocron import Holocron
from holobit_sdk.quantum_holocron.instructions.assembler_instructions import FLIP
from holobit_sdk.assembler.virtual_machine import AssemblerVM


class TestHolocron(unittest.TestCase):
    def setUp(self):
        self.holocron = Holocron()
        self.holocron.add_holobit("H1", 0b01)  # Representación binaria
        self.holocron.add_holobit("H2", 0b10)
        self.vm = AssemblerVM()
        self.vm.holocron = self.holocron
        self.vm.parser.holobits.update(self.holocron.holobits)

    def test_add_holobit(self):
        self.holocron.add_holobit("H3", 0b11)
        self.assertIn("H3", self.holocron.holobits)

    def test_create_group(self):
        self.holocron.create_group("G1", ["H1", "H2"])
        self.assertIn("G1", self.holocron.groups)

    def test_quantum_operation(self):
        self.holocron.create_group("G1", ["H1", "H2"])
        result = self.holocron.execute_quantum_operation(FLIP, "G1")
        self.assertEqual(result, [~0b01, ~0b10])

    def test_group_instruction(self):
        self.vm.execute_instruction("GRUPO", "G1", "H1", "H2")
        self.assertIn("G1", self.holocron.groups)
        result = self.holocron.execute_quantum_operation(FLIP, "G1")
        self.assertEqual(result, [~0b01, ~0b10])


if __name__ == "__main__":
    unittest.main()
