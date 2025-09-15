import numpy as np


class Quark:
    def __init__(self, *coords, estado=None):
        """Representa un quark en un espacio de ``n`` dimensiones.

        La firma acepta coordenadas variables. Para mantener compatibilidad
        con la API previa, si se proporcionan más de tres valores y ``estado``
        no se especifica, el último elemento se interpreta como el estado
        cuántico.

        Parameters
        ----------
        *coords:
            Coordenadas del quark. Si no se especifica ninguna se asume el
            origen ``(0, 0, 0)``.
        estado:
            Estado cuántico del quark como vector (default: ``|0⟩``).
        """

        if (
            estado is None
            and len(coords) >= 4
            and isinstance(coords[-1], (list, tuple, np.ndarray))
            and np.asarray(coords[-1]).shape == (2,)
        ):
            *coords, estado = coords
        if not coords:
            coords = (0.0, 0.0, 0.0)
        self.posicion = np.array(coords, dtype=float)
        self.estado = estado if estado is not None else np.array([1, 0])  # Estado inicial |0⟩

    def aplicar_puerta(self, puerta):
        """
        Aplica una puerta cuántica al estado del quark.

        Args:
            puerta: Matriz de la puerta cuántica.
        """
        self.estado = np.dot(puerta, self.estado)

    def __repr__(self):
        """Representación legible del quark."""
        pos = ', '.join(f"{coord}" for coord in self.posicion)
        estado = ', '.join(str(v) for v in self.estado)
        return f"Quark(posicion=[{pos}], estado=[{estado}])"
