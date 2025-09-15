import pytest
pytest.importorskip("qiskit")

import unittest
import numpy as np
from holobit_sdk.core.quark import Quark
from holobit_sdk.core.holobit import Holobit
from holobit_sdk.quantum_integration.qiskit_adapter import QiskitAdapter


class TestQiskitAdapter(unittest.TestCase):
    def setUp(self):
        quarks = [Quark(i, i, i) for i in range(6)]
        antiquarks = [Quark(-i, -i, -i) for i in range(6)]
        self.holobit = Holobit(quarks, antiquarks)
        self.adapter = QiskitAdapter()

    def test_holobit_to_native(self):
        circuit = self.adapter.holobit_to_native(self.holobit)
        self.assertEqual(circuit.num_qubits, 12)
        self.assertGreater(len(circuit.data), 0)

    def test_execute(self):
        circuit = self.adapter.holobit_to_native(self.holobit)
        state = self.adapter.execute(circuit)
        self.assertEqual(len(state), 2 ** 12)
        np.testing.assert_allclose(state.data[0], 1.0)


if __name__ == '__main__':
    unittest.main()
