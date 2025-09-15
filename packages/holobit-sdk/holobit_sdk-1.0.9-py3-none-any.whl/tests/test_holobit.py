import unittest
from holobit_sdk.core.quark import Quark
from holobit_sdk.core.holobit import Holobit


class TestHolobit(unittest.TestCase):
    def test_repr_incluye_listas(self):
        quarks = [Quark(i, i + 1, i + 2) for i in range(6)]
        hb = Holobit(quarks, list(reversed(quarks)))
        rep = repr(hb)
        self.assertIn("quarks", rep)
        self.assertIn("antiquarks", rep)
        self.assertIn("spin", rep)
        self.assertIn("Holobit", rep)

    def test_spin_por_defecto_y_personalizado(self):
        quarks = [Quark(i, i + 1, i + 2) for i in range(6)]
        hb_defecto = Holobit(quarks, list(reversed(quarks)))
        self.assertEqual(hb_defecto.spin, 0.5)
        hb_custom = Holobit(quarks, list(reversed(quarks)), spin=1.0)
        self.assertEqual(hb_custom.spin, 1.0)


if __name__ == "__main__":
    unittest.main()
