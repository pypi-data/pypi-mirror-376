import unittest

from holobit_sdk.quantum_holocron.core.holocron import Holocron
from holobit_sdk.core.quark import Quark
from holobit_sdk.core.holobit import Holobit
from holobit_sdk.core.interactions import cambiar_spin, sincronizar_spin


def _crear_holobit(spin):
    quarks = [Quark(i, i + 1, i + 2) for i in range(6)]
    antiquarks = [Quark(i + 3, i + 4, i + 5) for i in range(6)]
    return Holobit(quarks, antiquarks, spin=spin)


class TestHolocronInteractions(unittest.TestCase):
    def setUp(self):
        self.h1 = _crear_holobit(0.0)
        self.h2 = _crear_holobit(1.0)
        self.holocron = Holocron()
        self.holocron.add_holobit("H1", self.h1)
        self.holocron.add_holobit("H2", self.h2)
        self.holocron.create_group("G1", ["H1", "H2"])

    def test_cambiar_spin_en_grupo(self):
        self.holocron.apply_interaction(cambiar_spin, "G1", 2.0)
        self.assertEqual(self.h1.spin, 2.0)
        self.assertEqual(self.h2.spin, 2.0)

    def test_sincronizar_spin_en_grupo(self):
        self.h1.spin = 0.0
        self.h2.spin = 1.0
        self.holocron.apply_interaction(sincronizar_spin, "G1")
        self.assertEqual(self.h1.spin, self.h2.spin)
        self.assertAlmostEqual(self.h1.spin, 0.5)


if __name__ == "__main__":
    unittest.main()
