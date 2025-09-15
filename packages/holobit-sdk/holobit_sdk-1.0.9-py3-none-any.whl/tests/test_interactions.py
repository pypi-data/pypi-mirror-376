import unittest
import numpy as np

from holobit_sdk.core.quark import Quark
from holobit_sdk.core.holobit import Holobit
from holobit_sdk.core import interactions


class TestInteractions(unittest.TestCase):
    def _crear_holobit(self, spin=0.5, desplazamiento=0):
        quarks = [Quark(2 + desplazamiento, -2, 3) for _ in range(6)]
        antiquarks = [Quark(-3, 4, -5) for _ in range(6)]
        return Holobit(quarks, antiquarks, spin=spin)

    def test_confinar_quarks_limita_posiciones(self):
        hb = self._crear_holobit()
        interactions.confinar_quarks(hb, limite=1.0)
        for q in hb.quarks + hb.antiquarks:
            self.assertTrue(np.all(q.posicion <= 1.0))
            self.assertTrue(np.all(q.posicion >= -1.0))

    def test_cambiar_spin_modifica_valor(self):
        hb = self._crear_holobit()
        interactions.cambiar_spin(hb, 1.0)
        self.assertEqual(hb.spin, 1.0)

    def test_sincronizar_spin_promedio(self):
        hb1 = self._crear_holobit(spin=1.0)
        hb2 = self._crear_holobit(spin=0.0, desplazamiento=1)
        interactions.sincronizar_spin([hb1, hb2])
        self.assertAlmostEqual(hb1.spin, 0.5)
        self.assertEqual(hb1.spin, hb2.spin)


if __name__ == "__main__":
    unittest.main()
