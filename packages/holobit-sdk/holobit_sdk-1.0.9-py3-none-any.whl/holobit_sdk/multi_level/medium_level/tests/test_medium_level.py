import unittest
import numpy as np
from holobit_sdk.multi_level.medium_level.holographic_api import HolographicAPI
from holobit_sdk.multi_level.medium_level.vector_processor import VectorProcessor
from holobit_sdk.multi_level.medium_level.quantum_logic import QuantumLogic


class TestMidLevel(unittest.TestCase):
    """
    Pruebas unitarias para el Nivel Medio del SDK Holobit.
    """

    def setUp(self):
        self.api = HolographicAPI()

    def test_crear_holobit(self):
        """ Prueba la creación de un Holobit. """
        resultado = self.api.crear_holobit("H1", 0.1, 0.2, 0.3)
        self.assertEqual(resultado, "Holobit H1 asignado en (0.1, 0.2, 0.3).")

    def test_obtener_posicion(self):
        """ Prueba la obtención de la posición de un Holobit. """
        self.api.crear_holobit("H2", 0.4, 0.5, 0.6)
        resultado = self.api.obtener_posicion("H2")
        self.assertEqual(resultado, "Posición de H2: (0.4, 0.5, 0.6)")

    def test_eliminar_holobit(self):
        """ Prueba la eliminación de un Holobit. """
        self.api.crear_holobit("H3", 0.7, 0.8, 0.9)
        resultado = self.api.eliminar_holobit("H3")
        self.assertEqual(resultado, "Holobit H3 liberado.")

    def test_suma_vectores(self):
        """ Prueba la suma de dos vectores tridimensionales. """
        resultado = VectorProcessor.suma_vectores((1, 2, 3), (4, 5, 6))
        self.assertEqual(resultado, (5, 7, 9))

    def test_producto_escalar(self):
        """ Prueba el producto escalar entre dos vectores. """
        resultado = VectorProcessor.producto_escalar((1, 2, 3), (4, 5, 6))
        self.assertEqual(resultado, 32.0)

    def test_norma_vector(self):
        """ Prueba la norma de un vector. """
        resultado = VectorProcessor.norma_vector((3, 4, 0))
        self.assertEqual(resultado, 5.0)

    def test_producto_vectorial(self):
        """ Prueba el producto vectorial entre dos vectores. """
        resultado = VectorProcessor.producto_vectorial((1, 0, 0), (0, 1, 0))
        self.assertEqual(resultado, (0, 0, 1))

    def test_normalizar_vector(self):
        """ Prueba la normalización de un vector. """
        resultado = VectorProcessor.normalizar_vector((0, 3, 4))
        self.assertEqual(resultado, (0.0, 0.6, 0.8))

    def test_proyeccion_vector(self):
        """ Prueba la proyección de un vector sobre otro. """
        resultado = VectorProcessor.proyeccion_vector((2, 2, 0), (1, 0, 0))
        self.assertEqual(resultado, (2.0, 0.0, 0.0))

    def test_puerta_hadamard(self):
        """ Prueba la aplicación de la puerta Hadamard a un estado cuántico. """
        estado_0 = np.array([1, 0])
        resultado = QuantumLogic.puerta_hadamard(estado_0)
        esperado = np.array([1 / np.sqrt(2), 1 / np.sqrt(2)])
        np.testing.assert_array_almost_equal(resultado, esperado)

    def test_entrelazar(self):
        """ Prueba el entrelazamiento cuántico entre dos estados. """
        estado_0 = np.array([1, 0])
        estado_1 = np.array([0, 1])
        resultado = QuantumLogic.entrelazar(estado_0, estado_1)
        esperado = np.kron(estado_0, estado_1)
        np.testing.assert_array_almost_equal(resultado, esperado)

    def test_medir_estado(self):
        """ Prueba la medición de un estado cuántico. """
        estado = QuantumLogic.puerta_hadamard(np.array([1, 0]))
        resultado = QuantumLogic.medir_estado(estado)
        self.assertIn(resultado, [0, 1])

    def test_medir_estado_no_normalizado(self):
        """Prueba la medición con un estado no normalizado."""
        estado_no_normalizado = np.array([2, 0])
        resultado = QuantumLogic.medir_estado(estado_no_normalizado)
        self.assertEqual(resultado, 0)


if __name__ == "__main__":
    unittest.main()
