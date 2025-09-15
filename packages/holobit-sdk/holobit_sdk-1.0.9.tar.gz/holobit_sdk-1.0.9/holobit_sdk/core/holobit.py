import numpy as np

# Importación diferida para evitar dependencias circulares durante la
# inicialización de módulos.
from .genetic_optimizer import GeneticOptimizer


class Holobit:
    def __init__(self, quarks, antiquarks, spin=0.5):
        """
        Clase para representar un Holobit compuesto por quarks y antiquarks.

        Args:
            quarks: Lista de 6 objetos Quark.
            antiquarks: Lista de 6 objetos Quark (representan antiquarks).
            spin: Valor del spin asociado al Holobit (default: 0.5).
        """
        if len(quarks) != 6 or len(antiquarks) != 6:
            raise ValueError("Un Holobit debe tener exactamente 6 quarks y 6 antiquarks.")
        self.quarks = quarks
        self.antiquarks = antiquarks
        self.spin = spin

    def rotar(self, eje, angulo):
        """
        Rota el Holobit en el eje especificado por un ángulo dado.

        Args:
            eje: Eje de rotación ('x', 'y', 'z').
            angulo: Ángulo de rotación en grados.
        """
        radianes = np.deg2rad(angulo)
        matriz_rotacion = self._crear_matriz_rotacion(eje, radianes)
        for quark in self.quarks + self.antiquarks:
            quark.posicion = np.dot(matriz_rotacion, quark.posicion)

    def _crear_matriz_rotacion(self, eje, radianes):
        """
        Genera una matriz de rotación en 3D.

        Args:
            eje: Eje de rotación ('x', 'y', 'z').
            radianes: Ángulo de rotación en radianes.
        """
        if eje == 'x':
            return np.array([[1, 0, 0],
                             [0, np.cos(radianes), -np.sin(radianes)],
                             [0, np.sin(radianes), np.cos(radianes)]])
        elif eje == 'y':
            return np.array([[np.cos(radianes), 0, np.sin(radianes)],
                             [0, 1, 0],
                             [-np.sin(radianes), 0, np.cos(radianes)]])
        elif eje == 'z':
            return np.array([[np.cos(radianes), -np.sin(radianes), 0],
                             [np.sin(radianes), np.cos(radianes), 0],
                             [0, 0, 1]])
        else:
            raise ValueError("El eje debe ser 'x', 'y' o 'z'.")

    def __repr__(self):
        """Representación legible del Holobit."""
        return f"Holobit(quarks={self.quarks}, antiquarks={self.antiquarks}, spin={self.spin})"

    # ------------------------------------------------------------------
    # API de optimización
    # ------------------------------------------------------------------
    def optimizar(self, gene_bounds, fitness_func, **optimizer_params):
        """Optimiza atributos del ``Holobit`` mediante un algoritmo genético.

        Parameters
        ----------
        gene_bounds: dict
            Nombres de los atributos a optimizar junto con sus límites
            ``(mínimo, máximo)``.
        fitness_func: callable
            Función que recibe un ``Holobit`` y devuelve un valor numérico que
            representa su aptitud. El optimizador maximiza dicho valor.
        **optimizer_params:
            Parámetros opcionales que se pasan a ``GeneticOptimizer`` como
            ``population_size`` o ``generations``.

        Returns
        -------
        HolobitGenome
            El mejor genoma encontrado. Los atributos del ``Holobit`` se
            actualizan en el proceso.
        """

        optimizer = GeneticOptimizer(
            self, gene_bounds=gene_bounds, fitness_func=fitness_func, **optimizer_params
        )
        return optimizer.run()
