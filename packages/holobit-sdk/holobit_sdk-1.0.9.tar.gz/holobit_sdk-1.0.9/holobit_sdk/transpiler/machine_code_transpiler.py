# Archivo: transpiler/machine_code_transpiler.py
import argparse
from pathlib import Path
import sys


class MachineCodeTranspiler:
    """
    Transpilador de instrucciones holográficas a código máquina con optimización avanzada.
    """

    def __init__(self, architecture="x86"):
        """
        Inicializa el transpilador con la arquitectura deseada y mejoras de rendimiento.

        Args:
            architecture (str): Arquitectura objetivo ("x86", "ARM", "RISC-V").
        """
        self.architecture = architecture
        self.instruction_maps = {
            "x86": {
                "ALLOCATE": "MOV",
                "DEALLOCATE": "FREE",
                "GET_POSITION": "READ_POS",
                "ROTATE": "ROT",
                "LINK": "LINK",
                "UNLINK": "UNLINK",
                "JUMP": "JMP",
                "COMPARE": "CMP",
                "SI": "CMP",
                "SINO": "JMP",
                "MIENTRAS": "LOOP",
                "ADD": "ADD",
                "SUB": "SUB",
                "MULT": "MUL",
                "DIV": "DIV",
                "PUSH": "PUSH",
                "POP": "POP",
                "CREATE_STRUCT": "CSTRUCT",
                "TRANSFORM_STRUCT": "TSTRUCT",
                "SUPERPOS": "QSUPER",
                "MEDIR": "QMEASURE",
                "ENTANGLE": "QENTANGLE",
                "TELETRANSPORTAR": "TPORT",
                "COLAPSAR": "COLL",
                "FUSIONAR": "FUSE",
                "CREAR_FRACTAL_ND": "CFRACT_ND",
                "DINAMICA_FRACTAL": "FRACT_DYN",
                "DENSIDAD_MORFO": "MORPH_DENS"
            },
            "ARM": {
                "ALLOCATE": "LDR",
                "DEALLOCATE": "STR",
                "GET_POSITION": "LDR_POS",
                "ROTATE": "ROT_ARM",
                "LINK": "CONNECT",
                "UNLINK": "DISCONNECT",
                "JUMP": "B",
                "COMPARE": "CMP_ARM",
                "SI": "CMP_ARM",
                "SINO": "B",
                "MIENTRAS": "LOOP",
                "ADD": "ADD_ARM",
                "SUB": "SUB_ARM",
                "MULT": "MUL_ARM",
                "DIV": "DIV_ARM",
                "PUSH": "PUSH_ARM",
                "POP": "POP_ARM",
                "CREATE_STRUCT": "CSTRUCT_ARM",
                "TRANSFORM_STRUCT": "TSTRUCT_ARM",
                "SUPERPOS": "QSUPER_ARM",
                "MEDIR": "QMEASURE_ARM",
                "ENTANGLE": "QENTANGLE_ARM",
                "TELETRANSPORTAR": "TPORT_ARM",
                "COLAPSAR": "COLL_ARM",
                "FUSIONAR": "FUSE_ARM",
                "CREAR_FRACTAL_ND": "CFRACT_ND_ARM",
                "DINAMICA_FRACTAL": "FRACT_DYN_ARM",
                "DENSIDAD_MORFO": "MORPH_DENS_ARM"
            },
            "RISC-V": {
                "ALLOCATE": "LW",
                "DEALLOCATE": "SW",
                "GET_POSITION": "LW_POS",
                "ROTATE": "ROT_RV",
                "LINK": "RV_LINK",
                "UNLINK": "RV_UNLINK",
                "JUMP": "JAL",
                "COMPARE": "BNE",
                "SI": "BNE",
                "SINO": "JAL",
                "MIENTRAS": "LOOP",
                "ADD": "ADD_RV",
                "SUB": "SUB_RV",
                "MULT": "MUL_RV",
                "DIV": "DIV_RV",
                "PUSH": "PUSH_RV",
                "POP": "POP_RV",
                "CREATE_STRUCT": "CSTRUCT_RV",
                "TRANSFORM_STRUCT": "TSTRUCT_RV",
                "SUPERPOS": "QSUPER_RV",
                "MEDIR": "QMEASURE_RV",
                "ENTANGLE": "QENTANGLE_RV",
                "TELETRANSPORTAR": "TPORT_RV",
                "COLAPSAR": "COLL_RV",
                "FUSIONAR": "FUSE_RV",
                "CREAR_FRACTAL_ND": "CFRACT_ND_RV",
                "DINAMICA_FRACTAL": "FRACT_DYN_RV",
                "DENSIDAD_MORFO": "MORPH_DENS_RV"
            }
        }

        # Tabla de registros utilizados para optimización
        self.registers_in_use = set()
        # Seguimiento de registros colapsados para evitar redundancias
        self.collapsed_registers = set()

    def transpile(self, holographic_instruction):
        """
        Transpila una instrucción holográfica a su equivalente en código máquina optimizado.

        Args:
            holographic_instruction (str): La instrucción holográfica original.

        Returns:
            str: Instrucción traducida a código máquina optimizado según la arquitectura.
        """
        try:
            partes = holographic_instruction.split()
            if not partes:
                return "Instrucción vacía."

            comando_holografico = partes[0]
            argumentos = " ".join(partes[1:])

            instruction_map = self.instruction_maps.get(self.architecture, {})
            comando_maquina = instruction_map.get(comando_holografico)
            if not comando_maquina:
                return f"Instrucción holográfica desconocida para {self.architecture}: {comando_holografico}"

            # Optimización: reuso de registros
            if comando_holografico in ["ADD", "SUB", "MULT", "DIV"]:
                regs = argumentos.split()
                if len(regs) >= 2:
                    if regs[0] in self.registers_in_use:
                        return f"{comando_maquina} {regs[0]}, {regs[1]} ; Registro reutilizado"
                    else:
                        self.registers_in_use.add(regs[0])
                        return f"{comando_maquina} {regs[0]}, {regs[1]} ; Registro registrado y reutilizado"

            # Optimización avanzada: eliminar redundancias
            if comando_holografico in ["ADD", "SUB", "MULT", "DIV"] and argumentos.split()[0] == argumentos.split()[1]:
                return f"CLEAR {argumentos.split()[0]}"

            # Optimización: eliminación de instrucciones innecesarias
            if comando_holografico == "COMPARE" and len(argumentos.split()) == 2:
                arg1, arg2 = argumentos.split()
                if arg1 == arg2:
                    return "NOP"

            # Optimización: eliminación de MOV redundantes
            if comando_holografico == "ALLOCATE" and argumentos.split()[0] == argumentos.split()[1]:
                return "NOP"  # No es necesario mover un valor a sí mismo

            # Optimización: conversión de PUSH/POP en bloques para reducir accesos a memoria
            if comando_holografico == "PUSH" and len(argumentos.split()) > 1:
                return f"PUSH_MULTI {argumentos}"
            if comando_holografico == "POP" and len(argumentos.split()) > 1:
                return f"POP_MULTI {argumentos}"

            # Procesamiento y optimización de nuevas instrucciones
            if comando_holografico == "TELETRANSPORTAR":
                regs = argumentos.split()
                if len(regs) >= 2 and regs[0] == regs[1]:
                    return "NOP"
                return f"{comando_maquina} {argumentos}"

            if comando_holografico == "COLAPSAR":
                reg = argumentos.strip()
                if not reg or reg in self.collapsed_registers:
                    return "NOP"
                self.collapsed_registers.add(reg)
                return f"{comando_maquina} {reg}"

            if comando_holografico == "FUSIONAR":
                regs = argumentos.split()
                if len(set(regs)) < len(regs):
                    return "NOP"
                return f"{comando_maquina} {argumentos}"

            if comando_holografico == "CREAR_FRACTAL_ND":
                params = argumentos.split()
                if len(params) != 1:
                    return "Error: CREAR_FRACTAL_ND requiere un argumento de dimensión"
                return f"{comando_maquina} {params[0]}"

            if comando_holografico == "DINAMICA_FRACTAL":
                params = argumentos.split()
                if len(params) != 3:
                    return "Error: DINAMICA_FRACTAL requiere dimensión, pasos y dt"
                dim, pasos, dt = params
                return f"{comando_maquina} {dim}, {pasos}, {dt}"

            if comando_holografico == "DENSIDAD_MORFO":
                params = argumentos.split()
                if len(params) != 1:
                    return "Error: DENSIDAD_MORFO requiere un argumento de dimensión"
                return f"{comando_maquina} {params[0]}"

            return f"{comando_maquina} {argumentos}"

        except Exception as e:
            return f"Error en la transpilación: {str(e)}"


def main():
    """Punto de entrada para el transpilador desde la línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Transpila instrucciones holográficas a código máquina"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Ruta del archivo con instrucciones holográficas",
    )
    parser.add_argument(
        "--arch",
        default="x86",
        help="Arquitectura de destino (x86, ARM, RISC-V)",
    )
    args = parser.parse_args()

    file_path = Path(args.input)
    if not file_path.is_file():
        print(f"Archivo no encontrado: {file_path}", file=sys.stderr)
        sys.exit(1)

    transpiler = MachineCodeTranspiler(args.arch)
    with file_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            print(transpiler.transpile(line))


if __name__ == "__main__":
    main()

