import unittest
from holobit_sdk.assembler.virtual_machine import AssemblerVM, InstructionLimitExceeded


class TestInstructionLimitLoop(unittest.TestCase):
    def test_recursive_call_limit(self):
        program = [
            "FUNC LOOP",
            "CALL LOOP",
            "ENDFUNC",
            "CALL LOOP",
        ]
        vm = AssemblerVM()
        with self.assertRaises(InstructionLimitExceeded):
            vm.run_program(program, max_instructions=20)


if __name__ == "__main__":
    unittest.main()
