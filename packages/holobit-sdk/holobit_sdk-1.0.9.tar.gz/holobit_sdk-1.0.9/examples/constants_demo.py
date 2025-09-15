from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler


def main():
    compiler = HoloLangCompiler()
    program = """
CONSTANTE V = PI/4
CONSTANTE ITER = 2
CREAR H1 (V, V)
PARA ITER {
    SUPERPOSICION H1
}
"""
    resultados = compiler.compilar_y_ejecutar(program)
    print("Resultados:", resultados)


if __name__ == "__main__":
    main()
