from holobit_sdk.multi_level.low_level.low_level_api import LowLevelAPI


class ExecutionUnit:
    """
    Módulo de ejecución de instrucciones ensamblador-holográficas.
    """

    def __init__(self):
        self.api = LowLevelAPI()

    def ejecutar_instruccion(self, instruccion):
        """
        Ejecuta una instrucción en el ensamblador cuántico holográfico.

        Args:
            instruccion (str): Instrucción ensamblador a ejecutar.

        Returns:
            str: Resultado de la ejecución de la instrucción.
        """
        partes = instruccion.split()
        if not partes:
            return "Instrucción vacía."

        comando = partes[0]
        argumentos = partes[1:]

        try:
            return self.api.ejecutar_comando(comando, *argumentos)
        except Exception as e:
            return f"Error en la ejecución: {str(e)}"


# Ejemplo de uso
if __name__ == "__main__":
    executor = ExecutionUnit()
    print(executor.ejecutar_instruccion("ALLOCATE H1 0.1 0.2 0.3"))
    print(executor.ejecutar_instruccion("GET_POSITION H1"))
    print(executor.ejecutar_instruccion("DEALLOCATE H1"))

