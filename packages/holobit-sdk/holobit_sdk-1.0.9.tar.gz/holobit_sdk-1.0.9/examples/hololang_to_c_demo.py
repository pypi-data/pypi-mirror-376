from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler

def main():
    """Ejemplo de traducción de HoloLang a código C."""
    program = """
    SI 1 {
        IMPRIMIR H1
    }
    """
    compiler = HoloLangCompiler("c")
    codigo_c = compiler.compilar_y_ejecutar(program)
    print(codigo_c)

if __name__ == "__main__":
    main()
