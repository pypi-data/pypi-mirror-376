import unittest
from holobit_sdk.quantum_holocron.core.holocron import Holocron

executed = False

class Malicious:
    def __reduce__(self):
        def run():
            global executed
            executed = True
            return Malicious()
        return run, ()

    def __deepcopy__(self, memo):
        return Malicious()

class TestHolocronStateSafety(unittest.TestCase):
    def test_save_restore_does_not_execute_code(self):
        global executed
        executed = False
        h = Holocron()
        h.add_holobit("x", Malicious())
        h.save_state("s1")
        h.restore_state("s1")
        self.assertFalse(executed)

if __name__ == "__main__":
    unittest.main()
