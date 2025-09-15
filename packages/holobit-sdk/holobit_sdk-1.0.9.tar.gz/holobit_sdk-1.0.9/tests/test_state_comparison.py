import unittest
from holobit_sdk.assembler.virtual_machine import AssemblerVM


class TestStateComparison(unittest.TestCase):
    def test_compare_states_equal_si(self):
        vm = AssemblerVM()
        program = [
            "REGISTRAR A",
            "REGISTRAR B",
            "COMPARAR_ESTADO cmp A B",
            "SI cmp",
            "REGISTRAR C",
            "FIN",
        ]
        vm.run_program(program)
        self.assertTrue(vm.parser.measurements["cmp"] is True)
        self.assertIn("C", vm.parser.holocron._states)

    def test_compare_states_different_siq(self):
        vm = AssemblerVM()
        program = [
            "REGISTRAR A",
            "CREAR Q1 (0,0,0)",
            "CREAR Q2 (0,0,0)",
            "CREAR Q3 (0,0,0)",
            "CREAR Q4 (0,0,0)",
            "CREAR Q5 (0,0,0)",
            "CREAR Q6 (0,0,0)",
            "CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}",
            "REGISTRAR B",
            "COMPARAR_ESTADO cmp A B",
            "SIQ cmp",
            "REGISTRAR C",
            "ELSEQ",
            "REGISTRAR D",
            "FIN",
        ]
        vm.run_program(program)
        self.assertIsInstance(vm.parser.measurements["cmp"], dict)
        self.assertNotIn("C", vm.parser.holocron._states)
        self.assertIn("D", vm.parser.holocron._states)


if __name__ == "__main__":
    unittest.main()
