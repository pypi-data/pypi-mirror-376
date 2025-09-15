"""Demostración de nuevas instrucciones y macros de Hololang."""
from holobit_sdk.assembler.virtual_machine import AssemblerVM


def build_program():
    return [
        "#macro PREPARAR_PAR a b",
        "CREAR {a} (0.1, 0.2, 0.3)",
        "CREAR {b} (0.4, 0.5, 0.6)",
        "SUPERPOSICION {a}",
        "SUPERPOSICION {b}",
        "ENTRELAZAR {a} {b}",
        "#endmacro",
        "PREPARAR_PAR H1 H2",
        "GRUPO G1 {H1, H2}",
        "MEASURE H1",
        "SI H1",
        "    ROT H2 z 45",
        "SINO",
        "    ROT H2 z 180",
        "FIN",
    ]


def main():
    vm = AssemblerVM()
    vm.run_program(build_program())
    print("Mediciones registradas:", vm.parser.measurements)


if __name__ == "__main__":
    main()
