from ..low_level.low_level_api import LowLevelAPI
from .vector_processor import VectorProcessor


class HolographicAPI:
    """API de Nivel Medio para la manipulación de Holobits.

    Esta capa ofrece un conjunto de operaciones que abstraen la lógica de
    bajo nivel. Además de gestionar la memoria holográfica, incluye
    utilidades para operaciones vectoriales mediante :class:`VectorProcessor`,
    como ``producto_vectorial``, ``normalizar_vector`` y ``proyeccion_vector``.
    """

    def __init__(self):
        self.low_level_api = LowLevelAPI()

    def crear_holobit(self, holobit_id, x, y, z):
        """
        Crea un nuevo Holobit en la memoria holográfica.

        Args:
            holobit_id (str): Identificador único del Holobit.
            x (float): Coordenada X.
            y (float): Coordenada Y.
            z (float): Coordenada Z.

        Returns:
            str: Mensaje de confirmación.
        """
        return self.low_level_api.ejecutar_comando("ALLOCATE", holobit_id, x, y, z)

    def obtener_posicion(self, holobit_id):
        """
        Obtiene la posición de un Holobit en el espacio holográfico.

        Args:
            holobit_id (str): Identificador del Holobit.

        Returns:
            str: Coordenadas del Holobit.
        """
        return self.low_level_api.ejecutar_comando("GET_POSITION", holobit_id)

    def eliminar_holobit(self, holobit_id):
        """
        Elimina un Holobit de la memoria holográfica.

        Args:
            holobit_id (str): Identificador del Holobit.

        Returns:
            str: Mensaje de confirmación.
        """
        return self.low_level_api.ejecutar_comando("DEALLOCATE", holobit_id)

    # --- Operaciones vectoriales de nivel medio ---

    def producto_vectorial(self, v1, v2):
        """Wrapper del :func:`VectorProcessor.producto_vectorial`."""
        return VectorProcessor.producto_vectorial(v1, v2)

    def normalizar_vector(self, v):
        """Wrapper del :func:`VectorProcessor.normalizar_vector`."""
        return VectorProcessor.normalizar_vector(v)

    def proyeccion_vector(self, v1, v2):
        """Wrapper del :func:`VectorProcessor.proyeccion_vector`."""
        return VectorProcessor.proyeccion_vector(v1, v2)


# Ejemplo de uso
if __name__ == "__main__":
    api = HolographicAPI()
    print(api.crear_holobit("H1", 0.1, 0.2, 0.3))
    print(api.obtener_posicion("H1"))
    print(api.eliminar_holobit("H1"))

