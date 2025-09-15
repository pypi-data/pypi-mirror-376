import unittest

from holobit_sdk.quantum_holocron.core.holocron import Holocron
from holobit_sdk.quantum_holocron.entanglement import (
    ENTANGLE,
    DESENTANGLE,
    entangle_groups,
    entangle_holobits,
    desentangle_holobits,
)


class TestEntanglement(unittest.TestCase):
    def setUp(self):
        self.holocron = Holocron()
        self.holocron.add_holobit("H1", 0b01)
        self.holocron.add_holobit("H2", 0b10)
        self.holocron.add_holobit("H3", 0b11)
        self.holocron.create_group("G1", ["H1", "H2"])
        self.holocron.create_group("G2", ["H3"])

    def test_entangle_holobits(self):
        entangled = entangle_holobits(
            [
                self.holocron.holobits["H1"],
                self.holocron.holobits["H2"],
                self.holocron.holobits["H3"],
            ]
        )
        expected = [
            (0b01, 0b10),
            (0b01, 0b11),
            (0b10, 0b11),
        ]
        self.assertEqual(sorted(entangled), sorted(expected))

    def test_entangle_groups(self):
        groups = [self.holocron.groups["G1"], self.holocron.groups["G2"]]
        entangled = entangle_groups(groups)
        expected = [
            (0b01, 0b10),
            (0b01, 0b11),
            (0b10, 0b11),
        ]
        self.assertEqual(sorted(entangled), sorted(expected))

    def test_holocron_entangle_operation(self):
        result = self.holocron.execute_quantum_operation(ENTANGLE, ["G1", "G2"])
        expected = [
            (0b01, 0b10),
            (0b01, 0b11),
            (0b10, 0b11),
        ]
        self.assertEqual(sorted(result), sorted(expected))

    def test_desentangle_holobits(self):
        entangled = entangle_holobits(
            [
                self.holocron.holobits["H1"],
                self.holocron.holobits["H2"],
                self.holocron.holobits["H3"],
            ]
        )
        desentangled = desentangle_holobits(entangled, [(0b01, 0b10)])
        expected = [
            (0b01, 0b11),
            (0b10, 0b11),
        ]
        self.assertEqual(sorted(desentangled), sorted(expected))

    def test_desentangle_instruction(self):
        entangled = entangle_holobits(
            [self.holocron.holobits["H1"], self.holocron.holobits["H2"]]
        )
        result = DESENTANGLE.apply(entangled)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
