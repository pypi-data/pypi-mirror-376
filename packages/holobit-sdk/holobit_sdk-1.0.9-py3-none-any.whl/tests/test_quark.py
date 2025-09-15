import unittest
import numpy as np

from holobit_sdk.core.quark import Quark


class TestQuark(unittest.TestCase):
    def test_posicion_float(self):
        quark = Quark(1, 2, 3)
        self.assertTrue(np.issubdtype(quark.posicion.dtype, np.floating))

    def test_repr_incluye_coordenadas(self):
        quark = Quark(1, 2, 3)
        rep = repr(quark)
        self.assertIn("1", rep)
        self.assertIn("2", rep)
        self.assertIn("3", rep)


if __name__ == "__main__":
    unittest.main()
