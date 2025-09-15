import pytest
pytest.importorskip("pennylane")

import unittest
import numpy as np
from holobit_sdk.core.quark import Quark
from holobit_sdk.core.holobit import Holobit
from holobit_sdk.quantum_integration.pennylane_adapter import PennyLaneAdapter


class TestPennylaneAdapter(unittest.TestCase):
    def setUp(self):
        quarks = [Quark(i, i, i) for i in range(6)]
        antiquarks = [Quark(-i, -i, -i) for i in range(6)]
        self.holobit = Holobit(quarks, antiquarks)
        self.adapter = PennyLaneAdapter()

    def test_holobit_to_native(self):
        qnode = self.adapter.holobit_to_native(self.holobit)
        self.assertEqual(len(qnode.device.wires), 12)
        qnode()
        self.assertGreater(len(qnode._tape.operations), 0)

    def test_execute(self):
        qnode = self.adapter.holobit_to_native(self.holobit)
        state = self.adapter.execute(qnode)
        self.assertEqual(len(state), 2 ** 12)
        np.testing.assert_allclose(state[0], 1.0)


if __name__ == '__main__':
    unittest.main()
