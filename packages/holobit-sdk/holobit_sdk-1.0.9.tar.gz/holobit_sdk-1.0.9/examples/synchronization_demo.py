from holobit_sdk.multi_level.high_level.hololang_parser import HoloLangParser
import random


def main():
    parser = HoloLangParser()
    parser.interpretar("CREAR H1 (0.1, 0.2, 0.3)")
    parser.interpretar("CREAR H2 (0.4, 0.5, 0.6)")
    parser.interpretar("CREAR H3 (0.7, 0.8, 0.9)")
    parser.interpretar("CREAR H4 (1.0, 1.1, 1.2)")
    parser.interpretar("CREAR_GRUPO G1 (H1, H2)")
    parser.interpretar("CREAR_GRUPO G2 (H3, H4)")
    random.seed(0)
    resultados = parser.interpretar("SINCRONIZAR G1 G2")
    print("Resultados sincronizados:", resultados)
    print("Mediciones registradas:", parser.measurements)


if __name__ == "__main__":
    main()
