import unittest
from unittest.mock import patch
import numpy as np

from holobit_sdk.assembler.virtual_machine import AssemblerVM


def _build_vm():
    vm = AssemblerVM()
    for i in range(1, 7):
        vm.parser.parse_line(f"CREAR Q{i} ({i * 0.1}, {i * 0.2}, {i * 0.3})")
    vm.parser.parse_line("CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}")
    return vm


class TestControlFlow(unittest.TestCase):
    def test_si_branch(self):
        vm = _build_vm()
        program = [
            "MEDIR H1",
            "SI H1",
            "ROT H1 z 45",
            "SINO",
            "ROT H1 z 180",
            "FIN",
        ]
        with patch("holobit_sdk.quantum_holocron.quantum_algorithm.random.choice", return_value=1):
            vm.run_program(program)
        q = vm.parser.holobits["H1"].quarks[0]
        expected_y = 0.1 * np.sin(np.deg2rad(45)) + 0.2 * np.cos(np.deg2rad(45))
        self.assertAlmostEqual(q.posicion[1], expected_y, places=5)

    def test_sino_branch(self):
        vm = _build_vm()
        program = [
            "MEDIR H1",
            "SI H1",
            "ROT H1 z 45",
            "SINO",
            "ROT H1 z 180",
            "FIN",
        ]
        with patch("holobit_sdk.quantum_holocron.quantum_algorithm.random.choice", return_value=0):
            vm.run_program(program)
        q = vm.parser.holobits["H1"].quarks[0]
        self.assertAlmostEqual(q.posicion[1], -0.2, places=5)

    def test_siq_elseq_branch(self):
        vm = _build_vm()
        program = [
            "MEDIR H1",
            "SIQ H1 >= 1",
            "ROT H1 z 45",
            "ELSEQ",
            "ROT H1 z 180",
            "FIN",
        ]
        with patch("holobit_sdk.quantum_holocron.quantum_algorithm.random.choice", return_value=1):
            vm.run_program(program)
        q = vm.parser.holobits["H1"].quarks[0]
        expected_y = 0.1 * np.sin(np.deg2rad(45)) + 0.2 * np.cos(np.deg2rad(45))
        self.assertAlmostEqual(q.posicion[1], expected_y, places=5)

        vm = _build_vm()
        with patch("holobit_sdk.quantum_holocron.quantum_algorithm.random.choice", return_value=0):
            vm.run_program(program)
        q = vm.parser.holobits["H1"].quarks[0]
        self.assertAlmostEqual(q.posicion[1], -0.2, places=5)

    def test_siq_compound_expression(self):
        vm = _build_vm()
        vm.parser.measurements["G1"] = 1
        vm.parser.measurements["G2"] = 1
        program = [
            "SIQ (G1 + G2) > 1",
            "ROT H1 z 45",
            "ELSEQ",
            "ROT H1 z 180",
            "FIN",
        ]
        vm.run_program(program)
        q = vm.parser.holobits["H1"].quarks[0]
        expected_y = 0.1 * np.sin(np.deg2rad(45)) + 0.2 * np.cos(np.deg2rad(45))
        self.assertAlmostEqual(q.posicion[1], expected_y, places=5)

        vm = _build_vm()
        vm.parser.measurements["G1"] = 0
        vm.parser.measurements["G2"] = 0
        vm.run_program(program)
        q = vm.parser.holobits["H1"].quarks[0]
        self.assertAlmostEqual(q.posicion[1], -0.2, places=5)

    def test_siq_rejects_malicious_expression(self):
        vm = _build_vm()
        program = [
            "SIQ __import__('os').system('echo hack')",
            "ROT H1 z 45",
            "ELSEQ",
            "ROT H1 z 180",
            "FIN",
        ]
        vm.run_program(program)
        q = vm.parser.holobits["H1"].quarks[0]
        self.assertAlmostEqual(q.posicion[1], -0.2, places=5)

    def test_mientras_loop(self):
        vm = _build_vm()
        program = [
            "MEDIR H1",
            "MIENTRAS H1",
            "ROT H1 z 45",
            "MEDIR H1",
            "FIN",
        ]
        with patch(
            "holobit_sdk.quantum_holocron.quantum_algorithm.random.choice",
            side_effect=[1, 1, 0],
        ):
            vm.run_program(program)
        q = vm.parser.holobits["H1"].quarks[0]
        expected_x = 0.1 * np.cos(np.deg2rad(90)) - 0.2 * np.sin(np.deg2rad(90))
        self.assertAlmostEqual(q.posicion[0], expected_x, places=5)

    def test_para_loop(self):
        vm = _build_vm()
        program = [
            "PARA 3",
            "ROT H1 z 30",
            "FIN",
        ]
        vm.run_program(program)
        q = vm.parser.holobits["H1"].quarks[0]
        expected_x = 0.1 * np.cos(np.deg2rad(90)) - 0.2 * np.sin(np.deg2rad(90))
        self.assertAlmostEqual(q.posicion[0], expected_x, places=5)

    def test_caso_selection(self):
        vm = _build_vm()
        program = [
            "MEDIR H1",
            "CASO H1",
            "CUANDO 0",
            "ROT H1 z 90",
            "CUANDO 1",
            "ROT H1 z 180",
            "OTRO",
            "ROT H1 z 270",
            "FINCASO",
        ]
        with patch("holobit_sdk.quantum_holocron.quantum_algorithm.random.choice", return_value=0):
            vm.run_program(program)
        q = vm.parser.holobits["H1"].quarks[0]
        expected_x = 0.1 * np.cos(np.deg2rad(90)) - 0.2 * np.sin(np.deg2rad(90))
        self.assertAlmostEqual(q.posicion[0], expected_x, places=5)

    def test_caso_default(self):
        vm = _build_vm()
        program = [
            "MEDIR H1",
            "CASO H1",
            "CUANDO 0",
            "ROT H1 z 90",
            "CUANDO 1",
            "ROT H1 z 180",
            "OTRO",
            "ROT H1 z 270",
            "FINCASO",
        ]
        with patch("holobit_sdk.quantum_holocron.quantum_algorithm.random.choice", return_value=2):
            vm.run_program(program)
        q = vm.parser.holobits["H1"].quarks[0]
        expected_x = 0.1 * np.cos(np.deg2rad(270)) - 0.2 * np.sin(np.deg2rad(270))
        self.assertAlmostEqual(q.posicion[0], expected_x, places=5)

    def test_parag_iteration(self):
        vm = AssemblerVM()
        # Crear quarks y holobits
        for i in range(1, 13):
            vm.parser.parse_line(
                f"CREAR Q{i} ({i * 0.1}, {i * 0.2}, {i * 0.3})"
            )
        vm.parser.parse_line("CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}")
        vm.parser.parse_line("CREAR H2 {Q7, Q8, Q9, Q10, Q11, Q12}")
        vm.parser.parse_line("GRUPO G1 = {H1, H2}")

        program = [
            "PARAG G1",
            "ROT $ z 90",
            "FIN",
        ]

        vm.run_program(program)

        q1 = vm.parser.holobits["H1"].quarks[0]
        q2 = vm.parser.holobits["H2"].quarks[0]
        expected_x1 = 0.1 * np.cos(np.deg2rad(90)) - 0.2 * np.sin(np.deg2rad(90))
        expected_x2 = 0.7 * np.cos(np.deg2rad(90)) - 1.4 * np.sin(np.deg2rad(90))
        self.assertAlmostEqual(q1.posicion[0], expected_x1, places=5)
        self.assertAlmostEqual(q2.posicion[0], expected_x2, places=5)


if __name__ == "__main__":
    unittest.main()
