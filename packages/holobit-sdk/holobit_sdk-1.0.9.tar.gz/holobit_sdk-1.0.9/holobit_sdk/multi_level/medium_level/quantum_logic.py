import numpy as np


class QuantumLogic:
    """
    Implementación de operadores y estructuras de control cuántico para Holobits.
    """

    @staticmethod
    def puerta_hadamard(estado):
        """
        Aplica la puerta Hadamard a un estado cuántico.

        Args:
            estado (np.array): Vector de estado cuántico.

        Returns:
            np.array: Estado resultante tras aplicar Hadamard.
        """
        H = (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]])
        return np.dot(H, estado)

    @staticmethod
    def entrelazar(estado1, estado2):
        """
        Aplica entrelazamiento cuántico entre dos estados.

        Args:
            estado1 (np.array): Primer estado cuántico.
            estado2 (np.array): Segundo estado cuántico.

        Returns:
            np.array: Estado entrelazado resultante.
        """
        return np.kron(estado1, estado2)

    @staticmethod
    def medir_estado(estado):
        """
        Realiza una medición en un estado cuántico.

        Args:
            estado (np.array): Estado cuántico a medir.

        Returns:
            int: Resultado de la medición (0 o 1).
        """
        norma = np.linalg.norm(estado)
        if not np.isclose(norma, 1):
            estado = estado / norma

        probabilidades = np.abs(estado) ** 2
        return np.random.choice([0, 1], p=probabilidades)


# Ejemplo de uso
if __name__ == "__main__":
    estado_0 = np.array([1, 0])  # Estado |0>
    estado_1 = np.array([0, 1])  # Estado |1>

    print("Aplicación de Hadamard:", QuantumLogic.puerta_hadamard(estado_0))
    print("Entrelazamiento:", QuantumLogic.entrelazar(estado_0, estado_1))
    print("Medición:", QuantumLogic.medir_estado(QuantumLogic.puerta_hadamard(estado_0)))

