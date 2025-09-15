from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler



class HoloLangDebugger:
    """
    Depurador para el lenguaje de programación holográfico.
    """

    def __init__(self):
        self.compiler = HoloLangCompiler()
        self.break_points = set()

    def agregar_punto_de_ruptura(self, linea):
        """
        Agrega un punto de ruptura en una línea específica.

        Args:
            linea (int): Número de línea donde se coloca el punto de ruptura.
        """
        self.break_points.add(linea)

    def depurar(self, codigo):
        """
        Ejecuta el código línea por línea permitiendo detenerse en los puntos de ruptura.

        Args:
            codigo (list): Lista de líneas de código en HoloLang.
        """
        for i, linea in enumerate(codigo, start=1):
            if i in self.break_points:
                input(f"[DEBUG] Pausado en la línea {i}: {linea}. Presiona Enter para continuar...")
            resultado = self.compiler.compilar_y_ejecutar(linea)
            print(f"Línea {i}: {resultado}")


# Ejemplo de uso
if __name__ == "__main__":
    debugger = HoloLangDebugger()
    debugger.agregar_punto_de_ruptura(2)
    codigo = [
        "CREAR H1 (0.1, 0.2, 0.3)",
        "IMPRIMIR H1",
        "EJECUTAR ALLOCATE H2 0.4 0.5 0.6"
    ]
    debugger.depurar(codigo)

