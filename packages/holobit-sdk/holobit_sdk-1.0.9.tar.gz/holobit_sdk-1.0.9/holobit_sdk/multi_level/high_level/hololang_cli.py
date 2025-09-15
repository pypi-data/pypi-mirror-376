import argparse
import sys
from pathlib import Path

from holobit_sdk.multi_level.high_level.compiler import HoloLangCompiler


def main() -> int:
    """Punto de entrada del CLI para ejecutar código HoloLang."""
    parser = argparse.ArgumentParser(
        description="Ejecuta código HoloLang utilizando el compilador integrado"
    )
    parser.add_argument(
        "-f",
        "--file",
        help="Ruta de un archivo con instrucciones HoloLang",
    )
    parser.add_argument(
        "-c",
        "--code",
        action="append",
        help="Línea de código HoloLang; usa varias veces para múltiples líneas",
    )
    parser.add_argument(
        "--arch",
        default="x86",
        help="Arquitectura de destino (x86, ARM, RISC-V, c, cpp, rust, go)",
    )
    args = parser.parse_args()

    compiler = HoloLangCompiler(args.arch)
    lines = []

    if args.file:
        file_path = Path(args.file)
        if not file_path.is_file():
            print(f"Archivo no encontrado: {file_path}", file=sys.stderr)
            return 1
        content = file_path.read_text(encoding="utf-8")
        lines.extend(l.strip() for l in content.splitlines() if l.strip())

    if args.code:
        lines.extend(l.strip() for l in args.code if l.strip())

    if not lines:
        print("Debes proporcionar --file o --code", file=sys.stderr)
        return 1

    for line in lines:
        result = compiler.compilar_y_ejecutar(line)
        print(result)

    return 0


if __name__ == "__main__":
    sys.exit(main())
