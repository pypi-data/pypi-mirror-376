from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler

programa = """
CREAR H1 (0.1, 0.2, 0.3)
CREAR_ESTRUCTURA G1 {H1}

FUNCION medir_superposicion(h) {
    SUPERPOSICION h
    MEDIR h
}

LLAMAR medir_superposicion(G1)
"""

if __name__ == "__main__":
    compilador = HoloLangCompiler()
    resultados = compilador.compilar_y_ejecutar(programa)
    for r in resultados:
        print(r)
