"""Demostración del uso de FUNC y CALL en el ensamblador Holobit."""
from holobit_sdk.assembler.virtual_machine import AssemblerVM


def build_program():
    return [
        "FUNC construir_h1",
        "CREAR Q1 (0.0, 0.1, 0.2)",
        "CREAR Q2 (0.3, 0.4, 0.5)",
        "CREAR Q3 (0.6, 0.7, 0.8)",
        "CREAR Q4 (0.9, 1.0, 1.1)",
        "CREAR Q5 (1.2, 1.3, 1.4)",
        "CREAR Q6 (1.5, 1.6, 1.7)",
        "CREAR H1 {Q1, Q2, Q3, Q4, Q5, Q6}",
        "ENDFUNC",
        "CALL construir_h1",
        "ROT H1 z 45",
    ]


def main():
    vm = AssemblerVM()
    vm.run_program(build_program())
    print("Holobits construidos:", list(vm.parser.holobits.keys()))


if __name__ == "__main__":
    main()
