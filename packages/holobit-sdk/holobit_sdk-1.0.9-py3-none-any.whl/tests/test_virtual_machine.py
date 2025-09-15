import os
import tempfile
from pathlib import Path
import unittest

from holobit_sdk.assembler.virtual_machine import AssemblerVM, InstructionLimitExceeded
from holobit_sdk.core.holobit import Holobit


class TestAssemblerVM(unittest.TestCase):
    def setUp(self):
        self.vm = AssemblerVM()

    def test_run_simple_program(self):
        program = [
            "CREAR Q1 (0.0, 0.1, 0.2)",
            "CREAR Q2 (0.3, 0.4, 0.5)",
            "CREAR Q3 (0.6, 0.7, 0.8)",
            "CREAR Q4 (0.9, 1.0, 1.1)",
            "CREAR Q5 (1.2, 1.3, 1.4)",
            "CREAR Q6 (1.5, 1.6, 1.7)",
            "CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}",
            "ROT H1 z 45",
        ]
        self.vm.run_program(program)
        self.assertIn("H1", self.vm.parser.holobits)
        holobit = self.vm.parser.holobits["H1"]
        self.assertIsInstance(holobit, Holobit)

    def test_alias_instruction(self):
        program = [
            "CREAR Q1 (0.0, 0.1, 0.2)",
            "CREAR Q2 (0.3, 0.4, 0.5)",
            "CREAR Q3 (0.6, 0.7, 0.8)",
            "CREAR Q4 (0.9, 1.0, 1.1)",
            "CREAR Q5 (1.2, 1.3, 1.4)",
            "CREAR Q6 (1.5, 1.6, 1.7)",
            "CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}",
            "ROTAR H1 z 45",
        ]
        self.vm.run_program(program)
        self.assertIn("H1", self.vm.parser.holobits)

    def test_instruction_limit(self):
        program = [
            "MIENTRAS LOOP",
            "FIN",
        ]
        self.vm.parser.measurements["LOOP"] = True
        with self.assertRaises(InstructionLimitExceeded):
            self.vm.run_program(program, max_instructions=10)


class TestRunFileSecurity(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        os.environ["HOLOBIT_VM_ROOT"] = str(self.root)
        self.addCleanup(os.environ.pop, "HOLOBIT_VM_ROOT", None)
        self.vm = AssemblerVM()

    def test_run_file_within_root(self):
        program_file = self.root / "prog.asm"
        program_file.write_text("CREAR Q1 (0.0, 0.0, 0.0)\n", encoding="utf-8")
        self.vm.run_file(str(program_file))
        self.assertIn("Q1", self.vm.parser.holobits)

    def test_run_file_path_traversal(self):
        outside_file = Path(self.temp_dir.name).parent / "outside.asm"
        outside_file.write_text("CREAR Q1 (0.0, 0.0, 0.0)\n", encoding="utf-8")
        self.addCleanup(outside_file.unlink)
        traversal_path = self.root / "../outside.asm"
        with self.assertRaises(PermissionError):
            self.vm.run_file(str(traversal_path))

    def test_run_file_symlink_outside(self):
        outside_file = Path(self.temp_dir.name).parent / "outside.asm"
        outside_file.write_text("CREAR Q1 (0.0, 0.0, 0.0)\n", encoding="utf-8")
        self.addCleanup(outside_file.unlink)
        link = self.root / "link"
        link.symlink_to(Path(self.temp_dir.name).parent)
        self.addCleanup(link.unlink)
        symlink_path = link / "outside.asm"
        with self.assertRaises(PermissionError):
            self.vm.run_file(str(symlink_path))


if __name__ == "__main__":
    unittest.main()
