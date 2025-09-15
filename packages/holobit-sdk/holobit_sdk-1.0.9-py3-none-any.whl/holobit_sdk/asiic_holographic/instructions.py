class ASIICInstructions:
    """
    Definición de instrucciones del ASIIC Holográfico.
    """

    def __init__(self):
        self.instrucciones = {}

    def agregar_instruccion(self, nombre, funcion):
        """
        Registra una nueva instrucción en el ASIIC Holográfico.

        Args:
            nombre (str): Nombre de la instrucción.
            funcion (callable): Función que implementa la instrucción.
        """
        self.instrucciones[nombre] = funcion

    def ejecutar_instruccion(self, nombre, *args, **kwargs):
        """
        Ejecuta una instrucción registrada en el ASIIC Holográfico.

        Args:
            nombre (str): Nombre de la instrucción a ejecutar.
            *args: Argumentos posicionales para la instrucción.
            **kwargs: Argumentos clave-valor para la instrucción.

        Returns:
            Resultado de la ejecución de la instrucción.
        """
        if nombre not in self.instrucciones:
            raise ValueError(f"Instrucción desconocida: {nombre}")
        return self.instrucciones[nombre](*args, **kwargs)


# Ejemplo de uso
if __name__ == "__main__":
    asiic = ASIICInstructions()

    # Definir una instrucción de ejemplo

    def rotar_holobit(holobit, eje, angulo):
        return f"Rotando Holobit en el eje {eje} con ángulo {angulo} grados"

    asiic.agregar_instruccion("ROTAR", rotar_holobit)

    # Ejecutar la instrucción
    resultado = asiic.ejecutar_instruccion("ROTAR", "H1", "z", 90)
    print(resultado)
