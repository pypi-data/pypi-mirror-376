import unittest
from holobit_sdk.assembler.virtual_machine import AssemblerVM
from holobit_sdk.core.holobit import Holobit


class TestFunctions(unittest.TestCase):
    def setUp(self):
        self.vm = AssemblerVM()

    def test_function_call(self):
        program = [
            "FUNC construir",
            "CREAR Q1 (0.0, 0.1, 0.2)",
            "CREAR Q2 (0.3, 0.4, 0.5)",
            "CREAR Q3 (0.6, 0.7, 0.8)",
            "CREAR Q4 (0.9, 1.0, 1.1)",
            "CREAR Q5 (1.2, 1.3, 1.4)",
            "CREAR Q6 (1.5, 1.6, 1.7)",
            "CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}",
            "ENDFUNC",
            "CALL construir",
            "ROT H1 z 45",
        ]
        self.vm.run_program(program)
        self.assertIn("H1", self.vm.parser.holobits)
        self.assertIsInstance(self.vm.parser.holobits["H1"], Holobit)


if __name__ == "__main__":
    unittest.main()
