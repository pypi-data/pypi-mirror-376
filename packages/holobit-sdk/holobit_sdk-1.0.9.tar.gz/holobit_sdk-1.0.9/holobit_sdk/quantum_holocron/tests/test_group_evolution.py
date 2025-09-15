import unittest
import random

from holobit_sdk.quantum_holocron.core.holocron import Holocron


class TestGroupEvolution(unittest.TestCase):
    def setUp(self):
        self.holocron = Holocron()
        for i in range(1, 6):
            self.holocron.add_holobit(f"H{i}", i)

    def _ids_in_group(self, gid):
        return {hid for hid, hb in self.holocron.holobits.items() if hb in self.holocron.groups[gid]}

    def test_evolve_groups_maximize(self):
        self.holocron.create_group("G", ["H1", "H2"])

        def fitness(group):
            return sum(group)

        random.seed(0)
        self.holocron.evolve_groups(fitness, generations=5, population_size=10)
        self.assertEqual(self._ids_in_group("G"), {"H4", "H5"})

    def test_evolve_groups_minimize(self):
        self.holocron.create_group("G", ["H4", "H5"])

        def fitness(group):
            return -sum(group)

        random.seed(0)
        self.holocron.evolve_groups(fitness, generations=5, population_size=10)
        self.assertEqual(self._ids_in_group("G"), {"H1", "H2"})


if __name__ == "__main__":
    unittest.main()
