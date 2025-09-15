import unittest
import random

from holobit_sdk.quantum_holocron.core.holocron import Holocron
from holobit_sdk.assembler.virtual_machine import AssemblerVM


class TestSynchronizeMeasurements(unittest.TestCase):
    def setUp(self):
        self.holocron = Holocron()
        for idx in range(1, 5):
            self.holocron.add_holobit(f"H{idx}", idx)
        self.holocron.create_group("G1", ["H1", "H2"])
        self.holocron.create_group("G2", ["H3", "H4"])

    def test_holocron_method(self):
        random.seed(0)
        resultados = self.holocron.synchronize_measurements(["G1", "G2"])
        self.assertEqual(resultados["G1"], resultados["G2"])

    def test_vm_instruction(self):
        vm = AssemblerVM()
        vm.holocron = self.holocron
        vm.parser.holocron = self.holocron
        vm.parser.groups = self.holocron.groups
        vm.parser.holobits.update(self.holocron.holobits)
        random.seed(1)
        vm.execute_instruction("SINCRONIZAR", "G1", "G2")
        self.assertEqual(
            vm.parser.measurements["G1"], vm.parser.measurements["G2"]
        )


if __name__ == "__main__":
    unittest.main()
