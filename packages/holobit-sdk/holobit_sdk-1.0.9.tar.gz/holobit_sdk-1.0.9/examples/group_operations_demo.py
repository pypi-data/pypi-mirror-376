from holobit_sdk.multi_level.high_level.hololang_parser import HoloLangParser
import random


def main():
    parser = HoloLangParser()
    print(parser.interpretar("CREAR H1 (0.1, 0.2, 0.3)"))
    print(parser.interpretar("CREAR H2 (0.4, 0.5, 0.6)"))
    print(parser.interpretar("CREAR_GRUPO G1 (H1, H2)"))
    random.seed(0)
    print(parser.interpretar("APLICAR_GRUPO SUPERPOSICION G1"))
    random.seed(1)
    print(parser.interpretar("APLICAR_GRUPO MEDIR G1"))


if __name__ == "__main__":
    main()
