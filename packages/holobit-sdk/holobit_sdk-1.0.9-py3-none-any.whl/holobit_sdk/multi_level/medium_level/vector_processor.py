import numpy as np
from typing import Optional, Sequence


class VectorProcessor:
    """
    Procesador de operaciones vectoriales para Holobits en el entorno cuántico-holográfico.
    """

    @staticmethod
    def suma_vectores(v1, v2):
        """
        Suma dos vectores tridimensionales.

        Args:
            v1 (tuple): Primer vector (x, y, z).
            v2 (tuple): Segundo vector (x, y, z).

        Returns:
            tuple: Resultado de la suma.
        """
        return tuple(np.add(v1, v2))

    @staticmethod
    def producto_escalar(v1, v2):
        """
        Calcula el producto escalar entre dos vectores tridimensionales.

        Args:
            v1 (tuple): Primer vector (x, y, z).
            v2 (tuple): Segundo vector (x, y, z).

        Returns:
            float: Resultado del producto escalar.
        """
        return float(np.dot(v1, v2))

    @staticmethod
    def norma_vector(v):
        """
        Calcula la norma de un vector tridimensional.

        Args:
            v (tuple): Vector (x, y, z).

        Returns:
            float: Norma del vector.
        """
        return float(np.linalg.norm(v))

    @staticmethod
    def producto_vectorial(v1, v2):
        """Calcula el producto vectorial entre dos vectores tridimensionales.

        Args:
            v1 (tuple): Primer vector (x, y, z).
            v2 (tuple): Segundo vector (x, y, z).

        Returns:
            tuple: Resultado del producto vectorial.
        """
        return tuple(np.cross(v1, v2))

    @staticmethod
    def normalizar_vector(v):
        """Normaliza un vector tridimensional.

        Args:
            v (tuple): Vector (x, y, z).

        Returns:
            tuple: Vector normalizado. Si la norma es cero, devuelve el mismo
            vector.
        """
        norma = np.linalg.norm(v)
        if norma == 0:
            return tuple(v)
        return tuple(np.array(v) / norma)

    @staticmethod
    def proyeccion_vector(v1, v2):
        """Calcula la proyección de ``v1`` sobre ``v2``.

        Args:
            v1 (tuple): Vector a proyectar.
            v2 (tuple): Vector base de la proyección.

        Returns:
            tuple: Vector resultante de la proyección.
        """
        v2_array = np.array(v2)
        denom = np.dot(v2_array, v2_array)
        if denom == 0:
            return (0.0, 0.0, 0.0)
        factor = np.dot(v1, v2_array) / denom
        return tuple(factor * v2_array)

    @staticmethod
    def to_quantum_state(
        vector: Sequence[float], reduction: str = "pca", backend: Optional[str] = None
    ):
        """Convierte un vector clásico en un estado cuántico.

        Parameters
        ----------
        vector: sequence of float
            Vector a transformar.
        reduction: str
            Método de reducción de dimensionalidad a utilizar: ``'pca'`` o
            ``'svd'``.
        backend: str, optional
            Si se especifica, se genera un circuito para el backend indicado
            (``'qiskit'`` o ``'cirq'``). Si es ``None`` se devuelve únicamente el
            vector de amplitudes normalizado.

        Returns
        -------
        numpy.ndarray o backend circuit
            Amplitudes normalizadas o circuito cuántico según el parámetro
            ``backend``.
        """
        from .vector_quantization import encode_vector, amplitudes_to_circuit

        amplitudes = encode_vector(vector, reduction)
        if backend is None:
            return amplitudes
        return amplitudes_to_circuit(amplitudes, backend=backend)


# Ejemplo de uso
if __name__ == "__main__":
    v1 = (1.0, 2.0, 3.0)
    v2 = (4.0, 5.0, 6.0)

    print("Suma de vectores:", VectorProcessor.suma_vectores(v1, v2))
    print("Producto escalar:", VectorProcessor.producto_escalar(v1, v2))
    print("Norma del vector v1:", VectorProcessor.norma_vector(v1))

