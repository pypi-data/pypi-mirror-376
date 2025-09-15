import pytest
pytest.importorskip("qutip")

import unittest
import numpy as np
from holobit_sdk.core.quark import Quark
from holobit_sdk.core.holobit import Holobit
from holobit_sdk.quantum_integration.qutip_adapter import QutipAdapter


class TestQutipAdapter(unittest.TestCase):
    def setUp(self):
        quarks = [Quark(i, i, i) for i in range(6)]
        antiquarks = [Quark(-i, -i, -i) for i in range(6)]
        self.holobit = Holobit(quarks, antiquarks)
        self.adapter = QutipAdapter()

    def test_holobit_to_native(self):
        state = self.adapter.holobit_to_native(self.holobit)
        self.assertEqual(state.shape[0], 2 ** 12)

    def test_execute(self):
        state = self.adapter.holobit_to_native(self.holobit)
        result = self.adapter.execute(state)
        self.assertEqual(result.shape[0], 2 ** 12)
        np.testing.assert_allclose(result.full()[0, 0], 1.0)


if __name__ == '__main__':
    unittest.main()
