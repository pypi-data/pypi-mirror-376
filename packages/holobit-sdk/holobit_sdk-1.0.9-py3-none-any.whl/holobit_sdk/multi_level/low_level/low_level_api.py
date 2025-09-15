from holobit_sdk.multi_level.low_level.memory_manager import MemoryManager
from holobit_sdk.multi_level.low_level.structure import HoloStructure


class LowLevelAPI:
    """
    API de Bajo Nivel para interactuar con el Ensamblador Cuántico Holográfico.
    """

    def __init__(self):
        self.memory = MemoryManager()
        self.structures = {}

    def ejecutar_comando(self, comando, *args):
        """
        Ejecuta un comando ensamblador de bajo nivel.

        Args:
            comando (str): Nombre del comando a ejecutar.
            *args: Argumentos adicionales según el comando.

        Returns:
            str: Resultado de la ejecución del comando.
        """
        if comando == "ALLOCATE":
            holobit_id, x, y, z = args
            self.memory.allocate(holobit_id, (float(x), float(y), float(z)))
            return f"Holobit {holobit_id} asignado en ({x}, {y}, {z})."

        elif comando == "DEALLOCATE":
            holobit_id = args[0]
            self.memory.deallocate(holobit_id)
            return f"Holobit {holobit_id} liberado."

        elif comando == "GET_POSITION":
            holobit_id = args[0]
            position = self.memory.get_position(holobit_id)
            return f"Posición de {holobit_id}: {position}"

        elif comando == "CREATE_STRUCT":
            struct_id = args[0]
            holobit_ids = args[1:]
            self.structures[struct_id] = HoloStructure(holobit_ids, self.memory)
            return f"Estructura {struct_id} creada con {len(holobit_ids)} holobits."

        elif comando == "TRANSFORM_STRUCT":
            struct_id = args[0]
            operacion = args[1]
            if struct_id not in self.structures:
                return f"Estructura {struct_id} no existe."
            estructura = self.structures[struct_id]
            if operacion == "ROTATE":
                eje = args[2]
                angulo = args[3]
                estructura.rotate(eje, float(angulo))
            elif operacion == "TRANSLATE":
                dx, dy, dz = map(float, args[2:5])
                estructura.translate((dx, dy, dz))
            elif operacion == "SCALE":
                factor = args[2]
                estructura.scale(float(factor))
            else:
                return "Operación desconocida."
            return f"Estructura {struct_id} transformada."

        else:
            return "Comando desconocido."


# Ejemplo de uso
if __name__ == "__main__":
    api = LowLevelAPI()
    print(api.ejecutar_comando("ALLOCATE", "H1", 0.1, 0.2, 0.3))
    print(api.ejecutar_comando("GET_POSITION", "H1"))
    print(api.ejecutar_comando("DEALLOCATE", "H1"))

